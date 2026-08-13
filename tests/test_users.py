def _headers(client):
    token = client.post(
        "/auth/login", json={"username": "admin", "password": "admin123"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_and_list(client):
    h = _headers(client)
    r = client.post(
        "/users",
        json={"username": "alice", "email": "alice@example.com", "password": "secret1"},
        headers=h,
    )
    assert r.status_code == 200
    uid = r.json()["data"]["id"]
    listing = client.get("/users", headers=h)
    assert any(u["id"] == uid for u in listing.json()["data"])


def test_create_duplicate(client):
    h = _headers(client)
    client.post(
        "/users",
        json={"username": "bob", "email": "bob@example.com", "password": "secret1"},
        headers=h,
    )
    r2 = client.post(
        "/users",
        json={"username": "bob", "email": "bob2@example.com", "password": "secret1"},
        headers=h,
    )
    assert r2.json()["code"] == 409


def test_update_and_delete(client):
    h = _headers(client)
    uid = client.post(
        "/users",
        json={"username": "carol", "email": "carol@example.com", "password": "secret1"},
        headers=h,
    ).json()["data"]["id"]

    upd = client.put(f"/users/{uid}", json={"email": "carol.new@example.com"}, headers=h)
    assert upd.json()["data"]["email"] == "carol.new@example.com"

    dele = client.delete(f"/users/{uid}", headers=h)
    assert dele.status_code == 200
    assert client.get(f"/users/{uid}", headers=h).json()["code"] == 404


def test_requires_auth(client):
    assert client.get("/users").status_code == 401


def test_page_users(client):
    h = _headers(client)
    client.post(
        "/users",
        json={"username": "page1", "email": "page1@example.com", "password": "secret1"},
        headers=h,
    )
    client.post(
        "/users",
        json={"username": "page2", "email": "page2@example.com", "password": "secret1"},
        headers=h,
    )
    r = client.get("/users/page?page=1&page_size=1", headers=h)
    assert r.status_code == 200
    body = r.json()["data"]
    assert body["page"] == 1
    assert body["page_size"] == 1
    assert body["total"] >= 3  # admin + 2 created
    assert len(body["items"]) == 1
    assert all("id" in u and "email" in u for u in body["items"])
