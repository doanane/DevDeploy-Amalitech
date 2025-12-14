# test_all_endpoints.py - Test all endpoints
import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def print_result(test_name, success, message=""):
    """Print test result."""
    status = "PASS" if success else "FAIL"
    print(f"[{status}] {test_name}")
    if message:
        print(f"     {message}")

def test_root():
    """Test root endpoint."""
    try:
        response = requests.get(BASE_URL, timeout=5)
        if response.status_code == 200:
            return True, "API is running"
        return False, f"Status: {response.status_code}"
    except Exception as e:
        return False, str(e)

def test_register():
    """Test user registration."""
    data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "TestPass123!"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=data, timeout=5)
        if response.status_code == 200:
            return True, "User registered"
        elif response.status_code == 400 and "already" in response.text:
            return True, "User already exists"
        return False, f"Status: {response.status_code}, Response: {response.text}"
    except Exception as e:
        return False, str(e)

def test_login():
    """Test user login."""
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            params={"username": "test@example.com", "password": "TestPass123!"},
            timeout=5
        )
        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get("access_token")
            return True, token
        return False, f"Status: {response.status_code}, Response: {response.text}"
    except Exception as e:
        return False, str(e)

def test_auth_me(token):
    """Test /auth/me endpoint."""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers, timeout=5)
        if response.status_code == 200:
            return True, "User info retrieved"
        return False, f"Status: {response.status_code}"
    except Exception as e:
        return False, str(e)

def test_create_project(token):
    """Test project creation."""
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "name": "Test Project",
        "repository_url": "https://github.com/octocat/Hello-World",
        "branch": "main",
        "status": "active"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/projects/", json=data, headers=headers, timeout=5)
        if response.status_code == 200:
            project = response.json()
            return True, f"Project created (ID: {project.get('id')})", project.get('id')
        return False, f"Status: {response.status_code}, Response: {response.text}", None
    except Exception as e:
        return False, str(e), None

def test_list_projects(token):
    """Test project listing."""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(f"{BASE_URL}/projects/", headers=headers, timeout=5)
        if response.status_code == 200:
            projects = response.json()
            return True, f"Found {len(projects)} projects"
        return False, f"Status: {response.status_code}"
    except Exception as e:
        return False, str(e)

def test_create_build(token, project_id):
    """Test build creation."""
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "commit_hash": "abc123",
        "commit_message": "Test commit"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/builds/projects/{project_id}/builds",
            json=data,
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            build = response.json()
            return True, f"Build created (ID: {build.get('id')})", build.get('id')
        return False, f"Status: {response.status_code}, Response: {response.text}", None
    except Exception as e:
        return False, str(e), None

def test_list_builds(token, project_id):
    """Test build listing."""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(
            f"{BASE_URL}/builds/projects/{project_id}/builds",
            headers=headers,
            timeout=5
        )
        if response.status_code == 200:
            builds = response.json()
            return True, f"Found {len(builds)} builds"
        return False, f"Status: {response.status_code}"
    except Exception as e:
        return False, str(e)

