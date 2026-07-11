#!/usr/bin/env python3
"""Production-style smoke test for PocketPro SBA (frontend :3000, backend :5000)."""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
import uuid
from typing import Any, Callable, Optional

FE = "http://127.0.0.1:3000"
BE = "http://127.0.0.1:5000"
RESULTS: list[tuple[str, bool, str, int]] = []


def record(name: str, ok: bool, detail: str, ms: int = 0) -> None:
    RESULTS.append((name, ok, detail, ms))
    print(f"{'PASS' if ok else 'FAIL':4}  {name:48}  {detail}  ({ms}ms)")


def request(
    url: str,
    method: str = "GET",
    data: Optional[bytes] = None,
    headers: Optional[dict] = None,
    timeout: int = 60,
) -> tuple[int, bytes, int]:
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            return resp.status, body, int((time.perf_counter() - t0) * 1000)
    except urllib.error.HTTPError as e:
        body = e.read() if e.fp else b""
        return e.code, body, int((time.perf_counter() - t0) * 1000)


def jload(body: bytes) -> Any:
    try:
        return json.loads(body.decode("utf-8", "replace"))
    except Exception:
        return None


def check_get(
    name: str,
    url: str,
    expect: int = 200,
    min_len: int = 1,
    pred: Optional[Callable[[Any], bool]] = None,
) -> None:
    try:
        status, body, ms = request(url)
        ok = status == expect and len(body) >= min_len
        detail = f"status={status} len={len(body)}"
        if pred is not None:
            data = jload(body)
            pok = data is not None and bool(pred(data))
            ok = ok and pok
            detail += f" pred={pok}"
        record(name, ok, detail, ms)
    except Exception as e:
        record(name, False, str(e)[:180], 0)


def check_post_json(name: str, url: str, payload: dict, pred: Optional[Callable[[Any], bool]] = None) -> None:
    try:
        raw = json.dumps(payload).encode("utf-8")
        status, body, ms = request(
            url,
            method="POST",
            data=raw,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            timeout=90,
        )
        data = jload(body)
        ok = status == 200 and data is not None
        if pred is not None and data is not None:
            ok = ok and bool(pred(data))
        keys = list(data.keys())[:6] if isinstance(data, dict) else type(data).__name__
        record(name, ok, f"status={status} keys={keys}", ms)
    except Exception as e:
        record(name, False, str(e)[:180], 0)


def multipart_upload(url: str, filename: str, content: bytes) -> tuple[int, bytes, int]:
    boundary = "----WebKitFormBoundary" + uuid.uuid4().hex
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: text/plain\r\n\r\n"
    ).encode() + content + f"\r\n--{boundary}--\r\n".encode()
    return request(
        url,
        method="POST",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        timeout=90,
    )


