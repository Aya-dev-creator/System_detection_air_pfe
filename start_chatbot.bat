@echo off
REM Quick Start Script for Weather Chatbot (Windows)

echo.
echo 🤖 Weather Chatbot - Quick Start Guide
echo ======================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://www.python.org/
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo ✅ Python found: %PYTHON_VERSION%
echo.

REM Check if .env file exists
if not exist .env (
    echo ⚠️  .env file not found!
    echo Creating .env from template...
    copy .env.example .env >nul
    echo.
    echo 📝 Please edit .env and add your MISTRAL_API_KEY:
    echo    MISTRAL_API_KEY=your_key_here
    echo.
)

REM Install requirements
echo 📦 Installing dependencies...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

echo ✅ Dependencies installed successfully
echo.

REM Check for Mistral API key
findstr /M "MISTRAL_API_KEY=your_mistral_api_key_here" .env >nul 2>&1
if %errorlevel% equ 0 (
    echo ⚠️  MISTRAL_API_KEY not configured!
    echo.
    echo Please do the following:
    echo 1. Visit: https://console.mistral.ai/
    echo 2. Sign up for a free account
    echo 3. Generate an API key
    echo 4. Edit .env and replace: MISTRAL_API_KEY=your_mistral_api_key_here
    echo 5. Run this script again
    echo.
    pause
    exit /b 1
)

echo ✅ MISTRAL_API_KEY is configured
echo.

REM Create data directory if needed
if not exist data mkdir data

echo 🚀 Starting the server...
echo.
echo ═══════════════════════════════════════════════════════════
echo 🌐 Open your browser and go to:
echo.
echo    📱 Chatbot:    http://localhost:5000/chatbot
echo    📊 Dashboard:  http://localhost:5000/
echo    🗺️  Map:        http://localhost:5000/map
echo    📰 News:       http://localhost:5000/news
echo    🔮 AI Predictions: http://localhost:5000/predictions
echo.
echo ═══════════════════════════════════════════════════════════
echo.

REM Start the server
python web_server.py

pause
