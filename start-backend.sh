#!/bin/bash

# Baby Names Social Network - Backend Startup Script
# This script starts the FastAPI backend server

set -e

echo "🚀 Starting Baby Names Backend..."
echo ""

# Navigate to backend directory
cd "$(dirname "$0")/apps/backend"

# Check if .venv exists
if [ ! -d ".venv" ]; then
    echo "📦 Installing dependencies with UV..."
    uv sync
fi

# Start the FastAPI server
echo "✅ Starting FastAPI server on http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo "📋 OpenAPI Spec: http://localhost:8000/openapi.json"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uv run fastapi dev app/main.py --port 8000
