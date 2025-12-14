# tests/test_auth.py - Authentication tests
import pytest
from fastapi import status

def test_register_user(client, test_user_data):
    """Test user registration."""
    response = client.post("/auth/register", json=test_user_data)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "id" in data
    assert data["email"] == test_user_data["email"]
    assert data["username"] == test_user_data["username"]
    assert "password" not in data

def test_register_duplicate_email(client, test_user_data):
    """Test duplicate email registration."""
    # First registration
    client.post("/auth/register", json=test_user_data)
    
    # Second registration with same email
    response = client.post("/auth/register", json=test_user_data)
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already" in response.json()["detail"].lower()

def test_login_success(client, test_user_data):
    """Test successful login."""
    # Register first
    client.post("/auth/register", json=test_user_data)
    
    # Login
    response = client.post(
        "/auth/login",
        params={
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password(client, test_user_data):
    """Test login with wrong password."""
    # Register
    client.post("/auth/register", json=test_user_data)
    
    # Login with wrong password
    response = client.post(
        "/auth/login",
        params={
            "username": test_user_data["email"],
            "password": "WrongPass123!"
        }
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_current_user(client, test_user_data):
    """Test get current user endpoint."""
    # Register and login
    client.post("/auth/register", json=test_user_data)
    login_response = client.post(
        "/auth/login",
        params={
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        }
    )
    token = login_response.json()["access_token"]
    
    # Get current user
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == test_user_data["email"]
    assert data["username"] == test_user_data["username"]