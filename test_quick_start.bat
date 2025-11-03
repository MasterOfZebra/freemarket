@echo off
REM Quick test start script for user cabinet system (Windows)
echo 🚀 Starting User Cabinet System Test

REM Check if we're in the right directory
if not exist "backend" (
    echo ❌ Please run this script from the project root directory
    pause
    exit /b 1
)

if not exist "frontend" (
    echo ❌ Please run this script from the project root directory
    pause
    exit /b 1
)

echo 📋 Pre-flight checks...

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed
    pause
    exit /b 1
)

REM Check if Node.js is available
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed
    pause
    exit /b 1
)

echo ✅ Dependencies check passed

REM Backend setup
echo.
echo 🔧 Setting up backend...

cd backend

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
pip install -r requirements.txt

REM Initialize categories (if not already done)
python scripts\init_categories_v6.py

echo ✅ Backend setup complete

REM Start backend (in new window)
echo 🚀 Starting backend server...
start "Backend Server" cmd /k "cd /d %~dp0backend && call venv\Scripts\activate.bat && uvicorn main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 5 /nobreak >nul

REM Check if backend is running
powershell -Command "& {try { $response = Invoke-WebRequest -Uri 'http://localhost:8000/health' -TimeoutSec 5; exit 0 } catch { exit 1 }}" >nul 2>&1
if errorlevel 1 (
    echo ❌ Backend server failed to start
    pause
    exit /b 1
)

echo ✅ Backend server started successfully

REM Frontend setup
echo.
echo 🎨 Setting up frontend...

cd ..\frontend

REM Install dependencies
call npm install

echo ✅ Frontend setup complete

REM Start frontend (in new window)
echo 🚀 Starting frontend server...
start "Frontend Server" cmd /k "cd /d %~dp0frontend && npm start"

timeout /t 10 /nobreak >nul

echo ✅ System startup complete!
echo.
echo 🌐 Access points:
echo   Frontend: http://localhost:3000
echo   Backend API: http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo   Categories API: http://localhost:8000/v1/categories
echo.
echo 🧪 Test checklist:
echo   1. Open http://localhost:3000 in browser
echo   2. Click 'Войти / Регистрация'
echo   3. Register a new account
echo   4. Login and check personal cabinet
echo   5. Create a listing and verify categories
echo.
echo 🛑 Close the command windows to stop servers

pause
