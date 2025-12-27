# Name Tree - Implementation Plan

## Quick Start: MVP (2-3 days)

### Day 1: Backend - Prefix Tree

**Goal**: Build basic prefix tree functionality

#### Database Migration
```sql
-- Add to next migration
CREATE TABLE name_prefix_tree (
    id SERIAL PRIMARY KEY,
    prefix VARCHAR(50) NOT NULL UNIQUE,
    prefix_length INTEGER NOT NULL,
    name_ids INTEGER[] DEFAULT '{}',  -- Array of name IDs with this prefix
    child_count INTEGER DEFAULT 0,
    total_names INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_prefix (prefix),
    INDEX idx_prefix_length (prefix_length)
);

-- Function to build prefix tree (run once on existing data)
CREATE OR REPLACE FUNCTION build_prefix_tree() RETURNS void AS $$
DECLARE
    name_record RECORD;
    i INTEGER;
    current_prefix VARCHAR;
BEGIN
    -- Clear existing data
    TRUNCATE name_prefix_tree;

    -- For each name, generate all its prefixes
    FOR name_record IN SELECT id, name FROM names LOOP
        FOR i IN 1..LENGTH(name_record.name) LOOP
            current_prefix := SUBSTRING(name_record.name, 1, i);

            -- Insert or update prefix
            INSERT INTO name_prefix_tree (prefix, prefix_length, name_ids, total_names)
            VALUES (current_prefix, i, ARRAY[name_record.id], 1)
            ON CONFLICT (prefix) DO UPDATE
            SET name_ids = array_append(name_prefix_tree.name_ids, name_record.id),
                total_names = name_prefix_tree.total_names + 1;
        END LOOP;
    END LOOP;

    -- Update child counts
    UPDATE name_prefix_tree p1
    SET child_count = (
        SELECT COUNT(*)
        FROM name_prefix_tree p2
        WHERE p2.prefix LIKE p1.prefix || '_'
        AND p2.prefix_length = p1.prefix_length + 1
    );
END;
$$ LANGUAGE plpgsql;

-- Run the build
SELECT build_prefix_tree();
```

#### Backend Endpoints (FastAPI)

```python
# app/api/v1/endpoints/name_tree.py

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter()

class PrefixNode(BaseModel):
    prefix: str
    name_count: int
    child_count: int
    is_complete_name: bool
    names: Optional[List[dict]] = None  # Full name objects if requested
    children: Optional[List['PrefixNode']] = None

class PrefixTreeResponse(BaseModel):
    prefix: str
    total_names: int
    max_depth: int
    root: PrefixNode

@router.get("/tree/prefix", response_model=PrefixTreeResponse)
async def get_prefix_tree(
    prefix: str = Query("", description="Starting prefix (empty for root)"),
    max_depth: int = Query(3, ge=1, le=10),
    include_names: bool = Query(False),
    db: Session = Depends(get_db)
):
    """
    Get prefix tree starting from a given prefix.

    Examples:
    - GET /tree/prefix?prefix=Mar&max_depth=2
    - GET /tree/prefix?prefix=&max_depth=1  (get all first letters)
    """

    # Query for the starting prefix and its children
    start_prefix_length = len(prefix) if prefix else 0

    # Get root node
    if prefix:
        root_query = db.query(NamePrefixTree).filter(
            NamePrefixTree.prefix == prefix
        ).first()

        if not root_query:
            raise HTTPException(status_code=404, detail="Prefix not found")
    else:
        # Get all single-letter prefixes for root
        root_query = None

    # Build tree recursively
    def build_tree(current_prefix: str, current_depth: int, max_depth: int):
        if current_depth > max_depth:
            return None

        # Get node data
        node_data = db.query(NamePrefixTree).filter(
            NamePrefixTree.prefix == current_prefix
        ).first()

        if not node_data:
            return None

        # Get children (prefixes that are one character longer)
        children_query = db.query(NamePrefixTree).filter(
            NamePrefixTree.prefix.like(f"{current_prefix}_"),
            NamePrefixTree.prefix_length == len(current_prefix) + 1
        ).order_by(NamePrefixTree.total_names.desc()).limit(20)

        children = []
        for child_data in children_query:
            child_node = build_tree(child_data.prefix, current_depth + 1, max_depth)
            if child_node:
                children.append(child_node)

        # Optionally include full name objects
        names = None
        if include_names and node_data.name_ids:
            names = db.query(Name).filter(
                Name.id.in_(node_data.name_ids[:10])  # Limit to first 10
            ).all()

        return PrefixNode(
            prefix=node_data.prefix,
            name_count=node_data.total_names,
            child_count=node_data.child_count,
            is_complete_name=any(
                n.name == node_data.prefix for n in (names or [])
            ),
            names=[n.dict() for n in names] if names else None,
            children=children if children else None
        )

    # Build and return tree
    root_node = build_tree(prefix or "", 0, max_depth)

    return PrefixTreeResponse(
        prefix=prefix,
        total_names=root_node.name_count if root_node else 0,
        max_depth=max_depth,
        root=root_node
    )

@router.get("/tree/prefix/{prefix}/names")
async def get_names_by_prefix(
    prefix: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get all complete names that start with a prefix."""

    prefix_data = db.query(NamePrefixTree).filter(
        NamePrefixTree.prefix == prefix
    ).first()

    if not prefix_data:
        raise HTTPException(status_code=404, detail="Prefix not found")

    # Get all names
    total_count = len(prefix_data.name_ids)
    name_ids = prefix_data.name_ids[offset:offset + limit]

    names = db.query(Name).filter(
        Name.id.in_(name_ids)
    ).all()

    return {
        "prefix": prefix,
        "total_count": total_count,
        "limit": limit,
        "offset": offset,
        "names": [n.dict() for n in names]
    }

# Add to app/main.py
app.include_router(
    name_tree_router,
    prefix="/api/v1/names",
    tags=["name-tree"]
)
```

