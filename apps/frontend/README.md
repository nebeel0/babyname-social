# Baby Names Social Network - Frontend

A Flutter web application for discovering and sharing baby name preferences with your partner.

## Architecture

This Flutter app uses:
- **State Management**: Riverpod 2.x
- **Routing**: go_router
- **API Client**: OpenAPI-generated Dart client
- **UI Framework**: Material Design 3
- **Charts**: fl_chart

## Prerequisites

- Flutter SDK 3.32.6 or later
- Chrome (for web development)
- Backend server running on http://localhost:8001

## Getting Started

### 1. Install Dependencies

```bash
flutter pub get
```

### 2. Start the Backend

The frontend requires the FastAPI backend to be running:

```bash
cd ../backend
uv run fastapi dev app/main.py --port 8001
```

### 3. Run the App

```bash
flutter run -d chrome --web-port=5173
```

The app will be available at http://localhost:5173

## OpenAPI Client Generation

This project uses auto-generated API clients from the backend's OpenAPI specification.

### Quick Start: Regenerate API Client

```bash
./scripts/regenerate_api.sh
```

This script will:
1. Download the latest OpenAPI spec from the backend
2. Clean the cache
3. Generate the Dart client
4. Apply fixes for known generator bugs
5. Verify compilation

### Manual Generation

If you prefer to generate manually:

```bash
# Download OpenAPI spec
curl http://localhost:8001/openapi.json -o openapi.json

# Clean cache to force regeneration
rm -f .dart_tool/openapi-generator-cache.json

# Generate client
flutter pub run build_runner build --delete-conflicting-outputs
```

After generation, you may need to manually fix:
- Empty named parameter lists in `Detail` and `ValidationErrorLocInner` classes
- Incomplete `operator==` and `hashCode` methods

### OpenAPI Configuration

The OpenAPI generator is configured in `lib/api_client.dart`:

```dart
@Openapi(
  additionalProperties: AdditionalProperties(
    pubName: 'babynames_api',
    pubAuthor: 'Baby Names Social Network',
  ),
  inputSpec: InputSpec(path: './openapi.json'),
  generatorName: Generator.dart,
  outputDirectory: 'lib/generated/api',
  typeMappings: {
    'DateTime': 'DateTime',
  },
)
class ApiClient {}
```

Generated files are located in `lib/generated/api/`.

### API Providers

Access API endpoints through Riverpod providers in `lib/core/providers/api_client_provider.dart`:

```dart
// Example usage
final namesProvider = FutureProvider<List<NameRead>>((ref) async {
  final namesApi = ref.read(namesApiProvider);
  return await namesApi.listNamesNamesGet() ?? [];
});
```

## Project Structure

```
lib/
├── core/
│   ├── api/                  # Legacy API client (deprecated)
│   ├── models/              # Data models
│   └── providers/           # Riverpod providers for API
├── features/
│   ├── names/
│   │   ├── providers/       # Names feature providers
│   │   ├── screens/         # Names screens
│   │   └── widgets/         # Names widgets
│   └── profile/
│       ├── screens/         # Profile screens
│       └── providers/       # Profile providers
├── generated/
│   └── api/                 # OpenAPI-generated client
└── main.dart

test/
├── integration/             # Integration tests
└── widget_test.dart         # Widget tests

scripts/
└── regenerate_api.sh        # API regeneration automation
```

## Testing

### Unit and Widget Tests

```bash
flutter test
```

### Integration Tests

Integration tests require the backend to be running:

```bash
# Start backend first
cd ../backend && uv run fastapi dev app/main.py --port 8001

# Run integration tests
flutter test test/integration/
```

See [test/integration/README.md](test/integration/README.md) for more details.

## Building

### Development Build

```bash
flutter build web
```

### Release Build

```bash
flutter build web --release
```

The built files will be in `build/web/`.

## Development Workflow

### 1. Working with the API

When the backend API changes:

```bash
# Regenerate API client
./scripts/regenerate_api.sh

# Verify everything compiles
flutter analyze

# Run tests
flutter test
```

### 2. Adding New Features

1. Create feature directory in `lib/features/`
2. Add providers in `providers/` subdirectory
3. Create screens in `screens/` subdirectory
4. Add widgets in `widgets/` subdirectory
5. Update routing in `lib/main.dart`

### 3. State Management

This project uses Riverpod 2.x. Key patterns:

```dart
// Provider definition
final myProvider = Provider<MyService>((ref) => MyService());

// FutureProvider for async data
final dataProvider = FutureProvider<Data>((ref) async {
  final api = ref.read(apiProvider);
  return await api.fetchData();
});

// Consumer widget
class MyWidget extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final data = ref.watch(dataProvider);
    return data.when(
      data: (value) => Text(value.toString()),
      loading: () => CircularProgressIndicator(),
      error: (err, stack) => Text('Error: $err'),
    );
  }
}
```

## Common Tasks

### Analyze Code

```bash
flutter analyze
```

### Format Code

```bash
flutter format .
```

### Clean Build

```bash
flutter clean
flutter pub get
```

### Update Dependencies

```bash
flutter pub upgrade
```

## Troubleshooting

### OpenAPI Generation Fails

1. Ensure backend is running on port 8001
2. Clean the cache: `rm -f .dart_tool/openapi-generator-cache.json`
3. Delete generated files: `rm -rf lib/generated/api`
4. Regenerate: `flutter pub run build_runner build --delete-conflicting-outputs`

### Compilation Errors After Generation

Run the automated fix script:
```bash
./scripts/regenerate_api.sh
```

Or manually fix the generated files as documented in the script.

### Backend Connection Issues

Verify the backend URL in `lib/core/providers/api_client_provider.dart`:

```dart
final apiClientProvider = Provider<ApiClient>((ref) {
  return ApiClient(basePath: 'http://localhost:8001');
});
```

## Contributing

1. Create a feature branch
2. Make your changes
3. Run tests: `flutter test`
4. Run analyzer: `flutter analyze`
5. Format code: `flutter format .`
6. Submit a pull request

## Resources

- [Flutter Documentation](https://docs.flutter.dev/)
- [Riverpod Documentation](https://riverpod.dev/)
- [OpenAPI Generator](https://pub.dev/packages/openapi_generator)
- [Go Router](https://pub.dev/packages/go_router)
