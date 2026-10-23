"""
Security hardening tests: password reset tokens, password policy, account
enumeration, rate limiting, request size cap, generic 500s, RAG metadata
paths, CORS localhost reflection, DEBUG default.
"""
import hashlib
import importlib
import io
import json
import logging
from datetime import datetime, timedelta

import pytest

import backend.config as config_module
from backend.app import create_app
from backend.models.chat import db
from backend.tests.auth_helpers import authenticate

GOOD_PW = "correct-horse-1"


def _make_app(monkeypatch, name="testing", **overrides):
    """create_app with class-level config overrides (read at create time)."""
    cls = config_module.config[name]
    for key, value in overrides.items():
        monkeypatch.setattr(cls, key, value, raising=False)
    if name != "testing":
        monkeypatch.setattr(cls, "SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:", raising=False)
    app = create_app(name)
    return app


@pytest.fixture
def delivered():
    return []


@pytest.fixture
def app(monkeypatch, delivered):
    app = _make_app(monkeypatch)
    app.config["PASSWORD_RESET_DELIVERY"] = lambda email, token: delivered.append((email, token))
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _post(client, url, payload, **kw):
    return client.post(url, data=json.dumps(payload), content_type="application/json", **kw)


def _register(client, email="user@example.com", password=GOOD_PW, url="/api/register"):
    return _post(client, url, {"email": email, "password": password})


def _user(app, email="user@example.com"):
    from backend.models.user import User
    with app.app_context():
        u = User.query.filter_by(email=email).first()
        return None if u is None else {
            "reset_token": u.reset_token,
            "reset_token_expires": u.reset_token_expires,
        }


# ---------------------------------------------------------------------------
# (b) password reset + password policy + enumeration
# ---------------------------------------------------------------------------

class TestPasswordReset:
    @pytest.mark.parametrize("debug", [True, False])
    @pytest.mark.parametrize("url", ["/api/forgot-password", "/api/auth/forgot-password"])
    def test_forgot_never_returns_token(self, app, client, delivered, debug, url):
        app.config["DEBUG"] = debug
        app.debug = debug
        assert _register(client).status_code == 201
        resp = _post(client, url, {"email": "user@example.com"})
        assert resp.status_code == 200
        body = resp.get_json()
        assert "reset_token" not in body and "token" not in body and "dev_note" not in body
        assert len(delivered) == 1
        token = delivered[0][1]
        assert token not in resp.get_data(as_text=True)

    def test_forgot_never_returns_token_in_production_config(self, monkeypatch, delivered):
        monkeypatch.setenv("SECRET_KEY", "x")
        app = _make_app(monkeypatch, "production")
        app.config["PASSWORD_RESET_DELIVERY"] = lambda e, t: delivered.append((e, t))
        c = app.test_client()
        assert _register(c, email="prod@example.com").status_code == 201
        resp = _post(c, "/api/forgot-password", {"email": "prod@example.com"})
        assert resp.status_code == 200
        assert "reset_token" not in resp.get_json()
        assert delivered and delivered[0][1] not in resp.get_data(as_text=True)

    def test_token_is_hashed_at_rest_with_expiry(self, app, client, delivered):
        _register(client)
        _post(client, "/api/forgot-password", {"email": "user@example.com"})
        token = delivered[0][1]
        row = _user(app)
        assert row["reset_token"] != token
        assert row["reset_token"] == hashlib.sha256(token.encode()).hexdigest()
        assert row["reset_token_expires"] is not None
        remaining = row["reset_token_expires"] - datetime.utcnow()
        assert timedelta(minutes=50) < remaining <= timedelta(hours=1)

    def test_reset_flow_works_once(self, app, client, delivered):
        _register(client)
        _post(client, "/api/forgot-password", {"email": "user@example.com"})
        token = delivered[0][1]
        resp = _post(client, "/api/reset-password", {"token": token, "password": "brand-new-pw"})
        assert resp.status_code == 200, resp.get_json()
        assert _user(app)["reset_token"] is None
        assert _post(client, "/api/login", {"email": "user@example.com", "password": "brand-new-pw"}).status_code == 200
        # single use
        again = _post(client, "/api/reset-password", {"token": token, "password": "another-pw-9"})
        assert again.status_code == 400

    def test_hash_itself_is_not_a_valid_token(self, app, client, delivered):
        _register(client)
        _post(client, "/api/forgot-password", {"email": "user@example.com"})
        stored = _user(app)["reset_token"]
        resp = _post(client, "/api/reset-password", {"token": stored, "password": "brand-new-pw"})
        assert resp.status_code == 400

    def test_expired_token_rejected(self, app, client, delivered):
        from backend.models.user import User
        _register(client)
        _post(client, "/api/forgot-password", {"email": "user@example.com"})
        token = delivered[0][1]
        with app.app_context():
            u = User.query.filter_by(email="user@example.com").first()
            u.reset_token_expires = datetime.utcnow() - timedelta(minutes=1)
            db.session.commit()
        resp = _post(client, "/api/reset-password", {"token": token, "password": "brand-new-pw"})
        assert resp.status_code == 400
        assert resp.get_json()["error"] == "Invalid or expired reset token"
        assert _user(app)["reset_token"] is None

    def test_legacy_plaintext_token_rejected(self, app, client):
        from backend.models.user import User
        _register(client)
        with app.app_context():
            u = User.query.filter_by(email="user@example.com").first()
            u.reset_token = "legacy-plain-token"
            u.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()
        resp = _post(client, "/api/reset-password", {"token": "legacy-plain-token", "password": "brand-new-pw"})
        assert resp.status_code == 400

    def test_forgot_same_response_for_unknown_email(self, client, delivered):
        _register(client)
        known = _post(client, "/api/forgot-password", {"email": "user@example.com"})
        unknown = _post(client, "/api/forgot-password", {"email": "nobody@example.com"})
        assert known.status_code == unknown.status_code == 200
        assert known.get_json() == unknown.get_json()
        assert len(delivered) == 1

    def test_dev_log_only_when_debug(self, monkeypatch, caplog):
        app = _make_app(monkeypatch)
        with app.app_context():
            db.create_all()
        c = app.test_client()
        _register(c)
        caplog.set_level(logging.INFO)
        app.debug = False
        _post(c, "/api/forgot-password", {"email": "user@example.com"})
        assert "reset token for" not in caplog.text
        caplog.clear()
        app.debug = True
        _post(c, "/api/forgot-password", {"email": "user@example.com"})
        assert "DEV ONLY" in caplog.text


