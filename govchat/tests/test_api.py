import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient


def test_register_user(client):
    response = client.post("/auth/register", json={"username": "testuser", "password": "testpass"})
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert "id" in data


def test_login_returns_token(client):
    client.post("/auth/register", json={"username": "loginuser", "password": "pass123"})
    response = client.post("/auth/login", data={"username": "loginuser", "password": "pass123"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_create_session_requires_auth(client):
    response = client.post("/chat/sessions", json={"title": "My Session"})
    assert response.status_code == 401


def test_create_session_with_token(client):
    client.post("/auth/register", json={"username": "chatuser", "password": "pass123"})
    login = client.post("/auth/login", data={"username": "chatuser", "password": "pass123"})
    token = login.json()["access_token"]

    response = client.post(
        "/chat/sessions",
        json={"title": "Test Session"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    assert response.json()["title"] == "Test Session"


def test_send_message_to_missing_session(client):
    client.post("/auth/register", json={"username": "msguser", "password": "pass123"})
    login = client.post("/auth/login", data={"username": "msguser", "password": "pass123"})
    token = login.json()["access_token"]

    response = client.post(
        "/chat/sessions/9999/messages",
        json={"content": "Hello?"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


def test_access_other_users_session(client):
    # Create user1 with a session
    client.post("/auth/register", json={"username": "user1", "password": "pass1"})
    login1 = client.post("/auth/login", data={"username": "user1", "password": "pass1"})
    token1 = login1.json()["access_token"]

    session_resp = client.post(
        "/chat/sessions",
        json={"title": "User1 Session"},
        headers={"Authorization": f"Bearer {token1}"}
    )
    session_id = session_resp.json()["id"]

    # Create user2 and try to access user1's session
    client.post("/auth/register", json={"username": "user2", "password": "pass2"})
    login2 = client.post("/auth/login", data={"username": "user2", "password": "pass2"})
    token2 = login2.json()["access_token"]

    response = client.post(
        f"/chat/sessions/{session_id}/messages",
        json={"content": "Can I see this?"},
        headers={"Authorization": f"Bearer {token2}"}
    )
    assert response.status_code == 403


def test_public_query_endpoint(client):
    with patch("app.routers.query.run_agent", return_value=("Mocked answer", None)):
        response = client.get("/query?q=test+question")
    assert response.status_code == 200
    data = response.json()
    assert "question" in data
    assert "answer" in data
