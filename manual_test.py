# manual_test.py - Manual testing without dependencies
import requests
import json

BASE_URL = "http://localhost:8000"

def print_response(label, response):
    """Print formatted response."""
    print(f"\n{'='*60}")
    print(f"{label}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"Body: {response.text[:500]}...")

def test_authentication():
    """Test authentication manually."""
    print("\n🔐 TESTING AUTHENTICATION")
    
    # 1. Register a new user
    print("\n1. Registering new user...")
    register_data = {
        "email": "dev@example.com",
        "username": "devuser",
        "password": "DevPass123!"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
        print_response("REGISTER RESPONSE", response)
        
        if response.status_code == 200:
            print("✅ Registration successful")
        elif response.status_code == 400:
            error = response.json().get("detail", "")
            if "already" in error.lower():
                print("⚠️  User already exists, trying login...")
            else:
                print(f"❌ Registration error: {error}")
                return None
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return None
    
    # 2. Login
    print("\n2. Logging in...")
    login_data = {
        "username": "dev@example.com",  # Use email as username
        "password": "DevPass123!",
        "grant_type": "password"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        print_response("LOGIN RESPONSE", response)
        
        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get("access_token")
            print(f"✅ Login successful!")
            print(f"   Token: {token[:50]}...")
            return token
        else:
            print("❌ Login failed")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_with_token(token):
    """Test endpoints with token."""
    if not token:
        print("\n❌ No token, skipping protected endpoints")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n🔧 TESTING PROTECTED ENDPOINTS")
    
    # 1. Test /auth/me
    print("\n1. Testing /auth/me...")
    try:
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        print_response("AUTH/ME RESPONSE", response)
        if response.status_code == 200:
            print("✅ Get current user successful")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # 2. Create project
    print("\n2. Creating project...")
    project_data = {
        "name": "My First Project",
        "repository_url": "https://github.com/octocat/Hello-World",
        "branch": "main",
        "status": "active"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/projects/", json=project_data, headers=headers)
        print_response("CREATE PROJECT RESPONSE", response)
        if response.status_code == 200:
            project = response.json()
            project_id = project.get("id")
            print(f"✅ Project created (ID: {project_id})")
            return project_id
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return None

def test_builds(token, project_id):
    """Test build endpoints."""
    if not token or not project_id:
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n🔨 TESTING BUILDS")
    
    # Create build
    print(f"\n1. Creating build for project {project_id}...")
    build_data = {
        "commit_hash": "abc123",
        "commit_message": "Initial commit"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/builds/projects/{project_id}/builds",
            json=build_data,
            headers=headers
        )
        print_response("CREATE BUILD RESPONSE", response)
        if response.status_code == 200:
            print("✅ Build created")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_public_endpoints():
    """Test public endpoints."""
    print("\n🌐 TESTING PUBLIC ENDPOINTS")
    
    # Root endpoint
    print("\n1. Testing root endpoint...")
    try:
        response = requests.get(BASE_URL)
        print_response("ROOT RESPONSE", response)
        if response.status_code == 200:
            print("✅ API is running")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Health check
    print("\n2. Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/monitoring/health")
        print_response("HEALTH CHECK RESPONSE", response)
        if response.status_code == 200:
            print("✅ Health check passed")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Run manual tests."""
    print("=" * 60)
    print("DEVDEPLOY MANUAL TEST")
    print("=" * 60)
    
    # Test public endpoints first
    test_public_endpoints()
    
    # Test authentication
    token = test_authentication()
    
    if token:
        # Test with token
        project_id = test_with_token(token)
        
        if project_id:
            test_builds(token, project_id)
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()