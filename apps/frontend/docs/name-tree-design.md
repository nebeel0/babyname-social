# Name Tree Feature - Design Document

## Overview

A multi-dimensional tree visualization system for exploring baby names based on different organizational strategies (prefix similarity, origin, phonetic patterns, etc.).

## Goals

1. **Discover Similar Names**: Help users find names with similar characteristics
2. **Explore Patterns**: Visualize naming patterns across different dimensions
3. **Interactive Navigation**: Allow users to drill down through tree structures
4. **Multiple Views**: Support different organizational strategies for the same data

## Use Cases

### Primary Use Cases
- "Show me all names that start with 'Mar-'" (Prefix tree)
- "Show me Italian names and their variations" (Origin tree)
- "Find names that sound similar to 'Emma'" (Phonetic tree)
- "Show me short names (3-4 letters)" (Length-based clustering)

### Secondary Use Cases
- Compare naming patterns across cultures
- Discover name variations and derivatives
- Find names with common roots/meanings
- Explore trending name prefixes

## Data Structures

### 1. Trie/Prefix Tree

**Use Case**: Finding names with common prefixes

```python
# Backend Model
class NameTrieNode:
    prefix: str              # "Mar", "Mari", "Maria"
    is_complete_name: bool   # True if this prefix is also a complete name
    name_id: Optional[int]   # Reference to Name if is_complete_name
    count: int              # Number of names under this prefix
    children: List[NameTrieNode]

# Example structure:
M
├── Ma
│   ├── Mar (123 names)
│   │   ├── Mari (45 names)
│   │   │   ├── Maria ✓ (name_id: 1, 23 names)
│   │   │   ├── Marie ✓ (name_id: 2, 15 names)
│   │   │   └── Mario ✓ (name_id: 3, 7 names)
│   │   └── Mark ✓ (name_id: 4, 78 names)
│   └── Mat (89 names)
│       ├── Matt ✓
│       └── Matthew ✓
└── Mi (234 names)
    ├── Mia ✓
    └── Michael ✓
```

### 2. Origin/Country Tree

**Use Case**: Exploring names by cultural origin

```python
class OriginTreeNode:
    origin: str              # "European", "Italian", etc.
    level: int              # 0=continent, 1=country, 2=region
    name_count: int
    popular_prefixes: List[str]  # Common starting patterns
    children: List[OriginTreeNode]
    names: List[Name]       # Actual names at this level

# Example structure:
European
├── Italian
│   ├── Northern Italian
│   │   ├── Giovanni
│   │   ├── Giuseppe
│   │   └── Maria
│   └── Southern Italian
│       ├── Antonio
│       └── Francesco
├── Greek
│   ├── Alexander
│   └── Sophia
└── Germanic
    ├── Emma
    └── Wilhelm
```

### 3. Phonetic Similarity Tree

**Use Case**: Finding names that sound alike

```python
class PhoneticTreeNode:
    phonetic_pattern: str   # Soundex, Metaphone, or custom
    sound_group: str        # "soft vowel start", "hard consonant"
    names: List[Name]
    similar_patterns: List[PhoneticTreeNode]

# Example groupings:
Soft-A-Start
├── Emma (ˈɛmə)
├── Ava (ˈeɪvə)
└── Anna (ˈænə)

Hard-K-Start
├── Kate
├── Kyle
└── Carl
```

### 4. Hierarchical Clustering Tree

**Use Case**: Multi-attribute similarity

```python
class ClusterTreeNode:
    cluster_id: str
    center_name: Name       # Representative name for cluster
    attributes: Dict[str, Any]  # Length, origin, popularity, etc.
    similarity_score: float
    names: List[Name]
    subclusters: List[ClusterTreeNode]

# Example:
Short-Popular-Modern
├── Ava
├── Mia
├── Leo
└── Zoe

Classic-Traditional
├── William
├── Elizabeth
├── James
└── Catherine
```

## Database Schema

### Core Tables

