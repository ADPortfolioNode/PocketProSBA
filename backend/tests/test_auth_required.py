"""
Real authentication: signed, expiring access tokens and auth_required.

Covers valid / expired / tampered / missing tokens, password-reset and
disabled-account invalidation, /api/auth/me + /api/auth/refresh, the
AUTH_REQUIRED demo switch, and which routes are protected vs public.
"""
import io
import json
import time

import jwt
import pytest

import backend.config as config_module
from backend.app import create_app
from backend.app.auth import (
    TOKEN_EXPIRED,
    TOKEN_INVALID,
    TOKEN_MISSING,
    _signing_key,
    create_access_token,
    decode_access_token,
    AuthError,
)
from backend.models.chat import db
from backend.models.user import User
from backend.tests.auth_helpers import (
    TEST_EMAIL,
    TEST_PASSWORD,
    auth_header,
    make_token,
    make_user,
)


def _make_app(monkeypatch, name="testing", **overrides):
    cls = config_module.config[name]
    for key, value in overrides.items():
        monkeypatch.setattr(cls, key, value, raising=False)
    return create_app(name)


@pytest.fixture
def app(monkeypatch):
    # Rate limits off so many requests in one test never hit a 429.
    app = _make_app(monkeypatch, RATELIMIT_ENABLED=False)
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


def _bearer(token):
    return {"Authorization": f"Bearer {token}"}


def _login(client, email=TEST_EMAIL, password=TEST_PASSWORD, url="/api/login"):
    return _post(client, url, {"email": email, "password": password})


# A protected route that answers fast and offline once authenticated.
PROTECTED_PROBE = "/api/documents/list"


# ---------------------------------------------------------------------------
# Login issues a real token
# ---------------------------------------------------------------------------

class TestLoginToken:
    @pytest.mark.parametrize("url", ["/api/login", "/api/auth/login"])
    def test_login_returns_signed_expiring_bearer_token(self, app, client, url):
        make_user(app)
        resp = _login(client, url=url)
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["token_type"] == "Bearer"
        assert body["expires_in"] == 3600
        assert body["expires_at"] - int(time.time()) == pytest.approx(3600, abs=5)
        assert body["user"]["email"] == TEST_EMAIL
        with app.app_context():
            claims = decode_access_token(body["token"])
        assert claims["sub"] == str(body["user"]["id"])
        assert claims["exp"] - claims["iat"] == 3600
        # HS256 header, no "none"/asymmetric tricks.
        assert jwt.get_unverified_header(body["token"])["alg"] == "HS256"

    def test_login_token_unlocks_protected_route(self, app, client):
        make_user(app)
        token = _login(client).get_json()["token"]
        assert client.get(PROTECTED_PROBE).status_code == 401
        assert client.get(PROTECTED_PROBE, headers=_bearer(token)).status_code == 200

    def test_ttl_is_configurable(self, monkeypatch):
        app = _make_app(monkeypatch, RATELIMIT_ENABLED=False, JWT_ACCESS_TTL_SECONDS=120)
        make_user(app)
        body = _login(app.test_client()).get_json()
        assert body["expires_in"] == 120

    def test_bad_credentials_get_no_token(self, app, client):
        make_user(app)
        resp = _login(client, password="wrong-password")
        assert resp.status_code == 401
        assert "token" not in resp.get_json()


# ---------------------------------------------------------------------------
# Valid / expired / tampered / missing tokens
# ---------------------------------------------------------------------------

