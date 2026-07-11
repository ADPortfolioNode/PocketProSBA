from pathlib import Path
import re

t = Path("frontend/build/static/js/main.f54a4e20.js").read_text(encoding="utf-8", errors="ignore")
print("sba-content count", t.count("sba-content"))
# Ll assignment patterns near start of file sections
for m in re.finditer(r'Ll="[^"]{0,80}"', t):
    print("Ll assign", m.group(0))
for m in re.finditer(r'([A-Za-z_$][\w$]*)="(https?://[^"]{0,60})"', t):
    if "5000" in m.group(2) or m.group(2).endswith("/api") or m.group(2) == "/api":
        print("base", m.group(0)[:100])
i = t.find("sba-content/")
print("--- first sba-content context ---")
print(t[max(0, i - 250) : i + 180])
# also find what Ll is assigned earlier - search backwards for Ll=
idx = t.find('concat(Ll,"/sba-content/')
if idx < 0:
    idx = t.find("sba-content/")
chunk = t[max(0, idx - 5000) : idx]
# last assignment to Ll before use
assigns = list(re.finditer(r'Ll=([^,;]+)', chunk))
print("recent Ll assigns in 5k before:", [a.group(0)[:80] for a in assigns[-5:]])
