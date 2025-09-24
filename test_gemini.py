#!/usr/bin/env python3
"""
Script to test Gemini API and list available models
"""

import os
import sys
from pathlib import Path

# Add backend to path for imports
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

try:
    import google.generativeai as genai
    from backend.config import settings
    
    print(f"🔧 Testing Gemini API")
    print(f"API Key: {'✅ Set' if settings.GEMINI_API_KEY else '❌ Not set'}")
    
    if not settings.GEMINI_API_KEY:
        print("❌ Please set GEMINI_API_KEY in your .env file")
        sys.exit(1)
    
    # Configure API
    genai.configure(api_key=settings.GEMINI_API_KEY)
    
    print("\n📋 Available models:")
    try:
        models = genai.list_models()
        for model in models:
            if 'generateContent' in model.supported_generation_methods:
                print(f"  ✅ {model.name}")
    except Exception as e:
        print(f"❌ Error listing models: {e}")
    
    print(f"\n🧪 Testing model: {settings.GEMINI_MODEL}")
    try:
        model = genai.GenerativeModel(settings.GEMINI_MODEL)
        response = model.generate_content("Hello, can you respond with 'Test successful'?")
        print(f"✅ Model test successful!")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Model test failed: {e}")
        
        # Try alternative models
        alternative_models = [
            "gemini-1.5-pro-latest",
            "gemini-1.5-flash-latest", 
            "gemini-pro",
            "models/gemini-1.5-pro",
            "models/gemini-1.5-flash"
        ]
        
        print("\n🔄 Trying alternative models:")
        for alt_model in alternative_models:
            try:
                print(f"  Testing {alt_model}...")
                model = genai.GenerativeModel(alt_model)
                response = model.generate_content("Test")
                print(f"  ✅ {alt_model} works!")
                print(f"  Response: {response.text}")
                break
            except Exception as alt_e:
                print(f"  ❌ {alt_model} failed: {alt_e}")
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure you have the required packages installed:")
    print("pip install google-generativeai")
    sys.exit(1)
