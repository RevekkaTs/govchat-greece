from unittest.mock import patch

from app.dependencies import get_current_admin
from app.main import app
from app.models import User


def test_register_user(client):
    response = client.post(
        "/v1/auth/register", json={"username": "testuser", "password": "testpass"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert "id" in data


def test_login_returns_token(client):
    client.post(
        "/v1/auth/register", json={"username": "loginuser", "password": "pass123"}
    )
    response = client.post(
        "/v1/auth/login", data={"username": "loginuser", "password": "pass123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_create_session_requires_auth(client):
    response = client.post("/v1/chat/sessions", json={"title": "My Session"})
    assert response.status_code == 401


def test_create_session_with_token(client):
    client.post(
        "/v1/auth/register", json={"username": "chatuser", "password": "pass123"}
    )
    login = client.post(
        "/v1/auth/login", data={"username": "chatuser", "password": "pass123"}
    )
    token = login.json()["access_token"]

    response = client.post(
        "/v1/chat/sessions",
        json={"title": "Test Session"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    assert response.json()["title"] == "Test Session"


def test_send_message_to_missing_session(client):
    client.post(
        "/v1/auth/register", json={"username": "msguser", "password": "pass123"}
    )
    login = client.post(
        "/v1/auth/login", data={"username": "msguser", "password": "pass123"}
    )
    token = login.json()["access_token"]

    response = client.post(
        "/v1/chat/sessions/9999/messages",
        json={"content": "Hello?"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


def test_access_other_users_session(client):
    # Create user1 with a session
    client.post("/v1/auth/register", json={"username": "user1", "password": "pass1"})
    login1 = client.post(
        "/v1/auth/login", data={"username": "user1", "password": "pass1"}
    )
    token1 = login1.json()["access_token"]

    session_resp = client.post(
        "/v1/chat/sessions",
        json={"title": "User1 Session"},
        headers={"Authorization": f"Bearer {token1}"},
    )
    session_id = session_resp.json()["id"]

    # Create user2 and try to access user1's session
    client.post("/v1/auth/register", json={"username": "user2", "password": "pass2"})
    login2 = client.post(
        "/v1/auth/login", data={"username": "user2", "password": "pass2"}
    )
    token2 = login2.json()["access_token"]

    response = client.post(
        f"/v1/chat/sessions/{session_id}/messages",
        json={"content": "Can I see this?"},
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert response.status_code == 403


def test_public_query_endpoint(client):
    with patch("app.routers.query.run_agent", return_value=("Mocked answer", None)):
        response = client.get("/v1/query?q=test+question")
    assert response.status_code == 200
    data = response.json()
    assert "question" in data
    assert "answer" in data


def test_v2_auth_me_includes_is_admin(client):
    client.post("/v1/auth/register", json={"username": "v2user", "password": "pass123"})
    login = client.post(
        "/v1/auth/login", data={"username": "v2user", "password": "pass123"}
    )
    token = login.json()["access_token"]

    response = client.get(
        "/v2/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "v2user"
    assert "is_admin" in data
    assert data["is_admin"] is False


def test_v2_admin_users_non_admin_forbidden(client):
    client.post(
        "/v1/auth/register", json={"username": "plainuser", "password": "pass123"}
    )
    login = client.post(
        "/v1/auth/login", data={"username": "plainuser", "password": "pass123"}
    )
    token = login.json()["access_token"]

    response = client.get(
        "/v2/admin/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_v2_admin_users_returns_user_list_for_admin(client):
    client.post(
        "/v1/auth/register", json={"username": "adminlist1", "password": "pass123"}
    )
    client.post(
        "/v1/auth/register", json={"username": "adminlist2", "password": "pass123"}
    )

    def override_get_current_admin():
        return User(id=999, username="admin", hashed_password="x", is_admin=True)

    app.dependency_overrides[get_current_admin] = override_get_current_admin
    try:
        response = client.get("/v2/admin/users")
    finally:
        app.dependency_overrides.pop(get_current_admin, None)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    usernames = {u["username"] for u in data}
    assert "adminlist1" in usernames
    assert "adminlist2" in usernames
