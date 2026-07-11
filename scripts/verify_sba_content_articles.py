import re
import urllib.request
from pathlib import Path

print("=== bundle ===")
idx = Path("frontend/build/index.html").read_text(encoding="utf-8", errors="ignore")
m = re.search(r'/static/js/(main\.[^"\']+\.js)', idx)
print("index script:", m.group(1) if m else "MISSING")
if m:
    p = Path("frontend/build/static/js") / m.group(1)
    t = p.read_text(encoding="utf-8", errors="ignore")
    print("file exists:", p.exists(), "size", p.stat().st_size if p.exists() else 0)
    print("/sba-content/ count:", t.count("/sba-content/"))
    print("/api/sba/content/ count:", t.count("/api/sba/content/"))
    print('Ll="":', 'Ll=""' in t)
    print('Qs="/api":', 'Qs="/api"' in t)
    i = t.find("/api/sba/content/")
    print("snippet:", t[max(0, i - 60) : i + 80] if i >= 0 else "none")

print("=== HTTP ===")
urls = [
    "http://127.0.0.1:5000/sba-content/articles?query=&page=1",
    "http://127.0.0.1:5000/sba-content/articles?page=1",
    "http://localhost:5000/sba-content/articles?query=&page=1",
    "http://127.0.0.1:3000/sba-content/articles?page=1",
    "http://127.0.0.1:3000/",
]
for u in urls:
    try:
        r = urllib.request.urlopen(u, timeout=60)
        body = r.read()
        if u.rstrip("/").endswith(":3000"):
            mm = re.search(r"main\.[^\"'\s]+", body.decode("utf-8", "replace"))
            print("OK", r.status, "index→", mm.group(0) if mm else "?", u)
        else:
            print("OK", r.status, "len", len(body), u)
    except Exception as e:
        print("FAIL", u, e)
