#!/bin/bash

echo "🔧 Fixing dependency compatibility issues..."

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Virtual environment not detected. Activating .venv..."
    if [[ -f ".venv/bin/activate" ]]; then
        source .venv/bin/activate
        echo "✅ Activated virtual environment"
    else
        echo "❌ No .venv found. Please create one first:"
        echo "   python3 -m venv .venv"
        echo "   source .venv/bin/activate"
        exit 1
    fi
fi

echo "📦 Uninstalling problematic packages..."
pip uninstall -y sentence-transformers transformers huggingface_hub torch

echo "📦 Installing compatible versions..."
pip install huggingface_hub==0.19.4
pip install transformers==4.36.0
pip install torch==2.1.1 --index-url https://download.pytorch.org/whl/cpu
pip install sentence-transformers==2.3.1

echo "📦 Installing other required packages..."
pip install numpy==1.24.4

echo "✅ Dependencies fixed! You can now run the backend."
echo "🚀 Try: cd backend && uvicorn main:app --reload"
