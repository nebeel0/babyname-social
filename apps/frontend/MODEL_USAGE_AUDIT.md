# Frontend Model Usage Audit

**Date:** December 26, 2025
**Purpose:** Identify duplication between manual models and auto-generated models

## Executive Summary

| Status | Count | Details |
|--------|-------|---------|
| ✅ **Auto-Generated Models Available** | 34 | From OpenAPI spec in `lib/generated/api/lib/model/` |
| ❌ **Manual Model Duplicates** | 2 | In `lib/core/models/` duplicating generated ones |
| ⚠️ **Manual Models with Purpose** | 4 classes | Enhancement classes with helper methods |
| 🔧 **Files to Update** | 3 | Files using manual `UserProfile` |

**Verdict:** Moderate duplication found. Migration recommended for `UserProfile`.

---

## 1. Model Inventory

### Auto-Generated Models (34 total)

Located in: `/home/ben/babyname-social/universe1/apps/frontend/lib/generated/api/lib/model/`

**User/Auth Models:**
- `user_create.dart`
- `user_read.dart`
- `user_update.dart`
- `bearer_response.dart`

**Profile Models:**
- ✅ `user_profile_create.dart`
- ✅ `user_profile_read.dart` ⬅️ **We should use this!**
- ✅ `user_profile_update.dart`

**Name Models:**
- `name_create.dart`
- `name_read.dart`
- `name_update.dart`
- ✅ `name_with_enhancements.dart` ⬅️ **We should use this!**

**Enhancement/Enrichment Models:**
- ✅ `ethnicity_probability.dart`
- ✅ `nickname_info.dart`
- ✅ `feature_description.dart`
- `famous_namesake.dart`
- `name_trivia.dart`
- `related_name.dart`
- `popularity_trend.dart`
- `popularity_range.dart`

**Preferences Models:**
- `user_preference_create.dart`
- `user_preference_read.dart`

**Prefix Tree Models:**
- `prefix_node_read.dart`
- `prefix_tree_response.dart`
- `prefix_names_response.dart`
- `gender_counts.dart`

**Error Models:**
- `error_model.dart`
- `http_validation_error.dart`
- `validation_error.dart`
- `detail.dart`

**Auth Flow Models:**
- `body_reset_forgot_password_auth_forgot_password_post.dart`
- `body_reset_reset_password_auth_reset_password_post.dart`
- `body_verify_request_token_auth_request_verify_token_post.dart`
- `body_verify_verify_auth_verify_post.dart`

### Manual Models (2 files, 5 classes)

Located in: `/home/ben/babyname-social/universe1/apps/frontend/lib/core/models/`

**File 1: `user_profile.dart`** (176 lines)
- ❌ **DUPLICATE**: `UserProfile` class
  - Duplicates: `UserProfileRead` + `UserProfileCreate` + `UserProfileUpdate`
  - Has 176 lines of manual JSON serialization
  - Has manual `copyWith()` method
  - **Recommendation:** DELETE and migrate to generated models

**File 2: `name_enhancements.dart`** (167 lines)
- ⚠️ `EthnicityProbability` class (68 lines)
  - ✅ **HAS GENERATED EQUIVALENT**: `lib/generated/api/lib/model/ethnicity_probability.dart`
  - ❌ **BUT ADDS VALUE**: Helper methods (`getProbability()`, `dominantEthnicity`)
  - **Recommendation:** Extend generated class or create extension methods

- ⚠️ `NicknameInfo` class (16 lines)
  - ✅ **HAS GENERATED EQUIVALENT**: `lib/generated/api/lib/model/nickname_info.dart`
  - ✅ **NO ADDED VALUE**: Exact duplicate
  - **Recommendation:** DELETE and use generated model

- ⚠️ `CulturalFitScore` class (54 lines)
  - ❓ **NO GENERATED EQUIVALENT**: Appears to be frontend-only composite model
  - ✅ **HAS HELPER**: `hasData` getter
  - **Recommendation:** KEEP (frontend-only model)

- ⚠️ `FeatureDescription` class (29 lines)
  - ✅ **HAS GENERATED EQUIVALENT**: `lib/generated/api/lib/model/feature_description.dart`
  - ✅ **NO ADDED VALUE**: Exact duplicate
  - **Recommendation:** DELETE and use generated model

---

## 2. Detailed Comparison

### UserProfile vs UserProfileRead

