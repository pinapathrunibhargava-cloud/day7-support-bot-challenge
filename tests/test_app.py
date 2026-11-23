import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_chat_returns_a_reply(client):
    response = client.post(
        "/chat",
        headers={"Authorization": "Bearer demo-ravi-token"},
        json={"message": "Hello"}
    )

    assert response.status_code == 200
    assert "reply" in response.get_json()


def test_order_status(client):
    response = client.post(
        "/chat",
        headers={"Authorization": "Bearer demo-ravi-token"},
        json={"message": "Where is my order 10231?"}
    )

    assert response.status_code == 200
    assert response.get_json()["action_result"] == "Shipped"


def test_unknown_order_is_denied(client):
    response = client.post(
        "/chat",
        headers={"Authorization": "Bearer demo-priya-token"},
        json={"message": "What is the status of order 99999?"}
    )

    assert response.status_code == 403


def test_unauthorized_access(client):
    response = client.post(
        "/chat",
        json={"message": "Where is my order 10231?"}
    )

    assert response.status_code == 401


def test_customer_cannot_access_another_customers_order(client):
    response = client.post(
        "/chat",
        headers={"Authorization": "Bearer demo-ravi-token"},
        json={"message": "What is the status of order 10232?"}
    )

    assert response.status_code == 403


def test_refund_cannot_exceed_order_amount(client):
    response = client.post(
        "/chat",
        headers={"Authorization": "Bearer demo-ravi-token"},
        json={"message": "Please refund Rs 2000 for order 10231"}
    )

    assert response.status_code == 400


def test_valid_refund(client):
    response = client.post(
        "/chat",
        headers={"Authorization": "Bearer demo-ravi-token"},
        json={"message": "Please refund Rs 200 for order 10231"}
    )

    assert response.status_code == 200
    assert "Refunded Rs 200" in response.get_json()["action_result"]