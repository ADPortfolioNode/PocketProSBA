import requests
import os
import json
import sys

BASE_URL = "http://localhost:10000"
TEST_DOCUMENT = "production_test_document.txt"

def print_test_header(title):
    print("\n" + "=" * 60)
    print(f"Test: {title}")
    print("=" * 60)

def print_test_result(test_name, success, message=""):
    status = "PASS" if success else "FAIL"
    print(f"{test_name}: {status}")
    if message:
        print(f"   -> {message}")
    return success

def test_health_check():
    print_test_header("Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200 and response.json().get("status") == "healthy":
            return print_test_result("Health Check", True, f"Response: {response.json()}")
        else:
            return print_test_result("Health Check", False, f"Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        return print_test_result("Health Check", False, f"Error: {e}")

def test_api_info():
    print_test_header("API Info")
    try:
        response = requests.get(f"{BASE_URL}/api/info", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return print_test_result("API Info", True, f"App Name: {data.get('app_name', 'Unknown')}, Documents: {data.get('documents_count', 0)}")
        else:
            return print_test_result("API Info", False, f"Status: {response.status_code}")
    except Exception as e:
        return print_test_result("API Info", False, f"Error: {e}")

def test_chromadb_connection():
    print_test_header("ChromaDB Connection")
    try:
        response = requests.get(f"{BASE_URL}/api/debug/chromadb", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("connection_test", {}).get("available"):
                return print_test_result("ChromaDB Connection", True, "ChromaDB is connected.")
            else:
                return print_test_result("ChromaDB Connection", False, f"ChromaDB connection not available. Details: {data}")
        else:
            return print_test_result("ChromaDB Connection", False, f"Status: {response.status_code}")
    except Exception as e:
        return print_test_result("ChromaDB Connection", False, f"Error: {e}")

def test_document_upload_and_ingest():
    print_test_header("Document Upload and Ingest")
    if not os.path.exists(TEST_DOCUMENT):
        return print_test_result("Document Upload", False, f"Test document not found: {TEST_DOCUMENT}")

    try:
        with open(TEST_DOCUMENT, 'rb') as f:
            files = {'file': (os.path.basename(TEST_DOCUMENT), f, 'text/plain')}
            response = requests.post(f"{BASE_URL}/api/documents/upload_and_ingest_document", files=files, timeout=30)

        if response.status_code == 200:
            return print_test_result("Document Upload", True, "Document uploaded and ingested successfully.")
        else:
            return print_test_result("Document Upload", False, f"Status: {response.status_code} - {response.text}")
    except Exception as e:
        return print_test_result("Document Upload", False, f"Error: {e}")

def test_rag_query():
    print_test_header("RAG Query")
    try:
        query_data = {"query": "What is this document about?"}
        response = requests.post(f"{BASE_URL}/api/query", json=query_data, headers={'Content-Type': 'application/json'}, timeout=30)

        if response.status_code == 200 and response.json().get("success"):
            return print_test_result("RAG Query", True, "RAG query returned a successful response.")
        else:
            return print_test_result("RAG Query", False, f"Status: {response.status_code} - {response.text}")
    except Exception as e:
        return print_test_result("RAG Query", False, f"Error: {e}")

def run_production_tests():
    print("=" * 60)
    print("PocketProSBA Production Readiness Test Suite")
    print("=" * 60)

    results = {
        "Health Check": test_health_check(),
        "API Info": test_api_info(),
        "ChromaDB Connection": test_chromadb_connection(),
        "Document Upload": test_document_upload_and_ingest(),
        "RAG Query": test_rag_query(),
    }

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed_count = sum(1 for result in results.values() if result)
    total_count = len(results)

    for test, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"- {test}: {status}")

    print(f"\nTotal Tests: {total_count}, Passed: {passed_count}, Failed: {total_count - passed_count}")

    if passed_count == total_count:
        print("\nSuccess! All production tests passed. The application appears to be production-ready.")
        sys.exit(0)
    else:
        print("\nError: Some production tests failed. Please review the logs above.")
        sys.exit(1)

if __name__ == "__main__":
    run_production_tests()