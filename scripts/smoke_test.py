#!/usr/bin/env python3
"""Quick API smoke tests against a running PocketPro backend."""
import json
import sys
import requests

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5000"


def main():
    print("=== SMOKE TESTS ===")
    print(f"Target: {BASE}\n")
    results = []

    gets = [
        "/",
        "/health",
        "/api/health",
        "/api/info",
        "/api/diagnostics",
        "/api/chromadb_health",
        "/api/rag/health",
        "/api/orchestrator/health",
    ]
    for path in gets:
        try:
            r = requests.get(BASE + path, timeout=15)
            body = r.text[:140].replace("\n", " ")
            ok = r.status_code in (200, 503)  # 503 ok for degraded RAG
            results.append((f"GET {path}", r.status_code, ok, body))
            print(f"GET {path} -> {r.status_code} {body}")
        except Exception as e:
            results.append((f"GET {path}", 0, False, str(e)))
            print(f"GET {path} -> ERR {e}")

    # Decompose
    try:
        r = requests.post(
            BASE + "/api/decompose",
            json={"message": "Help me plan an SBA loan", "session_id": "smoke-1"},
            timeout=30,
        )
        ok = r.status_code == 200
        results.append(("POST /api/decompose", r.status_code, ok, r.text[:140]))
        print(f"POST /api/decompose -> {r.status_code} {r.text[:140].replace(chr(10), ' ')}")
    except Exception as e:
        results.append(("POST /api/decompose", 0, False, str(e)))
        print(f"POST /api/decompose -> ERR {e}")

    # Chat
    try:
        r = requests.post(
            BASE + "/api/chat",
            json={"user_id": 1, "message": "What SBA loans exist?", "session_id": "smoke-chat"},
            timeout=30,
        )
        data = r.json() if r.ok else {}
        ok = r.status_code == 200 and data.get("success") is True
        resp = (data.get("response") or "")[:80]
        results.append(("POST /api/chat", r.status_code, ok, resp))
        print(f"POST /api/chat -> {r.status_code} success={data.get('success')} resp={resp}")
    except Exception as e:
        results.append(("POST /api/chat", 0, False, str(e)))
        print(f"POST /api/chat -> ERR {e}")

    # Validate (short result may FAIL; longer should PASS)
    try:
        r = requests.post(
            BASE + "/api/validate",
            json={
                "result": "Completed SBA loan research with detailed findings and next steps.",
                "task": {"step": "test"},
            },
            timeout=15,
        )
        ok = r.status_code == 200 and r.json().get("status") in ("PASS", "FAIL")
        results.append(("POST /api/validate", r.status_code, ok, r.text[:100]))
        print(f"POST /api/validate -> {r.status_code} {r.json()}")
    except Exception as e:
        results.append(("POST /api/validate", 0, False, str(e)))
        print(f"POST /api/validate -> ERR {e}")

    # Chat without user_id (optional field in current API)
    try:
        r = requests.post(
            BASE + "/api/chat",
            json={"message": "hi", "session_id": "x"},
            timeout=30,
        )
        ok = r.status_code in (200, 400)
        results.append(("POST /api/chat (no user_id)", r.status_code, ok, r.text[:80]))
        print(f"POST /api/chat (no user_id) -> {r.status_code}")
    except Exception as e:
        results.append(("POST /api/chat (no user_id)", 0, False, str(e)))
        print(f"POST /api/chat (no user_id) -> ERR {e}")

    passed = sum(1 for _, _, ok, _ in results if ok)
    total = len(results)
    print(f"\n=== RESULT: {passed}/{total} checks passed ===")
    failed = [name for name, _, ok, _ in results if not ok]
    if failed:
        print("Failed:", ", ".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
