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
    
    def extract_layout(self, image_base64: str, page_number: int = 1) -> Dict[str, Any]:
        if not settings.OPENROUTER_API_KEY:
            return {
                "page_number": page_number,
                "layout": {"elements": [], "relationships": []},
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                "error": "OPENROUTER_API_KEY not configured"
            }
        
        prompt = f"""Analyze this document page {page_number} and identify all layout elements.
        
Return a JSON object with this exact structure:
{{
  "elements": [
    {{
      "id": "element_id",
      "type": "paragraph|table|chart|image|heading",
      "text": "extracted text content",
      "bbox": [x1, y1, x2, y2],
      "confidence": 0.95
    }}
  ],
  "relationships": [
    {{
      "from": "element_id1",
      "to": "element_id2",
      "type": "describes|references|follows|contains"
    }}
  ]
}}

Detect:
- Paragraphs with their text content
- Tables with structure
- Charts and figures
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
                    "HTTP-Referer": "https://replit.com",
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
            
            return {
                "page_number": page_number,
                "layout": result,
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
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                "error": f"Vision extraction failed: {str(e)}"
            }