### Day 2: Frontend - Basic Tree UI

#### Install Dependencies

```bash
cd apps/frontend
flutter pub add graphview  # For tree layout algorithms
```

#### Create Tree Models

```dart
// lib/features/names/models/prefix_tree.dart

class PrefixNode {
  final String prefix;
  final int nameCount;
  final int childCount;
  final bool isCompleteName;
  final List<NameRead>? names;
  final List<PrefixNode>? children;

  PrefixNode({
    required this.prefix,
    required this.nameCount,
    required this.childCount,
    required this.isCompleteName,
    this.names,
    this.children,
  });

  factory PrefixNode.fromJson(Map<String, dynamic> json) {
    return PrefixNode(
      prefix: json['prefix'],
      nameCount: json['name_count'],
      childCount: json['child_count'],
      isCompleteName: json['is_complete_name'],
      names: json['names'] != null
          ? (json['names'] as List).map((n) => NameRead.fromJson(n)!).toList()
          : null,
      children: json['children'] != null
          ? (json['children'] as List).map((c) => PrefixNode.fromJson(c)).toList()
          : null,
    );
  }
}

class PrefixTreeResponse {
  final String prefix;
  final int totalNames;
  final int maxDepth;
  final PrefixNode root;

  PrefixTreeResponse({
    required this.prefix,
    required this.totalNames,
    required this.maxDepth,
    required this.root,
  });

  factory PrefixTreeResponse.fromJson(Map<String, dynamic> json) {
    return PrefixTreeResponse(
      prefix: json['prefix'],
      totalNames: json['total_names'],
      maxDepth: json['max_depth'],
      root: PrefixNode.fromJson(json['root']),
    );
  }
}
```

#### Add API Method (OpenAPI will regenerate this, but here's what it will look like)

```dart
// This will be in the generated API after adding endpoint to backend
// For now, create manually in lib/features/names/providers/name_tree_provider.dart

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:frontend/core/providers/api_client_provider.dart';

final prefixTreeProvider = FutureProvider.family<PrefixTreeResponse, String>(
  (ref, prefix) async {
    final apiClient = ref.read(apiClientProvider);

    final response = await apiClient.get(
      '/api/v1/names/tree/prefix',
      queryParameters: {
        'prefix': prefix,
        'max_depth': 3,
        'include_names': false,
      },
    );

    return PrefixTreeResponse.fromJson(response.data);
  },
);

final prefixNamesProvider = FutureProvider.family<List<NameRead>, String>(
  (ref, prefix) async {
    final apiClient = ref.read(apiClientProvider);

    final response = await apiClient.get(
      '/api/v1/names/tree/prefix/$prefix/names',
      queryParameters: {
        'limit': 100,
        'offset': 0,
      },
    );

    return (response.data['names'] as List)
        .map((n) => NameRead.fromJson(n)!)
        .toList();
  },
);
```

