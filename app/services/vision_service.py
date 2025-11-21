from openai import OpenAI
from langfuse.openai import openai as langfuse_openai
from app.core.config import get_settings
from typing import List, Dict, Any
from PIL import Image
import json

settings = get_settings()


class VisionService:
    def __init__(self):
        self.use_langfuse = bool(settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY)
        
        if self.use_langfuse:
            self.client = langfuse_openai.OpenAI(
                api_key=settings.OPENROUTER_API_KEY,
                base_url=settings.OPENROUTER_BASE_URL
            )
        else:
            self.client = OpenAI(
                api_key=settings.OPENROUTER_API_KEY,
                base_url=settings.OPENROUTER_BASE_URL
            )
    
    def extract_chart_details(self, image_base64: str, page_number: int, chart_index: int, chart_location: str = None, chart_bbox: List[float] = None) -> Dict[str, Any]:
        """Extract detailed chart components: title, axes, legend, data series, gridlines, etc.
        
        Args:
            image_base64: Base64 encoded image
            page_number: Page number being analyzed
            chart_index: Index of chart (0-based)
            chart_location: Human-readable location (e.g., "top-left", "bottom-right")
            chart_bbox: Bounding box [x1, y1, x2, y2] as percentage or pixels
        """
        if not settings.OPENROUTER_API_KEY:
            return {
                "chart_index": chart_index,
                "chart_type": "unknown",
                "chart_title": "",
                "chart_area": {},
                "plot_area": {},
                "data_series": [],
                "horizontal_axis": {},
                "vertical_axis": {},
                "axis_titles": {},
                "legend": {},
                "data_labels": [],
                "gridlines": {},
                "key_insights": ""
            }
        
        # Build location context
        location_context = f"chart at {chart_location}" if chart_location else f"chart #{chart_index}"
        bbox_context = f" Located in image region: {chart_bbox}" if chart_bbox else ""
        
        prompt = f"""CRITICAL INSTRUCTION: Analyze ONLY the {location_context}{bbox_context} from page {page_number}.
IGNORE all other charts, images, text, and elements outside this specific chart region.
Focus EXCLUSIVELY on this one chart - do not mix data from other charts.

EXTRACTION REQUIREMENTS - STRICT FOCUS ON THIS CHART ONLY:
1. This chart is positioned as indicated above
2. Extract ONLY data that belongs to THIS specific chart
3. Completely IGNORE any other charts on the page
4. If chart boundaries overlap visually, use the specified location to determine which data belongs to this chart
5. Read title directly from this specific chart
6. Read axis labels from this chart only
7. Extract ALL data values from this specific chart
8. If multiple series exist in THIS chart, list each one separately with ALL its data points
9. Validate that all extracted data is from this chart, not from adjacent charts

Return ONLY this JSON structure (no markdown, no extra text):
{{
  "chart_index": {chart_index},
  "chart_type": "bar|line|pie|scatter|area|combination|bubble|stock|surface|other",
  "chart_title": "exact title text shown in chart",
  "chart_title_source": "read directly from chart|inferred from context|not visible",
  "chart_area": {{
    "position": "top-left|top-center|top-right|center-left|center|center-right|bottom-left|bottom-center|bottom-right|full-page",
    "approximate_bounds": "describe location and size",
    "background_color": "color name or hex if visible",
    "border": "yes|no|style if visible"
  }},
  "plot_area": {{
    "position": "describe location within chart",
    "background_color": "color if different from chart",
    "grid_background": "yes|no"
  }},
  "data_series": [
    {{
      "series_index": 0,
      "series_name": "exact name from legend or chart",
      "data_points": ["value1", "value2", "value3", "..."],
      "point_count": number,
      "series_color": "color name or hex",
      "line_style": "solid|dashed|dotted|other",
      "marker_style": "circle|square|triangle|none|other",
      "data_representation": "bars|lines|pie_slices|dots|areas|candlesticks|other",
      "all_values_extracted": true,
      "missing_values": "none|describe any unclear values",
      "notes": "any important observations about this series"
    }}
  ],
  "horizontal_axis": {{
    "axis_title": "exact title text if present",
    "axis_type": "category|value|time|date|other",
    "categories": ["item1", "item2", "item3", "..."],
    "category_count": number,
    "min_value": "if numeric",
    "max_value": "if numeric",
    "scale": "linear|logarithmic|other",
    "tick_interval": "if visible",
    "unit": "if applicable"
  }},
  "vertical_axis": {{
    "axis_title": "exact title text if present",
    "axis_type": "value|category|time|date|other",
    "categories": ["if applicable"],
    "min_value": "numeric minimum shown",
    "max_value": "numeric maximum shown",
    "scale": "linear|logarithmic|other",
    "tick_interval": "if visible",
    "unit": "currency|percentage|count|other"
  }},
  "axis_titles": {{
    "x_axis_title": "exact text",
    "y_axis_title": "exact text",
    "secondary_x_axis_title": "if present",
    "secondary_y_axis_title": "if present"
  }},
  "legend": {{
    "position": "top|bottom|left|right|inside|none|not visible",
    "entries": [
      {{"index": 0, "name": "series name", "color": "hex or color name", "symbol": "shape if visible"}}
    ],
    "entry_count": number,
    "is_visible": true,
    "orientation": "horizontal|vertical"
  }},
  "data_labels": [
    {{
      "location": "describe where label appears",
      "text": "exact label text",
      "associated_data": "which data point this labels",
      "format": "number|percentage|currency|text"
    }}
  ],
  "gridlines": {{
    "horizontal_visible": true,
    "horizontal_style": "solid|dashed|dotted",
    "horizontal_color": "color",
    "vertical_visible": true,
    "vertical_style": "solid|dashed|dotted",
    "vertical_color": "color",
    "major_gridlines": "visible|not visible",
    "minor_gridlines": "visible|not visible"
  }},
  "key_insights": "Summary of what chart shows, trends, key numbers, and important patterns",
  "extraction_quality": {{
    "title_confidence": "high|medium|low",
    "data_confidence": "high|medium|low",
    "legend_clarity": "clear|somewhat clear|unclear",
    "overall_readability": "excellent|good|poor"
  }}
}}"

    "axis_title": "Y-axis title if present",
    "value_range": {{"min": "value", "max": "value"}},
    "scale": "linear|logarithmic",
    "visible_tick_labels": ["label1", "label2"]
  }},
  "axis_titles": {{
    "x_axis_title": "title if present",
    "y_axis_title": "title if present",
    "secondary_x_axis_title": "if present",
    "secondary_y_axis_title": "if present"
  }},
  "legend": {{
    "position": "top|bottom|right|left|none",
    "entries": [
      {{"name": "series name", "color": "color", "symbol": "symbol type"}}
    ],
    "is_visible": true,
    "orientation": "horizontal|vertical"
  }},
  "data_labels": [
    {{
      "position": "location in chart",
      "text": "label text",
      "format": "percentage|absolute|currency"
    }}
  ],
  "gridlines": {{
    "horizontal_gridlines": {{"visible": true, "style": "solid|dashed", "color": "color"}},
    "vertical_gridlines": {{"visible": true, "style": "solid|dashed", "color": "color"}},
    "major_gridlines": "visible or not",
    "minor_gridlines": "visible or not"
  }},
  "key_insights": "summary of what the chart shows, main data points, trends, or important patterns"
}}

IMPORTANT:
- Extract ALL visible text from the chart
- Include all data series visible in the chart
- Capture axis labels and range values
- Describe colors, positions, and relationships
- Extract the key message/insight the chart conveys
- Return ONLY valid JSON, no markdown or code blocks"""

        try:
            response = self.client.chat.completions.create(
                model=settings.VISION_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": image_base64}}
                        ]
                    }
                ],
                temperature=0.1,
                max_tokens=3000,
                extra_headers={
                    "HTTP-Referer": "",
                    "X-Title": "Document Processor"
                }
            )
            
            content = response.choices[0].message.content
            
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                content_clean = content.strip()
                if content_clean.startswith("```json"):
                    content_clean = content_clean[7:]
                if content_clean.endswith("```"):
                    content_clean = content_clean[:-3]
                result = json.loads(content_clean.strip())
            
            result["chart_index"] = chart_index
            return result
            
        except Exception as e:
            return {
                "chart_index": chart_index,
                "error": f"Chart extraction failed: {str(e)}",
                "chart_type": "unknown"
            }
    
    def extract_layout(self, image_base64: str, page_number: int = 1) -> Dict[str, Any]:
        if not settings.OPENROUTER_API_KEY:
            return {
                "page_number": page_number,
                "layout": {"elements": [], "relationships": []},
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                "error": "OPENROUTER_API_KEY not configured"
            }
        
        prompt = f"""Analyze this document page {page_number} and identify ALL layout elements with special focus on charts.

Return a JSON object with this exact structure:
{{
  "elements": [
    {{
      "id": "element_id",
      "type": "paragraph|table|chart|image|heading",
      "text": "extracted text content or chart title",
      "bbox": [x1, y1, x2, y2],
      "confidence": 0.95,
      "is_chart": false
    }}
  ],
  "relationships": [
    {{
      "from": "element_id1",
      "to": "element_id2",
      "type": "describes|references|follows|contains"
    }}
  ],
  "chart_count": number_of_charts_detected
}}

CHART DETECTION REQUIREMENTS:
- Identify ALL charts (bar, line, pie, scatter, area, etc.)
- Mark chart elements with "is_chart": true
- Include chart title, type, and brief description in "text" field
- Mark each chart position with accurate bbox

Detect:
- Paragraphs with their text content
- Tables with structure and content
- Charts and figures (MUST identify all charts)
- Images
- Headings and titles
- Spatial relationships between elements

Return only the JSON object, no additional text."""

        try:
            response = self.client.chat.completions.create(
                model=settings.VISION_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": image_base64}}
                        ]
                    }
                ],
                temperature=0.1,
                max_tokens=4000,
                extra_headers={
                    "HTTP-Referer": "",
                    "X-Title": "Document Processor"
                }
            )
            
            content = response.choices[0].message.content
            
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                content_clean = content.strip()
                if content_clean.startswith("```json"):
                    content_clean = content_clean[7:]
                if content_clean.endswith("```"):
                    content_clean = content_clean[:-3]
                result = json.loads(content_clean.strip())
            
            # Extract detailed chart information for each detected chart
            chart_count = result.get("chart_count", 0)
            chart_elements = []
            
            if not chart_count:
                # Count charts from elements if not explicitly provided
                chart_elements = [elem for elem in result.get("elements", []) if elem.get("is_chart")]
                chart_count = len(chart_elements)
            else:
                # Extract chart elements for location information
                chart_elements = [elem for elem in result.get("elements", []) if elem.get("is_chart")]
            
            chart_details = []
            if chart_count > 0:
                for chart_idx in range(chart_count):
                    # Get chart location/bbox if available
                    chart_location = None
                    chart_bbox = None
                    
                    if chart_idx < len(chart_elements):
                        elem = chart_elements[chart_idx]
                        chart_location = elem.get("text", f"Chart {chart_idx + 1}")
                        chart_bbox = elem.get("bbox")
                    
                    chart_detail = self.extract_chart_details(
                        image_base64, 
                        page_number, 
                        chart_idx,
                        chart_location=chart_location,
                        chart_bbox=chart_bbox
                    )
                    chart_details.append(chart_detail)
            
            return {
                "page_number": page_number,
                "layout": result,
                "chart_details": chart_details,
                "chart_count": chart_count,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
        except Exception as e:
            return {
                "page_number": page_number,
                "layout": {"elements": [], "relationships": []},
                "chart_details": [],
                "chart_count": 0,
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                "error": f"Vision extraction failed: {str(e)}"
            }
