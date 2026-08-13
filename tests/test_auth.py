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
