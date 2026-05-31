#!/bin/bash
# Quick Start Script for Weather Chatbot

echo "🤖 Weather Chatbot - Quick Start Guide"
echo "======================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python found: $(python3 --version)"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "Creating .env from template..."
    cp .env.example .env
    echo ""
    echo "📝 Please edit .env and add your MISTRAL_API_KEY:"
    echo "   MISTRAL_API_KEY=your_key_here"
    echo ""
fi

# Install requirements
echo "📦 Installing dependencies..."
pip install -r requirements.txt --quiet

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed successfully"
echo ""

# Check for Mistral API key
if grep -q "MISTRAL_API_KEY=your_mistral_api_key_here" .env; then
    echo "⚠️  MISTRAL_API_KEY not configured!"
    echo ""
    echo "Please do the following:"
    echo "1. Visit: https://console.mistral.ai/"
    echo "2. Sign up for a free account"
    echo "3. Generate an API key"
    echo "4. Edit .env and replace: MISTRAL_API_KEY=your_mistral_api_key_here"
    echo "5. Run this script again"
    echo ""
    exit 1
fi

echo "✅ MISTRAL_API_KEY is configured"
echo ""

# Create data directory if needed
mkdir -p data

echo "🚀 Starting the server..."
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "🌐 Open your browser and go to:"
echo ""
echo "   📱 Chatbot:    http://localhost:5000/chatbot"
echo "   📊 Dashboard:  http://localhost:5000/"
echo "   🗺️  Map:        http://localhost:5000/map"
echo "   📰 News:       http://localhost:5000/news"
echo "   🔮 AI Predictions: http://localhost:5000/predictions"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""

# Start the server
python3 web_server.py
