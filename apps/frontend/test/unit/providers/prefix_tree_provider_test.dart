import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:frontend/features/names/providers/prefix_tree_provider.dart';
import 'package:frontend/generated/api/lib/api.dart';
import 'package:frontend/core/providers/api_client_provider.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';

import 'prefix_tree_provider_test.mocks.dart';

@GenerateMocks([PrefixTreeApi])
void main() {
  // These tests don't need container - they test a plain Dart class
  group('PrefixTreeFilters', () {
    test('should create with default values', () {
      const filters = PrefixTreeFilters();

      expect(filters.prefix, equals(''));
      expect(filters.maxDepth, equals(3));
      expect(filters.gender, isNull);
      expect(filters.originCountry, isNull);
      expect(filters.minPopularity, isNull);
      expect(filters.maxPopularity, isNull);
      expect(filters.highlightPrefixes, isEmpty);
      expect(filters.highlightNameIds, isEmpty);
      expect(filters.includeNames, isFalse);
    });

    test('should create with custom values', () {
      const filters = PrefixTreeFilters(
        prefix: 'a',
        maxDepth: 5,
        gender: 'male',
        originCountry: 'USA',
        minPopularity: 10.0,
        maxPopularity: 100.0,
        highlightPrefixes: ['ab', 'ac'],
        highlightNameIds: [1, 2, 3],
        includeNames: true,
      );

      expect(filters.prefix, equals('a'));
      expect(filters.maxDepth, equals(5));
      expect(filters.gender, equals('male'));
      expect(filters.originCountry, equals('USA'));
      expect(filters.minPopularity, equals(10.0));
      expect(filters.maxPopularity, equals(100.0));
      expect(filters.highlightPrefixes, equals(['ab', 'ac']));
      expect(filters.highlightNameIds, equals([1, 2, 3]));
      expect(filters.includeNames, isTrue);
    });

    test('copyWith should preserve existing values', () {
      const original = PrefixTreeFilters(
        prefix: 'a',
        maxDepth: 5,
        gender: 'male',
      );

      final copied = original.copyWith();

      expect(copied.prefix, equals('a'));
      expect(copied.maxDepth, equals(5));
      expect(copied.gender, equals('male'));
    });

    test('copyWith should update specified values', () {
      const original = PrefixTreeFilters(
        prefix: 'a',
        maxDepth: 3,
        gender: 'male',
      );

      final updated = original.copyWith(
        prefix: 'b',
        gender: () => 'female',
      );

      expect(updated.prefix, equals('b'));
      expect(updated.maxDepth, equals(3)); // Preserved
      expect(updated.gender, equals('female'));
    });

    test('copyWith should allow clearing nullable fields', () {
      const original = PrefixTreeFilters(
        gender: 'male',
        originCountry: 'USA',
      );

      final updated = original.copyWith(
        gender: () => null,
        originCountry: () => null,
      );

      expect(updated.gender, isNull);
      expect(updated.originCountry, isNull);
    });
  });

  // Provider tests that need container and mocks
  group('Provider Tests', () {
    late MockPrefixTreeApi mockApi;
    late ProviderContainer container;

    setUp(() {
      mockApi = MockPrefixTreeApi();
    });

    tearDown(() {
      container.dispose();
    });

    group('prefixTreeFiltersProvider', () {
      test('should have default filters initially', () {
        container = ProviderContainer();

      final filters = container.read(prefixTreeFiltersProvider);

      expect(filters.prefix, equals(''));
      expect(filters.maxDepth, equals(3));
      expect(filters.includeNames, isFalse);
    });

    test('should allow updating filters', () {
      container = ProviderContainer();

      const newFilters = PrefixTreeFilters(
        prefix: 'test',
        maxDepth: 5,
      );

      container.read(prefixTreeFiltersProvider.notifier).state = newFilters;

      final updatedFilters = container.read(prefixTreeFiltersProvider);

      expect(updatedFilters.prefix, equals('test'));
      expect(updatedFilters.maxDepth, equals(5));
    });
  });

  group('prefixTreeDataProvider', () {
    test('should fetch prefix tree data successfully', () async {
      // Create mock response
      final mockResponse = PrefixTreeResponse(
        prefix: 'a',
        totalNodes: 10,
        totalNames: 5,
        maxDepth: 3,
        filtersApplied: {},
        nodes: [
          PrefixNodeRead(
            id: 1,
            prefix: 'a',
            prefixLength: 1,
            isCompleteName: false,
            childCount: 5,
            totalDescendants: 10,
          ),
        ],
      );

      when(mockApi.getPrefixTreeApiV1PrefixTreeGet(
        prefix: anyNamed('prefix'),
        maxDepth: anyNamed('maxDepth'),
        gender: anyNamed('gender'),
        originCountry: anyNamed('originCountry'),
        minPopularity: anyNamed('minPopularity'),
        maxPopularity: anyNamed('maxPopularity'),
        highlightPrefixes: anyNamed('highlightPrefixes'),
        highlightNameIds: anyNamed('highlightNameIds'),
        includeNames: anyNamed('includeNames'),
      )).thenAnswer((_) async => mockResponse);

      container = ProviderContainer(
        overrides: [
          prefixTreeApiProvider.overrideWithValue(mockApi),
        ],
      );

      final result = await container.read(prefixTreeDataProvider.future);

      expect(result.prefix, equals('a'));
      expect(result.totalNodes, equals(10));
      expect(result.totalNames, equals(5));
      expect(result.nodes.length, equals(1));
      expect(result.nodes.first.prefix, equals('a'));

      verify(mockApi.getPrefixTreeApiV1PrefixTreeGet(
        prefix: '',
        maxDepth: 3,
        gender: null,
        originCountry: null,
        minPopularity: null,
        maxPopularity: null,
        highlightPrefixes: '',
        highlightNameIds: '',
        includeNames: false,
      )).called(1);
    });

    test('should apply filters when fetching data', () async {
      final mockResponse = PrefixTreeResponse(
        prefix: 'ab',
        totalNodes: 5,
        totalNames: 2,
        maxDepth: 5,
        filtersApplied: {'gender': 'male'},
        nodes: [],
      );

      when(mockApi.getPrefixTreeApiV1PrefixTreeGet(
        prefix: anyNamed('prefix'),
        maxDepth: anyNamed('maxDepth'),
        gender: anyNamed('gender'),
        originCountry: anyNamed('originCountry'),
        minPopularity: anyNamed('minPopularity'),
        maxPopularity: anyNamed('maxPopularity'),
        highlightPrefixes: anyNamed('highlightPrefixes'),
        highlightNameIds: anyNamed('highlightNameIds'),
        includeNames: anyNamed('includeNames'),
      )).thenAnswer((_) async => mockResponse);

      container = ProviderContainer(
        overrides: [
          prefixTreeApiProvider.overrideWithValue(mockApi),
          prefixTreeFiltersProvider.overrideWith((ref) {
            return const PrefixTreeFilters(
              prefix: 'ab',
              maxDepth: 5,
              gender: 'male',
              highlightPrefixes: ['abc', 'abd'],
              highlightNameIds: [1, 2],
            );
          }),
        ],
      );

      await container.read(prefixTreeDataProvider.future);

      verify(mockApi.getPrefixTreeApiV1PrefixTreeGet(
        prefix: 'ab',
        maxDepth: 5,
        gender: 'male',
        originCountry: null,
        minPopularity: null,
        maxPopularity: null,
        highlightPrefixes: 'abc,abd',
        highlightNameIds: '1,2',
        includeNames: false,
      )).called(1);
    });

    test('should throw exception when API returns null', () async {
      when(mockApi.getPrefixTreeApiV1PrefixTreeGet(
        prefix: anyNamed('prefix'),
        maxDepth: anyNamed('maxDepth'),
        gender: anyNamed('gender'),
        originCountry: anyNamed('originCountry'),
        minPopularity: anyNamed('minPopularity'),
        maxPopularity: anyNamed('maxPopularity'),
        highlightPrefixes: anyNamed('highlightPrefixes'),
        highlightNameIds: anyNamed('highlightNameIds'),
        includeNames: anyNamed('includeNames'),
      )).thenAnswer((_) async => null);

      container = ProviderContainer(
        overrides: [
          prefixTreeApiProvider.overrideWithValue(mockApi),
        ],
      );

      expect(
        () => container.read(prefixTreeDataProvider.future),
        throwsA(isA<Exception>()),
      );
    });

    test('should throw exception when API throws error', () async {
      when(mockApi.getPrefixTreeApiV1PrefixTreeGet(
        prefix: anyNamed('prefix'),
        maxDepth: anyNamed('maxDepth'),
        gender: anyNamed('gender'),
        originCountry: anyNamed('originCountry'),
        minPopularity: anyNamed('minPopularity'),
        maxPopularity: anyNamed('maxPopularity'),
        highlightPrefixes: anyNamed('highlightPrefixes'),
        highlightNameIds: anyNamed('highlightNameIds'),
        includeNames: anyNamed('includeNames'),
      )).thenThrow(Exception('Network error'));

      container = ProviderContainer(
        overrides: [
          prefixTreeApiProvider.overrideWithValue(mockApi),
        ],
      );

      expect(
        () => container.read(prefixTreeDataProvider.future),
        throwsA(isA<Exception>()),
      );
    });
  });

  group('expandedNodesProvider', () {
    test('should have empty set initially', () {
      container = ProviderContainer();

      final expandedNodes = container.read(expandedNodesProvider);

      expect(expandedNodes, isEmpty);
    });

    test('should allow adding nodes', () {
      container = ProviderContainer();

      container.read(expandedNodesProvider.notifier).state = {'a', 'ab', 'abc'};

      final expandedNodes = container.read(expandedNodesProvider);

      expect(expandedNodes, equals({'a', 'ab', 'abc'}));
      expect(expandedNodes.contains('a'), isTrue);
      expect(expandedNodes.contains('ab'), isTrue);
      expect(expandedNodes.contains('abc'), isTrue);
    });

    test('should allow removing nodes', () {
      container = ProviderContainer();

      container.read(expandedNodesProvider.notifier).state = {'a', 'ab', 'abc'};

      final updatedNodes = Set<String>.from(container.read(expandedNodesProvider));
      updatedNodes.remove('ab');
      container.read(expandedNodesProvider.notifier).state = updatedNodes;

      final expandedNodes = container.read(expandedNodesProvider);

      expect(expandedNodes, equals({'a', 'abc'}));
      expect(expandedNodes.contains('ab'), isFalse);
    });
  });

  group('selectedNodeProvider', () {
    test('should be null initially', () {
      container = ProviderContainer();

      final selectedNode = container.read(selectedNodeProvider);

      expect(selectedNode, isNull);
    });

    test('should allow selecting a node', () {
      container = ProviderContainer();

      container.read(selectedNodeProvider.notifier).state = 'abc';

      final selectedNode = container.read(selectedNodeProvider);

      expect(selectedNode, equals('abc'));
    });

    test('should allow clearing selection', () {
      container = ProviderContainer();

      container.read(selectedNodeProvider.notifier).state = 'abc';
      expect(container.read(selectedNodeProvider), equals('abc'));

      container.read(selectedNodeProvider.notifier).state = null;

      final selectedNode = container.read(selectedNodeProvider);

      expect(selectedNode, isNull);
    });
    });
  });
}
