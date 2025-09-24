#!/bin/bash

# Start the backend API server for local development
# This script sets up the correct Python path and runs uvicorn

echo "🚀 Starting PDF RAG Backend API..."

# Change to the project root directory
cd "$(dirname "$0")/.."

# Set Python path to include the current directory
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Virtual environment not detected. Activate your venv first:"
    echo "   source .venv/bin/activate"
    exit 1
fi

# Check if required environment variables are set
if [[ -z "$GEMINI_API_KEY" ]]; then
    echo "⚠️  GEMINI_API_KEY not set. Loading from .env file..."
    if [[ -f ".env" ]]; then
        export $(cat .env | grep -v '^#' | xargs)
    else
        echo "❌ No .env file found. Please create one from .env.example"
        exit 1
    fi
fi

echo "✅ Environment configured"
echo "📡 Starting server on http://localhost:8000"
echo "📖 API documentation: http://localhost:8000/docs"
echo ""

# Start the server
cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000
