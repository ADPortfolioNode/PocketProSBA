#!/usr/bin/env python3
"""
Force-fix prebuilt SPA SBAContentExplorer legacy URLs.

Must end as: fetch("".concat(Ll,"/api/sba/content/")...) with Ll=""
so the browser hits same-origin /api/sba/content/articles?...

Never strip /api from /api/sba/... paths.
"""
from __future__ import annotations

import re
import shutil
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS_DIR = ROOT / "frontend" / "build" / "static" / "js"
# Prefer the original main, then newest fix*.js
CANDIDATES = sorted(JS_DIR.glob("main.f54a4e20*.js"), key=lambda p: p.stat().st_mtime, reverse=True)
INDEX = ROOT / "frontend" / "build" / "index.html"


def patch_text(t: str) -> tuple[str, list[str]]:
    changes: list[str] = []

    for old, new, label in [
        ('Ll="http://127.0.0.1:5000"', 'Ll=""', "Ll→empty"),
        ('Ll="http://localhost:5000"', 'Ll=""', "Ll localhost→empty"),
        ('Il="http://127.0.0.1:5000"', 'Il=""', "Il→empty"),
        ('Il="http://localhost:5000"', 'Il=""', "Il localhost→empty"),
        ('Qs="http://127.0.0.1:5000/api"', 'Qs="/api"', "Qs→/api"),
        ('Qs="http://localhost:5000/api"', 'Qs="/api"', "Qs localhost→/api"),
        ('Qs="http://127.0.0.1:5000"', 'Qs="/api"', "Qs bare→/api"),
        ('Qs="http://localhost:5000"', 'Qs="/api"', "Qs bare localhost→/api"),
    ]:
        if old in t:
            t = t.replace(old, new)
            changes.append(label)

    # Normalize every broken variant to /api/sba/content/
    variants = [
        "/sba-content/",
        "/api/sba-content/",
        "/api/api/sba/content/",
        "/api/api/sba-content/",
        "/sba/content/",  # accidental strip of /api
    ]
    for v in variants:
        if v in t and v != "/api/sba/content/":
            c = t.count(v)
            t = t.replace(v, "/api/sba/content/")
            changes.append(f"{v} → /api/sba/content/ (x{c})")

    # Only strip /api for non-sba paths: concat(X,"/api/files") → concat(X,"/files")
    # Do NOT touch /api/sba/...
    def strip_non_sba(m: re.Match) -> str:
        prefix, rest = m.group(1), m.group(2)
        if rest.startswith("/sba/") or rest.startswith("/sba-content"):
            return m.group(0)  # keep as-is (should not happen after normalize)
        return prefix + rest

    t2, n = re.subn(
        r'(concat\([A-Za-z_$][\w$]*,\s*")/api(/[^"]*")',
        strip_non_sba,
        t,
    )
    # Re-apply: for Qs="/api" paths like /api/files become /files; for /api/sba keep full path
    # Actually strip_non_sba returns prefix+rest WITHOUT /api — so /api/sba becomes /sba if we strip.
    # Safer: only strip known safe suffixes
    safe_suffixes = ("/health", "/files", "/chat", "/rag", "/documents", "/info", "/search")
    def strip_safe(m: re.Match) -> str:
        rest = m.group(2)  # starts with /
        if rest.startswith("/sba"):
            return m.group(0)
        if any(rest == s or rest.startswith(s + "/") or rest.startswith(s + "?") for s in safe_suffixes):
            return m.group(1) + rest
        return m.group(0)

    t, n_safe = re.subn(
        r'(concat\([A-Za-z_$][\w$]*,\s*")/api(/[^"]*")',
        strip_safe,
        t,
    )
    if n_safe:
        changes.append(f"safe-stripped /api on {n_safe} non-sba concat paths")

    # Ensure explorer fetch path is correct literally
    if 'concat(Ll,"/api/sba/content/")' not in t and 'concat(Ll,"/sba' in t:
        t = t.replace('concat(Ll,"/sba/content/")', 'concat(Ll,"/api/sba/content/")')
        t = t.replace('concat(Ll,"/sba-content/")', 'concat(Ll,"/api/sba/content/")')
        changes.append("forced Ll concat path to /api/sba/content/")

    if 'throw new Error("Backend service is not available")' in t:
        t = t.replace(
            'throw new Error("Backend service is not available")',
            'console.warn("Backend service is not available")',
        )
        changes.append("softened health throw")

    return t, changes


def main() -> None:
    # Patch the newest main*.js that has Ll or sba-content patterns, prefer original f54a4e20
    src = None
    for p in CANDIDATES:
        if p.name.endswith(".map") or "LICENSE" in p.name:
            continue
        src = p
        break
    # Prefer base file if present
    base = JS_DIR / "main.f54a4e20.js"
    if base.exists():
        src = base
    # Prefer bak if current is broken and bak has good content
    bak = JS_DIR / "main.f54a4e20.js.bak_api_paths"
    if bak.exists() and src:
        bt = bak.read_text(encoding="utf-8", errors="ignore")
        st = src.read_text(encoding="utf-8", errors="ignore")
        # if current missing both sba-content and api/sba/content explorer fetch, restore from bak
        if "sba-content" not in st and 'concat(Ll,"/api/sba/content/' not in st and "sba-content" in bt:
            src.write_text(bt, encoding="utf-8")
            print("restored base from bak_api_paths")

    assert src is not None and src.exists()
    original = src.read_text(encoding="utf-8", errors="ignore")
    # If we accidentally destroyed sba path, restore from bak first
    if bak.exists() and 'concat(Ll,' in original and "/api/sba/content/" not in original and "/sba-content/" not in original:
        if "/sba/content/" in original or "sba-content" in bak.read_text(encoding="utf-8", errors="ignore"):
            original = bak.read_text(encoding="utf-8", errors="ignore")
            print("using bak as source (current was over-stripped)")

    patched, changes = patch_text(original)
    # Final guarantee
    if 'concat(Ll,"/sba/content/")' in patched:
        patched = patched.replace('concat(Ll,"/sba/content/")', 'concat(Ll,"/api/sba/content/")')
        changes.append("final fix sba/content")
    if 'concat(Ll,"/sba-content/")' in patched:
        patched = patched.replace('concat(Ll,"/sba-content/")', 'concat(Ll,"/api/sba/content/")')
        changes.append("final fix sba-content")

    stamp = str(int(time.time()))
    new_name = f"main.pocketpro.sba{stamp}.js"
    new_path = JS_DIR / new_name
    new_path.write_text(patched, encoding="utf-8")
    # also update canonical main.f54a4e20.js
    base.write_text(patched, encoding="utf-8")

    if INDEX.exists():
        html = INDEX.read_text(encoding="utf-8", errors="ignore").lstrip("\ufeff")
        html = re.sub(
            r'src="/static/js/main\.[^"]+\.js[^"]*"',
            f'src="/static/js/{new_name}"',
            html,
            count=1,
        )
        INDEX.write_text(html, encoding="utf-8")
        changes.append(f"index→{new_name}")

    print("changes:", changes)
    print("out:", new_name)
    print("sba-content left:", patched.count("/sba-content/"))
    print("sba/content broken left:", patched.count('"/sba/content/'))
    print("api/sba/content:", patched.count("/api/sba/content/"))
    print('Ll="":', 'Ll=""' in patched)
    i = patched.find('concat(Ll,"/api/sba/content/")')
    print("explorer fetch ok:", i >= 0)
    if i >= 0:
        print("snippet:", patched[i : i + 90])


if __name__ == "__main__":
    main()