#### Create Tree Visualization Widget

```dart
// lib/features/names/widgets/prefix_tree_viewer.dart

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class PrefixTreeViewer extends ConsumerStatefulWidget {
  final String initialPrefix;

  const PrefixTreeViewer({
    Key? key,
    this.initialPrefix = '',
  }) : super(key: key);

  @override
  ConsumerState<PrefixTreeViewer> createState() => _PrefixTreeViewerState();
}

class _PrefixTreeViewerState extends ConsumerState<PrefixTreeViewer> {
  String currentPrefix = '';
  final Set<String> expandedNodes = {};

  @override
  void initState() {
    super.initState();
    currentPrefix = widget.initialPrefix;
  }

  @override
  Widget build(BuildContext context) {
    final treeAsync = ref.watch(prefixTreeProvider(currentPrefix));

    return Column(
      children: [
        // Search/Filter Controls
        _buildControls(),

        // Tree View
        Expanded(
          child: treeAsync.when(
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (err, stack) => Center(child: Text('Error: $err')),
            data: (tree) => _buildTreeView(tree),
          ),
        ),
      ],
    );
  }

  Widget _buildControls() {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              decoration: const InputDecoration(
                labelText: 'Search prefix',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.search),
              ),
              onSubmitted: (value) {
                setState(() => currentPrefix = value);
              },
            ),
          ),
          const SizedBox(width: 16),
          if (currentPrefix.isNotEmpty)
            TextButton.icon(
              icon: const Icon(Icons.clear),
              label: const Text('Clear'),
              onPressed: () {
                setState(() => currentPrefix = '');
              },
            ),
        ],
      ),
    );
  }

  Widget _buildTreeView(PrefixTreeResponse tree) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: _buildNode(tree.root, 0),
    );
  }

  Widget _buildNode(PrefixNode node, int depth) {
    final isExpanded = expandedNodes.contains(node.prefix);
    final hasChildren = (node.children?.isNotEmpty ?? false) || node.childCount > 0;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Node row
        Padding(
          padding: EdgeInsets.only(left: depth * 24.0),
          child: InkWell(
            onTap: hasChildren ? () => _toggleNode(node.prefix) : null,
            child: Container(
              padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 12),
              margin: const EdgeInsets.only(bottom: 4),
              decoration: BoxDecoration(
                color: node.isCompleteName
                    ? Colors.blue.shade50
                    : Colors.grey.shade100,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(
                  color: node.isCompleteName
                      ? Colors.blue.shade200
                      : Colors.grey.shade300,
                ),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  // Expand/collapse icon
                  if (hasChildren)
                    Icon(
                      isExpanded ? Icons.expand_more : Icons.chevron_right,
                      size: 20,
                    ),
                  if (!hasChildren)
                    const SizedBox(width: 20),

                  const SizedBox(width: 8),

                  // Prefix text
                  Text(
                    node.prefix,
                    style: TextStyle(
                      fontWeight: node.isCompleteName
                          ? FontWeight.bold
                          : FontWeight.normal,
                      fontSize: 16,
                    ),
                  ),

                  const SizedBox(width: 12),

                  // Name count badge
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: Colors.blue.shade100,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      '${node.nameCount}',
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.blue.shade900,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),

                  // "See all" button for complete names
                  if (node.isCompleteName) ...[
                    const SizedBox(width: 8),
                    TextButton.icon(
                      icon: const Icon(Icons.list, size: 16),
                      label: const Text('View names', style: TextStyle(fontSize: 12)),
                      onPressed: () => _viewNames(node.prefix),
                      style: TextButton.styleFrom(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
        ),

        // Children (if expanded)
        if (isExpanded && node.children != null)
          ...node.children!.map((child) => _buildNode(child, depth + 1)),
      ],
    );
  }

  void _toggleNode(String prefix) {
    setState(() {
      if (expandedNodes.contains(prefix)) {
        expandedNodes.remove(prefix);
      } else {
        expandedNodes.add(prefix);
      }
    });
  }

  void _viewNames(String prefix) {
    // Navigate to names list for this prefix
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.7,
        maxChildSize: 0.95,
        minChildSize: 0.5,
        expand: false,
        builder: (context, scrollController) {
          return PrefixNamesSheet(prefix: prefix);
        },
      ),
    );
  }
}

// Sheet showing all names with a prefix
class PrefixNamesSheet extends ConsumerWidget {
  final String prefix;

  const PrefixNamesSheet({Key? key, required this.prefix}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final namesAsync = ref.watch(prefixNamesProvider(prefix));

    return Container(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Names starting with "$prefix"',
            style: Theme.of(context).textTheme.headlineSmall,
          ),
          const SizedBox(height: 16),
          Expanded(
            child: namesAsync.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (err, stack) => Text('Error: $err'),
              data: (names) => ListView.builder(
                itemCount: names.length,
                itemBuilder: (context, index) {
                  final name = names[index];
                  return ListTile(
                    title: Text(name.name!),
                    subtitle: Text(name.origin ?? ''),
                    trailing: Text('${name.popularity ?? 0}'),
                    onTap: () {
                      // Show name details
                    },
                  );
                },
              ),
            ),
          ),
        ],
      ),
    );
  }
}
```

