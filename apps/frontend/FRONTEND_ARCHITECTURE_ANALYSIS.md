# Frontend Architecture Analysis

**Date:** December 26, 2025
**Purpose:** Compare babyname-social frontend with landbridge-frontend patterns to identify improvements

## Executive Summary

| Aspect | Babyname-Social (Current) | Landbridge-Frontend | Recommendation |
|--------|---------------------------|---------------------|----------------|
| **State Management** | Riverpod | Flutter BLoC/Cubit | ✅ Keep Riverpod (more modern) |
| **Dependency Injection** | Riverpod Providers | GetIt (Service Locator) | ✅ Keep Riverpod (compile-time safety) |
| **API Client** | Mix of manual + generated | OpenAPI Generator | ⚠️ Standardize on generated |
| **Environment Config** | Hardcoded `const` | `.env` files | ❌ **CRITICAL: Add .env support** |
| **Token Storage** | None | Flutter Secure Storage | ❌ **CRITICAL: Add secure storage** |
| **Repository Pattern** | Direct API calls | Repository abstraction | ⚠️ Add for complex features |
| **Routing/Auth** | Basic GoRouter | Auth-aware redirects | ⚠️ Add when auth is implemented |
| **Singletons** | Few (ApiClient static) | GetIt-managed services | ✅ Current approach OK |

## 1. Singleton Pattern Usage

### Current State (Babyname-Social)

**Yes, we do use singletons, but in a limited way:**

```dart
// ❌ BAD: Static constant in ApiClient
class ApiClient {
  static const String baseUrl = 'http://localhost:8001/api/v1';  // Hardcoded singleton!

  Future<Map<String, dynamic>> get(String endpoint) async { ... }
}
```

**Problems:**
1. **Not testable** - Can't mock different base URLs
2. **Not environment-aware** - Same URL for dev/staging/prod
3. **Not configurable** - Hardcoded at compile time

### Landbridge Pattern (Better)

**GetIt Service Locator Pattern:**

```dart
// main.dart
final getIt = GetIt.instance;

Future<void> main() async {
  // Register services as singletons
  getIt.registerSingleton<TokenStorageService>(TokenStorageService());
  getIt.registerSingleton<AlottaClient>(alottaClient);
  getIt.registerSingleton<String>(baseUrl, instanceName: 'baseUrl');

  runApp(const MyApp());
}

// Usage anywhere in app
final storage = getIt<TokenStorageService>();
final baseUrl = getIt<String>(instanceName: 'baseUrl');
```

**Benefits:**
- Centralized dependency registration
- Easy to swap implementations (testing, mocking)
- Lazy initialization support
- Named instances for configuration values

### Riverpod Pattern (Best for our use case)

**We should use Riverpod providers (compile-time safety):**

```dart
// Environment config provider
final baseUrlProvider = Provider<String>((ref) {
  return const String.fromEnvironment('BASE_URL', defaultValue: 'http://localhost:8001');
});

// API client provider
final apiClientProvider = Provider<ApiClient>((ref) {
  final baseUrl = ref.watch(baseUrlProvider);
  return ApiClient(basePath: baseUrl);
});

// Usage in widgets
final apiClient = ref.watch(apiClientProvider);
```

**Benefits over GetIt:**
- **Compile-time safety** - No runtime type errors
- **Automatic disposal** - Riverpod manages lifecycle
- **Reactive** - Auto-rebuilds when dependencies change
- **Better testing** - Can override providers in tests

## 2. Critical Gaps to Address

### 🔴 CRITICAL #1: Environment Configuration

**Current:** Hardcoded URLs
```dart
static const String baseUrl = 'http://localhost:8001/api/v1';  // ❌ Wrong
```

**Landbridge Pattern:**
```dart
// .env.web
BASE_URL=http://localhost:9901

// .env.mobile
BASE_URL=http://10.0.2.2:9901

// .env.prod
BASE_URL=https://api.babynames.app

// main.dart
await dotenv.load(fileName: '.env.$environment');
final String baseUrl = dotenv.env['BASE_URL'] ?? defaultUrl;
```

