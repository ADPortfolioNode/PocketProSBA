import requests

BACKEND_URL = "https://pocketprosba-backend.onrender.com"

def check_health():
    endpoints = ["/health", "/api/health"]
    for ep in endpoints:
        url = BACKEND_URL + ep
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"[PASS] Health check {ep} returned 200 OK: {response.json()}")
            else:
                print(f"[FAIL] Health check {ep} returned status code {response.status_code}")
        except Exception as e:
            print(f"[ERROR] Health check {ep} failed: {e}")

def check_api_registry():
    url = BACKEND_URL + "/api/registry"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"[PASS] API registry returned 200 OK")
            data = response.json()
            print(f"Available endpoints: {list(data.keys())}")
        else:
            print(f"[FAIL] API registry returned status code {response.status_code}")
    except Exception as e:
        print(f"[ERROR] API registry check failed: {e}")

def main():
    print("Starting backend integration tests...")
    check_health()
    check_api_registry()
    print("Tests completed.")

if __name__ == "__main__":
    main()