```sql
-- Existing names table (enhanced)
CREATE TABLE names (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    gender VARCHAR(20),
    origin VARCHAR(100),
    meaning TEXT,
    popularity INTEGER,
    phonetic_code VARCHAR(50),  -- NEW: Soundex/Metaphone
    length_category VARCHAR(20), -- NEW: "short", "medium", "long"
    style_tags TEXT[],           -- NEW: ["modern", "classic", "trendy"]
    created_at TIMESTAMP DEFAULT NOW()
);

-- Trie/Prefix index
CREATE TABLE name_prefix_tree (
    id SERIAL PRIMARY KEY,
    prefix VARCHAR(50) NOT NULL,
    prefix_length INTEGER NOT NULL,
    is_complete_name BOOLEAN DEFAULT FALSE,
    name_id INTEGER REFERENCES names(id),
    child_count INTEGER DEFAULT 0,
    total_descendants INTEGER DEFAULT 0,
    parent_id INTEGER REFERENCES name_prefix_tree(id),
    INDEX idx_prefix (prefix),
    INDEX idx_prefix_length (prefix, prefix_length)
);

-- Origin hierarchy
CREATE TABLE origin_hierarchy (
    id SERIAL PRIMARY KEY,
    origin_name VARCHAR(100) NOT NULL,
    level INTEGER NOT NULL,  -- 0=continent, 1=country, 2=region
    parent_id INTEGER REFERENCES origin_hierarchy(id),
    name_count INTEGER DEFAULT 0,
    common_prefixes TEXT[]
);

-- Name-to-Origin mapping
CREATE TABLE name_origins (
    name_id INTEGER REFERENCES names(id),
    origin_id INTEGER REFERENCES origin_hierarchy(id),
    PRIMARY KEY (name_id, origin_id)
);

-- Phonetic similarity groups
CREATE TABLE phonetic_groups (
    id SERIAL PRIMARY KEY,
    phonetic_pattern VARCHAR(50) NOT NULL,
    sound_category VARCHAR(50),
    representative_name_id INTEGER REFERENCES names(id)
);

CREATE TABLE name_phonetics (
    name_id INTEGER REFERENCES names(id),
    phonetic_group_id INTEGER REFERENCES phonetic_groups(id),
    similarity_score FLOAT,  -- 0.0 to 1.0
    PRIMARY KEY (name_id, phonetic_group_id)
);

-- Generic clustering for multi-attribute similarity
CREATE TABLE name_clusters (
    id SERIAL PRIMARY KEY,
    cluster_type VARCHAR(50),  -- "style", "length", "popularity"
    cluster_name VARCHAR(100),
    parent_cluster_id INTEGER REFERENCES name_clusters(id),
    attributes JSONB,  -- Flexible metadata
    center_name_id INTEGER REFERENCES names(id)
);

CREATE TABLE name_cluster_members (
    name_id INTEGER REFERENCES names(id),
    cluster_id INTEGER REFERENCES name_clusters(id),
    similarity_score FLOAT,
    PRIMARY KEY (name_id, cluster_id)
);
```

## API Endpoints

### 1. Prefix Tree API

```python
# Get prefix tree starting from a prefix
GET /api/v1/names/tree/prefix?prefix={prefix}&max_depth={depth}

Response:
{
  "prefix": "Mar",
  "count": 123,
  "children": [
    {
      "prefix": "Mari",
      "count": 45,
      "is_name": false,
      "children": [
        {
          "prefix": "Maria",
          "count": 23,
          "is_name": true,
          "name": {
            "id": 1,
            "name": "Maria",
            "origin": "Latin",
            "popularity": 95
          },
          "children": [...]
        }
      ]
    }
  ]
}

# Get all names with a specific prefix
GET /api/v1/names/tree/prefix/{prefix}/names?limit=50&offset=0

Response:
{
  "prefix": "Mar",
  "total_count": 123,
  "names": [
    {"id": 1, "name": "Maria", ...},
    {"id": 2, "name": "Mark", ...},
    ...
  ]
}
```

### 2. Origin Tree API

