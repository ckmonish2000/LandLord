USER = {"email": "Asha@Example.com", "password": "correct-horse", "name": "Asha Rao"}


def signup(client, **overrides):
    return client.post("/auth/signup", json={**USER, **overrides})


def token(client) -> str:
    signup(client)
    res = client.post("/auth/signin", json={"email": USER["email"], "password": USER["password"]})
    return res.json()["access_token"]


def test_signup_returns_the_user_without_the_password(client):
    res = signup(client)
    assert res.status_code == 201
    body = res.json()
    assert body["email"] == "asha@example.com"  # stored lower case
    assert body["name"] == "Asha Rao"
    assert "password_hash" not in body and "password" not in body


def test_signup_twice_with_the_same_email_is_rejected(client):
    signup(client)
    assert signup(client, email="ASHA@example.com").status_code == 409


def test_signup_needs_a_long_enough_password(client):
    assert signup(client, password="short").status_code == 422


def test_signin_with_a_wrong_password_is_rejected(client):
    signup(client)
    res = client.post("/auth/signin", json={"email": USER["email"], "password": "wrong-password"})
    assert res.status_code == 401


def test_me_returns_the_signed_in_user(client):
    res = client.get("/auth/me", headers={"Authorization": f"Bearer {token(client)}"})
    assert res.status_code == 200
    assert res.json()["email"] == "asha@example.com"
    assert res.json()["created_at"].endswith("Z")  # UTC, even after a round trip through SQLite


def test_me_rejects_a_bad_token(client):
    assert client.get("/auth/me", headers={"Authorization": "Bearer not-a-token"}).status_code == 401
    assert client.get("/auth/me").status_code in (401, 403)  # no token at all
