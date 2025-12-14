# tests/test_monitoring.py - Monitoring tests
import pytest
from fastapi import status

def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/monitoring/health")
    
    # Health check can return 200 (healthy) or 503 (unhealthy)
    # Both are valid responses for testing
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE]
    
    data = response.json()
    assert "status" in data
    assert "timestamp" in data

def test_metrics(client):
    """Test metrics endpoint."""
    response = client.get("/monitoring/metrics")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "timestamp" in data
    assert "system" in data

def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "message" in data
    assert "status" in data
    assert data["status"] == "running"