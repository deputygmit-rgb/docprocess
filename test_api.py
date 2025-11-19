import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_health():
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_root():
    print("Testing root endpoint...")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_upload():
    print("Testing upload endpoint...")
    files = {"file": open("uploads/test_document.pdf", "rb")}
    response = requests.post(f"{BASE_URL}/upload", files=files)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        doc_id = response.json().get("document_id")
        print(f"\nDocument ID: {doc_id}")
        return doc_id
    print()
    return None

def test_list_documents():
    print("Testing list documents endpoint...")
    response = requests.get(f"{BASE_URL}/documents")
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Total documents: {result.get('total')}")
    print(f"Documents: {json.dumps(result.get('documents', []), indent=2)}")
    print()

def test_get_document(doc_id):
    print(f"Testing get document endpoint for ID {doc_id}...")
    response = requests.get(f"{BASE_URL}/documents/{doc_id}")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Filename: {result.get('filename')}")
        print(f"Status: {result.get('status')}")
        print(f"File type: {result.get('file_type')}")
        print(f"Has layout data: {result.get('layout_data') is not None}")
        print(f"Has graph data: {result.get('graph_data') is not None}")
        print(f"Has processed JSON: {result.get('processed_json') is not None}")
        
        if result.get('error_message'):
            print(f"Error: {result.get('error_message')}")
    else:
        print(f"Response: {response.json()}")
    print()

if __name__ == "__main__":
    print("=== Document Processor API Test ===\n")
    
    test_health()
    test_root()
    test_list_documents()
    
    doc_id = test_upload()
    
    if doc_id:
        print("Waiting for processing (5 seconds)...")
        time.sleep(5)
        test_get_document(doc_id)
        test_list_documents()
