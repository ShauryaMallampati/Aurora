#!/bin/bash

# Aurora Split View - Development Server Startup Script

echo "🚀 Starting AURORA Split View Development Server"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Navigate to aurora-web directory
cd /Users/ankit/Aurora/aurora-web

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
  echo "📦 Installing dependencies..."
  npm install
  echo ""
fi

# Start dev server
echo "✨ Starting development server..."
echo ""
echo "📍 URL: http://localhost:3000"
echo "⏹️  Stop with: Ctrl+C"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

npm run dev