def test_health_check():
    """Test health check."""
    try:
        response = requests.get(f"{BASE_URL}/monitoring/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            return True, f"Health: {health.get('status')}"
        return False, f"Status: {response.status_code}"
    except Exception as e:
        return False, str(e)

def test_metrics():
    """Test metrics endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/monitoring/metrics", timeout=5)
        if response.status_code == 200:
            return True, "Metrics retrieved"
        return False, f"Status: {response.status_code}"
    except Exception as e:
        return False, str(e)

def test_queue_status():
    """Test queue status endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/monitoring/queue", timeout=5)
        if response.status_code == 200:
            return True, "Queue status retrieved"
        return False, f"Status: {response.status_code}"
    except Exception as e:
        return False, str(e)

def test_notifications():
    """Test notifications endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/notifications/", timeout=5)
        if response.status_code == 200:
            return True, "Notifications retrieved"
        return False, f"Status: {response.status_code}"
    except Exception as e:
        return False, str(e)

def test_notification_preferences():
    """Test notification preferences endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/notifications/preferences", timeout=5)
        if response.status_code == 200:
            return True, "Preferences retrieved"
        return False, f"Status: {response.status_code}"
    except Exception as e:
        return False, str(e)

def test_webhooks():
    """Test webhooks availability."""
    try:
        response = requests.get(BASE_URL, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("features", {}).get("webhooks", False):
                return True, "Webhooks available"
            return True, "Webhooks not configured"
        return False, "API not reachable"
    except Exception as e:
        return False, str(e)

def main():
    """Run all tests."""
    print("=" * 60)
    print("DEVDEPLOY API COMPREHENSIVE TEST")
    print("=" * 60)
    
    results = []
    
    # Test 1: Root endpoint
    success, message = test_root()
    results.append(("Root endpoint", success, message))
    print_result("Root endpoint", success, message)
    
    if not success:
        print("API not reachable. Exiting.")
        sys.exit(1)
    
    # Test 2: Registration
    success, message = test_register()
    results.append(("User registration", success, message))
    print_result("User registration", success, message)
    
    # Test 3: Login
    success, message = test_login()
    results.append(("User login", success, "Login successful" if success else message))
    print_result("User login", success, "Login successful" if success else message)
    
    if not success or not isinstance(message, str):
        print("Login failed. Cannot test protected endpoints.")
        token = None
    else:
        token = message
    
    # Test protected endpoints if login successful
    if token:
        # Test 4: Auth me
        success, message = test_auth_me(token)
        results.append(("/auth/me", success, message))
        print_result("/auth/me", success, message)
        
        # Test 5: Create project
        success, message, project_id = test_create_project(token)
        results.append(("Create project", success, message))
        print_result("Create project", success, message)
        
        if project_id:
            # Test 6: List projects
            success, message = test_list_projects(token)
            results.append(("List projects", success, message))
            print_result("List projects", success, message)
            
            # Test 7: Create build
            success, message, build_id = test_create_build(token, project_id)
            results.append(("Create build", success, message))
            print_result("Create build", success, message)
            
            # Test 8: List builds
            success, message = test_list_builds(token, project_id)
            results.append(("List builds", success, message))
            print_result("List builds", success, message)
    
    # Test system endpoints
    print("\n" + "=" * 60)
    print("SYSTEM ENDPOINTS")
    print("=" * 60)
    
    # Test 9: Health check
    success, message = test_health_check()
    results.append(("Health check", success, message))
    print_result("Health check", success, message)
    
    # Test 10: Metrics
    success, message = test_metrics()
    results.append(("Metrics", success, message))
    print_result("Metrics", success, message)
    
    # Test 11: Queue status
    success, message = test_queue_status()
    results.append(("Queue status", success, message))
    print_result("Queue status", success, message)
    
    # Test 12: Notifications
    success, message = test_notifications()
    results.append(("Notifications", success, message))
    print_result("Notifications", success, message)
    
    # Test 13: Notification preferences
    success, message = test_notification_preferences()
    results.append(("Notification preferences", success, message))
    print_result("Notification preferences", success, message)
    
    # Test 14: Webhooks
    success, message = test_webhooks()
    results.append(("Webhooks", success, message))
    print_result("Webhooks", success, message)
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for test_name, success, message in results:
        status = "PASS" if success else "FAIL"
        print(f"{status}: {test_name}")
        if not success and message:
            print(f"     -> {message}")
    
    print("\n" + "=" * 60)
    print(f"TOTAL: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("ALL TESTS PASSED!")
    elif passed >= total * 0.8:
        print("MOST TESTS PASSED")
    else:
        print("MANY TESTS FAILED")
    
    print("\nSwagger UI: http://localhost:8000/docs")
    print("Test credentials:")
    print("  Email: test@example.com")
    print("  Password: TestPass123!")

if __name__ == "__main__":
    main()