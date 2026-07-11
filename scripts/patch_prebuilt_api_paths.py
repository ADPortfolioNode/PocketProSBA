#!/usr/bin/env python3
"""
Fix prebuilt main.*.js API base for the SPA running on :3000.

Problems seen in browser:
  POST http://localhost:5000/api/api/files 404
  GET  http://localhost:5000/api/api/health ERR_EMPTY_RESPONSE
  App.js:194 Backend service is not available

Root causes:
  1) API base baked as http://localhost|127.0.0.1:5000/api + paths /api/* → double /api
  2) Direct :5000 on Windows often flakes on localhost (IPv6) → ERR_EMPTY_RESPONSE
  3) Hard throw on health failure blocks upload

Fix:
  - Force API base Qs to same-origin "/api" (nginx on :3000 proxies to backend)
  - Paths become /api/health, /api/files, /api/chat (no double prefix, no direct :5000)
  - Soft-degrade health check before upload
  - Cache-bust index.html script tag
"""
from __future__ import annotations

import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS_DIR = ROOT / "frontend" / "build" / "static" / "js"
INDEX = ROOT / "frontend" / "build" / "index.html"


def patch_js(text: str) -> tuple[str, list[str]]:
    notes: list[str] = []

    # 1) Normalize API bases used by prebuilt App.js / SBAContentExplorer
    #    Qs  → same-origin /api  (chat/files/health)
    #    Ll  → same-origin ""    (paths already absolute /api/... after rewrites below)
    #    Il  → same-origin ""    (status monitors)
    replacements = [
        ('Qs="http://127.0.0.1:5000/api"', 'Qs="/api"'),
        ("Qs='http://127.0.0.1:5000/api'", 'Qs="/api"'),
        ('Qs="http://localhost:5000/api"', 'Qs="/api"'),
        ("Qs='http://localhost:5000/api'", 'Qs="/api"'),
        ('Qs="http://127.0.0.1:5000"', 'Qs="/api"'),
        ('Qs="http://localhost:5000"', 'Qs="/api"'),
        # SBAContentExplorer base (source map ~L32 fetch `${API}/sba-content/...`)
        ('Ll="http://127.0.0.1:5000"', 'Ll=""'),
        ('Ll="http://localhost:5000"', 'Ll=""'),
        ("Ll='http://127.0.0.1:5000'", "Ll=''"),
        ("Ll='http://localhost:5000'", "Ll=''"),
        ('Il="http://127.0.0.1:5000"', 'Il=""'),
        ('Il="http://localhost:5000"', 'Il=""'),
    ]
    for old, new in replacements:
        if old in text:
            text = text.replace(old, new)
            notes.append(f"rewrote {old} → {new}")

    # Catch remaining host:5000(/api) string constants for short var names
    text2, n = re.subn(
        r'([A-Za-z_$][\w$]*)="https?://(?:localhost|127\.0\.0\.1):5000/api"',
        r'\1="/api"',
        text,
    )
    if n:
        text = text2
        notes.append(f"rewrote {n} host:5000/api string constants to /api")
    text2b, n1b = re.subn(
        r'([A-Za-z_$][\w$]*)="https?://(?:localhost|127\.0\.0\.1):5000"',
        r'\1=""',
        text,
    )
    if n1b:
        text = text2b
        notes.append(f"rewrote {n1b} bare host:5000 bases to empty (same-origin)")

    # 1b) Legacy SBAContentExplorer path: /sba-content/X → /api/sba/content/X
    if "/sba-content/" in text:
        text = text.replace("/sba-content/", "/api/sba/content/")
        notes.append("rewrote /sba-content/ → /api/sba/content/")
    if '"/sba-content"' in text:
        text = text.replace('"/sba-content"', '"/api/sba/resources"')
        notes.append('rewrote "/sba-content" → resources catalog')

    # 2) If base is already /api, strip extra /api prefix on concat paths
    #    concat(Qs,"/api/files") → concat(Qs,"/files")
    def strip_double(m: re.Match) -> str:
        return m.group(1) + m.group(2)

    text3, n2 = re.subn(
        r'(concat\([A-Za-z_$][\w$]*,\s*")/api(/[^"]*")',
        strip_double,
        text,
    )
    if n2:
        text = text3
        notes.append(f"stripped /api from {n2} concat paths (avoid /api/api/*)")

    # 3) Soft-degrade health gate on upload (App.js:194)
    hard_patterns = [
        'if(!(await fetch("".concat(Qs,"/health"),{method:"GET"})).ok)throw new Error("Backend service is not available");',
        'if(!(await fetch("".concat(Qs,"/api/health"),{method:"GET"})).ok)throw new Error("Backend service is not available");',
        'if(!(await fetch("".concat(Qs,"/health"),{method:"GET"})).ok)throw new Error(\'Backend service is not available\');',
    ]
    soft = (
        'try{const __h=await fetch("".concat(Qs,"/health"),{method:"GET"});'
        'if(!__h.ok)console.warn("Backend health soft-fail",__h.status)}'
        'catch(__e){console.warn("Backend health probe failed",__e)};'
    )
    for hp in hard_patterns:
        if hp in text:
            text = text.replace(hp, soft, 1)
            notes.append("soft-degraded upload health throw (App.js:194)")
            break

    # Generic: remove remaining hard throw string if still present with health fetch nearby
    if 'throw new Error("Backend service is not available")' in text:
        text = text.replace(
            'throw new Error("Backend service is not available")',
            'console.warn("Backend service is not available")',
        )
        notes.append("replaced remaining hard throw with console.warn")

    return text, notes


def patch_index(html: str) -> tuple[str, list[str]]:
    notes: list[str] = []
    v = str(int(time.time()))
    # cache-bust main js
    new_html, n = re.subn(
        r'src="(/static/js/main\.[^"]+\.js)(?:\?v=[^"]*)?"',
        rf'src="\1?v={v}"',
        html,
        count=1,
    )
    if n:
        notes.append(f"cache-busted main.js ?v={v}")
        html = new_html
    # ensure no long-cache meta for dev
    if "Cache-Control" not in html:
        html = html.replace(
            "<head>",
            '<head>\n    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />\n'
            '    <meta http-equiv="Pragma" content="no-cache" />',
            1,
        )
        notes.append("added no-cache meta")
    return html, notes


def main() -> int:
    files = sorted(JS_DIR.glob("main.*.js"))
    files = [f for f in files if f.suffix == ".js" and "LICENSE" not in f.name]
    if not files:
        print("No main.*.js found", file=sys.stderr)
        return 1

    for path in files:
        original = path.read_text(encoding="utf-8", errors="ignore")
        patched, notes = patch_js(original)
        bak = path.with_suffix(path.suffix + ".bak_api_paths")
        if not bak.exists():
            bak.write_text(original, encoding="utf-8")
        if patched != original:
            path.write_text(patched, encoding="utf-8")
        print(f"{path.name}:")
        for n in notes or ["no structural changes (already patched?)"]:
            print(f"  - {n}")
        # summary
        t = patched
        m = re.search(r'Qs="[^"]+"', t)
        print("  Qs sample:", m.group(0) if m else "n/a")
        print("  has /api/api/files string:", "/api/api/files" in t)
        print("  hard throw:", 'throw new Error("Backend service is not available")' in t)

    if INDEX.exists():
        html = INDEX.read_text(encoding="utf-8", errors="ignore")
        # strip BOM if present
        if html.startswith("\ufeff"):
            html = html.lstrip("\ufeff")
        new_html, notes = patch_index(html)
        INDEX.write_text(new_html, encoding="utf-8")
        print("index.html:")
        for n in notes:
            print(f"  - {n}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
