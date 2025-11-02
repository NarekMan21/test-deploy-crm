"""
Базовые тесты для заказов
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def get_admin_token():
    """Получить токен администратора"""
    response = client.post(
        "/api/auth/login",
        data={"username": "admin1", "password": "nimda"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]

def get_logist_token():
    """Получить токен логистики"""
    response = client.post(
        "/api/auth/login",
        data={"username": "logist", "password": "logist"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]

def test_create_order_as_admin():
    """Тест создания заказа администратором"""
    token = get_admin_token()
    response = client.post(
        "/api/orders/",
        data={
            "customer_name": "Test Customer",
            "customer_phone": "+79991234567",
            "customer_address": "Test Address 123"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "message" in data

def test_create_order_unauthorized():
    """Тест создания заказа без авторизации"""
    response = client.post(
        "/api/orders/",
        data={
            "customer_name": "Test Customer",
            "customer_phone": "+79991234567",
            "customer_address": "Test Address 123"
        }
    )
    assert response.status_code == 403

def test_create_order_invalid_data():
    """Тест создания заказа с невалидными данными"""
    token = get_admin_token()
    response = client.post(
        "/api/orders/",
        data={
            "customer_name": "",
            "customer_phone": "+79991234567",
            "customer_address": "Test Address 123"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400

def test_get_orders():
    """Тест получения списка заказов"""
    token = get_admin_token()
    response = client.get(
        "/api/orders/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_order_not_found():
    """Тест получения несуществующего заказа"""
    token = get_admin_token()
    response = client.get(
        "/api/orders/99999",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404

