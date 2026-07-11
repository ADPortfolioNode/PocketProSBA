from pathlib import Path
import re
import time

jsdir = Path("frontend/build/static/js")
base = jsdir / "main.f54a4e20.js"
t = base.read_text(encoding="utf-8", errors="ignore")

# Prefer bak if needed
bak = jsdir / "main.f54a4e20.js.bak_api_paths"
if bak.exists() and 'concat(Ll,' in bak.read_text(encoding="utf-8", errors="ignore"):
    # start from bak if current looks wrong
    bt = bak.read_text(encoding="utf-8", errors="ignore")
    if t.count("/api/sba/content/") == 0 or "/api/api/sba/content/" in t:
        t = bt

# Bases
repl = {
    'Ll="http://127.0.0.1:5000"': 'Ll=""',
    'Ll="http://localhost:5000"': 'Ll=""',
    'Il="http://127.0.0.1:5000"': 'Il=""',
    'Il="http://localhost:5000"': 'Il=""',
    'Qs="http://127.0.0.1:5000/api"': 'Qs="/api"',
    'Qs="http://localhost:5000/api"': 'Qs="/api"',
    'Qs="http://127.0.0.1:5000"': 'Qs="/api"',
    'Qs="http://localhost:5000"': 'Qs="/api"',
}
for a, b in repl.items():
    t = t.replace(a, b)

# Normalize sba content path in one pass to final form
for bad in (
    "/api/api/sba/content/",
    "/api/api/sba-content/",
    "/api/sba-content/",
    "/sba-content/",
    "/sba/content/",
):
    t = t.replace(bad, "/api/sba/content/")

# Safe strip only for Qs non-sba endpoints
def strip_safe(m):
    rest = m.group(2)
    if rest.startswith("/sba"):
        return m.group(0)
    safe = ("/health", "/files", "/chat", "/rag", "/documents", "/info", "/search")
    if any(rest == s or rest.startswith(s + "/") for s in safe):
        return m.group(1) + rest
    return m.group(0)

t = re.sub(r'(concat\([A-Za-z_$][\w$]*,\s*")/api(/[^"]*")', strip_safe, t)

# Final literal guarantees for explorer
t = t.replace('concat(Ll,"/sba/content/")', 'concat(Ll,"/api/sba/content/")')
t = t.replace('concat(Ll,"/sba-content/")', 'concat(Ll,"/api/sba/content/")')
t = t.replace('concat(Ll,"/api/api/sba/content/")', 'concat(Ll,"/api/sba/content/")')

if 'throw new Error("Backend service is not available")' in t:
    t = t.replace(
        'throw new Error("Backend service is not available")',
        'console.warn("Backend service is not available")',
    )

stamp = str(int(time.time()))
name = f"main.pocketpro.sba{stamp}.js"
(jsdir / name).write_text(t, encoding="utf-8")
base.write_text(t, encoding="utf-8")

idx = Path("frontend/build/index.html")
html = idx.read_text(encoding="utf-8", errors="ignore").lstrip("\ufeff")
html = re.sub(
    r'src="/static/js/main\.[^"]+\.js[^"]*"',
    f'src="/static/js/{name}"',
    html,
    count=1,
)
idx.write_text(html, encoding="utf-8")

print("bundle", name)
print("Ll empty", 'Ll=""' in t)
print("Qs", 'Qs="/api"' in t)
print("double api/sba", t.count("/api/api/sba"))
print("api/sba/content", t.count("/api/sba/content/"))
print("sba-content", t.count("/sba-content/"))
print("explorer", 'concat(Ll,"/api/sba/content/")' in t)
i = t.find('concat(Ll,"/api/sba/content/")')
print("snippet", t[i : i + 100] if i >= 0 else "MISSING")
