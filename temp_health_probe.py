import urllib.request
for name, url in [('CHROMADB', 'http://localhost:8000/api/v1/heartbeat'), ('BACKEND', 'http://localhost:5000/api/health')]:
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            data = r.read(200).decode('utf-8', errors='replace')
            print(name, r.status, data)
    except Exception as e:
        print(name, 'ERROR', e)