**Recommended for Babyname-Social (Riverpod approach):**
```dart
// lib/core/config/env_config.dart
import 'package:flutter_dotenv/flutter_dotenv.dart';

class EnvConfig {
  static Future<void> load() async {
    const environment = String.fromEnvironment('ENV', defaultValue: 'dev');
    await dotenv.load(fileName: '.env.$environment');
  }

  static String get baseUrl => dotenv.env['BASE_URL'] ?? 'http://localhost:8001';
  static String get apiVersion => dotenv.env['API_VERSION'] ?? 'v1';
}

// lib/core/providers/config_provider.dart
final baseUrlProvider = Provider<String>((ref) => EnvConfig.baseUrl);

// lib/main.dart
Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await EnvConfig.load();

  runApp(const ProviderScope(child: BabyNamesApp()));
}
```

**Action Items:**
1. Add `flutter_dotenv` dependency
2. Create `.env.dev`, `.env.staging`, `.env.prod`
3. Add `.env.*` to `.gitignore` (use `.env.example`)
4. Update `ApiClient` to accept `baseUrl` parameter
5. Use `--dart-define ENV=dev` when running

### 🔴 CRITICAL #2: Secure Token Storage

**Current:** No authentication/token storage

**Landbridge Pattern:**
```dart
class TokenStorageService {
  final FlutterSecureStorage _secureStorage = const FlutterSecureStorage();

  Future<void> saveAccessToken(String token) async {
    await _secureStorage.write(key: 'auth_token', value: token);
  }

  Future<String?> getAccessToken() async {
    return await _secureStorage.read(key: 'auth_token');
  }
}
```

**Recommended for Babyname-Social:**
```dart
// lib/core/services/auth_storage_service.dart
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class AuthStorageService {
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  static const _tokenKey = 'babynames_auth_token';
  static const _userIdKey = 'babynames_user_id';

  Future<void> saveToken(String token) => _storage.write(key: _tokenKey, value: token);
  Future<String?> getToken() => _storage.read(key: _tokenKey);
  Future<void> deleteToken() => _storage.delete(key: _tokenKey);

  Future<void> saveUserId(String userId) => _storage.write(key: _userIdKey, value: userId);
  Future<String?> getUserId() => _storage.read(key: _userIdKey);
  Future<void> deleteAll() => _storage.deleteAll();
}

// Provider
final authStorageProvider = Provider<AuthStorageService>((ref) => AuthStorageService());
```

**Action Items:**
1. Add `flutter_secure_storage` dependency
2. Create `AuthStorageService`
3. Replace hardcoded `'default_user'` with actual user ID from storage
4. Implement proper authentication flow

### ⚠️ IMPORTANT #3: API Client Standardization

**Current:** Mix of manual and generated clients

**Manual API Client** (`lib/core/api/api_client.dart`):
```dart
class ApiClient {
  static const String baseUrl = 'http://localhost:8001/api/v1';

  Future<Map<String, dynamic>> get(String endpoint) async { ... }
}
```

**Generated API Client** (`lib/generated/api/lib/api_client.dart`):
```dart
class ApiClient {
  ApiClient({this.basePath = 'http://localhost:8001', this.authentication});

  String basePath;
  // Full OpenAPI-generated methods
}
```

**Problem:** Two different `ApiClient` classes causing confusion!

**Recommended Approach:**

1. **Use ONLY the generated client** for consistency
2. **Delete manual `ApiClient`** and migrate all code to generated APIs
3. **Update all API wrappers** to use generated client:

```dart
// OLD (manual)
class ProfileApi {
  final ApiClient _client = ApiClient();  // ❌ Which ApiClient?

  Future<UserProfile?> getProfile(String userId) async {
    try {
      final data = await _client.get('/profiles/$userId');
      return UserProfile.fromJson(data);
    } catch (e) { ... }
  }
}

// NEW (generated)
class ProfileApiWrapper {
  final ProfilesApi _api;

  ProfileApiWrapper(this._api);

  Future<UserProfile?> getProfile(String userId) async {
    try {
      final response = await _api.getProfileApiV1ProfilesUserIdGet(userId);
      return response.data;  // Already typed!
    } on ApiException catch (e) {
      if (e.code == 404) return null;
      rethrow;
    }
  }
}

// Provider
final profileApiProvider = Provider<ProfileApiWrapper>((ref) {
  final api = ref.watch(profilesApiProvider);
  return ProfileApiWrapper(api);
});
```

**Action Items:**
1. Delete `lib/core/api/api_client.dart`
2. Update all API wrappers to use generated clients
3. Add error handling wrapper around generated methods
4. Use Riverpod providers for all API instances

### ⚠️ IMPORTANT #4: Provider Duplication Issue

**Current Problem:** Two providers with same name!

