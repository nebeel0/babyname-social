#!/bin/bash

# Baby Names Social Network - Frontend Startup Script
# This script starts the Flutter web application

set -e

echo "🚀 Starting Baby Names Frontend..."
echo ""

# Navigate to frontend directory
cd "$(dirname "$0")/apps/frontend"

# Check if dependencies are installed
if [ ! -d ".dart_tool" ]; then
    echo "📦 Installing Flutter dependencies..."
    flutter pub get
fi

# Start Flutter web
echo "✅ Starting Flutter web app"
echo "🌐 Opening in Chrome..."
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

flutter run -d chrome
