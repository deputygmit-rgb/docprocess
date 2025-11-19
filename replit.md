# Document Processor API - Replit Project

## Overview
A comprehensive FastAPI-based document processing pipeline with vision-based layout extraction, graph construction, and LLM-powered context retrieval. The system processes PDF, DOC, PPT, and XLSX documents to extract structured data, build relationship graphs, and generate contextual JSON summaries.

## Recent Changes (November 19, 2025)
- Initial project setup with complete FastAPI application
- Implemented multi-format document processing (PDF, DOC, PPT, XLSX)
- Integrated Qwen2-VL-72B via OpenRouter for vision-based layout extraction
- Built NetworkX graph construction for document elements
- Added post-processor LLM for context retrieval and JSON generation
- Set up PostgreSQL for metadata storage
- Configured Qdrant (in-memory) for vector embeddings
- Implemented Redis caching layer (graceful degradation if unavailable)
- Created Celery task queue for async processing
- Integrated Langfuse for LLM observability and tracing
- Created test PDF document with sample content

## Project Architecture

### Core Components
1. **FastAPI Application** (`app/main.py`)
   - File upload endpoints for documents
   - RESTful API for document management
   - Async task queuing with Celery
   
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
   - Context retrieval from connected elements

5. **Post-Processor** (`app/services/post_processor.py`)
   - LLM-powered analysis of graph data
   - Semantic relationship inference
   - Structured JSON generation
   - Context retrieval for queries

6. **Infrastructure**
   - PostgreSQL: Document metadata and processing status
   - Qdrant: Vector embeddings (in-memory mode)
   - Redis: Caching and Celery broker (optional)
   - Celery: Async task processing

## API Endpoints

### Main Endpoints
- `POST /upload` - Upload document for processing
- `GET /documents` - List all documents with filtering
- `GET /documents/{id}` - Get document details with results
- `DELETE /documents/{id}` - Delete document and file
- `GET /health` - Health check endpoint
- `GET /` - API info

## Configuration

### Environment Variables
```env
DATABASE_URL - PostgreSQL connection (auto-configured)
OPENROUTER_API_KEY - Required for vision and LLM processing
LANGFUSE_PUBLIC_KEY - Optional for tracing
LANGFUSE_SECRET_KEY - Optional for tracing
REDIS_URL - Optional for caching
CELERY_BROKER_URL - Optional for async processing
```

### Models Used
- **Vision**: `qwen/qwen2.5-vl-72b-instruct` - Layout extraction
- **Processor**: `qwen/qwen-2.5-72b-instruct` - Context analysis

## Workflow
The FastAPI server runs on port 5000 and is configured to accept all hosts for the Replit iframe environment.

## Testing
A test PDF document is available at `uploads/test_document.pdf` containing:
- Multiple paragraphs
- Financial data tables
- Structured headings
- Business metrics

## User Preferences
None specified yet.

## Next Steps
1. Obtain OPENROUTER_API_KEY to enable vision extraction
2. Optional: Set up Langfuse for LLM monitoring
3. Optional: Configure Redis for caching
4. Optional: Start Celery worker for async processing
5. Test upload endpoint with test PDF

## Technical Notes

### Embeddings
- Uses deterministic bag-of-words embeddings via hashlib.md5
- Creates stable 768-dimensional vectors for similarity search
- Suitable for MVP; can be replaced with OpenAI/Cohere embeddings for production

### Qdrant Vector Database
- Currently configured for in-memory mode (:memory:)
- Embeddings are lost on restart (suitable for MVP/demo)
- To persist: Update QDRANT_HOST/PORT in .env to point to running Qdrant server
- Production deployment should use Qdrant Cloud or self-hosted instance

### Langfuse Tracing
- Optional integration (requires LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY)
- Traces document processing tasks when configured
- Gracefully degrades if keys not provided

### Graceful Degradation
- Redis unavailable → Caching disabled, system continues
- OPENROUTER_API_KEY missing → Task fails with clear error message
- Celery worker not running → Tasks still queued (start worker to process)
- Langfuse keys missing → No tracing, processing continues

### File Limitations
- Max file size: 50MB
- Supported formats: .pdf, .docx, .pptx, .xlsx only
- Legacy formats (.doc, .ppt, .xls) not supported
