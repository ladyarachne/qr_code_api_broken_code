import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from app.main import app  # Import your FastAPI app

def test_login_for_access_token():
    form_data = {
        "username": "admin",
        "password": "secret",
    }
    client = TestClient(app)
    response = client.post("/api/v1/auth/token", data=form_data)
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_create_qr_code_unauthorized():
    # Attempt to create a QR code without authentication
    qr_request = {
        "url": "https://example.com",
        "fill_color": "red",
        "back_color": "white",
        "size": 10,
    }
    client = TestClient(app)
    response = client.post("/api/v1/qr-codes/", json=qr_request)
    assert response.status_code == 401  # Unauthorized

def test_create_and_delete_qr_code():
    form_data = {
        "username": "admin",
        "password": "secret",
    }
    client = TestClient(app)
    # Login and get the access token
    token_response = client.post("/api/v1/auth/token", data=form_data)
    access_token = token_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # Create a QR code
    qr_request = {
        "url": "https://example.com",
        "fill_color": "red",
        "back_color": "white",
        "size": 10,
    }
    create_response = client.post("/api/v1/qr-codes/", json=qr_request, headers=headers)
    assert create_response.status_code in [201, 409]  # Created or already exists

    # If the QR code was created, attempt to delete it
    if create_response.status_code == 201:
        qr_code_url = create_response.json()["qr_code_url"]
        qr_filename = qr_code_url.split('/')[-1]
        delete_response = client.delete(f"/api/v1/qr-codes/{qr_filename}", headers=headers)
        assert delete_response.status_code == 204  # No Content, successfully deleted
