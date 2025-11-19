# Document Processor API - Replit Project

## Overview
A comprehensive FastAPI-based document processing pipeline with vision-based layout extraction, graph construction, and LLM-powered context retrieval. The system processes PDF, DOC, PPT, and XLSX documents to extract structured data, build relationship graphs, and generate contextual JSON summaries.

## Recent Updates (November 19, 2025)
- ✅ Added CORS middleware for cross-origin requests
- ✅ Implemented synchronous task execution (no Redis/Docker required)
- ✅ Enhanced element schema with embeddings metadata
- ✅ Added document_id, element_id, page_number tracking
- ✅ Implemented boolean flags for embedding creation status
- ✅ Added relationships, parent_element, child_elements, page_summary fields
- ✅ Added timing metrics for JSON generation
- ✅ Removed embedding data vectors (boolean flags only for efficiency)
- ✅ Made Celery task eager mode for immediate processing

## Project Architecture

### Core Components
1. **FastAPI Application** (`app/main.py`)
   - File upload endpoints for documents
   - RESTful API for document management
   - Synchronous task execution
   - CORS enabled
   
2. **Document Processor** (`app/utils/document_processor.py`)
   - PDF page extraction and image conversion
   - PowerPoint slide text extraction
   - Excel data parsing
   - Word document text/table extraction

3. **Vision Service** (`app/services/vision_service.py`)
   - Qwen2-VL-72B integration via OpenRouter
   - Layout element detection (paragraphs, tables, charts, images)
   - Bounding box extraction
   - Element relationship identification

4. **Graph Service** (`app/services/graph_service.py`)
   - NetworkX-based document graph construction
   - Node representation of layout elements
   - Edge representation of relationships
   - Deterministic embedding generation (768-dim)
   - Relationship tracking (parent, children, connections)

5. **Post-Processor** (`app/services/post_processor.py`)
   - LLM-powered analysis of graph data
   - Semantic relationship inference
   - Structured JSON generation with timing metrics
   - Context retrieval for queries

6. **Infrastructure**
   - SQLite: Document metadata and processing status (default)
   - PostgreSQL: Document metadata (optional)
   - Qdrant: Vector embeddings (in-memory mode by default)
   - Redis: Caching and Celery broker (optional)
   - Celery: Async task processing (eager mode by default)

## API Endpoints

### Main Endpoints
- `POST /upload` - Upload document for processing (immediate)
- `GET /documents` - List all documents with filtering
- `GET /documents/{id}` - Get document details with results
- `DELETE /documents/{id}` - Delete document and file
- `GET /health` - Health check endpoint
- `GET /` - API info

## Response Schema

### Document Upload Response
```json
{
  "document_id": 1,
  "filename": "test_document.pdf",
  "file_type": ".pdf",
  "file_size": 2959,
  "status": "completed",
  "error_message": null,
  "message": "Document processed successfully"
}
```

### Graph Data - Element Node Schema
```json
{
  "id": "p1_para_1",
  "document_id": 1,
  "element_id": "p1_para_1",
  "page": 1,
  "page_number": 1,
  "type": "paragraph",
  "text": "Element content text",
  "bbox": [0, 0, 100, 100],
  "confidence": 0.95,
  "extraction_confidence": 0.95,
  "content_embedding": true,
  "context_embedding": true,
  "combined_embedding": true,
  "relationships": [
    {
      "from": "p1_para_1",
      "to": "p1_para_2",
      "type": "follows"
    }
  ],
  "parent_element": null,
  "child_elements": ["p1_para_2"],
  "page_summary": "Page 1: paragraph element"
}
```

### Processed JSON Response
```json
{
  "summary": "Document summary text",
  "key_topics": ["topic1", "topic2"],
  "main_points": [...],
  "data_insights": [...],
  "semantic_relationships": [...],
  "metadata": {...},
  "generation_time_seconds": 0.45,
  "generated_at": "2025-11-19T14:30:45.123456"
}
```

## Configuration

### Environment Variables
```env
DATABASE_URL - SQLite (default) or PostgreSQL connection
OPENROUTER_API_KEY - Required for vision and LLM processing
LANGFUSE_PUBLIC_KEY - Optional for tracing
LANGFUSE_SECRET_KEY - Optional for tracing
REDIS_URL - Optional for caching (default: localhost:6379/0)
CELERY_BROKER_URL - Optional for async (default: memory://)
CELERY_RESULT_BACKEND - Optional for results (default: cache+memory://)
```

### Models Used
- **Vision**: `qwen/qwen2.5-vl-72b-instruct` - Layout extraction
- **Processor**: `qwen/qwen-2.5-72b-instruct` - Context analysis

## Running the Application

### Quick Start (No External Dependencies)
```powershell
# Terminal 1: Start server
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload

# Terminal 2: Test upload
python test_upload.py

# Check results
curl http://localhost:5000/documents/1
```

### With Full Features (Optional Redis)
```powershell
# Start Redis container
docker run -d -p 6379:6379 --name redis-server redis:latest

# Start server
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```

## Testing

### Upload Document
```bash
curl -X POST -F "file=@uploads/test_document.pdf" http://localhost:5000/upload
```

### List Documents
```bash
curl http://localhost:5000/documents
```

### Get Document Details
```bash
curl http://localhost:5000/documents/1
```

### Health Check
```bash
curl http://localhost:5000/health
```

### Using Python
```powershell
python test_api.py
python test_upload.py
```

## Technical Details

### Embeddings
- Uses deterministic bag-of-words embeddings via hashlib.md5
- Creates 768-dimensional vectors for similarity search
- Tracks three types: content, context, combined
- Only stores boolean flags (not actual vectors) for efficiency
- Suitable for MVP; can be replaced with OpenAI/Cohere for production

### Graph Construction
- NetworkX DiGraph for document elements
- Automatic relationship inference based on element sequence
- Hierarchical parent-child relationships
- Page-based organization

### Performance
- Synchronous processing by default (no queue overhead)
- Generation time tracking in JSON responses
- Graceful degradation for missing services
- In-memory Qdrant for MVP (no persistence)

### Graceful Degradation
- Redis unavailable → Caching disabled, system continues
- OPENROUTER_API_KEY missing → Task fails with clear error message
- Celery worker not running → Tasks execute synchronously
- Langfuse keys missing → No tracing, processing continues

## File Limitations
- Max file size: 50MB
- Supported formats: .pdf, .docx, .pptx, .xlsx only
- Legacy formats (.doc, .ppt, .xls) not supported

## Dependencies
See `requirements.txt` for complete list. Key packages:
- fastapi, uvicorn
- sqlalchemy, alembic
- networkx, numpy
- PyMuPDF, python-pptx, openpyxl, python-docx
- openai, langfuse, qdrant-client
- celery, redis, reportlab

## Next Steps
1. (Optional) Obtain OPENROUTER_API_KEY to enable vision extraction
2. (Optional) Set up Langfuse for LLM monitoring
3. (Optional) Configure Redis for caching/async
4. (Optional) Set up PostgreSQL for production
5. Deploy to production environment
