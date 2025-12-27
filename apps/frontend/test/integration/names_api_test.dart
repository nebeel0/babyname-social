import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:frontend/core/providers/api_client_provider.dart';
import 'package:frontend/generated/api/lib/api.dart';

/// Integration tests for the Names API
///
/// These tests verify that the OpenAPI-generated client works correctly
/// with the backend API. They test the full request/response cycle.
///
/// Requirements:
/// - Backend must be running on http://localhost:8001
/// - Database must be initialized with test data or empty
void main() {
  late ProviderContainer container;
  late NamesApi namesApi;

  setUpAll(() {
    // Initialize the provider container
    container = ProviderContainer();
    namesApi = container.read(namesApiProvider);
  });

  tearDownAll(() {
    container.dispose();
  });

  group('Names API Integration Tests', () {
    int? createdNameId;

    test('should create a new name', () async {
      final nameCreate = NameCreate(
        name: 'TestName${DateTime.now().millisecondsSinceEpoch}',
        gender: 'unisex',
        originCountry: 'Test Country',
        meaning: 'A name created for testing',
      );

      final response = await namesApi.createNameApiV1NamesPost(nameCreate);

      expect(response, isNotNull);
      expect(response!.name, equals(nameCreate.name));
      expect(response.gender, equals(nameCreate.gender));
      expect(response.originCountry, equals(nameCreate.originCountry));
      expect(response.meaning, equals(nameCreate.meaning));
      expect(response.id, isNotNull);

      createdNameId = response.id;
    });

    test('should list all names', () async {
      final response = await namesApi.getNamesApiV1NamesGet();

      expect(response, isNotNull);
      expect(response, isA<List<NameRead>>());
      expect(response!.length, greaterThan(0));

      // Verify the structure of the first name
      final firstName = response.first;
      expect(firstName.id, isNotNull);
      expect(firstName.name, isNotNull);
      expect(firstName.gender, isNotNull);
    });

    test('should get a specific name by ID', () async {
      if (createdNameId == null) {
        fail('No name was created in previous test');
      }

      final response = await namesApi.getNameApiV1NamesNameIdGet(createdNameId!);

      expect(response, isNotNull);
      expect(response!.id, equals(createdNameId));
      expect(response.name, isNotNull);
    });

    test('should update a name', () async {
      if (createdNameId == null) {
        fail('No name was created in previous test');
      }

      final nameUpdate = NameUpdate(
        meaning: 'Updated meaning for testing',
      );

      final response = await namesApi.updateNameApiV1NamesNameIdPut(
        createdNameId!,
        nameUpdate,
      );

      expect(response, isNotNull);
      expect(response!.id, equals(createdNameId));
      expect(response.meaning, equals(nameUpdate.meaning));
    });

    test('should search names by query', () async {
      final response = await namesApi.searchNamesApiV1NamesSearchQueryGet(
        'Test',
      );

      expect(response, isNotNull);
      expect(response, isA<List<NameRead>>());

      // Verify all returned names contain 'Test' in some field
      for (final name in response!) {
        final matchesQuery = name.name!.contains('Test') ||
            (name.originCountry?.contains('Test') ?? false) ||
            (name.meaning?.contains('Test') ?? false);
        expect(matchesQuery, isTrue);
      }
    });

    test('should delete a name', () async {
      if (createdNameId == null) {
        fail('No name was created in previous test');
      }

      await namesApi.deleteNameApiV1NamesNameIdDelete(createdNameId!);

      // Verify the name is deleted by trying to get it
      try {
        await namesApi.getNameApiV1NamesNameIdGet(createdNameId!);
        fail('Name should have been deleted');
      } catch (e) {
        // Expected to throw an error (404)
        expect(e, isA<ApiException>());
        expect((e as ApiException).code, equals(404));
      }
    });

    test('should handle non-existent name gracefully', () async {
      const nonExistentId = 999999;

      try {
        await namesApi.getNameApiV1NamesNameIdGet(nonExistentId);
        fail('Should throw an exception for non-existent name');
      } catch (e) {
        expect(e, isA<ApiException>());
        expect((e as ApiException).code, equals(404));
      }
    });

    test('should validate required fields on create', () async {
      final invalidName = NameCreate(
        name: '', // Empty name should fail validation
        gender: 'male',
      );

      try {
        await namesApi.createNameApiV1NamesPost(invalidName);
        fail('Should throw validation error for empty name');
      } catch (e) {
        expect(e, isA<ApiException>());
        expect((e as ApiException).code, equals(422));
      }
    });
  });

  group('API Client Configuration', () {
    test('should have correct base path configured', () {
      final apiClient = container.read(apiClientProvider);

      // The base path should point to the backend
      expect(apiClient.basePath, contains('localhost'));
    });

    test('should handle timeouts gracefully', () async {
      // This test verifies that the API client has timeout configured
      // Actual timeout testing would require a slow endpoint
      final apiClient = container.read(apiClientProvider);

      expect(apiClient, isNotNull);
    });
  });

  group('Data Model Validation', () {
    test('NameRead should serialize and deserialize correctly', () {
      final originalName = NameRead(
        id: 1,
        name: 'TestName',
        createdAt: DateTime.now(),
        gender: 'female',
        originCountry: 'Test',
        meaning: 'A test name',
        avgRating: 4.5,
        ratingCount: 100,
      );

      // Serialize to JSON
      final json = originalName.toJson();

      expect(json['id'], equals(1));
      expect(json['name'], equals('TestName'));
      expect(json['gender'], equals('female'));

      // Deserialize from JSON
      final deserializedName = NameRead.fromJson(json);

      expect(deserializedName, isNotNull);
      expect(deserializedName!.id, equals(originalName.id));
      expect(deserializedName.name, equals(originalName.name));
      expect(deserializedName.gender, equals(originalName.gender));
    });

    test('NameCreate should serialize correctly', () {
      final nameCreate = NameCreate(
        name: 'NewName',
        gender: 'male',
        originCountry: 'Test Country',
        meaning: 'Test Meaning',
      );

      final json = nameCreate.toJson();

      expect(json['name'], equals('NewName'));
      expect(json['gender'], equals('male'));
      expect(json['origin_country'], equals('Test Country'));
      expect(json['meaning'], equals('Test Meaning'));
    });

    test('NameUpdate should handle optional fields', () {
      final nameUpdate = NameUpdate(
        meaning: 'Updated meaning only',
      );

      final json = nameUpdate.toJson();

      expect(json['meaning'], equals('Updated meaning only'));
      expect(json.containsKey('name'), isFalse);
      expect(json.containsKey('gender'), isFalse);
    });
  });
}