**Manual Model** (`lib/core/models/user_profile.dart`):
```dart
class UserProfile {
  final int? id;
  final String userId;
  final String? ethnicity;
  // ... 20+ fields

  UserProfile({ /* manual constructor */ });
  factory UserProfile.fromJson(Map<String, dynamic> json) { /* manual parsing */ }
  Map<String, dynamic> toJson() { /* manual serialization */ }
  UserProfile copyWith({ /* manual 150-line copyWith */ });
}
```

**Generated Model** (`lib/generated/api/lib/model/user_profile_read.dart`):
```dart
class UserProfileRead {
  int id;
  String userId;
  String createdAt;  // ⬅️ Generated has this as String (ISO format)
  String updatedAt;  // ⬅️ Generated has this as String (ISO format)
  String? ethnicity;
  // ... same fields

  UserProfileRead({ /* auto-generated */ });
  static UserProfileRead? fromJson(dynamic value) { /* auto-generated with validation */ }
  Map<String, dynamic> toJson() { /* auto-generated */ }
  // ⚠️ No copyWith() - but do we need it? (immutable pattern)
}
```

**Key Differences:**

| Aspect | Manual `UserProfile` | Generated `UserProfileRead` |
|--------|----------------------|------------------------------|
| **Lines of Code** | 176 | 370 (more features) |
| **DateTime Handling** | `DateTime?` objects | `String` (ISO 8601) |
| **Validation** | None | Built-in assertions |
| **Equality** | No `==` operator | Full `==` and `hashCode` |
| **copyWith()** | Yes (manual) | No (use Create/Update models) |
| **Maintainability** | Manual updates needed | Auto-regenerates |

**Migration Impact:**

1. **DateTime handling change:**
   ```dart
   // OLD
   profile.createdAt  // DateTime?

   // NEW
   DateTime.parse(profile.createdAt)  // Need to parse ISO string
   ```

2. **No copyWith()** - Use separate models:
   ```dart
   // OLD
   final updated = profile.copyWith(age: 31);

   // NEW - Use UserProfileUpdate model
   final updateData = UserProfileUpdate(age: 31);
   await profilesApi.updateProfile(userId, updateData);
   ```

3. **Required fields:**
   - Manual: Only `userId` required
   - Generated: `id`, `userId`, `createdAt`, `updatedAt` required

---

## 3. Current Usage Analysis

### UserProfile (Manual Model) Usage

**Files using manual `UserProfile`:** 3 files

1. **`lib/features/profile/screens/profile_onboarding_screen.dart`**
   - Creates new `UserProfile` instances
   - Calls `profile.toJson()` for API
   - ✅ Easy migration: Use `UserProfileCreate` instead

2. **`lib/features/profile/screens/profile_settings_screen.dart`**
   - Displays profile data in UI
   - Read-only access to fields
   - ✅ Easy migration: Use `UserProfileRead` instead

3. **`lib/features/profile/providers/user_profile_provider.dart`**
   - Stores profile in state
   - Converts to/from JSON
   - ✅ Medium migration: Update provider types

**Usage Patterns:**

```dart
// Pattern 1: Creating new profiles (ONBOARDING)
final profile = UserProfile(
  userId: 'user-123',
  ethnicity: 'Asian',
  age: 30,
  // ...
);
await api.createProfile(profile.toJson());

// Pattern 2: Displaying existing profiles (SETTINGS)
Text('Ethnicity: ${profile.ethnicity}')
Text('Age: ${profile.age} years old')

// Pattern 3: State management (PROVIDER)
final userProfileProvider = FutureProvider<UserProfile?>((ref) async {
  final json = await api.getProfile(userId);
  return UserProfile.fromJson(json);
});
```

---

## 4. Migration Plan

### Phase 1: Low-Hanging Fruit (30 minutes)

**Delete exact duplicates in `name_enhancements.dart`:**

```bash
# Files to update:
- lib/core/models/name_enhancements.dart
```

**Changes:**

1. ❌ **Delete** `NicknameInfo` class (lines 70-89)
   - Already exists in `lib/generated/api/lib/model/nickname_info.dart`
   - Exact duplicate, no added value

2. ❌ **Delete** `FeatureDescription` class (lines 138-167)
   - Already exists in `lib/generated/api/lib/model/feature_description.dart`
   - Exact duplicate, no added value

