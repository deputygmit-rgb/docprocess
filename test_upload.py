import requests
import sys
import os

url = "http://localhost:5000/upload"

# Test files - update these paths to your actual test files
test_files = [
    # Document formats
    "uploads/Draft.pdf",           # PDF
    #"uploads/document.docx",       # Word document
    #"uploads/document.doc",        # Older Word format
    #"uploads/presentation.pptx",   # PowerPoint
    #"uploads/presentation.ppt",    # Older PowerPoint format
    #"uploads/spreadsheet.xlsx",    # Excel
    #"uploads/spreadsheet.xls",     # Older Excel format
    
    # Image formats
    #"uploads/Screenshot.png",           # PNG image
    #"uploads/image.jpg",           # JPEG image
    #"uploads/image.jpeg",          # JPEG image (alt extension)
    #"uploads/image.gif",           # GIF image
    #"uploads/image.bmp",           # Bitmap image
    #"uploads/image.webp",          # WebP image
    
    # Other document formats
    #"uploads/document.odt",        # OpenDocument Text
    #"uploads/presentation.odp",    # OpenDocument Presentation
    #"uploads/spreadsheet.ods",     # OpenDocument Spreadsheet
]

# Use the first test file that exists
test_file = None
for file_path in test_files:
    if os.path.exists(file_path):
        test_file = file_path
        break

if not test_file:
    print(f"No test files found. Tested paths: {test_files}")
    print("Please place a test file in one of the above locations")
    sys.exit(1)

try:
    print(f"Uploading: {test_file}")
    with open(test_file, "rb") as f:
        files = {"file": f}
        response = requests.post(url, files=files)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
