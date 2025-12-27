# Frontend Tests

This directory contains all tests for the Baby Names Social Network Flutter frontend.

## Test Structure

```
test/
├── unit/
│   ├── providers/          # Provider/state management tests
│   └── widgets/            # Widget unit tests
├── integration/            # API integration tests
└── widget_test.dart        # Basic smoke tests
```

## Running Tests

### Run all tests
```bash
flutter test
```

### Run specific test file
```bash
flutter test test/unit/providers/prefix_tree_provider_test.dart
```

### Run tests with coverage
```bash
./test_coverage.sh
```

Or manually:
```bash
flutter test --coverage
genhtml coverage/lcov.info -o coverage/html
open coverage/html/index.html
```

### Run tests in watch mode
```bash
flutter test --watch
```

## Test Categories

### Unit Tests (`test/unit/`)
- **Provider Tests**: Test state management logic, API interactions, and business logic
  - `prefix_tree_provider_test.dart`: Tests for prefix tree data fetching and filtering

- **Widget Tests**: Test individual widgets in isolation
  - `prefix_tree_node_test.dart`: Tests for prefix tree node rendering and interactions

### Integration Tests (`test/integration/`)
- **API Tests**: Test full API request/response cycles
  - `names_api_test.dart`: Tests for CRUD operations on names

## Writing Tests

### Provider Tests Example

```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mockito/mockito.dart';

void main() {
  late ProviderContainer container;

  setUp(() {
    container = ProviderContainer();
  });

  tearDown(() {
    container.dispose();
  });

  test('provider should return expected value', () {
    final value = container.read(myProvider);
    expect(value, equals(expectedValue));
  });
}
```

### Widget Tests Example

```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter/material.dart';

void main() {
  testWidgets('widget should display text', (WidgetTester tester) async {
    await tester.pumpWidget(
      MaterialApp(home: MyWidget()),
    );

    expect(find.text('Expected Text'), findsOneWidget);
  });
}
```

## Mocking

We use `mockito` for mocking dependencies. To generate mocks:

```bash
flutter pub run build_runner build
```

Example mock annotation:
```dart
@GenerateMocks([MyApi])
void main() {
  late MockMyApi mockApi;

  setUp(() {
    mockApi = MockMyApi();
  });
}
```

## Coverage Requirements

- **Minimum Coverage**: 60%
- **Generated Files**: Excluded from coverage
- **Test Files**: Excluded from coverage

### Coverage Configuration

Coverage is configured in `.coveragerc` and enforced by `test_coverage.sh`.

Files excluded from coverage:
- Generated API client code (`lib/generated/**`)
- Test files (`test/**`)
- Generated Dart files (`**/*.g.dart`, `**/*.freezed.dart`)
- Main entry point (`lib/main.dart`)

## Continuous Integration

Tests are run automatically on:
- Pull requests
- Pushes to main branch
- Manual workflow dispatch

### CI Workflow
The GitHub Actions workflow (`.github/workflows/test.yml`) will:
1. Install Flutter dependencies
2. Generate mocks
3. Run all tests
4. Generate coverage report
5. Fail if coverage is below 60%

## Best Practices

1. **Test Organization**: Group related tests using `group()`
2. **Setup/Teardown**: Use `setUp()` and `tearDown()` for common initialization
3. **Descriptive Names**: Use clear, descriptive test names
4. **Isolation**: Each test should be independent and not rely on other tests
5. **Mock External Dependencies**: Use mocks for API calls and external services
6. **Widget Tests**: Use `pump` and `pumpAndSettle` appropriately
7. **Coverage**: Aim for high coverage but focus on meaningful tests

## Debugging Tests

### Run single test
```bash
flutter test test/unit/providers/prefix_tree_provider_test.dart --plain-name "should create with default values"
```

### Debug in VS Code
Add breakpoints and use the Flutter test debug configuration.

### Verbose output
```bash
flutter test --verbose
```

## Common Issues

### Mock not generated
Run: `flutter pub run build_runner build --delete-conflicting-outputs`

### Tests passing locally but failing in CI
- Check for platform-specific dependencies
- Ensure all async operations complete
- Verify file paths are correct

### Widget test failures
- Use `pumpAndSettle()` to wait for animations
- Check widget tree with `debugDumpApp()`
- Verify you're using `MaterialApp` or `WidgetsApp` wrapper

## Resources

- [Flutter Testing Documentation](https://docs.flutter.dev/testing)
- [Mockito Documentation](https://pub.dev/packages/mockito)
- [Riverpod Testing](https://riverpod.dev/docs/cookbooks/testing)
