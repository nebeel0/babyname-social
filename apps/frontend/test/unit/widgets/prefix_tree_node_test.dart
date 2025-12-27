import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:frontend/features/names/widgets/prefix_tree_node.dart';
import 'package:frontend/features/names/providers/prefix_tree_provider.dart';
import 'package:frontend/generated/api/lib/api.dart';

void main() {
  group('PrefixTreeNodeWidget', () {
    testWidgets('should display node prefix', (WidgetTester tester) async {
      final node = PrefixNodeRead(
        id: 1,
        prefix: 'test',
        prefixLength: 4,
        isCompleteName: false,
        childCount: 0,
        totalDescendants: 0,
      );

      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: PrefixTreeNodeWidget(
                node: node,
                depth: 0,
              ),
            ),
          ),
        ),
      );

      expect(find.text('test'), findsOneWidget);
    });

    testWidgets('should display NAME badge for complete names',
        (WidgetTester tester) async {
      final node = PrefixNodeRead(
        id: 1,
        prefix: 'test',
        prefixLength: 4,
        isCompleteName: true,
        childCount: 0,
        totalDescendants: 0,
      );

      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: PrefixTreeNodeWidget(
                node: node,
                depth: 0,
              ),
            ),
          ),
        ),
      );

      expect(find.text('NAME'), findsOneWidget);
    });

    testWidgets('should not display NAME badge for non-complete names',
        (WidgetTester tester) async {
      final node = PrefixNodeRead(
        id: 1,
        prefix: 'test',
        prefixLength: 4,
        isCompleteName: false,
        childCount: 0,
        totalDescendants: 0,
      );

      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: PrefixTreeNodeWidget(
                node: node,
                depth: 0,
              ),
            ),
          ),
        ),
      );

      expect(find.text('NAME'), findsNothing);
    });

    testWidgets('should display descendant count',
        (WidgetTester tester) async {
      final node = PrefixNodeRead(
        id: 1,
        prefix: 'test',
        prefixLength: 4,
        isCompleteName: false,
        childCount: 5,
        totalDescendants: 15,
      );

      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: PrefixTreeNodeWidget(
                node: node,
                depth: 0,
              ),
            ),
          ),
        ),
      );

      expect(find.text('15 names'), findsOneWidget);
    });

    testWidgets('should not display descendant count when zero',
        (WidgetTester tester) async {
      final node = PrefixNodeRead(
        id: 1,
        prefix: 'test',
        prefixLength: 4,
        isCompleteName: false,
        childCount: 0,
        totalDescendants: 0,
      );

      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: PrefixTreeNodeWidget(
                node: node,
                depth: 0,
              ),
            ),
          ),
        ),
      );

      expect(find.textContaining('names'), findsNothing);
    });

    testWidgets('should show expand icon when node has children',
        (WidgetTester tester) async {
      final node = PrefixNodeRead(
        id: 1,
        prefix: 'test',
        prefixLength: 4,
        isCompleteName: false,
        childCount: 2,
        totalDescendants: 5,
        children: [
          PrefixNodeRead(
            id: 2,
            prefix: 'testa',
            prefixLength: 5,
            isCompleteName: false,
            childCount: 0,
            totalDescendants: 0,
          ),
        ],
      );

      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: PrefixTreeNodeWidget(
                node: node,
                depth: 0,
              ),
            ),
          ),
        ),
      );

      expect(find.byIcon(Icons.chevron_right), findsOneWidget);
    });

    testWidgets('should expand when tapped on node with children',
        (WidgetTester tester) async {
      final node = PrefixNodeRead(
        id: 1,
        prefix: 'test',
        prefixLength: 4,
        isCompleteName: false,
        childCount: 1,
        totalDescendants: 1,
        children: [
          PrefixNodeRead(
            id: 2,
            prefix: 'testa',
            prefixLength: 5,
            isCompleteName: false,
            childCount: 0,
            totalDescendants: 0,
          ),
        ],
      );

      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: PrefixTreeNodeWidget(
                node: node,
                depth: 0,
              ),
            ),
          ),
        ),
      );

      // Initially collapsed - child not visible
      expect(find.text('testa'), findsNothing);

      // Tap to expand
      await tester.tap(find.text('test'));
      await tester.pumpAndSettle();

      // Now child should be visible
      expect(find.text('testa'), findsOneWidget);
      expect(find.byIcon(Icons.expand_more), findsOneWidget);
    });

    testWidgets('should select node when tapped',
        (WidgetTester tester) async {
      final container = ProviderContainer();

      final node = PrefixNodeRead(
        id: 1,
        prefix: 'test',
        prefixLength: 4,
        isCompleteName: false,
        childCount: 0,
        totalDescendants: 0,
      );

      await tester.pumpWidget(
        UncontrolledProviderScope(
          container: container,
          child: MaterialApp(
            home: Scaffold(
              body: PrefixTreeNodeWidget(
                node: node,
                depth: 0,
              ),
            ),
          ),
        ),
      );

      expect(container.read(selectedNodeProvider), isNull);

      await tester.tap(find.text('test'));
      await tester.pumpAndSettle();

      expect(container.read(selectedNodeProvider), equals('test'));
    });

    testWidgets('should apply indentation based on depth',
        (WidgetTester tester) async {
      final node = PrefixNodeRead(
        id: 1,
        prefix: 'test',
        prefixLength: 4,
        isCompleteName: false,
        childCount: 0,
        totalDescendants: 0,
      );

      // Test depth 0
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: PrefixTreeNodeWidget(
                node: node,
                depth: 0,
              ),
            ),
          ),
        ),
      );

      final containerDepth0 = tester.widget<Container>(
        find.ancestor(
          of: find.text('test'),
          matching: find.byType(Container),
        ).first,
      );

      final paddingDepth0 = containerDepth0.padding as EdgeInsets;
      expect(paddingDepth0.left, equals(8.0)); // depth * 24 + 8 = 0 * 24 + 8

      // Test depth 2
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: PrefixTreeNodeWidget(
                node: node,
                depth: 2,
              ),
            ),
          ),
        ),
      );

      final containerDepth2 = tester.widget<Container>(
        find.ancestor(
          of: find.text('test'),
          matching: find.byType(Container),
        ).first,
      );

      final paddingDepth2 = containerDepth2.padding as EdgeInsets;
      expect(paddingDepth2.left, equals(56.0)); // depth * 24 + 8 = 2 * 24 + 8
    });

    testWidgets('should highlight node when isHighlighted is true',
        (WidgetTester tester) async {
      final node = PrefixNodeRead(
        id: 1,
        prefix: 'test',
        prefixLength: 4,
        isCompleteName: false,
        isHighlighted: true,
        highlightReason: 'prefix_match',
        childCount: 0,
        totalDescendants: 0,
      );

      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: PrefixTreeNodeWidget(
                node: node,
                depth: 0,
              ),
            ),
          ),
        ),
      );

      final container = tester.widget<Container>(
        find.ancestor(
          of: find.text('test'),
          matching: find.byType(Container),
        ).first,
      );

      expect(container.color, isNotNull);
      expect(container.color!.alpha, greaterThan(0));
    });

    testWidgets('should render multiple children when expanded',
        (WidgetTester tester) async {
      // This test validates the JSArray fix - multiple children must be properly converted to List<Widget>
      // NOTE: The JSArray error only occurs on web platform (flutter test --platform chrome)
      // These tests pass on VM but are still valuable for catching the logic
      final node = PrefixNodeRead(
        id: 1,
        prefix: 'a',
        prefixLength: 1,
        isCompleteName: false,
        childCount: 3,
        totalDescendants: 3,
        children: [
          PrefixNodeRead(
            id: 2,
            prefix: 'ab',
            prefixLength: 2,
            isCompleteName: false,
            childCount: 0,
            totalDescendants: 0,
          ),
          PrefixNodeRead(
            id: 3,
            prefix: 'ac',
            prefixLength: 2,
            isCompleteName: true,
            childCount: 0,
            totalDescendants: 0,
          ),
          PrefixNodeRead(
            id: 4,
            prefix: 'ad',
            prefixLength: 2,
            isCompleteName: false,
            childCount: 0,
            totalDescendants: 0,
          ),
        ],
      );

      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: PrefixTreeNodeWidget(
                node: node,
                depth: 0,
              ),
            ),
          ),
        ),
      );

      // Initially collapsed - children not visible
      expect(find.text('ab'), findsNothing);
      expect(find.text('ac'), findsNothing);
      expect(find.text('ad'), findsNothing);

      // Tap to expand
      await tester.tap(find.text('a'));
      await tester.pumpAndSettle();

      // All children should be visible
      expect(find.text('ab'), findsOneWidget);
      expect(find.text('ac'), findsOneWidget);
      expect(find.text('ad'), findsOneWidget);

      // Should have 4 total PrefixTreeNodeWidget (1 parent + 3 children)
      expect(find.byType(PrefixTreeNodeWidget), findsNWidgets(4));
    });

    testWidgets('should render nested children (multi-level tree)',
        (WidgetTester tester) async {
      // This test validates the JSArray fix for nested structures
      final node = PrefixNodeRead(
        id: 1,
        prefix: 'a',
        prefixLength: 1,
        isCompleteName: false,
        childCount: 2,
        totalDescendants: 4,
        children: [
          PrefixNodeRead(
            id: 2,
            prefix: 'ab',
            prefixLength: 2,
            isCompleteName: false,
            childCount: 2,
            totalDescendants: 2,
            children: [
              PrefixNodeRead(
                id: 3,
                prefix: 'aba',
                prefixLength: 3,
                isCompleteName: true,
                childCount: 0,
                totalDescendants: 0,
              ),
              PrefixNodeRead(
                id: 4,
                prefix: 'abb',
                prefixLength: 3,
                isCompleteName: false,
                childCount: 0,
                totalDescendants: 0,
              ),
            ],
          ),
          PrefixNodeRead(
            id: 5,
            prefix: 'ac',
            prefixLength: 2,
            isCompleteName: true,
            childCount: 0,
            totalDescendants: 0,
          ),
        ],
      );

      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: PrefixTreeNodeWidget(
                node: node,
                depth: 0,
              ),
            ),
          ),
        ),
      );

      // Initially collapsed - children not visible
      expect(find.text('ab'), findsNothing);
      expect(find.text('ac'), findsNothing);

      // Expand first level
      await tester.tap(find.text('a'));
      await tester.pumpAndSettle();

      // First level children visible, second level not
      expect(find.text('ab'), findsOneWidget);
      expect(find.text('ac'), findsOneWidget);
      expect(find.text('aba'), findsNothing);
      expect(find.text('abb'), findsNothing);

      // Expand second level
      await tester.tap(find.text('ab'));
      await tester.pumpAndSettle();

      // All nodes should be visible
      expect(find.text('a'), findsOneWidget);
      expect(find.text('ab'), findsOneWidget);
      expect(find.text('ac'), findsOneWidget);
      expect(find.text('aba'), findsOneWidget);
      expect(find.text('abb'), findsOneWidget);

      // Should have 5 total PrefixTreeNodeWidget (all nodes)
      expect(find.byType(PrefixTreeNodeWidget), findsNWidgets(5));
    });

    testWidgets('should handle many children without JSArray error',
        (WidgetTester tester) async {
      // Create a node with many children to ensure .toList() works correctly
      final children = List.generate(
        10,
        (i) => PrefixNodeRead(
          id: i + 2,
          prefix: 'a${String.fromCharCode(97 + i)}',
          prefixLength: 2,
          isCompleteName: false,
          childCount: 0,
          totalDescendants: 0,
        ),
      );

      final node = PrefixNodeRead(
        id: 1,
        prefix: 'a',
        prefixLength: 1,
        isCompleteName: false,
        childCount: 10,
        totalDescendants: 10,
        children: children,
      );

      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: PrefixTreeNodeWidget(
                node: node,
                depth: 0,
              ),
            ),
          ),
        ),
      );

      // Tap to expand
      await tester.tap(find.text('a'));
      await tester.pumpAndSettle();

      // Should have 11 total PrefixTreeNodeWidget (1 parent + 10 children)
      expect(find.byType(PrefixTreeNodeWidget), findsNWidgets(11));

      // Verify a few children are visible
      expect(find.text('aa'), findsOneWidget);
      expect(find.text('ae'), findsOneWidget);
      expect(find.text('aj'), findsOneWidget);
    });
  });

  group('PrefixTreeViewer', () {
    testWidgets('should show loading indicator initially',
        (WidgetTester tester) async {
      await tester.pumpWidget(
        ProviderScope(
          child: const MaterialApp(
            home: Scaffold(
              body: PrefixTreeViewer(),
            ),
          ),
        ),
      );

      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });

    testWidgets('should show empty state when no nodes',
        (WidgetTester tester) async {
      final mockResponse = PrefixTreeResponse(
        prefix: '',
        totalNodes: 0,
        totalNames: 0,
        maxDepth: 3,
        filtersApplied: {},
        nodes: [],
      );

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            prefixTreeDataProvider.overrideWith(
              (ref) => Future.value(mockResponse),
            ),
          ],
          child: const MaterialApp(
            home: Scaffold(
              body: PrefixTreeViewer(),
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('No names found'), findsOneWidget);
      expect(find.text('Try adjusting your filters'), findsOneWidget);
      expect(find.byIcon(Icons.search_off), findsOneWidget);
    });

    testWidgets('should display tree nodes when data is available',
        (WidgetTester tester) async {
      final mockResponse = PrefixTreeResponse(
        prefix: 'a',
        totalNodes: 2,
        totalNames: 1,
        maxDepth: 3,
        filtersApplied: {},
        nodes: [
          PrefixNodeRead(
            id: 1,
            prefix: 'a',
            prefixLength: 1,
            isCompleteName: false,
            childCount: 1,
            totalDescendants: 1,
          ),
          PrefixNodeRead(
            id: 2,
            prefix: 'ab',
            prefixLength: 2,
            isCompleteName: true,
            childCount: 0,
            totalDescendants: 0,
          ),
        ],
      );

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            prefixTreeDataProvider.overrideWith(
              (ref) => Future.value(mockResponse),
            ),
          ],
          child: const MaterialApp(
            home: Scaffold(
              body: PrefixTreeViewer(),
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('2 nodes'), findsOneWidget);
      expect(find.text('1 complete names'), findsOneWidget);
      expect(find.byType(PrefixTreeNodeWidget), findsNWidgets(2));
    });

    testWidgets('should display error state when loading fails',
        (WidgetTester tester) async {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            prefixTreeDataProvider.overrideWith(
              (ref) => Future.error(Exception('Network error')),
            ),
          ],
          child: const MaterialApp(
            home: Scaffold(
              body: PrefixTreeViewer(),
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('Error loading tree'), findsOneWidget);
      expect(find.byIcon(Icons.error_outline), findsOneWidget);
      expect(find.byIcon(Icons.refresh), findsOneWidget);
    });

    testWidgets('should render many top-level nodes without JSArray error',
        (WidgetTester tester) async {
      // This test validates the JSArray fix in PrefixTreeViewer
      // The ListView children mapping needs <Widget> type parameter and .toList()
      // NOTE: JSArray error only occurs on web platform (flutter test --platform chrome)
      final nodes = List.generate(
        10,
        (i) => PrefixNodeRead(
          id: i + 1,
          prefix: String.fromCharCode(97 + i), // a, b, c, ...
          prefixLength: 1,
          isCompleteName: false,
          childCount: 0,
          totalDescendants: i + 1,
        ),
      );

      final mockResponse = PrefixTreeResponse(
        prefix: '',
        totalNodes: 10,
        totalNames: 0,
        maxDepth: 1,
        filtersApplied: {},
        nodes: nodes,
      );

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            prefixTreeDataProvider.overrideWith(
              (ref) => Future.value(mockResponse),
            ),
          ],
          child: const MaterialApp(
            home: Scaffold(
              body: PrefixTreeViewer(),
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Should display all 10 nodes
      expect(find.byType(PrefixTreeNodeWidget), findsNWidgets(10));

      // Verify a few specific nodes are visible
      expect(find.text('a'), findsOneWidget);
      expect(find.text('e'), findsOneWidget);
      expect(find.text('j'), findsOneWidget);

      // Should show correct counts
      expect(find.text('10 nodes'), findsOneWidget);
    });
  });
}
