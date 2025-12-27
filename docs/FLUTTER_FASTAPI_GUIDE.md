# Flutter + FastAPI Full-Stack Development Guide

> **Purpose**: Standard patterns and best practices for building full-stack applications with Flutter (frontend) and FastAPI (backend). Use this as a template for new projects.

**Version**: 1.0
**Last Updated**: 2025-12-22

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Project Structure](#project-structure)
3. [API Communication](#api-communication)
4. [State Management](#state-management)
5. [Authentication Flow](#authentication-flow)
6. [Error Handling](#error-handling)
7. [Testing Strategy](#testing-strategy)
8. [Development Workflow](#development-workflow)
9. [Deployment Considerations](#deployment-considerations)
10. [Common Patterns](#common-patterns)

---

## Architecture Overview

### Tech Stack

**Backend (FastAPI)**
- FastAPI 0.100+ (Python 3.11+)
- SQLAlchemy 2.0 (Async ORM)
- Alembic (Migrations)
- Pydantic 2.0 (Validation)
- PostgreSQL 15+ (Database)
- Redis (Caching/Sessions)
- fastapi-users (Auth - optional but recommended)

**Frontend (Flutter)**
- Flutter 3.7+
- Riverpod 2.x (State Management)
- go_router (Navigation)
- OpenAPI Generator (API Client)
- Dio (HTTP client, used by generated code)
- flutter_secure_storage (Token storage)

**Infrastructure**
- Docker Compose (Local development)
- GitHub Actions / GitLab CI (CI/CD)
- Cloud provider (AWS/GCP/Azure for production)

### Communication Flow

```
┌─────────────┐                  ┌─────────────┐
│   Flutter   │ ◄────JSON/HTTP───► │   FastAPI   │
│  (Dart/Web) │                  │   (Python)  │
└─────────────┘                  └─────────────┘
      │                                  │
      │ OpenAPI-generated               │ SQLAlchemy
      │ type-safe client                │ async ORM
      │                                  │
      ▼                                  ▼
┌─────────────┐                  ┌─────────────┐
│  Riverpod   │                  │ PostgreSQL  │
│   Providers │                  │   Database  │
└─────────────┘                  └─────────────┘
```

**Key Principles:**
1. **Single Source of Truth**: Backend owns the schema, frontend consumes it
2. **Type Safety**: End-to-end type safety via OpenAPI
3. **Separation of Concerns**: Clear boundaries between layers
4. **Convention over Configuration**: Follow established patterns

---

## Project Structure

### Monorepo Layout (Recommended)

```
project-name/
├── apps/
│   ├── backend/                # FastAPI application
│   │   ├── app/
│   │   │   ├── main.py        # FastAPI app instance
│   │   │   ├── api/           # API routes
│   │   │   │   ├── v1/        # Versioned API
│   │   │   │   │   ├── endpoints/
│   │   │   │   │   └── router.py
│   │   │   │   └── deps.py    # Shared dependencies
│   │   │   ├── core/          # Core functionality
│   │   │   │   ├── config.py  # Settings
│   │   │   │   ├── security.py
│   │   │   │   └── db.py      # Database setup
│   │   │   ├── models/        # SQLAlchemy models
│   │   │   ├── schemas/       # Pydantic schemas
│   │   │   ├── services/      # Business logic
│   │   │   └── repositories/  # Data access layer
│   │   ├── alembic/           # Database migrations
│   │   ├── tests/
│   │   └── pyproject.toml
│   │
│   └── frontend/              # Flutter application
│       ├── lib/
│       │   ├── main.dart
│       │   ├── core/          # Core functionality
│       │   │   ├── config/    # App configuration
│       │   │   ├── models/    # Custom models
│       │   │   ├── providers/ # App-wide providers
│       │   │   ├── routing/   # Navigation
│       │   │   ├── theme/     # Theming
│       │   │   └── utils/     # Utilities
│       │   ├── features/      # Feature modules
│       │   │   └── {feature}/
│       │   │       ├── models/    # Feature-specific models
│       │   │       ├── providers/ # Feature providers
│       │   │       ├── screens/   # UI screens
│       │   │       ├── widgets/   # Feature widgets
│       │   │       └── services/  # Feature services
│       │   ├── shared/        # Shared widgets/utils
│       │   └── generated/     # Auto-generated code
│       │       └── api/       # OpenAPI client
│       ├── test/
│       └── pubspec.yaml
│
├── docker-compose.yml         # Local development
├── Makefile                   # Development commands
└── docs/
    └── FLUTTER_FASTAPI_GUIDE.md  # This file
```

---

## API Communication

### ⭐ Golden Rule: Use OpenAPI-Generated Client

**NEVER write manual HTTP calls. ALWAYS use OpenAPI-generated client.**

### Backend: Define Pydantic Schemas

```python
# apps/backend/app/schemas/user.py
from pydantic import BaseModel, EmailStr
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True  # SQLAlchemy 2.0
```

### Backend: Create API Endpoints

```python
# apps/backend/app/api/v1/endpoints/users.py
from fastapi import APIRouter, Depends
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserResponse)
async def create_user(
    user: UserCreate,
    service: UserService = Depends()
) -> UserResponse:
    """Create a new user."""
    return await service.create_user(user)

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    service: UserService = Depends()
) -> UserResponse:
    """Get user by ID."""
    return await service.get_user(user_id)
```

### Frontend: Generate Client

1. **Get OpenAPI spec:**
   ```bash
   curl http://localhost:8000/openapi.json > apps/frontend/openapi.json
   ```

2. **Create annotation file** (`apps/frontend/lib/api_client.dart`):
   ```dart
   import 'package:openapi_generator_annotations/openapi_generator_annotations.dart';

   @Openapi(
     additionalProperties: AdditionalProperties(
       pubName: 'api_client',
       pubAuthor: 'Your Name',
     ),
     inputSpec: InputSpec(path: './openapi.json'),
     generatorName: Generator.dart,
     outputDirectory: 'lib/generated/api',
     skipValidateSpec: false,
   )
   class ApiClient {}
   ```

3. **Run generator:**
   ```bash
   cd apps/frontend
   flutter pub run build_runner build --delete-conflicting-outputs
   ```

### Frontend: Use Generated Client with Riverpod

```dart
// apps/frontend/lib/core/providers/api_providers.dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:frontend/generated/api/api.dart';
import 'package:frontend/core/config/api_config.dart';

// Base API client
final apiClientProvider = Provider<ApiClient>((ref) {
  return ApiClient(basePath: ApiConfig.baseUrl);
});

// Users API
final usersApiProvider = Provider<UsersApi>((ref) {
  final client = ref.watch(apiClientProvider);
  return UsersApi(client);
});

// Data provider
final userProvider = FutureProvider.family<UserResponse, int>(
  (ref, userId) async {
    final api = ref.watch(usersApiProvider);
    return await api.getUserUsersUserIdGet(userId: userId);
  },
);
```

### Frontend: Use in Widget

```dart
class UserProfileScreen extends ConsumerWidget {
  final int userId;

  const UserProfileScreen({required this.userId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final userAsync = ref.watch(userProvider(userId));

    return userAsync.when(
      loading: () => CircularProgressIndicator(),
      error: (err, stack) => ErrorWidget(err),
      data: (user) => Column(
        children: [
          Text(user.username),
          Text(user.email),
        ],
      ),
    );
  }
}
```

---

## State Management

### Riverpod Provider Types

**Choose the right provider for the job:**

#### 1. Provider (Immutable)
```dart
// For constants, configuration
final apiConfigProvider = Provider<ApiConfig>((ref) {
  return ApiConfig(baseUrl: 'http://localhost:8000');
});
```

#### 2. FutureProvider (Async Read)
```dart
// For one-time async data fetch
final userListProvider = FutureProvider<List<User>>((ref) async {
  final api = ref.watch(usersApiProvider);
  return await api.getUsersUsersGet();
});
```

#### 3. StreamProvider (Realtime)
```dart
// For realtime data streams
final notificationsProvider = StreamProvider<Notification>((ref) {
  return websocketService.notificationsStream();
});
```

#### 4. StateProvider (Simple State)
```dart
// For simple mutable state
final counterProvider = StateProvider<int>((ref) => 0);

// Usage:
ref.read(counterProvider.notifier).state++;
```

#### 5. StateNotifierProvider (Complex State)
```dart
// For complex state with business logic
class FilterState {
  final String searchQuery;
  final Set<String> selectedTags;

  FilterState({this.searchQuery = '', this.selectedTags = const {}});
}

class FilterNotifier extends StateNotifier<FilterState> {
  FilterNotifier() : super(FilterState());

  void setSearchQuery(String query) {
    state = FilterState(
      searchQuery: query,
      selectedTags: state.selectedTags,
    );
  }

  void toggleTag(String tag) {
    final tags = Set<String>.from(state.selectedTags);
    tags.contains(tag) ? tags.remove(tag) : tags.add(tag);
    state = FilterState(
      searchQuery: state.searchQuery,
      selectedTags: tags,
    );
  }
}

final filterProvider = StateNotifierProvider<FilterNotifier, FilterState>(
  (ref) => FilterNotifier(),
);
```

### Combining Providers

```dart
// Dependent providers
final filteredUsersProvider = FutureProvider<List<User>>((ref) async {
  final filter = ref.watch(filterProvider);
  final api = ref.watch(usersApiProvider);

  return await api.getUsersUsersGet(
    search: filter.searchQuery,
    tags: filter.selectedTags.join(','),
  );
});
```

---

## Authentication Flow

### Backend: JWT Authentication with fastapi-users

```python
# apps/backend/app/core/auth.py
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)

SECRET = "YOUR-SECRET-KEY"

bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

# In main.py
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
```

### Frontend: Token Management

```dart
// apps/frontend/lib/core/providers/auth_provider.dart
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class AuthState {
  final String? token;
  final User? user;
  final bool isAuthenticated;

  AuthState({
    this.token,
    this.user,
    this.isAuthenticated = false,
  });
}

class AuthNotifier extends StateNotifier<AuthState> {
  final FlutterSecureStorage _storage;
  final AuthApi _authApi;

  AuthNotifier(this._storage, this._authApi) : super(AuthState()) {
    _loadToken();
  }

  Future<void> _loadToken() async {
    final token = await _storage.read(key: 'auth_token');
    if (token != null) {
      // Validate token & load user
      try {
        final user = await _authApi.getMeAuthMeGet();
        state = AuthState(
          token: token,
          user: user,
          isAuthenticated: true,
        );
      } catch (e) {
        await logout();
      }
    }
  }

  Future<void> login(String email, String password) async {
    final response = await _authApi.loginAuthJwtLoginPost(
      email: email,
      password: password,
    );

    await _storage.write(key: 'auth_token', value: response.accessToken);

    final user = await _authApi.getMeAuthMeGet();
    state = AuthState(
      token: response.accessToken,
      user: user,
      isAuthenticated: true,
    );
  }

  Future<void> logout() async {
    await _storage.delete(key: 'auth_token');
    state = AuthState();
  }
}

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  return AuthNotifier(
    const FlutterSecureStorage(),
    ref.watch(authApiProvider),
  );
});

// Authenticated API client
final authenticatedApiClientProvider = Provider<ApiClient>((ref) {
  final authState = ref.watch(authProvider);
  final client = ApiClient(basePath: ApiConfig.baseUrl);

  if (authState.token != null) {
    client.addDefaultHeader('Authorization', 'Bearer ${authState.token}');
  }

  return client;
});
```

### Frontend: Route Guards

```dart
// apps/frontend/lib/core/routing/router.dart
import 'package:go_router/go_router.dart';

final routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authProvider);

  return GoRouter(
    refreshListenable: /* create listenable from authProvider */,
    redirect: (context, state) {
      final isAuth = authState.isAuthenticated;
      final isLoggingIn = state.location == '/login';

      // Redirect to login if not authenticated
      if (!isAuth && !isLoggingIn) {
        return '/login';
      }

      // Redirect to home if already authenticated
      if (isAuth && isLoggingIn) {
        return '/';
      }

      return null;
    },
    routes: [
      GoRoute(
        path: '/login',
        builder: (context, state) => LoginScreen(),
      ),
      GoRoute(
        path: '/',
        builder: (context, state) => HomeScreen(),
      ),
      // ... other routes
    ],
  );
});
```

---

## Error Handling

### Backend: Consistent Error Responses

```python
# apps/backend/app/core/exceptions.py
from fastapi import HTTPException, status

class AppException(HTTPException):
    """Base application exception."""
    pass

class NotFoundError(AppException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

class UnauthorizedError(AppException):
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)

class ValidationError(AppException):
    def __init__(self, detail: str = "Validation failed"):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)

# Exception handler
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )
```

### Frontend: Centralized Error Handling

```dart
// apps/frontend/lib/core/errors/api_error.dart
class ApiError implements Exception {
  final int? statusCode;
  final String message;
  final dynamic data;

  ApiError({
    this.statusCode,
    required this.message,
    this.data,
  });

  factory ApiError.fromApiException(ApiException e) {
    return ApiError(
      statusCode: e.code,
      message: e.message ?? 'Unknown error',
      data: e.innerException,
    );
  }

  String get userMessage {
    switch (statusCode) {
      case 401:
        return 'Please log in to continue';
      case 403:
        return 'You don\'t have permission';
      case 404:
        return 'Resource not found';
      case 422:
        return 'Please check your input';
      case 500:
        return 'Server error. Please try again';
      default:
        return message;
    }
  }
}

// Error handling in providers
final userProvider = FutureProvider.family<User, int>((ref, id) async {
  try {
    final api = ref.watch(usersApiProvider);
    return await api.getUserUsersUserIdGet(userId: id);
  } on ApiException catch (e) {
    final error = ApiError.fromApiException(e);
    // Log error
    print('API Error: ${error.message}');
    throw error;
  } catch (e) {
    throw ApiError(message: 'Unexpected error: $e');
  }
});
```

---

## Testing Strategy

### Backend Tests

```python
# apps/backend/tests/test_users.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_user():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/users/",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "password123",
            },
        )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "password" not in data
```

### Frontend Tests

```dart
// apps/frontend/test/features/users/user_provider_test.dart
void main() {
  late MockUsersApi mockApi;
  late ProviderContainer container;

  setUp(() {
    mockApi = MockUsersApi();
    container = ProviderContainer(
      overrides: [
        usersApiProvider.overrideWithValue(mockApi),
      ],
    );
  });

  tearDown(() {
    container.dispose();
  });

  test('userProvider fetches user successfully', () async {
    final mockUser = UserResponse(
      id: 1,
      email: 'test@example.com',
      username: 'testuser',
    );

    when(() => mockApi.getUserUsersUserIdGet(userId: 1))
        .thenAnswer((_) async => mockUser);

    final user = await container.read(userProvider(1).future);

    expect(user.id, 1);
    expect(user.email, 'test@example.com');
    verify(() => mockApi.getUserUsersUserIdGet(userId: 1)).called(1);
  });

  test('userProvider handles errors', () async {
    when(() => mockApi.getUserUsersUserIdGet(userId: 1))
        .thenThrow(ApiException(code: 404, message: 'Not found'));

    expect(
      () => container.read(userProvider(1).future),
      throwsA(isA<ApiError>()),
    );
  });
}
```

---

## Development Workflow

### 1. Backend-First Development

```bash
# 1. Design database models
apps/backend/app/models/user.py

# 2. Create Pydantic schemas
apps/backend/app/schemas/user.py

# 3. Implement API endpoints
apps/backend/app/api/v1/endpoints/users.py

# 4. Test API manually
curl -X POST http://localhost:8000/api/v1/users/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","username":"test","password":"pass"}'

# 5. Export OpenAPI spec
curl http://localhost:8000/openapi.json > ../frontend/openapi.json
```

### 2. Frontend Code Generation

```bash
cd apps/frontend

# Generate API client
flutter pub run build_runner build --delete-conflicting-outputs

# Verify generated code
ls lib/generated/api/lib/model/
```

### 3. Frontend Implementation

```bash
# 1. Create providers
lib/features/users/providers/user_providers.dart

# 2. Create UI
lib/features/users/screens/user_list_screen.dart

# 3. Test
flutter test
```

### 4. Integration Testing

```bash
# Start backend
cd apps/backend
uvicorn app.main:app --reload

# Start frontend
cd apps/frontend
flutter run -d chrome

# Manual testing or E2E tests
```

---

## Common Patterns

### Pagination

**Backend:**
```python
from fastapi import Query

@router.get("/users/", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=100),
    service: UserService = Depends(),
):
    return await service.list_users(skip=skip, limit=limit)
```

**Frontend:**
```dart
final usersPageProvider = FutureProvider.family<List<User>, int>(
  (ref, page) async {
    final api = ref.watch(usersApiProvider);
    final skip = page * 20;
    return await api.listUsersUsersGet(skip: skip, limit: 20);
  },
);
```

### Search & Filtering

**Backend:**
```python
@router.get("/users/search", response_model=List[UserResponse])
async def search_users(
    q: str = Query(..., min_length=1),
    service: UserService = Depends(),
):
    return await service.search_users(query=q)
```

**Frontend:**
```dart
final searchQueryProvider = StateProvider<String>((ref) => '');

final searchResultsProvider = FutureProvider<List<User>>((ref) async {
  final query = ref.watch(searchQueryProvider);
  if (query.isEmpty) return [];

  final api = ref.watch(usersApiProvider);
  return await api.searchUsersUsersSearchGet(q: query);
});
```

### File Uploads

**Backend:**
```python
from fastapi import UploadFile, File

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()
    # Process file
    return {"filename": file.filename}
```

**Frontend:**
```dart
import 'package:file_picker/file_picker.dart';

Future<void> uploadFile() async {
  final result = await FilePicker.platform.pickFiles();
  if (result != null) {
    final file = result.files.first;
    final api = ref.read(filesApiProvider);
    await api.uploadFileUploadPost(file: MultipartFile.fromBytes(
      'file',
      file.bytes!,
      filename: file.name,
    ));
  }
}
```

---

## Deployment Considerations

### Environment Configuration

**Backend `.env`:**
```bash
DATABASE_URL=postgresql+asyncpg://user:pass@host/db
SECRET_KEY=your-secret-key
CORS_ORIGINS=https://yourapp.com,https://www.yourapp.com
```

**Frontend (build-time):**
```bash
flutter build web --dart-define=API_BASE_URL=https://api.yourapp.com
```

### Docker Deployment

```dockerfile
# Backend Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# Frontend Dockerfile
FROM cirrusci/flutter:stable AS build
WORKDIR /app
COPY . .
RUN flutter build web --release

FROM nginx:alpine
COPY --from=build /app/build/web /usr/share/nginx/html
```

---

## Checklist for New Projects

### Backend Setup
- [ ] Create FastAPI project structure
- [ ] Set up SQLAlchemy models
- [ ] Configure Alembic migrations
- [ ] Implement Pydantic schemas
- [ ] Create API endpoints with proper typing
- [ ] Add authentication (fastapi-users)
- [ ] Write unit tests
- [ ] Configure CORS
- [ ] Set up error handling
- [ ] Document API with docstrings

### Frontend Setup
- [ ] Create Flutter project
- [ ] Add dependencies (riverpod, dio, etc.)
- [ ] Configure openapi_generator
- [ ] Generate API client
- [ ] Create API client providers
- [ ] Implement authentication flow
- [ ] Set up routing (go_router)
- [ ] Create feature structure
- [ ] Write widget tests
- [ ] Configure build flavors

### Integration
- [ ] Verify OpenAPI generation works
- [ ] Test authentication flow end-to-end
- [ ] Implement error handling
- [ ] Add loading states
- [ ] Test pagination
- [ ] Verify file uploads work
- [ ] Test on multiple platforms
- [ ] Performance testing
- [ ] Security audit
- [ ] Documentation

---

**This guide should be updated as patterns evolve and new best practices emerge.**