class TestTokenValidation:
    def test_valid_token(self, app, client):
        resp = client.get(PROTECTED_PROBE, headers=auth_header(app))
        assert resp.status_code == 200

    def test_missing_token(self, client):
        resp = client.get(PROTECTED_PROBE)
        assert resp.status_code == 401
        body = resp.get_json()
        assert body["code"] == TOKEN_MISSING
        assert body["success"] is False
        assert body["error"]
        assert resp.headers["WWW-Authenticate"].startswith("Bearer")
        assert resp.content_type.startswith("application/json")

    @pytest.mark.parametrize("header", [
        "Bearer",            # no token
        "Bearer   ",         # blank token
        "Basic dXNlcjpwYXNz",  # wrong scheme
        "Token abc",
    ])
    def test_malformed_header_is_missing(self, client, header):
        resp = client.get(PROTECTED_PROBE, headers={"Authorization": header})
        assert resp.status_code == 401
        assert resp.get_json()["code"] == TOKEN_MISSING

    def test_expired_token(self, app, client):
        token = make_token(app, ttl_seconds=-60)  # expired a minute ago (past leeway)
        resp = client.get(PROTECTED_PROBE, headers=_bearer(token))
        assert resp.status_code == 401
        assert resp.get_json()["code"] == TOKEN_EXPIRED
        assert 'error="invalid_token"' in resp.headers["WWW-Authenticate"]

    def test_tampered_payload(self, app, client):
        token = make_token(app)
        header, payload, sig = token.split(".")
        claims = jwt.decode(token, options={"verify_signature": False})
        claims["sub"] = "999"
        forged = jwt.encode(claims, "not-the-key", algorithm="HS256").split(".")[1]
        resp = client.get(PROTECTED_PROBE, headers=_bearer(f"{header}.{forged}.{sig}"))
        assert resp.status_code == 401
        assert resp.get_json()["code"] == TOKEN_INVALID

    def test_tampered_signature(self, app, client):
        token = make_token(app)
        flipped = token[:-2] + ("AA" if token[-2:] != "AA" else "BB")
        resp = client.get(PROTECTED_PROBE, headers=_bearer(flipped))
        assert resp.status_code == 401
        assert resp.get_json()["code"] == TOKEN_INVALID

    def test_token_signed_with_other_secret(self, app, client):
        user_id = make_user(app)
        now = int(time.time())
        forged = jwt.encode(
            {"sub": str(user_id), "iss": "pocketpro-sba", "typ": "access", "iat": now, "exp": now + 600},
            "some-other-secret", algorithm="HS256",
        )
        resp = client.get(PROTECTED_PROBE, headers=_bearer(forged))
        assert resp.status_code == 401
        assert resp.get_json()["code"] == TOKEN_INVALID

    def test_alg_none_rejected(self, app, client):
        user_id = make_user(app)
        now = int(time.time())
        unsigned = jwt.encode(
            {"sub": str(user_id), "iss": "pocketpro-sba", "typ": "access", "iat": now, "exp": now + 600},
            None, algorithm="none",
        )
        resp = client.get(PROTECTED_PROBE, headers=_bearer(unsigned))
        assert resp.status_code == 401

    def test_garbage_token(self, client):
        resp = client.get(PROTECTED_PROBE, headers=_bearer("not-a-jwt"))
        assert resp.status_code == 401
        assert resp.get_json()["code"] == TOKEN_INVALID

    def test_old_opaque_random_token_rejected(self, client):
        # What login used to mint: random, never stored, never checked.
        import secrets
        resp = client.get(PROTECTED_PROBE, headers=_bearer(secrets.token_urlsafe(32)))
        assert resp.status_code == 401

    def test_wrong_token_type_rejected(self, app, client):
        user_id = make_user(app)
        now = int(time.time())
        with app.app_context():
            key = _signing_key(app)
        other = jwt.encode(
            {"sub": str(user_id), "iss": "pocketpro-sba", "typ": "refresh", "iat": now, "exp": now + 600},
            key, algorithm="HS256",
        )
        resp = client.get(PROTECTED_PROBE, headers=_bearer(other))
        assert resp.status_code == 401
        assert resp.get_json()["code"] == TOKEN_INVALID

    def test_unknown_user_rejected(self, app, client):
        with app.app_context():
            ghost = User(email="ghost@example.com")
            ghost.id = 4242
            token = create_access_token(ghost)["token"]
        resp = client.get(PROTECTED_PROBE, headers=_bearer(token))
        assert resp.status_code == 401

    def test_disabled_account_rejected(self, app, client):
        token = make_token(app)
        with app.app_context():
            user = User.query.filter_by(email=TEST_EMAIL).first()
            user.is_active = False
            db.session.commit()
        assert client.get(PROTECTED_PROBE, headers=_bearer(token)).status_code == 401

    def test_password_change_invalidates_old_tokens(self, app, client):
        token = make_token(app)
        assert client.get(PROTECTED_PROBE, headers=_bearer(token)).status_code == 200
        with app.app_context():
            user = User.query.filter_by(email=TEST_EMAIL).first()
            user.set_password("a-brand-new-password")
            db.session.commit()
        resp = client.get(PROTECTED_PROBE, headers=_bearer(token))
        assert resp.status_code == 401
        assert resp.get_json()["code"] == TOKEN_INVALID

    def test_key_changes_with_secret(self, app, monkeypatch):
        token = make_token(app)
        app.config["SECRET_KEY"] = "rotated-secret"
        with app.app_context(), pytest.raises(AuthError):
            decode_access_token(token)


# ---------------------------------------------------------------------------
# /api/auth/me and /api/auth/refresh
# ---------------------------------------------------------------------------

