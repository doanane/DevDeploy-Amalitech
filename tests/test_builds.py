# tests/test_builds.py - Build tests
import pytest
from fastapi import status

@pytest.fixture
def test_project(client, auth_token):
    """Create a test project."""
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
    return response.json()

def test_create_build(client, auth_token, test_project):
    """Test build creation."""
    build_data = {
        "commit_hash": "abc123def456",
        "commit_message": "Test commit"
    }
    
    response = client.post(
        f"/builds/projects/{test_project['id']}/builds",
        json=build_data,
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["project_id"] == test_project["id"]
    assert data["status"] == "pending"
    assert "id" in data

def test_list_builds(client, auth_token, test_project):
    """Test build listing."""
    # Create a build first
    build_data = {
        "commit_hash": "abc123def456",
        "commit_message": "Test commit"
    }
    
    client.post(
        f"/builds/projects/{test_project['id']}/builds",
        json=build_data,
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    # List builds
    response = client.get(
        f"/builds/projects/{test_project['id']}/builds",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["project_id"] == test_project["id"]