class TestPasswordPolicyAndEnumeration:
    @pytest.mark.parametrize("url", ["/api/register", "/api/auth/register"])
    def test_min_length_8_on_register(self, client, url):
        short = _register(client, password="seven77", url=url)
        assert short.status_code == 400
        assert "8" in short.get_json()["error"]
        assert _register(client, password="eight888", url=url).status_code == 201

    def test_min_length_8_on_reset(self, client, delivered):
        _register(client)
        _post(client, "/api/forgot-password", {"email": "user@example.com"})
        resp = _post(client, "/api/reset-password", {"token": delivered[0][1], "password": "short7!"})
        assert resp.status_code == 400

    def test_register_existing_email_is_indistinguishable(self, client):
        first = _register(client)
        second = _register(client, password="different-pw-2")
        assert first.status_code == second.status_code == 201
        assert first.get_json() == second.get_json()
        assert "user" not in second.get_json()
        # existing account untouched
        assert _post(client, "/api/login", {"email": "user@example.com", "password": GOOD_PW}).status_code == 200
        assert _post(client, "/api/login", {"email": "user@example.com", "password": "different-pw-2"}).status_code == 401

    def test_login_still_works(self, client):
        _register(client)
        resp = _post(client, "/api/login", {"email": "USER@example.com ", "password": GOOD_PW})
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True and body["user"]["email"] == "user@example.com" and body["token"]


# ---------------------------------------------------------------------------
# (c) rate limits + request size cap
# ---------------------------------------------------------------------------

