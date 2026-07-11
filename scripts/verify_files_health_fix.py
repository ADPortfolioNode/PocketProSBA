import re
import urllib.request
from pathlib import Path

# disk
p = Path("frontend/build/static/js/main.f54a4e20.js")
t = p.read_text(encoding="utf-8", errors="ignore")
m = re.search(r'Qs="[^"]+"', t)
print("disk", m.group(0) if m else "n/a")
print("disk has :5000", ":5000" in t)
print("disk soft", "Backend health soft-fail" in t)
print("disk hard throw", 'throw new Error("Backend service is not available")' in t)

# served
for url in [
    "http://127.0.0.1:3000/static/js/main.f54a4e20.js",
    "http://127.0.0.1:3000/",
]:
    try:
        body = urllib.request.urlopen(url, timeout=20).read().decode("utf-8", "ignore")
        if url.endswith(".js"):
            m = re.search(r'Qs="[^"]+"', body)
            print("served js", m.group(0) if m else "n/a", "has5000", ":5000" in body)
        else:
            m = re.search(r'main\.[^"\s]+', body)
            print("index", m.group(0) if m else "n/a")
    except Exception as e:
        print(url, "FAIL", e)

for u in [
    "http://127.0.0.1:3000/api/health",
    "http://127.0.0.1:3000/api/api/health",
    "http://127.0.0.1:5000/api/api/health",
    "http://127.0.0.1:5000/api/api/files",
    "http://localhost:5000/api/api/files",
]:
    try:
        method = "OPTIONS" if u.endswith("files") else "GET"
        req = urllib.request.Request(u, method=method)
        r = urllib.request.urlopen(req, timeout=15)
        print(method, u, r.status)
    except Exception as e:
        print(method if "files" in u else "GET", u, "FAIL", e)