**After deletions, `name_enhancements.dart` will contain:**
- ✅ KEEP: `EthnicityProbability` (with helper methods)
- ✅ KEEP: `CulturalFitScore` (frontend-only model)

### Phase 2: EthnicityProbability Enhancement (45 minutes)

**Option A: Extension Methods** (Recommended)

```dart
// lib/core/extensions/ethnicity_probability_extensions.dart
import 'package:frontend/generated/api/lib/model/ethnicity_probability.dart';

extension EthnicityProbabilityHelpers on EthnicityProbability {
  /// Get probability for a specific ethnicity
  double getProbabilityForEthnicity(String ethnicity) {
    switch (ethnicity.toLowerCase()) {
      case 'white': return whiteProbability ?? 0.0;
      case 'black': return blackProbability ?? 0.0;
      case 'hispanic': return hispanicProbability ?? 0.0;
      case 'asian': return asianProbability ?? 0.0;
      case 'other': return otherProbability ?? 0.0;
      default: return 0.0;
    }
  }

  /// Get the dominant ethnicity (highest probability)
  String get dominantEthnicity {
    final probs = {
      'White': whiteProbability ?? 0.0,
      'Black': blackProbability ?? 0.0,
      'Hispanic': hispanicProbability ?? 0.0,
      'Asian': asianProbability ?? 0.0,
      'Other': otherProbability ?? 0.0,
    };
    return probs.entries.reduce((a, b) => a.value > b.value ? a : b).key;
  }
}
```

**Option B: Wrapper Class** (If you need state)

```dart
// lib/core/models/ethnicity_analysis.dart
import 'package:frontend/generated/api/lib/model/ethnicity_probability.dart';

class EthnicityAnalysis {
  final EthnicityProbability data;

  EthnicityAnalysis(this.data);

  double getProbability(String ethnicity) => /* same logic */;
  String get dominantEthnicity => /* same logic */;
}
```

**Recommendation:** Use **Extension Methods** (Option A) - cleaner and no duplication.

### Phase 3: UserProfile Migration (2-3 hours)

**Step 1: Update ProfileApi to use generated models**

```dart
// lib/core/api/profile_api.dart
import 'package:frontend/generated/api/lib/model/user_profile_read.dart';
import 'package:frontend/generated/api/lib/model/user_profile_create.dart';
import 'package:frontend/generated/api/lib/model/user_profile_update.dart';

class ProfileApi {
  final ApiClient _client = ApiClient();

  Future<UserProfileRead?> getProfile(String userId) async {
    try {
      final data = await _client.get('/profiles/$userId');
      return UserProfileRead.fromJson(data);
    } on NotFoundException {
      return null;
    }
  }

  Future<UserProfileRead> createProfile(UserProfileCreate profile) async {
    final data = await _client.post('/profiles/', profile.toJson());
    return UserProfileRead.fromJson(data)!;
  }

  Future<UserProfileRead> updateProfile(String userId, UserProfileUpdate updates) async {
    final data = await _client.put('/profiles/$userId', updates.toJson());
    return UserProfileRead.fromJson(data)!;
  }
}
```

**Step 2: Update providers**

```dart
// lib/features/profile/providers/user_profile_provider.dart
import 'package:frontend/generated/api/lib/model/user_profile_read.dart';

final userProfileProvider = FutureProvider<UserProfileRead?>((ref) async {
  final profileApi = ref.watch(profileApiProvider);
  const userId = 'default_user';

  try {
    final profile = await profileApi.getProfile(userId);
    return profile;
  } catch (e) {
    return null;
  }
});
```

**Step 3: Update onboarding screen**

```dart
// lib/features/profile/screens/profile_onboarding_screen.dart
import 'package:frontend/generated/api/lib/model/user_profile_create.dart';

Future<void> _saveProfile() async {
  final profileCreate = UserProfileCreate(
    userId: 'default_user',
    ethnicity: ethnicity,
    age: age,
    currentState: currentState,
    currentCity: currentCity,
    country: country ?? 'US',
    // ... other fields
  );

  await ref.read(userProfileProvider.notifier).createProfile(profileCreate);
}
```

**Step 4: Update settings screen**

