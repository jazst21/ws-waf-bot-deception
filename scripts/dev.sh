#!/bin/bash

# Bot Trapper Development Script - React Version
# Starts both React frontend and backend in development mode

echo "🚀 Starting Bot Trapper Development Environment (React)"
echo "====================================================="

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm first."
    exit 1
fi

# Function to install dependencies
install_deps() {
    local dir=$1
    local name=$2
    
    echo "📦 Installing $name dependencies..."
    cd "$dir"
    if [ ! -d "node_modules" ]; then
        npm install
    else
        echo "✅ $name dependencies already installed"
    fi
    cd - > /dev/null
}

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Install dependencies
install_deps "$PROJECT_DIR/source/backend" "Backend"
install_deps "$PROJECT_DIR/source/frontend" "React Frontend"

echo ""
echo "🔧 Starting services..."
echo ""

# Function to start backend
start_backend() {
    echo "🖥️  Starting Backend API (Port 3001)..."
    cd "$PROJECT_DIR/source/backend"
    npm run dev &
    BACKEND_PID=$!
    echo "Backend PID: $BACKEND_PID"
    echo "Backend file: app.js"
}

# Function to start React frontend
start_frontend() {
    echo "⚛️  Starting React Frontend SPA (Port 3000)..."
    cd "$PROJECT_DIR/source/frontend"
    npm run dev &
    FRONTEND_PID=$!
    echo "React Frontend PID: $FRONTEND_PID"
}

# Start backend first
start_backend
sleep 3

# Start React frontend
start_frontend
sleep 3

echo ""
echo "✅ Development environment started!"
echo ""
echo "⚛️  React Frontend: http://localhost:3000"
echo "🖥️  Backend API:    http://localhost:3001"
echo "📊 API Status:     http://localhost:3001/api/status"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        echo "✅ Backend stopped"
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
        echo "✅ React Frontend stopped"
    fi
    
    echo "👋 Development environment stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Wait for processes
wait
