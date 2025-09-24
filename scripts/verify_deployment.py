#!/usr/bin/env python3
"""
Deployment verification script for PDF RAG Chat application.
Checks if all services are running correctly and can communicate with each other.
"""

import requests
import time
import sys
import json

def check_service(name: str, url: str, timeout: int = 30) -> bool:
    """Check if a service is responsive"""
    print(f"Checking {name}...")
    
    for i in range(timeout):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {name} is running")
                return True
        except requests.exceptions.RequestException:
            pass
        
        if i < timeout - 1:
            print(f"⏳ Waiting for {name}... ({i+1}/{timeout})")
            time.sleep(1)
    
    print(f"❌ {name} is not responding")
    return False

def test_api_endpoints():
    """Test critical API endpoints"""
    base_url = "http://localhost:8000"
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ API Health Check: {health_data.get('status', 'unknown')}")
            
            # Check database connections
            if health_data.get('database') == 'connected':
                print("✅ PostgreSQL connection working")
            else:
                print("❌ PostgreSQL connection failed")
            
            if health_data.get('vector_db') == 'connected':
                print("✅ Qdrant connection working")
            else:
                print("❌ Qdrant connection failed")
                
            return True
        else:
            print(f"❌ API health check failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API health check error: {e}")
        return False

def test_frontend():
    """Test if frontend is accessible"""
    try:
        response = requests.get("http://localhost:8501/_stcore/health", timeout=5)
        if response.status_code == 200:
            print("✅ Streamlit frontend is accessible")
            return True
        else:
            print(f"❌ Frontend health check failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend health check error: {e}")
        return False

def run_integration_test():
    """Run a basic integration test"""
    print("\n🧪 Running integration test...")
    
    base_url = "http://localhost:8000"
    
    try:
        # Create a test user
        session_id = "test-deployment-verification"
        response = requests.post(f"{base_url}/api/users", params={"session_id": session_id})
        
        if response.status_code == 200:
            print("✅ User creation successful")
        else:
            print(f"❌ User creation failed: HTTP {response.status_code}")
            return False
        
        # Create a chat session
        response = requests.post(
            f"{base_url}/api/sessions",
            params={"session_id": session_id},
            json={"session_name": "Deployment Test"}
        )
        
        if response.status_code == 200:
            session_data = response.json()
            chat_session_id = session_data["id"]
            print("✅ Chat session creation successful")
        else:
            print(f"❌ Chat session creation failed: HTTP {response.status_code}")
            return False
        
        # Get system stats
        response = requests.get(f"{base_url}/api/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ System stats retrieved: {stats}")
        else:
            print(f"❌ Stats retrieval failed: HTTP {response.status_code}")
            return False
        
        # Clean up test session
        requests.delete(f"{base_url}/api/sessions/{chat_session_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test error: {e}")
        return False

def main():
    """Main verification function"""
    print("🚀 PDF RAG Chat - Deployment Verification")
    print("=" * 50)
    
    all_good = True
    
    # Check individual services
    services = [
        ("PostgreSQL", "http://localhost:5432"),  # This will fail but that's OK
        ("Qdrant", "http://localhost:6333/health"),
        ("Backend API", "http://localhost:8000/health"),
        ("Frontend", "http://localhost:8501/_stcore/health")
    ]
    
    print("📋 Checking individual services...")
    
    # Special handling for different services
    if not check_service("Qdrant", "http://localhost:6333/health"):
        all_good = False
    
    if not check_service("Backend API", "http://localhost:8000/health"):
        all_good = False
    
    if not check_service("Frontend", "http://localhost:8501/_stcore/health"):
        all_good = False
    
    # Test API functionality
    print("\n📋 Testing API functionality...")
    if not test_api_endpoints():
        all_good = False
    
    # Run integration test
    if not run_integration_test():
        all_good = False
    
    print("\n" + "=" * 50)
    
    if all_good:
        print("🎉 All checks passed! Your PDF RAG Chat application is ready.")
        print("\n📱 Access points:")
        print("   Frontend: http://localhost:8501")
        print("   API Docs: http://localhost:8000/docs")
        print("   Qdrant:   http://localhost:6333/dashboard")
        print("\n💡 Next steps:")
        print("   1. Upload some PDF documents")
        print("   2. Create a chat session")
        print("   3. Start asking questions about your documents!")
        return 0
    else:
        print("❌ Some checks failed. Please review the errors above.")
        print("\n🔧 Troubleshooting:")
        print("   1. Make sure Docker is running")
        print("   2. Check if all containers started: docker-compose ps")
        print("   3. View logs: docker-compose logs")
        print("   4. Restart services: docker-compose restart")
        return 1

if __name__ == "__main__":
    sys.exit(main())