```python
# Get origin hierarchy
GET /api/v1/names/tree/origin?origin={origin}&max_depth={depth}

Response:
{
  "origin": "European",
  "level": 0,
  "name_count": 1234,
  "children": [
    {
      "origin": "Italian",
      "level": 1,
      "name_count": 456,
      "common_prefixes": ["Gi", "Ma", "An"],
      "children": [
        {
          "origin": "Northern Italian",
          "level": 2,
          "name_count": 200,
          "names": [...]
        }
      ]
    }
  ]
}

# Get names from specific origin
GET /api/v1/names/tree/origin/{origin_id}/names

Response:
{
  "origin": "Italian",
  "total_count": 456,
  "names": [...],
  "sub_origins": [...]
}
```

### 3. Phonetic Similarity API

```python
# Get phonetically similar names
GET /api/v1/names/tree/phonetic?name={name}&threshold=0.8

Response:
{
  "query_name": "Emma",
  "phonetic_code": "EM",
  "similar_groups": [
    {
      "sound_pattern": "soft-vowel-start",
      "names": [
        {
          "id": 1,
          "name": "Ava",
          "similarity": 0.85,
          "phonetic_code": "AV"
        },
        {
          "id": 2,
          "name": "Anna",
          "similarity": 0.82,
          "phonetic_code": "AN"
        }
      ]
    }
  ]
}
```

### 4. Cluster Tree API

```python
# Get clustered names by attributes
GET /api/v1/names/tree/cluster?type={type}&attributes={attrs}

# type: "style", "length", "popularity", "hybrid"
# attributes: JSON filter like {"length": "short", "style": "modern"}

Response:
{
  "cluster_type": "style",
  "clusters": [
    {
      "id": 1,
      "name": "Modern-Short",
      "center_name": {"id": 1, "name": "Mia"},
      "attributes": {
        "avg_length": 3.5,
        "avg_popularity": 85,
        "style": "modern"
      },
      "member_count": 45,
      "members": [
        {"id": 1, "name": "Mia", "similarity": 1.0},
        {"id": 2, "name": "Ava", "similarity": 0.92},
        ...
      ],
      "subclusters": [...]
    }
  ]
}
```

### 5. Search and Navigation

```python
# Search across all tree types
GET /api/v1/names/tree/search?q={query}&tree_types=prefix,origin,phonetic

Response:
{
  "query": "Mar",
  "results": {
    "prefix_matches": {
      "count": 123,
      "preview": [...]
    },
    "origin_matches": {
      "count": 45,
      "preview": [...]
    },
    "phonetic_matches": {
      "count": 12,
      "preview": [...]
    }
  }
}
```

## Frontend Components

### 1. Tree Visualization Component

```dart
// lib/features/names/widgets/name_tree_viewer.dart

class NameTreeViewer extends ConsumerStatefulWidget {
  final TreeType type;  // prefix, origin, phonetic, cluster
  final String? rootId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Interactive tree visualization
    // - Expandable/collapsible nodes
    // - Search within tree
    // - Zoom/pan controls
    // - Node details on hover/click
  }
}

// Tree node widget
class TreeNodeWidget extends StatelessWidget {
  final TreeNode node;
  final int depth;
  final VoidCallback onExpand;

  // Visual:
  // - Circle/box for node
  // - Name count badge
  // - Connection lines
  // - Expand/collapse icon
}
```

### 2. Tree Type Selector

```dart
class TreeTypeSelector extends StatelessWidget {
  final TreeType selected;
  final ValueChanged<TreeType> onChanged;

  // Tabs or pills for:
  // - Prefix Tree
  // - Origin Tree
  // - Sound-Alike
  // - Clusters
}
```

### 3. Tree Controls

```dart
class TreeControls extends StatelessWidget {
  // - Zoom in/out
  // - Fit to screen
  // - Search box
  // - Depth slider
  // - Export/share
}
```

## Visualization Strategies

### Option 1: Collapsible Tree (D3-style)

