# tests/test_auth.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_user_registration():
    response = client.post("/auth/signup", json={
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
    assert "email" in response.json()
    assert "id" in response.json()

def test_user_login():
    response = client.post("/auth/login", json={
        "email": "test@example.com", 
        "password": "password123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_protected_route_without_token():
    response = client.get("/projects/")
    assert response.status_code == 401