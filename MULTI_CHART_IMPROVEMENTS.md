# Multi-Chart Extraction Improvements

## Problem
When processing images with multiple charts, the extraction was returning:
- Wrong titles for each chart
- Wrong categories/axis labels
- Wrong data values
- Wrong series assignments

## Root Cause
The vision API couldn't distinguish between multiple charts using only a numeric index. When told "analyze chart #0", it might mix data from chart #0 and chart #1.

## Solution

### 1. Spatial Location Passing
Instead of just passing a chart index, the system now:
- Extracts chart **bounding boxes** (bbox) from the initial layout detection
- Passes spatial location information like "chart at top-left" instead of just "chart #0"
- Provides explicit bbox coordinates to focus the vision API on specific regions

### 2. Enhanced Chart Isolation
The prompt now includes explicit instructions:
- "IGNORE all other charts, images, text, and elements outside this specific chart region"
- "Focus EXCLUSIVELY on this one chart - do not mix data from other charts"
- "If chart boundaries overlap visually, use the specified location to determine which data belongs to this chart"

### 3. Implementation Details

**File: `app/services/vision_service.py`**
- Updated `extract_chart_details()` signature to accept:
  - `chart_location` (str): Human-readable position (e.g., "top-left", "bottom-right")
  - `chart_bbox` (List[float]): Bounding box coordinates [x1, y1, x2, y2]

**File: `app/services/vision_service.py`** - `extract_layout()` method
- Now extracts chart elements with their bbox information
- Passes location and bbox to `extract_chart_details()` for each chart
- Uses bbox from the layout detection to provide spatial context

**File: `app/main.py`**
- Added `/api/extract-layout` endpoint for direct testing
- Allows testing chart extraction without file upload
- Returns full layout and chart details

## Usage

### Direct Extract-Layout API
```bash
curl -X POST http://localhost:5000/api/extract-layout \
  -H "Content-Type: application/json" \
  -d '{
    "image": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
  }'
```

### Test Script
```bash
python test_multi_chart_extraction.py
```

This script:
1. Tests images in `uploads/` directory
2. Validates chart count, titles, series, and categories
3. Shows detailed extraction results
4. Compares against expected values if provided

## Expected Improvements

With these changes:
✓ Each chart in a multi-chart image gets its own correct title
✓ Axis labels are properly extracted for each chart
✓ Data values are correctly assigned to their source chart
✓ Series names match the correct series in the correct chart
✓ Gridlines, legends, and other components are accurately identified per chart

## Spatial Context Example

For an image with 2 charts (top row):
```
Chart #0:
  location: "top-left chart"
  bbox: [0.0, 0.0, 0.5, 0.5]
  
Chart #1:
  location: "top-right chart"
  bbox: [0.5, 0.0, 1.0, 0.5]
```

The vision API now knows:
- Chart 0 is the LEFT half of the image
- Chart 1 is the RIGHT half of the image
- Don't mix data between them

## Testing Approach

1. Upload image with 2-3 charts
2. Verify each chart gets correct:
   - Title (not mixed with other chart titles)
   - Axis labels (categories/values from correct chart)
   - Data series (correct names and values)
   - Series count (only count series in THIS chart)

## Files Modified

1. **app/services/vision_service.py**
   - Enhanced `extract_chart_details()` with location parameters
   - Updated `extract_layout()` to extract and pass bbox information
   - Improved prompt with spatial focus instructions

2. **app/main.py**
   - Added VisionService import
   - Added `/api/extract-layout` POST endpoint

3. **test_multi_chart_extraction.py** (NEW)
   - Test script for multi-chart validation
   - Supports expected results verification
   - Detailed extraction reporting

## Next Steps

1. Test with actual multi-chart images
2. Monitor extraction_quality scores in response
3. If needed, refine prompt further based on results
4. Consider adding chart boundary visualization debugging

## Known Limitations

- Very large images might still have boundary precision issues
- Overlapping chart boundaries may still cause some confusion
- Extremely small charts might be harder to isolate
- Different chart densities (many charts in small space) may need additional refinement
