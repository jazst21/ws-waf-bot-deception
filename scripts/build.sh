#!/bin/bash

# Bot Trapper Build Script - React Version
# Builds both React frontend and backend for production

echo "🏗️  Building Bot Trapper for Production (React)"
echo "=============================================="

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Build React frontend
echo "⚛️  Building React Frontend SPA..."
cd "$PROJECT_DIR/source/frontend"

if [ ! -d "node_modules" ]; then
    echo "📦 Installing React frontend dependencies..."
    npm install
fi

npm run build

if [ $? -eq 0 ]; then
    echo "✅ React frontend build completed successfully"
    echo "📁 Build output: $PROJECT_DIR/source/frontend/dist"
else
    echo "❌ React frontend build failed"
    exit 1
fi

# Prepare backend for deployment
echo ""
echo "🖥️  Preparing Backend for deployment..."
cd "$PROJECT_DIR/source/backend"

if [ ! -d "node_modules" ]; then
    echo "📦 Installing backend dependencies..."
    npm install --production
fi

echo "✅ Backend prepared for deployment"

echo ""
echo "🎉 Build completed successfully!"
echo ""
echo "📁 React Frontend build: $PROJECT_DIR/source/frontend/dist"
echo "📁 Backend source: $PROJECT_DIR/source/backend"
echo ""
echo "Next steps:"
echo "1. Deploy React frontend dist/ to S3"
echo "2. Deploy backend to Lambda"
echo "3. CloudFront will serve the React SPA"