class TestRateLimits:
    def test_login_limited_and_shared_across_aliases(self, monkeypatch):
        app = _make_app(monkeypatch, RATELIMIT_AUTH="3 per minute")
        c = app.test_client()
        creds = {"email": "x@example.com", "password": "whatever-pw"}
        assert _post(c, "/api/login", creds).status_code == 401
        assert _post(c, "/api/auth/login", creds).status_code == 401
        assert _post(c, "/api/login", creds).status_code == 401
        blocked = _post(c, "/api/auth/login", creds)
        assert blocked.status_code == 429
        assert blocked.is_json and "Too many requests" in blocked.get_json()["error"]
        assert blocked.headers.get("Retry-After")
        # other auth actions have their own bucket
        assert _post(c, "/api/forgot-password", {"email": "x@example.com"}).status_code == 200

    @pytest.mark.parametrize("url,payload", [
        ("/api/register", {"email": "a@example.com", "password": "x"}),
        ("/api/forgot-password", {"email": "a@example.com"}),
        ("/api/reset-password", {"token": "t", "password": "x"}),
    ])
    def test_other_auth_routes_limited(self, monkeypatch, url, payload):
        app = _make_app(monkeypatch, RATELIMIT_AUTH="2 per minute")
        c = app.test_client()
        assert _post(c, url, payload).status_code != 429
        assert _post(c, url, payload).status_code != 429
        assert _post(c, url, payload).status_code == 429

    def test_llm_routes_share_a_limit(self, monkeypatch):
        app = _make_app(monkeypatch, RATELIMIT_LLM="2 per minute")
        c = app.test_client()
        authenticate(c, app)
        # empty messages are rejected fast (400) but still count
        assert _post(c, "/api/chat", {}).status_code == 400
        assert _post(c, "/api/decompose", {}).status_code != 429
        assert _post(c, "/api/rag/decompose", {}).status_code == 429
        # read-only and auth routes are unaffected
        assert c.get("/api/health").status_code == 200
        assert _post(c, "/api/login", {"email": "a@b.co", "password": "x"}).status_code == 401

    def test_limits_are_per_app_instance(self, monkeypatch):
        a1 = _make_app(monkeypatch, RATELIMIT_AUTH="1 per minute").test_client()
        assert _post(a1, "/api/login", {"email": "a@b.co", "password": "x"}).status_code == 401
        assert _post(a1, "/api/login", {"email": "a@b.co", "password": "x"}).status_code == 429
        a2 = _make_app(monkeypatch, RATELIMIT_AUTH="1 per minute").test_client()
        assert _post(a2, "/api/login", {"email": "a@b.co", "password": "x"}).status_code == 401

    def test_can_be_disabled(self, monkeypatch):
        c = _make_app(monkeypatch, RATELIMIT_AUTH="1 per minute", RATELIMIT_ENABLED=False).test_client()
        for _ in range(3):
            assert _post(c, "/api/login", {"email": "a@b.co", "password": "x"}).status_code == 401

    def test_storage_uri_from_config(self, monkeypatch):
        app = _make_app(monkeypatch, RATELIMIT_STORAGE_URI="memory://")
        limiter = app.extensions["sba_limiter"]
        assert type(limiter.storage).__name__ == "MemoryStorage"


class TestRequestSize:
    def test_default_is_16mb(self, app):
        assert app.config["MAX_CONTENT_LENGTH"] == 16 * 1024 * 1024

    @pytest.mark.parametrize("url", ["/api/files", "/api/documents/upload", "/api/api/files"])
    def test_oversized_upload_gets_413_json(self, monkeypatch, url):
        app = _make_app(monkeypatch, MAX_CONTENT_LENGTH=1024)
        c = app.test_client()
        data = {"file": (io.BytesIO(b"a" * 4096), "big.txt")}
        resp = c.post(url, data=data, content_type="multipart/form-data")
        assert resp.status_code == 413
        body = resp.get_json()
        assert body["success"] is False and "too large" in body["error"].lower()
        assert body["max_content_length"] == 1024

    def test_oversized_json_gets_413(self, monkeypatch):
        c = _make_app(monkeypatch, MAX_CONTENT_LENGTH=100).test_client()
        resp = _post(c, "/api/login", {"email": "a@b.co", "password": "x" * 500})
        assert resp.status_code == 413 and resp.is_json


# ---------------------------------------------------------------------------
# (e) generic 500s + RAG metadata paths
# ---------------------------------------------------------------------------

SECRET_DETAIL = "/srv/secret/path/db.sqlite exploded: password=hunter2"


