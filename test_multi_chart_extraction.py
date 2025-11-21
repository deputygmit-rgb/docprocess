"""Test multi-chart extraction accuracy.

This script tests the chart extraction pipeline with images containing multiple charts
to verify that:
1. Each chart gets the correct title
2. Categories/axis labels are correct for each chart
3. Data values are correctly assigned to each chart
4. Series names are correct for each chart
"""

import json
import base64
import requests
from pathlib import Path


def encode_image_to_base64(image_path: str) -> str:
    """Encode image file to base64 data URI."""
    path = Path(image_path)
    
    # Determine MIME type
    mime_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.webp': 'image/webp'
    }
    
    ext = path.suffix.lower()
    mime_type = mime_types.get(ext, 'image/jpeg')
    
    with open(path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    
    return f"data:{mime_type};base64,{image_data}"


def test_multi_chart_extraction(image_path: str, expected_results: dict = None):
    """Test chart extraction on an image with multiple charts.
    
    Args:
        image_path: Path to test image
        expected_results: Dict with expected values for validation
            {
                "chart_count": 2,
                "charts": [
                    {
                        "index": 0,
                        "title": "Expected Title",
                        "series_count": 2,
                        "category_count": 5
                    },
                    ...
                ]
            }
    """
    print(f"\n{'='*80}")
    print(f"Testing: {image_path}")
    print(f"{'='*80}")
    
    # Encode image
    try:
        image_data = encode_image_to_base64(image_path)
        print(f"✓ Image encoded successfully")
    except Exception as e:
        print(f"✗ Failed to encode image: {e}")
        return
    
    # Call API
    try:
        response = requests.post(
            "http://localhost:5000/api/extract-layout",
            json={"image": image_data},
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        print(f"✓ API call successful")
    except Exception as e:
        print(f"✗ API call failed: {e}")
        return
    
    # Parse results
    chart_count = result.get("chart_count", 0)
    chart_details = result.get("chart_details", [])
    
    print(f"\nDetected {chart_count} charts")
    
    if chart_count == 0:
        print("✗ No charts detected")
        return
    
    # Validate each chart
    all_valid = True
    for chart_idx, chart in enumerate(chart_details):
        print(f"\n--- Chart {chart_idx + 1} ---")
        
        # Check for errors
        if "error" in chart:
            print(f"✗ Error: {chart['error']}")
            all_valid = False
            continue
        
        # Extract key information
        title = chart.get("chart_title", "")
        chart_type = chart.get("chart_type", "unknown")
        series_count = len(chart.get("data_series", []))
        
        # Get axis information
        h_axis = chart.get("horizontal_axis", {})
        v_axis = chart.get("vertical_axis", {})
        
        h_categories = h_axis.get("categories", [])
        v_range = v_axis.get("value_range", {}) if "value_range" in v_axis else {"min": v_axis.get("min_value"), "max": v_axis.get("max_value")}
        
        # Print extracted data
        print(f"  Type: {chart_type}")
        print(f"  Title: {title if title else '(no title)'}")
        print(f"  Series: {series_count}")
        print(f"  Categories: {len(h_categories)}")
        
        if h_categories:
            print(f"    Labels: {h_categories[:5]}{'...' if len(h_categories) > 5 else ''}")
        
        # Print series data
        for series_idx, series in enumerate(chart.get("data_series", [])):
            series_name = series.get("series_name", f"Series {series_idx + 1}")
            data_points = series.get("data_points", [])
            all_extracted = series.get("all_values_extracted", False)
            
            print(f"  Series {series_idx + 1}: {series_name}")
            print(f"    Data: {data_points[:5]}{'...' if len(data_points) > 5 else ''}")
            print(f"    Complete: {'✓' if all_extracted else '✗'}")
        
        # Validate against expected results if provided
        if expected_results and "charts" in expected_results:
            if chart_idx < len(expected_results["charts"]):
                expected = expected_results["charts"][chart_idx]
                
                # Check title
                expected_title = expected.get("title", "")
                if expected_title and title.lower() != expected_title.lower():
                    print(f"  ✗ Title mismatch: expected '{expected_title}', got '{title}'")
                    all_valid = False
                else:
                    print(f"  ✓ Title correct")
                
                # Check series count
                expected_series = expected.get("series_count")
                if expected_series and series_count != expected_series:
                    print(f"  ✗ Series count mismatch: expected {expected_series}, got {series_count}")
                    all_valid = False
                else:
                    print(f"  ✓ Series count correct")
                
                # Check category count
                expected_cats = expected.get("category_count")
                if expected_cats and len(h_categories) != expected_cats:
                    print(f"  ✗ Category count mismatch: expected {expected_cats}, got {len(h_categories)}")
                    all_valid = False
                else:
                    print(f"  ✓ Category count correct")
    
    # Summary
    print(f"\n{'='*80}")
    if all_valid and expected_results:
        print("✓ ALL VALIDATIONS PASSED")
    elif expected_results:
        print("✗ SOME VALIDATIONS FAILED - See details above")
    else:
        print(f"✓ Extraction complete - {chart_count} charts extracted")
    
    # Print full JSON for review
    print(f"\nFull response (first 2000 chars):")
    print(json.dumps(result, indent=2)[:2000])
    
    return result


if __name__ == "__main__":
    import sys
    
    # Check if API is running
    try:
        requests.get("http://localhost:5000/health", timeout=5)
    except:
        print("✗ API not running on http://localhost:5000")
        print("Start the API with: python app/main.py")
        sys.exit(1)
    
    # Look for test images in uploads directory
    uploads_dir = Path("uploads")
    if uploads_dir.exists():
        multi_chart_images = list(uploads_dir.glob("*multi*")) + list(uploads_dir.glob("*chart*"))
        if multi_chart_images:
            print(f"Found {len(multi_chart_images)} potential multi-chart images")
            for img in multi_chart_images[:1]:  # Test first one
                test_multi_chart_extraction(str(img))
        else:
            print("No multi-chart images found in uploads/")
            print("Please add test images with multiple charts to uploads/")
    else:
        print("uploads/ directory not found")
        print("Please create it and add test images")