class TestMeAndRefresh:
    def test_me(self, app, client):
        resp = client.get("/api/auth/me", headers=auth_header(app))
        assert resp.status_code == 200
        assert resp.get_json()["user"]["email"] == TEST_EMAIL

    def test_me_requires_token(self, client):
        assert client.get("/api/auth/me").status_code == 401

    def test_refresh_issues_new_valid_token(self, app, client):
        old = make_token(app)
        resp = client.post("/api/auth/refresh", headers=_bearer(old))
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["token"] != old
        assert body["expires_in"] == 3600
        assert client.get(PROTECTED_PROBE, headers=_bearer(body["token"])).status_code == 200

    def test_refresh_rejects_expired_token(self, app, client):
        expired = make_token(app, ttl_seconds=-60)
        resp = client.post("/api/auth/refresh", headers=_bearer(expired))
        assert resp.status_code == 401
        assert resp.get_json()["code"] == TOKEN_EXPIRED

    def test_me_and_refresh_need_token_even_in_demo_mode(self, monkeypatch):
        app = _make_app(monkeypatch, RATELIMIT_ENABLED=False, AUTH_REQUIRED=False)
        c = app.test_client()
        assert c.get("/api/auth/me").status_code == 401
        assert c.post("/api/auth/refresh").status_code == 401


# ---------------------------------------------------------------------------
# Protected vs public routes
# ---------------------------------------------------------------------------

# (method, path) for every route that must demand a token.
PROTECTED_ROUTES = [
    ("POST", "/api/chat"),
    ("POST", "/api/api/chat"),
    ("GET", "/api/chat/history/s1"),
    ("POST", "/api/chat/clear/s1"),
    ("POST", "/api/rag"),
    ("POST", "/api/rag/"),
    ("POST", "/api/rag/query"),
    ("POST", "/api/rag/sba-query"),
    ("POST", "/api/rag/decompose"),
    ("POST", "/api/rag/execute"),
    ("POST", "/api/rag/validate"),
    ("POST", "/api/decompose"),
    ("POST", "/api/execute"),
    ("POST", "/api/validate"),
    ("POST", "/api/query"),
    ("GET", "/api/search?query=loans"),
    ("POST", "/api/search"),
    ("GET", "/api/documents/list"),
    ("POST", "/api/documents/upload"),
    ("POST", "/api/documents/upload_and_ingest_document"),
    ("POST", "/api/files"),
    ("POST", "/api/files/"),
    ("POST", "/api/files/upload"),
    ("POST", "/api/api/files"),
    ("POST", "/api/api/documents/upload"),
    ("POST", "/api/orchestrator/submit"),
    ("GET", "/api/orchestrator/task/t1"),
    ("GET", "/api/orchestrator/task/t1/details"),
    ("GET", "/api/orchestrator/tasks"),
    ("GET", "/api/orchestrator/strategies"),
    ("GET", "/api/orchestrator/memory/stats"),
    ("POST", "/api/orchestrator/memory/cleanup"),
    ("POST", "/api/assistants/search"),
    ("POST", "/api/assistants/file"),
    ("POST", "/api/assistants/function"),
    ("POST", "/api/assistants/concierge"),
]

# Routes that must stay open with no token.
PUBLIC_ROUTES = [
    ("GET", "/health"),
    ("GET", "/api/health"),
    ("GET", "/api/info"),
    ("GET", "/api/api/health"),
    ("GET", "/api/auth/health"),
    ("GET", "/api/chat/health"),
    ("GET", "/api/rag/health"),
    ("GET", "/api/orchestrator/health"),
    ("GET", "/api/assistants/health"),
    ("GET", "/api/programs"),
    ("GET", "/api/sba/resources"),
    ("GET", "/api/sba/programs"),
    ("GET", "/api/sba/lifecycle"),
    ("GET", "/api/sba/local-resources"),
    ("GET", "/api/rag/sba-overview"),
]


def _call(client, method, path, **kw):
    if method == "GET":
        return client.get(path, **kw)
    return client.post(path, data=json.dumps({}), content_type="application/json", **kw)


@pytest.mark.parametrize("method,path", PROTECTED_ROUTES)
def test_protected_route_rejects_missing_token(client, method, path):
    resp = _call(client, method, path)
    assert resp.status_code == 401, f"{method} {path} -> {resp.status_code}"
    assert resp.get_json()["code"] == TOKEN_MISSING


@pytest.mark.parametrize("method,path", PROTECTED_ROUTES)
def test_protected_route_rejects_invalid_token(client, method, path):
    resp = _call(client, method, path, headers=_bearer("tampered.token.value"))
    assert resp.status_code == 401


@pytest.mark.parametrize("method,path", PROTECTED_ROUTES)
def test_protected_route_accepts_valid_token(app, client, method, path, monkeypatch, tmp_path):
    import backend.routes.files as files
    monkeypatch.setattr(files, "UPLOAD_FOLDER", str(tmp_path / "uploads"))
    monkeypatch.setattr("backend.services.rag.get_rag_manager", lambda: None, raising=False)
    resp = _call(client, method, path, headers=auth_header(app))
    # Past the guard: whatever the route answers (400 for an empty body etc.),
    # it is not an auth failure.
    assert resp.status_code != 401, f"{method} {path} -> 401 with a valid token"