class TestGenericErrors:
    @pytest.mark.parametrize("url,payload", [
        ("/api/register", {"email": "a@example.com", "password": GOOD_PW}),
        ("/api/login", {"email": "a@example.com", "password": GOOD_PW}),
        ("/api/forgot-password", {"email": "a@example.com"}),
        ("/api/reset-password", {"token": "abc", "password": GOOD_PW}),
    ])
    def test_auth_500_is_generic(self, client, monkeypatch, caplog, url, payload):
        import backend.routes.auth as auth

        class _Q:
            def filter_by(self, **kw):
                raise RuntimeError(SECRET_DETAIL)

        class _FakeUser:
            query = _Q()

        monkeypatch.setattr(auth, "_get_user_model", lambda: (_FakeUser, db))
        caplog.set_level(logging.ERROR)
        resp = _post(client, url, payload)
        assert resp.status_code == 500
        text = resp.get_data(as_text=True)
        assert SECRET_DETAIL not in text and "hunter2" not in text and "/srv/" not in text
        assert resp.get_json()["error"]
        assert SECRET_DETAIL in caplog.text  # still logged server-side

    @pytest.mark.parametrize("url,target", [
        ("/api/decompose", "backend.routes.api.decompose_task_service"),
        ("/api/rag/decompose", "backend.routes.rag.decompose_task_service"),
    ])
    def test_route_500_is_generic(self, client, app, monkeypatch, url, target):
        authenticate(client, app)
        mod, name = target.rsplit(".", 1)
        module = importlib.import_module(mod)
        if not hasattr(module, name):
            pytest.skip(f"{target} not present")

        def boom(*a, **k):
            raise RuntimeError(SECRET_DETAIL)

        monkeypatch.setattr(module, name, boom)
        resp = _post(client, url, {"message": "hi"})
        assert resp.status_code == 500
        assert SECRET_DETAIL not in resp.get_data(as_text=True)

    def test_no_raw_exception_text_in_routes_source(self):
        import pathlib
        import re
        routes = pathlib.Path(__file__).resolve().parents[1] / "routes"
        offenders = []
        for py in routes.glob("*.py"):
            for n, line in enumerate(py.read_text(encoding="utf-8").splitlines(), 1):
                s = line.strip()
                if s.startswith(("logger.", "logging.", "#")) or py.name == "_errors.py":
                    continue
                if re.search(r"str\(e\)|\{e\}|\{str\(e\)\}", s):
                    offenders.append(f"{py.name}:{n}: {s}")
        assert offenders == []

    def test_internal_error_message_reraises_http_errors(self):
        from werkzeug.exceptions import RequestEntityTooLarge
        from backend.routes._errors import GENERIC_ERROR, internal_error_message
        with pytest.raises(RequestEntityTooLarge):
            internal_error_message(RequestEntityTooLarge())
        assert internal_error_message(ValueError(SECRET_DETAIL)) == GENERIC_ERROR


class TestRagMetadataPaths:
    @pytest.fixture
    def kb(self, tmp_path, monkeypatch):
        import backend.routes.rag as rag
        live = tmp_path / "sba_api_live"
        live.mkdir()
        (live / "api_sba_content_loans_7a__combined.txt").write_text(
            "SBA 7a loans help small businesses. 7a loan eligibility and rates.", encoding="utf-8"
        )
        (tmp_path / "general.txt").write_text("microloan basics for a small business", encoding="utf-8")
        monkeypatch.setattr(rag, "_knowledge_base_roots", lambda: [tmp_path])
        return tmp_path

    def test_local_kb_metadata_has_basename_only(self, kb):
        from backend.routes.rag import _local_kb_sba_answer
        result = _local_kb_sba_answer("7a loan eligibility microloan")
        sources = result["source_documents"]
        assert sources
        for s in sources:
            p = s["metadata"]["path"]
            assert "/" not in p and "\\" not in p and str(kb) not in p
        dumped = json.dumps(result)
        assert str(kb) not in dumped
        assert result["mode"] == "sba_api_live"

    def test_resolve_kb_path(self, kb):
        from backend.routes.rag import resolve_kb_path
        found = resolve_kb_path("api_sba_content_loans_7a__combined.txt", "sba_api_live")
        assert found is not None and found.is_file()
        assert resolve_kb_path("general.txt") is not None
        assert resolve_kb_path("../general.txt") is None
        assert resolve_kb_path("/etc/passwd") is None
        assert resolve_kb_path("general.txt", "../..") is not None  # bad folder ignored, basename still found

    def test_upload_response_has_no_server_path(self, client, tmp_path, monkeypatch):
        import backend.routes.files as files
        monkeypatch.setattr(files, "UPLOAD_FOLDER", str(tmp_path / "uploads"))
        authenticate(client)
        resp = client.post("/api/files", data={"file": (io.BytesIO(b"hello sba"), "notes.txt")},
                           content_type="multipart/form-data")
        assert resp.status_code == 200, resp.get_data(as_text=True)
        body = resp.get_json()
        assert body["document"]["path"] == "notes.txt"
        assert str(tmp_path) not in resp.get_data(as_text=True)


# ---------------------------------------------------------------------------
# (f) CORS + DEBUG default
# ---------------------------------------------------------------------------

class TestCors:
    def test_production_does_not_reflect_arbitrary_localhost(self, monkeypatch):
        monkeypatch.setenv("SECRET_KEY", "x")
        c = _make_app(monkeypatch, "production").test_client()
        for method in ("get", "options"):
            r = getattr(c, method)("/api/health", headers={"Origin": "http://localhost:5173",
                                                           "Access-Control-Request-Method": "GET"})
            assert r.headers.get("Access-Control-Allow-Origin") is None
        ok = c.get("/api/health", headers={"Origin": "http://localhost:3000"})
        assert ok.headers.get("Access-Control-Allow-Origin") == "http://localhost:3000"

    def test_production_allow_list_from_env(self, monkeypatch):
        monkeypatch.setenv("SECRET_KEY", "x")
        c = _make_app(monkeypatch, "production", CORS_ALLOWED_ORIGINS=["https://app.example.com"],
                      FRONTEND_URL="https://www.example.com").test_client()
        for origin in ("https://app.example.com", "https://www.example.com"):
            r = c.get("/api/health", headers={"Origin": origin})
            assert r.headers.get("Access-Control-Allow-Origin") == origin
        evil = c.get("/api/health", headers={"Origin": "https://evil.example.net"})
        assert evil.headers.get("Access-Control-Allow-Origin") is None

    @pytest.mark.parametrize("env", ["development", "testing"])
    def test_dev_and_testing_reflect_localhost_ports(self, monkeypatch, env):
        c = _make_app(monkeypatch, env).test_client()
        r = c.options("/api/health", headers={"Origin": "http://localhost:5173",
                                              "Access-Control-Request-Method": "GET"})
        assert r.headers.get("Access-Control-Allow-Origin") == "http://localhost:5173"
        r2 = c.get("/api/health", headers={"Origin": "http://127.0.0.1:8080"})
        assert r2.headers.get("Access-Control-Allow-Origin") == "http://127.0.0.1:8080"
        r3 = c.get("/api/health", headers={"Origin": "http://evil.localhost.example.com"})
        assert r3.headers.get("Access-Control-Allow-Origin") is None


class TestConfigFromEnv:
    @pytest.fixture
    def reload_config(self, monkeypatch):
        for var in ("FLASK_DEBUG", "DEBUG", "MAX_CONTENT_LENGTH", "RATELIMIT_STORAGE_URI"):
            monkeypatch.delenv(var, raising=False)

        def _reload(**env):
            for k, v in env.items():
                monkeypatch.setenv(k, v)
            return importlib.reload(config_module)

        yield _reload
        for var in ("FLASK_DEBUG", "DEBUG", "MAX_CONTENT_LENGTH", "RATELIMIT_STORAGE_URI"):
            monkeypatch.delenv(var, raising=False)
        importlib.reload(config_module)

    def test_debug_defaults_false_everywhere(self, reload_config):
        cfg = reload_config()
        for name in ("development", "production", "testing", "default"):
            assert cfg.config[name].DEBUG is False, name

    def test_debug_only_when_explicit(self, reload_config):
        assert reload_config(FLASK_DEBUG="1").DevelopmentConfig.DEBUG is True
        assert reload_config(FLASK_DEBUG="0").DevelopmentConfig.DEBUG is False

    def test_production_never_debug(self, reload_config):
        assert reload_config(FLASK_DEBUG="1").ProductionConfig.DEBUG is False

    def test_size_and_storage_env_overrides(self, reload_config):
        cfg = reload_config(MAX_CONTENT_LENGTH="2048", RATELIMIT_STORAGE_URI="redis://cache:6379/0")
        assert cfg.Config.MAX_CONTENT_LENGTH == 2048
        assert cfg.Config.RATELIMIT_STORAGE_URI == "redis://cache:6379/0"
        cfg = reload_config(MAX_CONTENT_LENGTH="not-a-number")
        assert cfg.Config.MAX_CONTENT_LENGTH == 16 * 1024 * 1024
