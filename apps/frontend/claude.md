# Claude Context - Frontend (Flutter)

> **Purpose**: Frontend-specific context for AI assistants working on the Flutter application. Focuses on architecture, API communication patterns, and development conventions.

**Last Updated**: 2025-12-22
**Migration Status**: ✅ COMPLETED - OpenAPI client fully integrated
**Verification**: ⚠️ REQUIRED - Always run `dart analyze` before completing UI work

## Backend-Frontend Communication Pattern

### ⚠️ IMPORTANT: API Communication Standard

**DO NOT use direct HTTP calls (Dio, http package, etc.) for API communication.**

**DO use OpenAPI-generated client code for all backend communication.**

### Current State - ✅ IMPLEMENTED

#### ✅ Current Implementation
```dart
// Using auto-generated OpenAPI client with Riverpod
import 'package:frontend/generated/api/lib/api.dart';
import 'package:frontend/core/providers/api_client_provider.dart';

// In providers (lib/features/names/providers/names_provider.dart)
final namesProvider = FutureProvider<List<NameRead>>((ref) async {
  final namesApi = ref.read(namesApiProvider);
  final names = await namesApi.listNamesNamesGet();
  return names ?? [];
});

// In screens - type-safe with compile-time validation!
final namesAsync = ref.watch(namesProvider);
```

**Benefits:**
- Type-safe models and methods
- Compile-time validation
- Automatic serialization/deserialization
- Single source of truth (OpenAPI spec)
- Auto-updates when backend changes
- Consistent error handling

## OpenAPI Code Generation Setup

### Configuration Files

**`openapi_generator_config.json`** (root of frontend/)
```json
{
  "openapiGeneratorVersion": "7.9.0",
  "jarCacheDir": ".dart_tool/openapi_generator_cache",
  "customGeneratorUrls": [
    "https://repo1.maven.org/maven2/com/bluetrainsoftware/maven/openapi-dart-generator/7.2/openapi-dart-generator-7.2.jar"
  ]
}
```

### Setup Steps (✅ COMPLETED)

1. **Get OpenAPI spec from backend:**
   ```bash
   curl http://localhost:8001/openapi.json > openapi.json
   ```
   ✅ Done - automated in `scripts/regenerate_api.sh`

2. **Created annotation file** (`lib/api_client.dart`):
   ```dart
   import 'package:openapi_generator_annotations/openapi_generator_annotations.dart';

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
   ✅ Done - file exists and is configured

3. **Run code generation:**
   ```bash
   ./scripts/regenerate_api.sh  # Automated script with fixes
   # OR manually:
   flutter pub run build_runner build --delete-conflicting-outputs
   ```
   ✅ Done - automation script created

4. **Generated code location:**
   ```
   lib/generated/api/
   ├── lib/
   │   ├── api.dart           # Main export
   │   ├── api/               # API endpoint classes
   │   │   ├── names_api.dart
   │   │   └── auth_api.dart
   │   └── model/             # Data models
   │       ├── name.dart
   │       ├── popularity_history.dart
   │       └── user_profile.dart
   └── ...
   ```

5. **Add to .gitignore:**
   ```
   # Generated API client
   lib/generated/api/
   openapi.json
   ```

### Using the Generated Client

#### Setup API Client Provider (Riverpod) - ✅ IMPLEMENTED

**`lib/core/providers/api_client_provider.dart`**:
```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:frontend/generated/api/lib/api.dart';

// Base API client
final apiClientProvider = Provider<ApiClient>((ref) {
  return ApiClient(basePath: 'http://localhost:8001');
});

// Names API
final namesApiProvider = Provider<NamesApi>((ref) {
  final client = ref.watch(apiClientProvider);
  return NamesApi(client);
});

// Auth API
final authApiProvider = Provider<AuthApi>((ref) {
  final client = ref.watch(apiClientProvider);
  return AuthApi(client);
});
```

#### Use in Screens/Providers - ✅ IMPLEMENTED

**Example: Names Provider** (`lib/features/names/providers/names_provider.dart`):
```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:frontend/core/providers/api_client_provider.dart';
import 'package:frontend/generated/api/lib/api.dart';

// Provider for all names
final namesProvider = FutureProvider<List<NameRead>>((ref) async {
  final namesApi = ref.read(namesApiProvider);
  final names = await namesApi.listNamesNamesGet();
  return names ?? [];
});

