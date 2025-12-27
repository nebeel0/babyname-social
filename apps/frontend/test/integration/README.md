# Integration Tests

This directory contains integration tests that verify the Flutter frontend works correctly with the FastAPI backend.

## Prerequisites

1. **Backend must be running**: Start the backend server on port 8001
   ```bash
   cd ../../backend
   uv run fastapi dev app/main.py --port 8001
   ```

2. **Database**: The backend should have an initialized database (migrations applied)

## Running Tests

### Run all integration tests
```bash
flutter test test/integration/
```

### Run specific test file
```bash
flutter test test/integration/names_api_test.dart
```

### Run with verbose output
```bash
flutter test test/integration/ --reporter expanded
```

## Test Coverage

### Names API Tests (`names_api_test.dart`)

Tests the complete CRUD operations for baby names:

- ✅ Create a new name
- ✅ List all names
- ✅ Get a specific name by ID
- ✅ Update a name
- ✅ Search names by query
- ✅ Filter names by gender
- ✅ Delete a name
- ✅ Handle non-existent names gracefully
- ✅ Validate required fields
- ✅ API client configuration
- ✅ Data model serialization/deserialization

## Test Data

Tests create temporary test data that is cleaned up after execution. Test names are generated with timestamps to avoid conflicts:

```dart
'TestName${DateTime.now().millisecondsSinceEpoch}'
```

## Common Issues

### Backend not running
```
Error: Connection refused (OS Error: Connection refused, errno = 111)
```
**Solution**: Start the backend server on port 8001

### Database not initialized
```
Error: relation "names" does not exist
```
**Solution**: Run database migrations in the backend

### Port conflicts
If port 8001 is in use, update the backend URL in the test files or configure the backend URL via environment variable.

## Adding New Tests

1. Create a new test file in this directory: `test/integration/your_api_test.dart`
2. Follow the pattern from `names_api_test.dart`
3. Use `ProviderContainer` to access API providers
4. Clean up any created test data in tearDown or test cleanup

Example structure:
```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:frontend/core/providers/api_client_provider.dart';

void main() {
  late ProviderContainer container;
  late YourApi yourApi;

  setUpAll(() {
    container = ProviderContainer();
    yourApi = container.read(yourApiProvider);
  });

  tearDownAll(() {
    container.dispose();
  });

  group('Your API Integration Tests', () {
    test('should do something', () async {
      // Test implementation
    });
  });
}
```

## CI/CD Integration

These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Start backend
  run: |
    cd backend
    uv run fastapi dev app/main.py --port 8001 &
    sleep 5  # Wait for backend to start

- name: Run integration tests
  run: |
    cd frontend
    flutter test test/integration/
```

## Debugging Tests

To debug failing tests:

1. Run tests with verbose output
2. Check backend logs for API errors
3. Verify database state
4. Use `print()` statements in tests for debugging
5. Run individual tests in isolation

## Performance Considerations

- Integration tests are slower than unit tests (they make real HTTP requests)
- Run integration tests separately from unit tests
- Consider using test tags to separate test types:

```dart
test('should create a name', () async {
  // ...
}, tags: ['integration']);
```

Then run only unit tests:
```bash
flutter test --exclude-tags=integration
```
