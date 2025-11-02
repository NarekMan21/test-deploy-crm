"""
Базовые тесты для аутентификации
"""
import pytest
from fastapi.testclient import TestClient
from main import app

# TestClient автоматически обрабатывает async функции
client = TestClient(app)

def test_health_check():
    """Тест проверки здоровья API"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_login_success():
    """Тест успешного входа"""
    response = client.post(
        "/api/auth/login",
        data={"username": "admin1", "password": "nimda"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"
    assert "user" in data

def test_login_invalid_credentials():
    """Тест входа с неверными учетными данными"""
    response = client.post(
        "/api/auth/login",
        data={"username": "admin1", "password": "wrongpassword"}
    )
    assert response.status_code == 401

def test_login_empty_username():
    """Тест входа с пустым именем пользователя"""
    response = client.post(
        "/api/auth/login",
        data={"username": "", "password": "nimda"}
    )
    assert response.status_code == 400

def test_get_me_without_token():
    """Тест получения информации о пользователе без токена"""
    response = client.get("/api/auth/me")
    assert response.status_code == 403

def test_get_me_with_token():
    """Тест получения информации о пользователе с токеном"""
    # Сначала логинимся
    login_response = client.post(
        "/api/auth/login",
        data={"username": "admin1", "password": "nimda"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Затем используем токен
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "username" in data
    assert "role" in data

