def _login(client, username="admin", password="admin123"):
    return client.post("/auth/login", json={"username": username, "password": password})


def test_login_success(client):
    r = _login(client)
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_wrong_password(client):
    r = _login(client, password="wrong")
    assert r.status_code == 401


def test_me_requires_token(client):
    r = client.get("/auth/me")
    assert r.status_code == 401


def test_me_with_token(client):
    token = _login(client).json()["access_token"]
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["data"]["username"] == "admin"


def test_register_success(client):
    r = client.post(
        "/auth/register",
        json={"username": "newbie", "email": "newbie@example.com", "password": "secret1"},
    )
    assert r.status_code == 200
    assert r.json()["data"]["username"] == "newbie"
    assert r.json()["data"]["email"] == "newbie@example.com"


def test_register_duplicate(client):
    client.post(
        "/auth/register",
        json={"username": "dupuser", "email": "dup@example.com", "password": "secret1"},
    )
    r2 = client.post(
        "/auth/register",
        json={"username": "dupuser", "email": "dup2@example.com", "password": "secret1"},
    )
    assert r2.json()["code"] == 409


def test_register_validation_error(client):
    # password equal to username is rejected by the cross-field validator
    r = client.post(
        "/auth/register",
        json={"username": "shortp", "email": "short@example.com", "password": "shortp"},
    )
    assert r.status_code == 422
    # invalid username characters
    r2 = client.post(
        "/auth/register",
        json={"username": "bad name", "email": "bad@example.com", "password": "secret1"},
    )
    assert r2.status_code == 422