```dart
// lib/core/providers/profile_provider.dart
final userProfileProvider = StateNotifierProvider<...>  // Provider #1

// lib/features/profile/providers/user_profile_provider.dart
final userProfileProvider = FutureProvider<...>  // Provider #2 (DUPLICATE NAME!)
```

**This causes:**
- Import conflicts
- Wrong provider used in different files
- Hard-to-debug issues (like we just experienced!)

**Recommended Solution:**

**Option 1: Rename for clarity**
```dart
// Core provider (app-wide state)
final appUserProfileProvider = StateNotifierProvider<...>

// Feature provider (one-time fetch)
final profileDataProvider = FutureProvider<...>
```

**Option 2: Use only one provider** (preferred)
```dart
// lib/core/providers/profile_provider.dart
final userProfileProvider = StateNotifierProvider.autoDispose<UserProfileNotifier, AsyncValue<UserProfile?>>((ref) {
  final api = ref.watch(profileApiProvider);
  final storage = ref.watch(authStorageProvider);
  return UserProfileNotifier(api, storage);
});

class UserProfileNotifier extends StateNotifier<AsyncValue<UserProfile?>> {
  final ProfileApi _api;
  final AuthStorageService _storage;

  UserProfileNotifier(this._api, this._storage) : super(const AsyncValue.loading()) {
    _loadProfile();
  }

  Future<void> _loadProfile() async {
    try {
      final userId = await _storage.getUserId() ?? 'default_user';
      final profile = await _api.getProfile(userId);
      state = AsyncValue.data(profile);
    } catch (e, stack) {
      state = AsyncValue.error(e, stack);
    }
  }

  Future<void> createProfile(UserProfile profile) async {
    state = const AsyncValue.loading();
    try {
      final created = await _api.createProfile(profile);
      await _storage.saveUserId(created.userId);
      state = AsyncValue.data(created);
    } catch (e, stack) {
      state = AsyncValue.error(e, stack);
    }
  }
}
```

**Action Items:**
1. Delete duplicate `user_profile_provider.dart` in features/
2. Consolidate to single provider in core/
3. Update all imports to use single provider

## 3. Repository Pattern (Optional but Recommended)

**Landbridge Pattern:**

```dart
// Data layer
class SearchSource {
  final AlottaClient _client;

  Future<List<SearchItem>> search(SearchQuery query) async {
    final response = await _client.getSearchApi().search(...);
    return response.data?.items ?? [];
  }
}

// Repository layer (business logic)
class SearchRepository {
  final SearchSource _source;

  SearchRepository({required SearchSource searchSource}) : _source = searchSource;

  Future<SearchResults> searchWithFilters(SearchFilters filters) async {
    final query = _convertFiltersToQuery(filters);
    final items = await _source.search(query);
    return SearchResults(items: items, count: items.length);
  }
}

// Usage in Cubit/Provider
class DiscoveryCubit extends Cubit<DiscoveryState> {
  final SearchRepository _repository;

  DiscoveryCubit(this._repository) : super(DiscoveryInitial());

  Future<void> search(SearchFilters filters) async {
    emit(DiscoveryLoading());
    try {
      final results = await _repository.searchWithFilters(filters);
      emit(DiscoverySuccess(results));
    } catch (e) {
      emit(DiscoveryError(e.toString()));
    }
  }
}
```

**When to use Repository Pattern:**
- ✅ Complex data transformations
- ✅ Multiple data sources (API + local cache)
- ✅ Business logic that doesn't belong in UI
- ❌ Simple CRUD operations (overkill)

**Recommended for Babyname-Social:**

Use repositories for **complex features only**:

```dart
// lib/features/names/data/repositories/name_discovery_repository.dart
class NameDiscoveryRepository {
  final NamesApi _namesApi;
  final EnrichmentApi _enrichmentApi;
  final PreferencesApi _preferencesApi;

  NameDiscoveryRepository(this._namesApi, this._enrichmentApi, this._preferencesApi);

  Future<List<EnrichedName>> getPersonalizedNames(UserProfile profile) async {
    // Business logic: Combine multiple APIs
    final names = await _namesApi.getAllNames();
    final preferences = await _preferencesApi.getUserPreferences(profile.userId);

    // Filter and enrich based on preferences
    final filtered = _applyPreferences(names, preferences);
    final enriched = await Future.wait(
      filtered.map((name) => _enrichmentApi.getEnhancedName(name.id)),
    );

    return enriched;
  }
}

// Provider
final nameDiscoveryRepoProvider = Provider<NameDiscoveryRepository>((ref) {
  final namesApi = ref.watch(namesApiProvider);
  final enrichmentApi = ref.watch(enrichmentApiProvider);
  final preferencesApi = ref.watch(preferencesApiProvider);
  return NameDiscoveryRepository(namesApi, enrichmentApi, preferencesApi);
});
```

