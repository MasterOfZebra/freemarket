#!/bin/bash

# Quick test start script for user cabinet system
echo "🚀 Starting User Cabinet System Test"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in the right directory
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

echo "📋 Pre-flight checks..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python3 is not installed"
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed"
    exit 1
fi

print_status "Dependencies check passed"

# Backend setup
echo ""
echo "🔧 Setting up backend..."

cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_warning "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize categories (if not already done)
python scripts/init_categories_v6.py

print_status "Backend setup complete"

# Start backend in background
echo "🚀 Starting backend server..."
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 3

# Check if backend is running
if curl -s http://localhost:8000/health > /dev/null; then
    print_status "Backend server started successfully"
else
    print_error "Backend server failed to start"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Frontend setup
echo ""
echo "🎨 Setting up frontend..."

cd ../frontend

# Install dependencies
npm install

print_status "Frontend setup complete"

# Start frontend in background
echo "🚀 Starting frontend server..."
npm start &
FRONTEND_PID=$!

# Wait for frontend to start
sleep 10

print_status "System startup complete!"
echo ""
echo "🌐 Access points:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "  Categories API: http://localhost:8000/v1/categories"
echo ""
echo "🧪 Test checklist:"
echo "  1. Open http://localhost:3000 in browser"
echo "  2. Click 'Войти / Регистрация'"
echo "  3. Register a new account"
echo "  4. Login and check personal cabinet"
echo "  5. Create a listing and verify categories"
echo ""
echo "🛑 To stop: Ctrl+C"

# Wait for user interrupt
trap "echo ''; print_warning 'Shutting down...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT
wait