// CRUD operations
Future<NameRead> createName(WidgetRef ref, NameCreate nameCreate) async {
  final namesApi = ref.read(namesApiProvider);
  final created = await namesApi.createNameNamesPost(nameCreate);
  if (created == null) throw Exception('Failed to create name');
  ref.invalidate(namesProvider);
  return created;
}
```

**Example: In Widget**:
```dart
class NamesListScreen extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final namesAsync = ref.watch(namesListProvider);

    return namesAsync.when(
      loading: () => CircularProgressIndicator(),
      error: (err, stack) => Text('Error: $err'),
      data: (names) => ListView.builder(
        itemCount: names.length,
        itemBuilder: (context, index) {
          final name = names[index];
          return ListTile(
            title: Text(name.name),  // Type-safe!
            subtitle: Text(name.meaning ?? ''),
          );
        },
      ),
    );
  }
}
```

## Directory Structure

```
apps/frontend/
├── lib/
│   ├── main.dart                    # App entry point
│   ├── core/                        # Core functionality
│   │   ├── models/                  # Manual/custom models
│   │   │   ├── user_profile.dart    # Custom business models
│   │   │   └── name_enhancements.dart
│   │   ├── providers/               # App-wide providers
│   │   │   └── api_client_provider.dart  # (TO BE CREATED)
│   │   ├── routing/                 # go_router configuration
│   │   └── theme/                   # App theme
│   ├── features/                    # Feature modules
│   │   ├── names/
│   │   │   ├── providers/           # Names-specific providers
│   │   │   ├── screens/            # UI screens
│   │   │   └── widgets/            # Reusable widgets
│   │   ├── profile/
│   │   └── auth/                   # (TO BE CREATED)
│   ├── shared/                      # Shared widgets/utilities
│   └── generated/                   # Auto-generated code
│       └── api/                     # OpenAPI generated (TO BE CREATED)
│           ├── lib/
│           │   ├── api.dart
│           │   ├── api/            # API classes
│           │   └── model/          # Data models
│           └── ...
├── pubspec.yaml
├── openapi_generator_config.json
└── claude.md                        # This file
```

## Model Strategy

### When to Use Generated Models vs Custom Models

**Use Generated Models (from OpenAPI):**
- ✅ API request/response objects
- ✅ Data that comes directly from backend
- ✅ Database entities exposed via API
- Examples: `Name`, `PopularityHistory`, `User`, `Comment`

**Use Custom Models (manual):**
- ✅ UI-specific state
- ✅ Computed/derived data
- ✅ Local-only data
- ✅ Complex business logic
- Examples: `NameEnhancements`, `FilterState`, `ComparisonState`

**Conversion Between Models:**
```dart
// Convert generated model to custom model
final enhancement = NameEnhancement.fromApiName(apiName);

// Or use extension methods
extension NameExtension on Name {
  NameEnhancement toEnhancement() {
    return NameEnhancement(/* ... */);
  }
}
```

## API Client Configuration

### Environment-Based Base URLs

**`lib/core/config/api_config.dart`** (TO BE CREATED):
```dart
class ApiConfig {
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8001',
  );

  static const String apiVersion = 'v1';
  static const Duration timeout = Duration(seconds: 30);
}
```

**Usage:**
```dart
final apiClientProvider = Provider<ApiClient>((ref) {
  final client = ApiClient(basePath: ApiConfig.baseUrl);
  // Configure timeout, interceptors, etc.
  return client;
});
```

### Authentication

**With JWT tokens** (TO BE IMPLEMENTED):
```dart
final authenticatedApiClientProvider = Provider<ApiClient>((ref) {
  final token = ref.watch(authTokenProvider);

  final client = ApiClient(basePath: ApiConfig.baseUrl);

  if (token != null) {
    client.addDefaultHeader('Authorization', 'Bearer $token');
  }

  return client;
});
```

## Error Handling Pattern

### Centralized Error Handling

**`lib/core/errors/api_error.dart`** (TO BE CREATED):
```dart
class ApiError {
  final int? statusCode;
  final String message;
  final dynamic data;

  ApiError({this.statusCode, required this.message, this.data});