**For simple CRUD, skip the repository:**
```dart
// Simple case - direct API call in provider
final userProfileProvider = FutureProvider<UserProfile?>((ref) async {
  final api = ref.watch(profileApiProvider);
  return await api.getProfile('user-123');
});
```

## 4. Routing & Authentication

**Landbridge Pattern (Auth-aware routing):**

```dart
final _router = GoRouter(
  refreshListenable: AuthInjection.authRefreshNotifier,
  redirect: (context, state) {
    final profileCubit = context.read<UserProfileCubit>();
    final isLoggedIn = profileCubit.state is UserProfileLoadSuccess;

    if (isLoggedIn && state.uri.path == '/') {
      return '/maps';  // Redirect authenticated users to main app
    }

    if (!isLoggedIn && state.uri.path == '/maps') {
      return '/';  // Redirect unauthenticated users to landing
    }

    return null;
  },
  routes: [ ... ],
);
```

**Recommended for Babyname-Social (when auth is added):**

```dart
// lib/core/providers/auth_provider.dart
final authStateProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  final storage = ref.watch(authStorageProvider);
  return AuthNotifier(storage);
});

class AuthNotifier extends StateNotifier<AuthState> {
  final AuthStorageService _storage;

  AuthNotifier(this._storage) : super(AuthLoading()) {
    _checkAuthStatus();
  }

  Future<void> _checkAuthStatus() async {
    final token = await _storage.getToken();
    if (token != null) {
      state = AuthAuthenticated(token);
    } else {
      state = AuthUnauthenticated();
    }
  }
}

// lib/main.dart
final _router = GoRouter(
  refreshListenable: /* Riverpod equivalent */,
  redirect: (context, state) {
    final container = ProviderScope.containerOf(context);
    final authState = container.read(authStateProvider);

    final publicRoutes = ['/login', '/register', '/'];
    final isPublicRoute = publicRoutes.contains(state.uri.path);

    if (authState is AuthUnauthenticated && !isPublicRoute) {
      return '/login';
    }

    if (authState is AuthAuthenticated && state.uri.path == '/login') {
      return '/home';
    }

    return null;
  },
  routes: [ ... ],
);
```

## 5. General Flutter Best Practices from Landbridge

### Code Generation

**Always use code generation for:**
- JSON serialization (`json_serializable`)
- Immutable data classes (`freezed`)
- API clients (`openapi_generator`)

**Setup:**
```yaml
# pubspec.yaml
dev_dependencies:
  build_runner: ^2.4.0
  json_serializable: ^6.7.0
  freezed: ^2.4.0
```

```bash
# Watch mode (recommended during development)
dart run build_runner watch --delete-conflicting-outputs

# One-time build
dart run build_runner build --delete-conflicting-outputs
```

### Immutable Models with Freezed

```dart
import 'package:freezed_annotation/freezed_annotation.dart';

part 'user_profile.freezed.dart';
part 'user_profile.g.dart';

@freezed
class UserProfile with _$UserProfile {
  const factory UserProfile({
    required String userId,
    required String ethnicity,
    required int age,
    List<String>? existingChildrenNames,
  }) = _UserProfile;

  factory UserProfile.fromJson(Map<String, dynamic> json) => _$UserProfileFromJson(json);
}
```

**Benefits:**
- Immutability by default
- `copyWith()` method
- Value equality
- Pattern matching
- JSON serialization

### Platform-Specific Code

**Landbridge approach (conditional imports):**

```dart
// lib/core/client/alotta.dart
import 'package:landbridge_frontend/core/client/mobile.dart'
    if (dart.library.js_interop) 'package:landbridge_frontend/core/client/web.dart';

AlottaClient getAlottaClient(String baseUrl) {
  final AlottaClient alottaClient = AlottaClient(basePathOverride: baseUrl);
  setupClient(alottaClient);  // Platform-specific setup
  return alottaClient;
}
```

