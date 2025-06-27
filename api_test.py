import requests

BASE_URL = "http://localhost:5000"

def test_decompose():
    url = f"{BASE_URL}/api/decompose"
    payload = {"message": "Test task decomposition"}
    response = requests.post(url, json=payload)
    print("Decompose Response:", response.status_code, response.text)

def test_execute():
    url = f"{BASE_URL}/api/execute"
    payload = {
        "task": {
            "step_number": 1,
            "instruction": "Test execution step",
            "suggested_agent_type": "FunctionAgent"
        }
    }
    response = requests.post(url, json=payload)
    print("Execute Response:", response.status_code, response.text)

def test_validate():
    url = f"{BASE_URL}/api/validate"
    payload = {
        "result": "Test result",
        "task": {
            "step_number": 1,
            "instruction": "Test validation step"
        }
    }
    response = requests.post(url, json=payload)
    print("Validate Response:", response.status_code, response.text)

def test_files_get():
    url = f"{BASE_URL}/api/files"
    response = requests.get(url)
    print("Files GET Response:", response.status_code, response.text)

def test_files_post():
    url = f"{BASE_URL}/api/files"
    files = {'file': open('INSTRUCTIONS.md', 'rb')}
    response = requests.post(url, files=files)
    print("Files POST Response:", response.status_code, response.text)

def run_all_tests():
    test_decompose()
    test_execute()
    test_validate()
    test_files_get()
    test_files_post()

if __name__ == "__main__":
    run_all_tests()