```dart
// lib/features/profile/screens/profile_settings_screen.dart
import 'package:frontend/generated/api/lib/model/user_profile_read.dart';

Widget build(BuildContext context, WidgetRef ref) {
  final profileAsync = ref.watch(userProfileProvider);

  return profileAsync.when(
    data: (UserProfileRead? profile) {
      if (profile == null) {
        return /* No profile UI */;
      }

      // ⚠️ NOTE: createdAt is now String, not DateTime
      final createdDate = DateTime.parse(profile.createdAt);

      return /* Profile display */;
    },
    // ...
  );
}
```

**Step 5: Delete manual model**

```bash
# After all migrations complete:
rm lib/core/models/user_profile.dart
```

---

## 5. Risk Assessment

### Low Risk
- ✅ Deleting `NicknameInfo` duplicate
- ✅ Deleting `FeatureDescription` duplicate
- ✅ Adding extension methods for `EthnicityProbability`

### Medium Risk
- ⚠️ Migrating `UserProfile` → `UserProfileRead`/`Create`/`Update`
  - Datetime handling changes (String ↔ DateTime)
  - No more `copyWith()` (need to use Update model)
  - Only 3 files to update

### Test Plan

1. **Unit Tests:**
   ```bash
   flutter test test/unit/providers/user_profile_provider_test.dart
   ```

2. **Manual Testing:**
   - [ ] Create new profile via onboarding
   - [ ] Verify profile displays in settings
   - [ ] Update profile fields
   - [ ] Check DateTime fields parse correctly

---

## 6. Benefits of Migration

### Immediate Benefits
1. ✅ **Reduced Maintenance:** 176 lines of manual code deleted
2. ✅ **Automatic Updates:** Models regenerate when backend changes
3. ✅ **Type Safety:** Generated models have validation
4. ✅ **Consistency:** Same models used everywhere
5. ✅ **Better Equality:** Generated models have `==` and `hashCode`

### Long-Term Benefits
1. ✅ **No Schema Drift:** Frontend always matches backend
2. ✅ **Fewer Bugs:** Validation catches missing required fields
3. ✅ **Easier Onboarding:** New devs know to use generated models
4. ✅ **Better Tooling:** IDE autocomplete for all fields

---

## 7. Estimated Effort

| Task | Time | Difficulty |
|------|------|------------|
| Delete `NicknameInfo` duplicate | 10 min | Easy |
| Delete `FeatureDescription` duplicate | 10 min | Easy |
| Create `EthnicityProbability` extensions | 30 min | Easy |
| Update ProfileApi | 30 min | Medium |
| Update providers | 30 min | Medium |
| Update onboarding screen | 30 min | Medium |
| Update settings screen | 30 min | Medium |
| Testing | 45 min | Medium |
| **Total** | **3.5 hours** | **Medium** |

---

## 8. Recommended Action Plan

### Option 1: Do It All Now (Recommended)
- Complete migration in one session
- Prevents confusion with mixed models
- Clean slate going forward
- **Time:** 3.5 hours

### Option 2: Incremental Migration
- Phase 1: Delete exact duplicates (20 min)
- Phase 2: Add extensions (30 min)
- Phase 3: Migrate UserProfile later (2-3 hours)
- **Time:** 3.5 hours total (spread over time)
- **Risk:** Temporary inconsistency

### Option 3: Leave As-Is
- Keep manual models
- Risk of drift from backend
- Continue maintaining 176 lines manually
- **Not Recommended**

---

## 9. Post-Migration Checklist

After completing migration:

- [ ] All 3 files using `UserProfile` updated
- [ ] Manual `user_profile.dart` deleted
- [ ] Duplicate enhancement classes deleted
- [ ] Extension methods created for `EthnicityProbability`
- [ ] Unit tests passing
- [ ] Manual testing complete
- [ ] Update `FRONTEND_ARCHITECTURE_ANALYSIS.md`
- [ ] Document decision in ADR (Architecture Decision Record)

---

## 10. Conclusion

**Current State:**
- ❌ 2 duplicate model files
- ❌ 176 lines of redundant code
- ❌ Manual maintenance burden
- ⚠️ Risk of schema drift

**After Migration:**
- ✅ Single source of truth (generated models)
- ✅ Automatic updates from backend
- ✅ Type-safe validation
- ✅ Reduced maintenance

**Recommendation:** ✅ **Proceed with full migration (Option 1)**

The migration is straightforward, low-risk, and provides immediate value. The 3.5-hour investment will pay off in reduced maintenance and fewer bugs.

---

*For questions or to begin migration, refer to the step-by-step instructions in Phase 1-3 above.*