#### Add Screen to Navigation

```dart
// lib/features/names/screens/name_tree_screen.dart

class NameTreeScreen extends StatelessWidget {
  const NameTreeScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Name Tree Explorer'),
        actions: [
          IconButton(
            icon: const Icon(Icons.help_outline),
            onPressed: () {
              // Show help dialog
            },
          ),
        ],
      ),
      body: const PrefixTreeViewer(),
    );
  }
}

// Add to lib/main.dart router
GoRoute(
  path: '/names/tree',
  builder: (context, state) => const NameTreeScreen(),
),
```

### Day 3: Testing & Polish

#### Test Data Setup

```python
# Create test script: scripts/generate_tree_test_data.py

import requests

names = [
    "Maria", "Mario", "Marie", "Mark", "Marcus",
    "Emma", "Emily", "Ethan", "Eva", "Ella",
    "Sophia", "Sophie", "Samuel", "Sarah", "Sebastian",
]

for name in names:
    requests.post(
        "http://localhost:8001/api/v1/names",
        json={
            "name": name,
            "gender": "unisex",
            "origin": "Test"
        }
    )

# Rebuild tree
requests.post("http://localhost:8001/api/v1/admin/rebuild-tree")
```

#### Manual Testing Checklist

- [ ] Empty prefix shows all first letters
- [ ] Clicking a node expands/collapses it
- [ ] Complete names are highlighted
- [ ] "View names" button works
- [ ] Search box filters correctly
- [ ] Name counts are accurate
- [ ] Navigation back works
- [ ] Mobile responsive

## Next Steps (Future Enhancements)

### Week 2: Origin Tree
- Build origin hierarchy in database
- Create origin tree endpoints
- Add origin tree visualization

### Week 3: Phonetic Similarity
- Implement Soundex/Metaphone
- Create similarity API
- Build "sounds like" UI

### Week 4: Advanced Features
- Animated tree transitions
- Export/share tree views
- Bookmark favorite trees
- Compare two names side-by-side

## Quick Reference

### API Endpoints
```
GET  /api/v1/names/tree/prefix?prefix={prefix}&max_depth={depth}
GET  /api/v1/names/tree/prefix/{prefix}/names
POST /api/v1/admin/rebuild-tree
```

### Key Files
```
Backend:
- app/models/name_tree.py (new)
- app/api/v1/endpoints/name_tree.py (new)
- migrations/xxx_add_prefix_tree.py (new)

Frontend:
- lib/features/names/models/prefix_tree.dart (new)
- lib/features/names/providers/name_tree_provider.dart (new)
- lib/features/names/widgets/prefix_tree_viewer.dart (new)
- lib/features/names/screens/name_tree_screen.dart (new)
```
