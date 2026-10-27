"""Remember me: long-lived refresh tokens restore a session after the
1-hour access token expires, without storing the password anywhere.

Covers: login without remember_me issues no refresh token; login with
remember_me issues one; that token swaps for a fresh access token that
passes a protected route; an access token cannot be used as a refresh
token; a tampered refresh token is rejected.
"""
import json

import pytest

import backend.config as config_module
from backend.app import create_app
from backend.models.chat import db
from backend.tests.auth_helpers import TEST_EMAIL, TEST_PASSWORD, make_user


def _make_app(monkeypatch):
    cls = config_module.config["testing"]
    monkeypatch.setattr(cls, "RATELIMIT_ENABLED", False, raising=False)
    return create_app("testing")


@pytest.fixture
def app(monkeypatch):
    app = _make_app(monkeypatch)
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _post(client, url, payload=None, **kw):
    return client.post(url, data=json.dumps(payload or {}), content_type="application/json", **kw)


def _login(client, remember_me):
    make_user(client.application)
    return _post(client, "/api/login", {"email": TEST_EMAIL, "password": TEST_PASSWORD, "remember_me": remember_me})


def test_login_without_remember_me_issues_no_refresh_token(client):
    resp = _login(client, False)
    assert resp.status_code == 200
    assert "refresh_token" not in resp.get_json()


def test_remember_me_refresh_token_restores_session(client):
    resp = _login(client, True)
    data = resp.get_json()
    assert resp.status_code == 200
    refresh = data["refresh_token"]
    assert refresh and refresh != data["token"]

    swapped = _post(client, "/api/auth/refresh-token", {"refresh_token": refresh})
    assert swapped.status_code == 200
    new_token = swapped.get_json()["token"]
    # The fresh access token passes a protected route.
    probe = client.get("/api/documents/list", headers={"Authorization": f"Bearer {new_token}"})
    assert probe.status_code == 200


def test_access_token_cannot_pose_as_refresh_token(client):
    resp = _login(client, True)
    access = resp.get_json()["token"]
    swapped = _post(client, "/api/auth/refresh-token", {"refresh_token": access})
    assert swapped.status_code == 401


def test_tampered_refresh_token_rejected(client):
    resp = _login(client, True)
    refresh = resp.get_json()["refresh_token"]
    tampered = refresh[:-2] + ("aa" if not refresh.endswith("aa") else "bb")
    swapped = _post(client, "/api/auth/refresh-token", {"refresh_token": tampered})
    assert swapped.status_code == 401