**Use when:**
- Different HTTP configurations for web vs mobile
- Platform-specific storage implementations
- Feature flags per platform

### Logging

**Don't use `print()`:**

```dart
// ❌ Bad
print('Error: $error');

// ✅ Good
import 'package:logger/logger.dart';

final _logger = Logger();

_logger.d('Debug message');
_logger.i('Info message');
_logger.w('Warning message');
_logger.e('Error message', error: error, stackTrace: stack);
```

## 6. Action Plan (Priority Order)

### Phase 1: Critical Fixes (Do Immediately)

1. **Add environment configuration**
   - [ ] Add `flutter_dotenv` dependency
   - [ ] Create `.env.dev`, `.env.staging`, `.env.prod`
   - [ ] Update `main.dart` to load env files
   - [ ] Create `EnvConfig` class
   - [ ] Update API client to use dynamic base URL

2. **Fix provider duplication**
   - [ ] Delete duplicate `user_profile_provider.dart`
   - [ ] Consolidate to single provider in `core/`
   - [ ] Update all imports

3. **Add secure token storage**
   - [ ] Add `flutter_secure_storage` dependency
   - [ ] Create `AuthStorageService`
   - [ ] Replace `'default_user'` with real user ID from storage

### Phase 2: Standardization (Do Soon)

4. **Standardize API clients**
   - [ ] Delete manual `api_client.dart`
   - [ ] Update all API wrappers to use generated clients
   - [ ] Add error handling layer
   - [ ] Create Riverpod providers for all APIs

5. **Add logging**
   - [ ] Add `logger` dependency
   - [ ] Replace all `print()` statements
   - [ ] Create centralized logger instance

6. **Code generation setup**
   - [ ] Add `freezed`, `json_serializable` dependencies
   - [ ] Migrate models to Freezed
   - [ ] Setup build_runner watch command

### Phase 3: Architecture Improvements (Do Later)

7. **Add repository pattern (where needed)**
   - [ ] Identify complex features needing repositories
   - [ ] Create repository layer for name discovery
   - [ ] Keep simple CRUD as direct API calls

8. **Authentication flow**
   - [ ] Implement auth state management
   - [ ] Add auth-aware routing
   - [ ] Add login/logout flows

9. **Add BLoC observer**
   - [ ] Create observer for debugging state changes
   - [ ] Add in development mode only

## 7. Key Differences Summary

### Riverpod vs BLoC/Cubit

**Both are excellent state management solutions:**

| Aspect | Riverpod (Babyname) | BLoC/Cubit (Landbridge) |
|--------|---------------------|-------------------------|
| **Learning Curve** | Moderate | Steeper |
| **Boilerplate** | Less | More |
| **Compile-time Safety** | ✅ Yes | ❌ Runtime |
| **Testing** | Easy | Easy |
| **DevTools** | Good | Excellent |
| **Architecture** | Flexible | Structured |
| **Community** | Growing | Mature |

**Verdict:** ✅ **Keep Riverpod** - It's more modern, has less boilerplate, and provides compile-time safety.

### GetIt vs Riverpod for DI

| Aspect | GetIt (Landbridge) | Riverpod (Babyname) |
|--------|---------------------|---------------------|
| **Type** | Service Locator | Provider Pattern |
| **Safety** | Runtime | Compile-time |
| **Disposal** | Manual | Automatic |
| **Testing** | Manual mocking | Provider overrides |
| **Setup** | Centralized (main.dart) | Distributed (providers) |

**Verdict:** ✅ **Keep Riverpod** - No need for GetIt when you have Riverpod.

## 8. Conclusion

**Current Architecture Grade: C+**

**Strengths:**
- ✅ Modern state management (Riverpod)
- ✅ Good feature-based structure
- ✅ Generated API clients available

**Critical Issues:**
- ❌ Hardcoded configuration (not environment-aware)
- ❌ No secure token storage
- ❌ Provider name duplication
- ❌ Mixed API client patterns

**Recommended Improvements:**
1. Add `.env` configuration (**CRITICAL**)
2. Add secure storage (**CRITICAL**)
3. Fix provider duplication (**HIGH**)
4. Standardize on generated API clients (**HIGH**)
5. Add proper logging (**MEDIUM**)
6. Implement Freezed for models (**MEDIUM**)

**After implementing these changes, architecture grade: A-**

---

*For questions or clarifications on any of these patterns, refer to the Landbridge CLAUDE.md or Flutter Best Practices documentation.*
