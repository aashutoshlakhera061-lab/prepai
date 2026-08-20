"""Tests for registration, login, and token-protected access."""


def test_register_creates_user(client):
    resp = client.post(
        "/auth/register",
        json={"email": "new@example.com", "password": "securepass123", "name": "New User"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "new@example.com"
    assert body["name"] == "New User"
    assert "id" in body
    # Password must never be echoed back
    assert "password" not in body
    assert "hashed_password" not in body


def test_register_rejects_duplicate_email(client):
    payload = {"email": "dup@example.com", "password": "securepass123", "name": "First"}
    client.post("/auth/register", json=payload)
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 400


def test_login_with_correct_credentials_returns_token(client):
    client.post(
        "/auth/register",
        json={"email": "login@example.com", "password": "correctpass", "name": "Login User"},
    )
    resp = client.post(
        "/auth/login",
        data={"username": "login@example.com", "password": "correctpass"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()
    assert resp.json()["token_type"] == "bearer"


def test_login_with_wrong_password_fails(client):
    client.post(
        "/auth/register",
        json={"email": "wrongpass@example.com", "password": "correctpass", "name": "User"},
    )
    resp = client.post(
        "/auth/login",
        data={"username": "wrongpass@example.com", "password": "totally-wrong"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 401


def test_protected_route_rejects_missing_token(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_protected_route_accepts_valid_token(client, registered_user):
    _, _, headers = registered_user
    resp = client.get("/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "testuser@example.com"