```
Root
├─┬─ Node A (expand/collapse)
│ ├── Child 1
│ └── Child 2
└─┬─ Node B
  ├── Child 3
  └── Child 4
```

**Pros**: Clear hierarchy, familiar pattern
**Cons**: Can get wide with many children

### Option 2: Radial Tree (Sunburst)

```
        ┌─ Child 3
    ┌─ B ┤
    │   └─ Child 4
Root┤
    │   ┌─ Child 1
    └─ A ┤
        └─ Child 2
```

**Pros**: Space-efficient, beautiful
**Cons**: Hard to read labels at depth

### Option 3: Treemap (Rectangles)

```
┌────────────────────┐
│ Root               │
├──────┬─────────────┤
│ A    │ B           │
├──┬───├──────┬──────┤
│C1│C2 │  C3  │  C4  │
└──┴───┴──────┴──────┘
```

**Pros**: Shows relative sizes well
**Cons**: Harder to see hierarchy

### Recommendation: Start with Collapsible Tree

Use Flutter's `CustomPaint` or a package like `graphview` for the tree layout.

## Implementation Phases

### Phase 1: Prefix Tree (MVP)
- Build trie structure in backend
- Create API endpoints
- Basic tree visualization in Flutter
- Search by prefix

### Phase 2: Origin Tree
- Build origin hierarchy
- Multiple levels of drill-down
- Visual grouping by region

### Phase 3: Phonetic & Clustering
- Implement phonetic algorithms
- Multi-attribute clustering
- Advanced similarity search

### Phase 4: Interactive Features
- Drag-to-pan
- Pinch-to-zoom
- Animated transitions
- Bookmarkable tree states

## Performance Considerations

### Backend Optimizations
1. **Pre-compute trees**: Build trees during database migrations
2. **Materialized views**: Cache common queries
3. **Pagination**: Limit nodes returned per request
4. **Lazy loading**: Load children on-demand

### Frontend Optimizations
1. **Virtual scrolling**: For large lists of names
2. **Memoization**: Cache tree node widgets
3. **Progressive loading**: Show skeleton while loading
4. **Debounced search**: Avoid excessive API calls

## Example Queries

### Building Prefix Tree
```sql
-- Generate all prefixes for a name
WITH RECURSIVE prefixes AS (
  SELECT
    id,
    name,
    substring(name, 1, 1) as prefix,
    1 as prefix_length
  FROM names

  UNION ALL

  SELECT
    p.id,
    p.name,
    substring(p.name, 1, p.prefix_length + 1),
    p.prefix_length + 1
  FROM prefixes p
  WHERE p.prefix_length < length(p.name)
)
INSERT INTO name_prefix_tree (prefix, prefix_length, name_id, is_complete_name)
SELECT DISTINCT
  prefix,
  prefix_length,
  id,
  prefix_length = length(name)
FROM prefixes;
```

### Finding Similar Names (Phonetic)
```sql
SELECT
  n1.name as original,
  n2.name as similar,
  levenshtein(n1.phonetic_code, n2.phonetic_code) as distance
FROM names n1
JOIN names n2 ON n1.id != n2.id
WHERE
  n1.name = 'Emma'
  AND levenshtein(n1.phonetic_code, n2.phonetic_code) <= 2
ORDER BY distance;
```

## Future Enhancements

1. **Name Evolution Trees**: Show historical evolution of names
2. **Popularity Timeline Trees**: Branch by decade of popularity
3. **User Collections**: Personal tree of favorite names
4. **Collaborative Trees**: Share and merge with partner
5. **3D Visualization**: For very large datasets
6. **AI-Powered Clustering**: ML-based similarity detection

## References

- [Trie Data Structure](https://en.wikipedia.org/wiki/Trie)
- [Soundex Algorithm](https://en.wikipedia.org/wiki/Soundex)
- [Hierarchical Clustering](https://en.wikipedia.org/wiki/Hierarchical_clustering)
- [D3 Tree Layouts](https://observablehq.com/@d3/tree)
- [Flutter GraphView Package](https://pub.dev/packages/graphview)