@pytest.mark.parametrize("method,path", PUBLIC_ROUTES)
def test_public_route_needs_no_token(client, method, path):
    resp = _call(client, method, path)
    assert resp.status_code != 401, f"{method} {path} should be public"


def test_preflight_is_never_blocked(client):
    resp = client.open("/api/chat", method="OPTIONS", headers={
        "Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Authorization, Content-Type"})
    assert resp.status_code in (200, 204)


def test_every_route_under_protected_prefixes_is_guarded(app):
    """New routes in chat/rag/documents/files/orchestrator/assistants must use
    auth_required unless they are a health check or public SBA content."""
    prefixes = ("/api/chat", "/api/rag", "/api/documents", "/api/files",
                "/api/orchestrator", "/api/assistants", "/api/api/chat",
                "/api/api/files", "/api/api/documents")
    allowed_public = {"/api/rag/sba-overview"}
    unguarded = []
    for rule in app.url_map.iter_rules():
        path = rule.rule
        if not path.startswith(prefixes) or path.endswith("/health") or path in allowed_public:
            continue
        view = app.view_functions[rule.endpoint]
        if not getattr(view, "auth_required", False):
            unguarded.append(f"{rule.endpoint} {path}")
    assert not unguarded, f"routes missing @auth_required: {unguarded}"


def test_upload_with_token_saves_file(app, client, tmp_path, monkeypatch):
    import backend.routes.files as files
    monkeypatch.setattr(files, "UPLOAD_FOLDER", str(tmp_path / "up"))
    monkeypatch.setattr("backend.services.rag.get_rag_manager", lambda: None, raising=False)
    data = {"file": (io.BytesIO(b"hello"), "plan.txt")}
    assert client.post("/api/documents/upload", data=data,
                       content_type="multipart/form-data").status_code == 401
    assert not (tmp_path / "up" / "plan.txt").exists()
    data = {"file": (io.BytesIO(b"hello"), "plan.txt")}
    resp = client.post("/api/documents/upload", data=data, headers=auth_header(app),
                       content_type="multipart/form-data")
    assert resp.status_code == 200
    assert (tmp_path / "up" / "plan.txt").exists()


# ---------------------------------------------------------------------------
# AUTH_REQUIRED switch
# ---------------------------------------------------------------------------

class TestAuthRequiredFlag:
    def test_default_is_on(self):
        assert config_module.Config.AUTH_REQUIRED is True

    def test_env_parsing(self, monkeypatch):
        monkeypatch.setenv("AUTH_REQUIRED", "false")
        assert config_module.env_bool("AUTH_REQUIRED", True) is False
        monkeypatch.setenv("AUTH_REQUIRED", "true")
        assert config_module.env_bool("AUTH_REQUIRED", True) is True
        monkeypatch.delenv("AUTH_REQUIRED")
        assert config_module.env_bool("AUTH_REQUIRED", True) is True

    def test_demo_mode_opens_protected_routes(self, monkeypatch):
        app = _make_app(monkeypatch, RATELIMIT_ENABLED=False, AUTH_REQUIRED=False)
        assert app.test_client().get(PROTECTED_PROBE).status_code == 200

    def test_production_with_auth_off_logs_loudly(self, monkeypatch, caplog):
        monkeypatch.setenv("SECRET_KEY", "x")
        monkeypatch.setattr(config_module.ProductionConfig, "SQLALCHEMY_DATABASE_URI",
                            "sqlite:///:memory:", raising=False)
        with caplog.at_level("ERROR"):
            _make_app(monkeypatch, "production", AUTH_REQUIRED=False)
        assert any("AUTH_REQUIRED=false in PRODUCTION" in r.message for r in caplog.records)

    def test_production_enforces_by_default(self, monkeypatch):
        monkeypatch.setenv("SECRET_KEY", "x")
        monkeypatch.setattr(config_module.ProductionConfig, "SQLALCHEMY_DATABASE_URI",
                            "sqlite:///:memory:", raising=False)
        app = _make_app(monkeypatch, "production")
        assert app.config["AUTH_REQUIRED"] is True
        assert app.test_client().get(PROTECTED_PROBE).status_code == 401


def test_rate_limit_still_applies_to_protected_llm_routes(monkeypatch):
    app = _make_app(monkeypatch, RATELIMIT_LLM="1 per minute")
    c = app.test_client()
    h = auth_header(app)
    assert _post(c, "/api/decompose", {}, headers=h).status_code != 429
    assert _post(c, "/api/decompose", {}, headers=h).status_code == 429


def test_401_body_is_generic(client):
    text = client.get(PROTECTED_PROBE, headers=_bearer("x.y.z")).get_data(as_text=True)
    for leak in ("Traceback", "jwt", "Signature", "secret"):
        assert leak.lower() not in text.lower()
