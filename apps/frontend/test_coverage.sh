#!/bin/bash

# Frontend Test Coverage Script
# This script runs tests with coverage and enforces minimum coverage thresholds

set -e

echo "🧪 Running Flutter tests with coverage..."

# Clean previous coverage
rm -rf coverage

# Generate mock classes for testing
echo "📝 Generating mocks..."
flutter pub run build_runner build --delete-conflicting-outputs

# Run tests with coverage
echo "🏃 Running tests..."
flutter test --coverage

# Check if coverage was generated
if [ ! -f "coverage/lcov.info" ]; then
    echo "❌ Coverage file not generated"
    exit 1
fi

echo "✅ Tests passed!"
echo ""
echo "📊 Coverage Report:"
echo "==================="

# Install lcov if not available (for generating HTML reports)
if ! command -v lcov &> /dev/null; then
    echo "⚠️  lcov not installed. Install with: sudo apt-get install lcov"
    echo "Skipping HTML report generation..."
else
    # Generate HTML report
    genhtml coverage/lcov.info -o coverage/html
    echo "📄 HTML coverage report generated at: coverage/html/index.html"
fi

# Parse coverage percentage
if command -v lcov &> /dev/null; then
    COVERAGE=$(lcov --summary coverage/lcov.info 2>&1 | grep "lines" | awk '{print $2}' | sed 's/%//')

    echo ""
    echo "Total Line Coverage: $COVERAGE%"

    # Set minimum coverage threshold
    MIN_COVERAGE=60

    if (( $(echo "$COVERAGE < $MIN_COVERAGE" | bc -l) )); then
        echo "❌ Coverage $COVERAGE% is below minimum threshold of $MIN_COVERAGE%"
        exit 1
    else
        echo "✅ Coverage threshold met!"
    fi
fi

echo ""
echo "To view detailed coverage report:"
echo "  open coverage/html/index.html"
