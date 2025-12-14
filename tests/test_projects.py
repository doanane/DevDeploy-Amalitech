# tests/test_projects.py - Project tests
import pytest
from fastapi import status

@pytest.fixture
def auth_token(client, test_user_data):
    """Get authentication token."""
    client.post("/auth/register", json=test_user_data)
    login_response = client.post(
        "/auth/login",
        params={
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        }
    )
    return login_response.json()["access_token"]

def test_create_project(client, auth_token):
    """Test project creation."""
    project_data = {
        "name": "Test Project",
        "repository_url": "https://github.com/testuser/test-repo",
        "branch": "main",
        "status": "active"
    }
    
    response = client.post(
        "/projects/",
        json=project_data,
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == project_data["name"]
    assert data["repository_url"] == project_data["repository_url"]
    assert data["branch"] == project_data["branch"]
    assert "id" in data
    assert "owner_id" in data

def test_list_projects(client, auth_token):
    """Test project listing."""
    # Create a project first
    project_data = {
        "name": "Test Project",
        "repository_url": "https://github.com/testuser/test-repo",
        "branch": "main",
        "status": "active"
    }
    
    client.post(
        "/projects/",
        json=project_data,
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    # List projects
    response = client.get(
        "/projects/",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["name"] == project_data["name"]

def test_create_project_unauthorized(client):
    """Test project creation without authentication."""
    project_data = {
        "name": "Test Project",
        "repository_url": "https://github.com/testuser/test-repo",
        "branch": "main",
        "status": "active"
    }
    
    response = client.post("/projects/", json=project_data)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED