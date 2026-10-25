"""Deploy config stays consistent: one backend entry (wsgi:application),
supported Node base images, a non-root dev image, compose that runs without
a .env, and Chroma server/client versions in lockstep."""
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
ENTRY = "wsgi:application"
STUB_ENTRIES = (
    "run.py", "app:app", "python app.py", "startup_simple", "app_simple",
    "minimal_app", "app_fixed", "app_minimal", "app_fastapi", "fastapi_app",
    "app_full",
)
LAUNCHERS = [
    "Procfile", "Dockerfile.production", "Dockerfile.dev",
    "docker-compose.yml", "docker-compose.dev.yml",
    "start.sh", "start-dev.sh", "start-dev-full.sh",
    "scripts/backend-entrypoint.sh",
]


def _read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def _compose(rel):
    return yaml.safe_load(_read(rel))


@pytest.mark.parametrize("rel", ["Procfile", "Dockerfile.production", "Dockerfile.dev",
                                 "docker-compose.dev.yml", "start.sh", "start-dev.sh",
                                 "start-dev-full.sh", "scripts/backend-entrypoint.sh"])
def test_launcher_uses_single_entrypoint(rel):
    assert ENTRY in _read(rel), f"{rel} does not start {ENTRY}"


@pytest.mark.parametrize("rel", LAUNCHERS + ["start-dev.bat", "start-dev-full.bat",
                                             "start-dev-full.ps1", "run_all_tests.sh",
                                             "run_all_tests.bat"])
def test_launcher_does_not_reference_stub_apps(rel):
    text = _read(rel)
    # Ignore comments, the chroma server's own uvicorn app, and `chown app:app`.
    lines = [
        ln for ln in text.splitlines()
        if not ln.lstrip().startswith(("#", "REM", "rem"))
        and "chromadb.app:app" not in ln
        and "chown" not in ln
    ]
    body = "\n".join(lines)
    for stub in STUB_ENTRIES:
        assert stub not in body, f"{rel} references stub entry {stub!r}"


REMOVED_STUBS = [
    "app.py", "app_fixed.py", "app_simple.py", "minimal_app.py", "app_fastapi.py",
    "fastapi_app.py", "app_full.py", "startup_simple.py", "run.py",
    "backend/app.py", "backend/run.py", "backend/app_minimal.py", "backend/server.js",
    "frontend/public/static/js/chat-magazine.js",
]


@pytest.mark.parametrize("rel", REMOVED_STUBS)
def test_removed_stub_entry_stays_removed(rel):
    assert not (ROOT / rel).exists(), f"{rel} came back; the only entry is {ENTRY}"


def test_backend_app_resolves_to_package():
    # With backend/app.py gone, `backend.app` must be the backend/app/ package.
    import backend.app as pkg
    assert Path(pkg.__file__).resolve() == ROOT / "backend" / "app" / "__init__.py"
    assert callable(pkg.create_app)


def test_wsgi_exposes_application():
    text = _read("wsgi.py")
    assert "application = app" in text


@pytest.mark.parametrize("rel", ["Dockerfile.frontend", "frontend/Dockerfile"])
def test_node_images_are_supported_lts(rel):
    froms = re.findall(r"^FROM\s+node:(\d+)", _read(rel), flags=re.M)
    assert froms, f"{rel} has no node base image"
    for major in froms:
        assert major in ("20", "22", "24"), f"{rel} uses node:{major}"


def test_dev_image_runs_as_non_root():
    users = re.findall(r"^USER\s+(\S+)", _read("Dockerfile.dev"), flags=re.M)
    assert users and users[-1] not in ("root", "0")


@pytest.mark.parametrize("rel", ["Dockerfile.production", "Dockerfile.dev",
                                 "Dockerfile.frontend", "frontend/Dockerfile"])
def test_dockerfiles_have_healthchecks(rel):
    assert re.search(r"^HEALTHCHECK\s", _read(rel), flags=re.M)


@pytest.mark.parametrize("rel", ["docker-compose.yml", "docker-compose.dev.yml"])
def test_compose_env_file_is_optional(rel):
    for name, svc in _compose(rel)["services"].items():
        for entry in svc.get("env_file", []) or []:
            assert isinstance(entry, dict) and entry.get("required") is False, (
                f"{rel}:{name} env_file must be optional so a fresh clone starts"
            )


@pytest.mark.parametrize("rel", ["docker-compose.yml", "docker-compose.dev.yml"])
def test_compose_services_have_healthchecks(rel):
    services = _compose(rel)["services"]
    for name in ("backend", "chromadb"):
        assert services[name].get("healthcheck"), f"{rel}:{name} has no healthcheck"


def test_chroma_server_matches_persistent_data_schema():
    m = re.search(r"^chromadb==([\d.]+)", _read("backend/requirements.txt"), flags=re.M)
    assert m, "chromadb is not pinned in backend/requirements.txt"
    client = m.group(1)
    assert client == "0.4.24", "The backend client pin is constrained by the pydantic v1 AI stack."
    server = "0.5.3"
    images = [
        _compose("docker-compose.yml")["services"]["chromadb"]["image"],
        _compose("docker-compose.dev.yml")["services"]["chromadb"]["image"],
        re.search(r"^FROM\s+(\S+)", _read("Dockerfile.chromadb"), flags=re.M).group(1),
    ]
    for image in images:
        assert image == f"chromadb/chroma:{server}", f"{image} != persistent data schema {server}"


@pytest.mark.parametrize("rel,out", [("vercel.json", "frontend/build"),
                                     ("frontend/vercel.json", "build")])
def test_vercel_config_builds_frontend(rel, out):
    import json
    cfg = json.loads(_read(rel))
    # Vercel sets CI=1, so react-scripts treats ESLint warnings as errors,
    # the same strict build GitHub CI runs (CI=true).
    assert "npm run build" in cfg["buildCommand"]
    assert cfg["outputDirectory"] == out
    assert any(r["destination"] == "/index.html" for r in cfg.get("rewrites", []))


def test_dev_image_pins_match_backend_requirements():
    """Dockerfile.dev installs pinned packages in batches instead of reading
    backend/requirements.txt; every pin it names must match, and the
    rate limiter must be there (security.py silently disables limits without it)."""
    req = dict(
        (m.group(1).lower(), m.group(2))
        for m in re.finditer(r"^([A-Za-z0-9_.\-]+)==([\w.]+)", _read("backend/requirements.txt"), flags=re.M)
    )
    dev = dict(
        (m.group(1).lower(), m.group(2))
        for m in re.finditer(r"(?<![\w\"<>=-])([A-Za-z][A-Za-z0-9_.\-]*)==([\w.]+)", _read("Dockerfile.dev"))
    )
    assert "flask-limiter" in dev
    mismatched = {k: (v, req[k]) for k, v in dev.items() if k in req and req[k] != v}
    assert not mismatched, f"Dockerfile.dev pins differ from backend/requirements.txt: {mismatched}"
