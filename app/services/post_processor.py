from openai import OpenAI
from langfuse.openai import openai as langfuse_openai
from app.core.config import get_settings
from typing import Dict, Any
import json

settings = get_settings()


class PostProcessorService:
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
    
    def process_graph_data(self, graph_data: Dict[str, Any], document_context: str = "") -> Dict[str, Any]:
        if not settings.OPENROUTER_API_KEY:
            return {
                "processed_data": {
                    "summary": "API key not configured",
                    "key_topics": [],
                    "main_points": [],
                    "data_insights": [],
                    "semantic_relationships": [],
                    "metadata": graph_data.get("node_count", 0)
                },
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            }
        
        prompt = f"""You are a document analysis expert. Analyze this document graph and generate a comprehensive JSON summary.

Document Graph Data:
{json.dumps(graph_data, indent=2)}

{f"Additional Context: {document_context}" if document_context else ""}

Your task:
1. Analyze the document structure and elements
2. Identify key topics, themes, and main points
3. Extract important data from tables and charts
4. Infer semantic relationships beyond spatial layout
5. Generate a structured JSON summary

Return JSON with this structure:
{{
  "summary": "Brief document summary",
  "key_topics": ["topic1", "topic2"],
  "main_points": [
    {{
      "point": "Main point description",
      "supporting_elements": ["element_id1", "element_id2"]
    }}
  ],
  "data_insights": [
    {{
      "type": "table|chart|figure",
      "element_id": "id",
      "insight": "Key insight from this data"
    }}
  ],
  "semantic_relationships": [
    {{
      "from_element": "id1",
      "to_element": "id2",
      "relationship": "explains|supports|contradicts|extends",
      "description": "How they relate"
    }}
  ],
  "metadata": {{
    "total_elements": 0,
    "element_types": {{}},
    "pages_analyzed": 0
  }}
}}

Return only the JSON, no additional text."""

        try:
            response = self.client.chat.completions.create(
                model=settings.PROCESSOR_MODEL,
                messages=[
                    {"role": "system", "content": "You are a document analysis expert. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=3000,
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
                "processed_data": result,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
        except Exception as e:
            return {
                "processed_data": {
                    "summary": f"Processing failed: {str(e)}",
                    "key_topics": [],
                    "main_points": [],
                    "data_insights": [],
                    "semantic_relationships": [],
                    "metadata": {"error": str(e)}
                },
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            }
    
    def generate_context_retrieval(self, query: str, graph_data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""Given this document graph and user query, retrieve relevant context.

Query: {query}

Document Graph:
{json.dumps(graph_data, indent=2)}

Return JSON:
{{
  "relevant_elements": ["element_id1", "element_id2"],
  "answer": "Direct answer to the query",
  "supporting_text": "Relevant excerpts",
  "confidence": 0.95
}}"""

        try:
            response = self.client.chat.completions.create(
                model=settings.PROCESSOR_MODEL,
                messages=[
                    {"role": "system", "content": "You are a document Q&A assistant. Return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1500
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
            
            return result
            
        except Exception as e:
            raise Exception(f"Context retrieval failed: {str(e)}")
