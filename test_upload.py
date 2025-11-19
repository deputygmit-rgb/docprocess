import requests
import sys

url = "http://localhost:5000/upload"
file_path = "uploads/test_document.pdf"

try:
    with open(file_path, "rb") as f:
        files = {"file": f}
        response = requests.post(url, files=files)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
