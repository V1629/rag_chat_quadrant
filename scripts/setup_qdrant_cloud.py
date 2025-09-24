#!/usr/bin/env python3
"""
Script to setup and test Qdrant Cloud connection for PDF RAG application.
This script helps configure and verify Qdrant Cloud integration.
"""

import os
import sys
from pathlib import Path

# Add backend to path for imports
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams
    from config import QDRANT_URL, QDRANT_API_KEY
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure you have the required packages installed:")
    print("pip install qdrant-client python-dotenv")
    sys.exit(1)


def test_connection():
    """Test connection to Qdrant Cloud."""
    print("🔧 Testing Qdrant Cloud connection...")
    print(f"URL: {QDRANT_URL}")
    print(f"API Key: {'✅ Set' if QDRANT_API_KEY else '❌ Not set'}")
    
    if not QDRANT_API_KEY:
        print("❌ QDRANT_API_KEY is not set in environment variables")
        print("Please set your Qdrant Cloud API key in the .env file")
        return False
    
    try:
        client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
        
        # Test connection by getting cluster info
        collections = client.get_collections()
        print(f"✅ Successfully connected to Qdrant Cloud!")
        print(f"📊 Found {len(collections.collections)} existing collections")
        
        return True
    except Exception as e:
        print(f"❌ Failed to connect to Qdrant Cloud: {e}")
        print("\n🔍 Troubleshooting tips:")
        print("1. Verify your API key is correct")
        print("2. Check your cluster URL format")
        print("3. Ensure your cluster is running")
        print("4. Check firewall/network settings")
        return False


def setup_collection():
    """Setup the pdf_embeddings collection if it doesn't exist."""
    print("\n🏗️ Setting up pdf_embeddings collection...")
    
    try:
        client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
        
        # Check if collection exists
        collections = client.get_collections()
        collection_names = [col.name for col in collections.collections]
        
        if "pdf_embeddings" in collection_names:
            print("✅ Collection 'pdf_embeddings' already exists")
            collection_info = client.get_collection("pdf_embeddings")
            print(f"📊 Collection info: {collection_info}")
        else:
            print("🔨 Creating 'pdf_embeddings' collection...")
            client.create_collection(
                collection_name="pdf_embeddings",
                vectors_config=VectorParams(
                    size=384,  # all-MiniLM-L6-v2 embedding dimension
                    distance=Distance.COSINE
                )
            )
            print("✅ Collection 'pdf_embeddings' created successfully!")
        
        return True
    except Exception as e:
        print(f"❌ Failed to setup collection: {e}")
        return False


def display_config_help():
    """Display configuration help for Qdrant Cloud."""
    print("\n📝 Qdrant Cloud Configuration Help")
    print("=" * 50)
    print("\n1. Get your Qdrant Cloud credentials:")
    print("   - Go to https://cloud.qdrant.io/")
    print("   - Create an account and cluster")
    print("   - Get your cluster URL and API key")
    print("\n2. Update your .env file:")
    print("   QDRANT_URL=https://your-cluster.europe-west3-0.gcp.cloud.qdrant.io:6333")
    print("   QDRANT_API_KEY=your_api_key_here")
    print("\n3. For Docker deployment:")
    print("   docker-compose up -d  # (without --profile local-qdrant)")
    print("\n4. For local development:")
    print("   Make sure to source your .env file or set environment variables")


def main():
    """Main function to run Qdrant Cloud setup and testing."""
    print("🚀 Qdrant Cloud Setup Script")
    print("=" * 40)
    
    # Check if we have the required environment variables
    if not QDRANT_URL or not QDRANT_API_KEY:
        print("❌ Missing required environment variables")
        display_config_help()
        return
    
    # Test connection
    if not test_connection():
        display_config_help()
        return
    
    # Setup collection
    if not setup_collection():
        return
    
    print("\n🎉 Qdrant Cloud setup completed successfully!")
    print("Your PDF RAG application is ready to use Qdrant Cloud.")


if __name__ == "__main__":
    main()
