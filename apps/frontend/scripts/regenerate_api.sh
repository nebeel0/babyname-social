#!/bin/bash
set -e

# OpenAPI Client Regeneration Script
# This script automates the process of regenerating the Flutter OpenAPI client
# and applying necessary fixes for known generator bugs.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_URL="${BACKEND_URL:-http://localhost:8001}"
OPENAPI_SPEC="$FRONTEND_DIR/openapi.json"

echo "🔧 OpenAPI Client Regeneration"
echo "==============================="
echo "Frontend directory: $FRONTEND_DIR"
echo "Backend URL: $BACKEND_URL"
echo ""

cd "$FRONTEND_DIR"

# Step 1: Download fresh OpenAPI spec
echo "📥 Step 1: Downloading OpenAPI spec from $BACKEND_URL/openapi.json..."
if ! curl -f "$BACKEND_URL/openapi.json" -o "$OPENAPI_SPEC" 2>/dev/null; then
    echo "❌ Error: Could not download OpenAPI spec from $BACKEND_URL/openapi.json"
    echo "   Make sure the backend is running on $BACKEND_URL"
    exit 1
fi
echo "✅ Downloaded $(wc -c < "$OPENAPI_SPEC") bytes"
echo ""

# Step 2: Clean cache to force regeneration
echo "🧹 Step 2: Cleaning OpenAPI generator cache..."
rm -f .dart_tool/openapi-generator-cache.json
echo "✅ Cache cleared"
echo ""

# Step 3: Remove old generated files
echo "🗑️  Step 3: Removing old generated files..."
rm -rf lib/generated/api
echo "✅ Old files removed"
echo ""

# Step 4: Run OpenAPI generator
echo "⚙️  Step 4: Running OpenAPI generator..."
if ! flutter pub run build_runner build --delete-conflicting-outputs 2>&1 | tee /tmp/openapi_generation.log; then
    echo "⚠️  Generation completed with warnings (this is expected)"
else
    echo "✅ Generation completed"
fi
echo ""

# Step 5: Apply fixes for known generator bugs
echo "🔧 Step 5: Applying fixes for known generator bugs..."

# Fix 1: Fix empty named parameter lists in Detail class
DETAIL_FILE="lib/generated/api/lib/model/detail.dart"
if [ -f "$DETAIL_FILE" ]; then
    echo "  Fixing Detail class..."
    # Fix constructor: Detail({ }) -> Detail()
    sed -i 's/Detail({\s*});/Detail();/g' "$DETAIL_FILE"
    # Fix fromJson return: Detail( ) -> Detail()
    sed -i 's/return Detail(\s*);/return Detail();/g' "$DETAIL_FILE"
    # Fix incomplete operator==
    sed -i 's/other is Detail &&$/other is Detail;/g' "$DETAIL_FILE"
    # Fix incomplete hashCode
    sed -i '/int get hashCode =>$/,/^$/ { /int get hashCode =>$/ { N; s/int get hashCode =>\s*\/\/ ignore: unnecessary_parenthesis\s*/int get hashCode => 0;/g; } }' "$DETAIL_FILE"
    # Alternative simpler fix for hashCode
    sed -i 's/int get hashCode =>\s*$/int get hashCode => 0;/g' "$DETAIL_FILE"
    # Remove orphaned comment lines
    sed -i '/^[[:space:]]*\/\/ ignore: unnecessary_parenthesis[[:space:]]*$/d' "$DETAIL_FILE"
    echo "  ✅ Detail class fixed"
fi

# Fix 2: Fix empty named parameter lists in ValidationErrorLocInner class
VALIDATION_FILE="lib/generated/api/lib/model/validation_error_loc_inner.dart"
if [ -f "$VALIDATION_FILE" ]; then
    echo "  Fixing ValidationErrorLocInner class..."
    # Fix constructor: ValidationErrorLocInner({ }) -> ValidationErrorLocInner()
    sed -i 's/ValidationErrorLocInner({\s*});/ValidationErrorLocInner();/g' "$VALIDATION_FILE"
    # Fix fromJson return: ValidationErrorLocInner( ) -> ValidationErrorLocInner()
    sed -i 's/return ValidationErrorLocInner(\s*);/return ValidationErrorLocInner();/g' "$VALIDATION_FILE"
    # Fix incomplete operator==
    sed -i 's/other is ValidationErrorLocInner &&$/other is ValidationErrorLocInner;/g' "$VALIDATION_FILE"
    # Fix incomplete hashCode
    sed -i 's/int get hashCode =>\s*$/int get hashCode => 0;/g' "$VALIDATION_FILE"
    # Remove orphaned comment lines
    sed -i '/^[[:space:]]*\/\/ ignore: unnecessary_parenthesis[[:space:]]*$/d' "$VALIDATION_FILE"
    echo "  ✅ ValidationErrorLocInner class fixed"
fi

echo "✅ All fixes applied"
echo ""

# Step 6: Verify compilation
echo "🔍 Step 6: Verifying compilation..."
if flutter analyze 2>&1 | grep -q "^  error"; then
    echo "⚠️  Compilation errors found:"
    flutter analyze 2>&1 | grep "^  error"
    echo ""
    echo "❌ Please review and fix errors manually"
    exit 1
else
    echo "✅ No compilation errors found"
fi
echo ""

echo "🎉 OpenAPI client regeneration completed successfully!"
echo ""
echo "Summary:"
echo "  - OpenAPI spec: $OPENAPI_SPEC"
echo "  - Generated files: lib/generated/api/"
echo "  - Fixes applied: Detail, ValidationErrorLocInner classes"
echo ""
echo "Next steps:"
echo "  1. Review the generated code"
echo "  2. Run tests: flutter test"
echo "  3. Build: flutter build web"