  factory ApiError.fromException(dynamic e) {
    if (e is ApiException) {
      return ApiError(
        statusCode: e.code,
        message: e.message ?? 'Unknown error',
        data: e.innerException,
      );
    }
    return ApiError(message: e.toString());
  }
}
```

**Usage in Providers:**
```dart
final namesListProvider = FutureProvider<List<Name>>((ref) async {
  try {
    final api = ref.watch(namesApiProvider);
    return await api.getNamesApiV1NamesGet() ?? [];
  } on ApiException catch (e) {
    final error = ApiError.fromException(e);
    // Log or report error
    throw error;
  } catch (e) {
    throw ApiError(message: 'Unexpected error: $e');
  }
});
```

## Migration Status - ✅ COMPLETED

### Completed Migration

All files have been successfully migrated from manual HTTP calls to OpenAPI-generated client:

1. **✅ `lib/core/providers/api_client_provider.dart`**
   - Created with all API providers (NamesApi, AuthApi)
   - Configured with Riverpod for dependency injection

2. **✅ `lib/features/names/providers/names_provider.dart`**
   - Migrated to use generated NamesApi
   - All CRUD operations implemented with type safety

3. **✅ `lib/features/names/screens/names_list_screen.dart`**
   - Refactored to use namesProvider
   - Removed all direct Dio calls

4. **✅ `lib/features/names/widgets/*`**
   - AddNameDialog: Updated to use NameCreate/NameRead
   - NameDetailModal: Updated to accept NameRead
   - All widgets now type-safe

5. **✅ `lib/features/names/screens/favorites_screen.dart`**
   - Fully migrated to use NameRead models
   - Integrated with API providers

### Migration Checklist - ✅ ALL DONE

- [x] Generate OpenAPI spec from backend
- [x] Create API client annotation file (`lib/api_client.dart`)
- [x] Run build_runner to generate client
- [x] Create API client providers (Riverpod)
- [x] Create feature-specific providers using generated API
- [x] Refactor all screens to use providers
- [x] Add error handling with ApiException
- [x] Fix null safety issues
- [x] Test compilation and build
- [x] Remove direct Dio calls from features
- [x] Create automation script (`scripts/regenerate_api.sh`)
- [x] Add integration tests (`test/integration/`)
- [x] Update documentation (README.md, claude.md)

## Development Workflow

### When Backend API Changes

1. **Backend team updates FastAPI endpoints**
2. **Regenerate OpenAPI spec:**
   ```bash
   curl http://localhost:8001/openapi.json > openapi.json
   ```
3. **Regenerate Dart client:**
   ```bash
   flutter pub run build_runner build --delete-conflicting-outputs
   ```
4. **Fix any breaking changes** (compiler will tell you!)
5. **Verify compilation:**
   ```bash
   dart analyze lib/features/affected_feature/
   ```
6. **Test affected features**

### Adding New API Endpoints

1. Backend adds new endpoint
2. Update OpenAPI spec
3. Regenerate client (automatic models/methods)
4. Create Riverpod provider if needed
5. Use in UI
6. **Verify compilation with `dart analyze`**

**No manual model creation needed!**

## Testing Strategy

### Testing with Generated API Client

**Mock the API client:**
```dart
class MockNamesApi extends Mock implements NamesApi {}

void main() {
  late MockNamesApi mockApi;
  late ProviderContainer container;

  setUp(() {
    mockApi = MockNamesApi();
    container = ProviderContainer(
      overrides: [
        namesApiProvider.overrideWithValue(mockApi),
      ],
    );
  });

  test('fetches names successfully', () async {
    final mockNames = [Name(id: 1, name: 'Emma')];
    when(() => mockApi.getNamesApiV1NamesGet())
        .thenAnswer((_) async => mockNames);

    final result = await container.read(namesListProvider.future);
    expect(result, mockNames);
  });
}
```

## Best Practices

### DO ✅

- ✅ Use OpenAPI-generated client for all backend communication
- ✅ Use Riverpod providers to manage API calls
- ✅ Handle errors gracefully with try-catch
- ✅ Add loading states for async operations
- ✅ Use FutureProvider for one-time fetches
- ✅ Use StateNotifierProvider for mutable state
- ✅ Regenerate client when backend changes
- ✅ Keep generated code in .gitignore
- ✅ Type-check everything (generated code is fully typed)
- ✅ **ALWAYS verify code compiles before finishing** (see Verification Workflow below)

### DON'T ❌

- ❌ Make direct HTTP calls with Dio/http
- ❌ Manually parse JSON from API responses
- ❌ Hardcode API URLs in widgets
- ❌ Commit generated API code to git
- ❌ Modify generated code (it will be overwritten)
- ❌ Skip regeneration after backend updates
- ❌ Use `dynamic` for API responses

## Dependencies

### Required Packages

**Already in `pubspec.yaml`:**
```yaml
dependencies:
  flutter_riverpod: ^2.6.1
  dio: ^5.8.0  # Used by generated client
  json_annotation: ^4.9.0
  openapi_generator_annotations: ^6.1.0

dev_dependencies:
  build_runner: ^2.4.13
  json_serializable: ^6.9.0
  openapi_generator: ^6.1.0
```

### Configuration Files

- ✅ `openapi_generator_config.json` - Generator settings
- ✅ `build.yaml` - Build configuration
- ⏳ `lib/api_client.dart` - Annotation file (TO BE CREATED)
- ⏳ `openapi.json` - API spec (TO BE DOWNLOADED)

## Related Documentation

- **Main project context**: `../../claude.md`
- **Backend API docs**: http://localhost:8001/docs
- **OpenAPI spec**: http://localhost:8001/openapi.json
- **Flutter Riverpod**: https://riverpod.dev/
- **OpenAPI Generator**: https://pub.dev/packages/openapi_generator

## Code Verification Workflow

### ⚠️ CRITICAL: Always Verify Code Compiles

**Before completing any UI implementation task, you MUST verify the code compiles without errors.**

#### Verification Steps

1. **Analyze specific files** (fastest for targeted changes):
   ```bash
   dart analyze lib/features/names/screens/my_new_screen.dart
   dart analyze lib/features/names/widgets/my_new_widget.dart
   ```

2. **Analyze entire feature module**:
   ```bash
   dart analyze lib/features/names/
   ```

3. **Analyze entire project**:
   ```bash
   dart analyze
   ```

4. **Check for compilation errors** (most thorough):
   ```bash
   flutter build web --web-renderer html
   # OR for faster dry-run:
   flutter analyze
   ```

#### What to Check For

**Critical Errors (Must Fix):**
- ❌ Undefined methods or properties
- ❌ Type mismatches
- ❌ Missing imports
- ❌ Null safety violations
- ❌ API method name mismatches (check generated API client)

**Acceptable Warnings:**
- ⚠️ Deprecated member usage (e.g., `withOpacity` → `withValues`)
- ⚠️ Unused imports
- ⚠️ Dead code
- ⚠️ Linting suggestions (unnecessary_null_aware_expression, etc.)

#### Common Issues After API Changes

When adding new screens/features that use the OpenAPI client:

1. **Wrong API method names**: Generated method names follow pattern `operationIdApiV1PathGet`
   ```bash
   # Check actual method names:
   grep "Future.*" lib/generated/api/lib/api/my_api.dart
   ```

2. **Response type mismatches**: API may return `Type?` instead of `Response<Type>`
   ```dart
   // Check if method returns nullable or wrapped response
   final response = await api.getDataApiV1DataGet();
   if (response == null) { ... }  // Handle nullable return
   ```

3. **Missing provider setup**: Ensure API providers are registered
   ```dart
   // Verify in lib/core/providers/api_client_provider.dart
   final myApiProvider = Provider<MyApi>((ref) {
     final client = ref.watch(apiClientProvider);
     return MyApi(client);
   });
   ```

#### Example Workflow

```bash
# After creating new screen/widget:
$ dart analyze lib/features/names/screens/prefix_tree_screen.dart
Analyzing prefix_tree_screen.dart...

  error - screens/prefix_tree_screen.dart:25:15 - The method 'getPrefixTree' isn't defined
          ^^^^^^^^^^^^^^^^

# Fix the error by checking correct method name:
$ grep "Future.*prefix.*tree" lib/generated/api/lib/api/prefix_tree_api.dart
  Future<PrefixTreeResponse?> getPrefixTreeApiV1PrefixTreeGet({

# Update code to use correct method name, then verify again:
$ dart analyze lib/features/names/screens/prefix_tree_screen.dart
Analyzing prefix_tree_screen.dart...
No issues found!
```

#### When Errors Exist

**DO NOT** mark implementation as complete if:
- Any `error` level issues exist
- Code fails to compile
- App fails to run

**It's OK to complete** with:
- `warning` level issues (document them)
- `info` level suggestions
- Linting hints

### Pre-Completion Checklist

Before finishing any UI task:

- [ ] Run `dart analyze` on modified files
- [ ] Fix all compilation errors
- [ ] Verify correct API method names (check generated code)
- [ ] Ensure all imports are present
- [ ] Check null safety handling
- [ ] Document any remaining warnings

## Quick Reference Commands

```bash
# Verify code compilation
dart analyze lib/path/to/file.dart           # Single file
dart analyze lib/features/myfeature/         # Feature directory
dart analyze                                 # Entire project
flutter analyze                              # Full analysis with warnings

# Generate/update API client
curl http://localhost:8001/openapi.json > openapi.json
flutter pub run build_runner build --delete-conflicting-outputs

# Check generated API method names
grep "Future.*" lib/generated/api/lib/api/my_api.dart

# Watch mode (auto-regenerate on changes)
flutter pub run build_runner watch

# Clean generated files
flutter pub run build_runner clean

# Run app
flutter run -d chrome --web-port=5173

# Build for production (catches compilation errors)
flutter build web --web-renderer html
```

---

## Known Issues & Workarounds

### OpenAPI Generator Bugs

The Dart OpenAPI generator has known bugs that generate invalid code:

1. **Empty named parameter lists**: Generates `Detail({})` instead of `Detail()`
2. **Incomplete operators**: Generates incomplete `operator==` and `hashCode`

**Solution**: Use the automated script `./scripts/regenerate_api.sh` which applies fixes automatically.

### Testing

- Integration tests are in `test/integration/`
- Require backend running on port 8001
- Run with: `flutter test test/integration/`

---

**Last Migration**: 2025-12-22
**Status**: ✅ Complete - All features using OpenAPI-generated client
