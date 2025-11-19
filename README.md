# Document Processor API

A FastAPI-based document processing system with vision-based layout extraction, graph construction, and LLM-powered context retrieval.

## Features

- **Multi-Format Support**: PDF, DOC, PPT, XLSX document processing
- **Vision-Based Layout Extraction**: Uses Qwen2-VL-72B via OpenRouter for detecting paragraphs, tables, charts, and images
- **Graph Construction**: NetworkX-based document layout graphs with element relationships
- **Post-Processor LLM**: Context retrieval and structured JSON generation
- **PostgreSQL**: Metadata storage and document tracking
- **Qdrant**: Vector database for chunking and embedding storage
- **Redis**: Caching layer for improved performance
- **Celery**: Asynchronous task queue for document processing
- **Langfuse**: LLM observability and tracing
- **FastAPI**: High-performance REST API

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file with your API keys:

```env
OPENROUTER_API_KEY=your_openrouter_api_key
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
```

### 3. Start Redis (Optional for Caching & Celery)

```bash
redis-server
```

### 4. Start Celery Worker (Optional for Async Processing)

```bash
python celery_worker.py
```

### 5. Start API Server

```bash
python app/main.py
```

Or with uvicorn:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```

## API Endpoints

### Upload Document
```bash
POST /upload
Content-Type: multipart/form-data

curl -X POST "http://localhost:5000/upload" \
  -F "file=@test_document.pdf"
```

### List Documents
```bash
GET /documents?skip=0&limit=10&status=completed
```

### Get Document Details
```bash
GET /documents/{document_id}
```

### Delete Document
```bash
DELETE /documents/{document_id}
```

### Health Check
```bash
GET /health
```

## Architecture

### Processing Pipeline

1. **Document Upload** → FastAPI endpoint receives file
2. **File Validation** → Check file type and size
3. **Database Entry** → Create document record in PostgreSQL
4. **Async Task** → Queue processing with Celery
5. **Document Extraction** → Convert pages to images/text
6. **Vision Analysis** → Qwen2-VL-72B extracts layout elements
7. **Graph Construction** → NetworkX builds element relationships
8. **Post-Processing** → LLM generates structured JSON summary
9. **Storage** → Save results to PostgreSQL
10. **Caching** → Store in Redis for fast retrieval

### Technology Stack

- **FastAPI** - Web framework
- **SQLAlchemy** - ORM for PostgreSQL
- **Celery** - Distributed task queue
- **Redis** - Cache and message broker
- **Qdrant** - Vector database
- **NetworkX** - Graph processing
- **OpenRouter** - LLM API gateway
- **Langfuse** - LLM observability
- **PyMuPDF** - PDF processing
- **python-pptx** - PowerPoint processing
- **openpyxl** - Excel processing

## Models

### Vision Model
- **Qwen2.5-VL-72B-Instruct** - Layout detection, OCR, chart analysis
- Cost: $0.70 per 1M tokens (input/output)

### Processor Model
- **Qwen-2.5-72B-Instruct** - Context retrieval, JSON generation
- Cost: $0.35 per 1M tokens (input/output)

## Test Document

A test PDF is included in `uploads/test_document.pdf` with:
- Multiple paragraphs
- Tables with financial data
- Headings and structured content

## Development

### Database Migrations

The database tables are automatically created on startup. For custom migrations:

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Adding New Document Types

1. Add processor to `app/utils/document_processor.py`
2. Update task logic in `app/services/celery_app.py`
3. Add file extension to allowed types in `app/main.py`

## Monitoring

- **Langfuse Dashboard**: Track LLM calls, tokens, and costs
- **Logs**: Application logs for debugging
- **PostgreSQL**: Query document processing status

## License

MIT License