def main() -> int:
    print("=" * 76)
    print("PocketPro SBA — PRODUCTION SMOKE TEST")
    print(f"FE={FE}  BE={BE}  {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 76)

    print("\n## Stack & health")
    check_get("BE /api/health", f"{BE}/api/health")
    check_get("BE /api/api/health", f"{BE}/api/api/health")
    check_get("BE /api/info", f"{BE}/api/info")
    check_get("FE proxy /api/health", f"{FE}/api/health")
    check_get("FE proxy /api/api/health", f"{FE}/api/api/health")

    print("\n## UI pages")
    for path in ["/", "/browse", "/sba", "/chat", "/rag", "/resources.html", "/programs.html", "/logo.gif"]:
        check_get(f"UI {path}", f"{FE}{path}", min_len=40)

    try:
        status, body, ms = request(f"{FE}/static/js/main.f54a4e20.js", timeout=30)
        text = body.decode("utf-8", "replace")
        has_qs = 'Qs="/api"' in text
        has_soft = "soft-fail" in text
        no_throw = 'throw new Error("Backend service is not available")' not in text
        ok = status == 200 and has_qs and no_throw
        record(
            "SPA main.js same-origin API",
            ok,
            f"status={status} Qs_api={has_qs} soft={has_soft}",
            ms,
        )
    except Exception as e:
        record("SPA main.js same-origin API", False, str(e)[:180])

    print("\n## SBA API parents/children")
    check_get(
        "SBA resources catalog",
        f"{BE}/api/sba/resources",
        pred=lambda d: isinstance(d.get("resources"), list) and len(d["resources"]) >= 5,
    )
    check_get(
        "SBA programs",
        f"{BE}/api/sba/programs",
        pred=lambda d: isinstance(d.get("items"), list) and len(d["items"]) >= 5,
    )
    check_get(
        "SBA lifecycle",
        f"{BE}/api/sba/lifecycle",
        pred=lambda d: isinstance(d.get("items"), list) and len(d["items"]) >= 5,
    )
    check_get(
        "Lifecycle /start children",
        f"{BE}/api/sba/lifecycle/start",
        pred=lambda d: isinstance(d.get("items"), list) and len(d["items"]) >= 5,
    )
    check_get(
        "Loans parent",
        f"{BE}/api/sba/content/loans",
        pred=lambda d: len(d.get("items") or []) >= 4 and bool(d.get("topic")),
    )
    check_get(
        "Loans child /7a",
        f"{BE}/api/sba/content/loans/7a",
        pred=lambda d: len(d.get("items") or []) >= 1,
    )
    check_get(
        "Contracting parent",
        f"{BE}/api/sba/content/contracting",
        pred=lambda d: len(d.get("items") or []) >= 5,
    )
    check_get(
        "Contracting child /8a",
        f"{BE}/api/sba/content/contracting/8a",
        pred=lambda d: len(d.get("items") or []) >= 1,
    )
    check_get(
        "Disaster parent",
        f"{BE}/api/sba/content/disaster",
        pred=lambda d: len(d.get("items") or []) >= 3,
    )
    check_get("Articles", f"{BE}/api/sba/content/articles?page=1", pred=lambda d: len(d.get("items") or []) >= 1)
    check_get("Offices", f"{BE}/api/sba/content/offices?page=1", pred=lambda d: len(d.get("items") or []) >= 1)
    check_get("Local resources", f"{BE}/api/sba/local-resources", pred=lambda d: len(d.get("items") or []) >= 1)

    try:
        status, body, ms = request(f"{BE}/api/sba/programs")
        items = (jload(body) or {}).get("items") or []
        loans = next((i for i in items if i.get("name") == "SBA Loans"), None)
        contracting = next((i for i in items if "Contract" in (i.get("name") or "")), None)
        ok = (
            loans is not None
            and loans.get("path") == "/api/sba/content/loans"
            and contracting is not None
            and contracting.get("path") == "/api/sba/content/contracting"
        )
        record(
            "Program badge paths",
            ok,
            f"loans={getattr(loans,'get',lambda k:None)('path') if not isinstance(loans,dict) else loans.get('path')} "
            f"contracting={contracting.get('path') if isinstance(contracting, dict) else None}",
            ms,
        )
    except Exception as e:
        record("Program badge paths", False, str(e)[:180])

    print("\n## FE proxy SBA")
    check_get("Proxy loans", f"{FE}/api/sba/content/loans", pred=lambda d: len(d.get("items") or []) >= 4)
    check_get("Proxy contracting", f"{FE}/api/sba/content/contracting", pred=lambda d: len(d.get("items") or []) >= 5)
    check_get("Proxy lifecycle/start", f"{FE}/api/sba/lifecycle/start", pred=lambda d: len(d.get("items") or []) >= 5)

    print("\n## File upload")
    for label, url in [
        ("BE /api/files", f"{BE}/api/files"),
        ("BE /api/api/files", f"{BE}/api/api/files"),
        ("FE /api/files", f"{FE}/api/files"),
        ("FE /api/api/files", f"{FE}/api/api/files"),
    ]:
        try:
            status, body, ms = multipart_upload(url, "prod-test.txt", b"production test upload\n")
            data = jload(body) or {}
            ok = status == 200 and (data.get("success") is True or data.get("document") or data.get("filename"))
            record(f"Upload {label}", ok, f"status={status} success={data.get('success')} file={data.get('filename')}", ms)
        except Exception as e:
            record(f"Upload {label}", False, str(e)[:180])

    print("\n## Chat")
    check_post_json(
        "Chat BE /api/chat",
        f"{BE}/api/chat",
        {"message": "What is an SBA 7(a) loan?", "session_id": "prod-test"},
        pred=lambda d: d.get("success") is True or bool(d.get("response") or d.get("message")),
    )
    check_post_json(
        "Chat BE /api/api/chat",
        f"{BE}/api/api/chat",
        {"message": "Hello", "session_id": "prod-test-2"},
        pred=lambda d: d.get("success") is True or bool(d.get("response") or d.get("message")),
    )
    check_post_json(
        "Chat FE proxy /api/chat",
        f"{FE}/api/chat",
        {"message": "Hi", "session_id": "prod-test-3"},
        pred=lambda d: d.get("success") is True or bool(d.get("response") or d.get("message")),
    )

    passed = sum(1 for _n, ok, _d, _m in RESULTS if ok)
    failed = sum(1 for _n, ok, _d, _m in RESULTS if not ok)
    print("\n" + "=" * 76)
    print(f"SUMMARY  pass={passed}  fail={failed}  total={len(RESULTS)}")
    if failed:
        print("FAILURES:")
        for name, ok, detail, _ms in RESULTS:
            if not ok:
                print(f"  - {name}: {detail}")
    if failed == 0:
        verdict = "PASS"
    elif failed <= 2 and passed >= 25:
        verdict = "PASS WITH NOTES"
    else:
        verdict = "FAIL"
    print(f"VERDICT: {verdict}")
    print("=" * 76)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
