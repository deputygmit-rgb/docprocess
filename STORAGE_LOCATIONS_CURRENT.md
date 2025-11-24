# Where Embeddings and Metadata Are Saved

## Quick Summary

### EMBEDDINGS
**Location:** Qdrant Vector Database (In-Memory)
- **Path:** RAM memory during application runtime
- **Format:** 768-dimensional vectors
- **Persistence:** ❌ Temporary (lost when app restarts)
- **Unique ID:** MD5 hash of (document_id + chunk_index)
- **Max per document:** 50 chunks
- **Distance Metric:** COSINE similarity
- **Code:** `app/services/qdrant_service.py`

### METADATA
**Location:** PostgreSQL Database (document_processor)
- **Path:** PostgreSQL database on localhost:5432
- **Persistence:** ✅ Permanent (survives restarts)
- **Format:** Structured + JSON fields
- **Code:** `app/models/document.py`

---

## Detailed Breakdown

### 1. EMBEDDINGS - WHERE THEY'RE STORED

**Location:** `Qdrant` (in-memory vector database)

**Code File:** `app/services/qdrant_service.py`

**Function:** `store_chunks(document_id, chunks, embeddings)`

**Flow:**
```
Document Upload
    ↓
Extract text chunks
    ↓
Generate 768-dim vectors via generate_simple_embedding()
    ↓
Store in Qdrant via store_chunks()
    ↓
Stored as PointStruct:
    {
        "id": MD5(document_id + chunk_index),
        "vector": [0.123, 0.456, ..., 0.789],  # 768 floats
        "payload": {
            "document_id": 1,
            "chunk_index": 0,
            "text": "extracted text",
            "element_id": "e1",
            "element_type": "paragraph",
            "page": 1
        }
    }
    ↓
Stored in Qdrant collection "documents"
```

**When Lost:** Application restart (in-memory mode)

**How to Make Permanent:** Switch to Qdrant server mode (requires separate Qdrant service running)

---

### 2. METADATA - WHERE IT'S STORED

**Location:** `PostgreSQL` database

**Database:** `document_processor`
**User:** `postgres`
**Password:** `1234`
**Host:** `localhost:5432`

**Code File:** `app/models/document.py`

**Table:** `documents`

**Columns:**
```sql
CREATE TABLE documents (
    id (Primary Key),
    filename (String),
    status (Enum: PENDING, PROCESSING, COMPLETED, FAILED),
    created_at (DateTime),
    processed_at (DateTime),
    error_message (Text),
    
    -- JSON Data Columns:
    layout_data (JSON) - Raw extracted layout information
    graph_data (JSON) - Graph structure with nodes/edges
    processed_json (JSON) - Processed output from processors
)
```

**Persistence:** ✅ Permanent (survives restarts)

**File Location:** PostgreSQL database directory

**How to Query:**
```powershell
psql -U postgres -d document_processor
\dt  # List tables
SELECT * FROM documents;  # View all documents
```

---

### 3. CACHE - TEMPORARY STORAGE

**Location:** Memory (optional Redis)

**TTL:** 2 hours

**What's Cached:**
```python
{
    "layout_data": {...},
    "graph_data": {...},
    "processed_json": {...}
}
```

**Code File:** `app/services/cache_service.py`

**When Cleared:** TTL expires (2 hours) or on restart

---

## Storage Comparison

| Data Type | Location | Persistence | Speed | Query |
|-----------|----------|-------------|-------|-------|
| **Embeddings** | Qdrant (RAM) | Temporary | ~2ms | search_similar() |
| **Metadata** | PostgreSQL | Permanent | ~5ms | SQL queries |
| **Cache** | Memory | 2-hour TTL | ~1ms | Key lookup |
| **Files** | ./uploads/ | Permanent | Disk I/O | File system |

---

## Code Reference

### Storing Embeddings
**File:** `app/services/celery_app.py` (lines 283-291)
```python
if chunks:
    embeddings = []
    for chunk in chunks[:50]:  # Max 50 chunks
        embedding = generate_simple_embedding(chunk['text'], dim=768)
        embeddings.append(embedding)
    
    qdrant_service = QdrantService()
    qdrant_service.store_chunks(document_id, chunks[:50], embeddings)
```

### Storing Metadata
**File:** `app/services/celery_app.py` (lines 306-315)
```python
doc.layout_data = layout_data  # JSON stored in PostgreSQL
doc.graph_data = graph_dict  # JSON stored in PostgreSQL
doc.processed_json = processed_result['processed_data']  # JSON stored
doc.status = ProcessingStatus.COMPLETED
doc.processed_at = datetime.utcnow()
db.commit()  # Save to PostgreSQL
```

### Searching Embeddings
**File:** `app/services/qdrant_service.py`
```python
def search_similar(self, query_embedding, document_id=None, limit=5):
    # Searches Qdrant for similar vectors
    # Returns top-5 matches with similarity scores
```

### Retrieving Metadata
**File:** `app/main.py` (API endpoints)
```python
@app.get("/documents/{document_id}")
def get_document(document_id: int):
    # Fetches from PostgreSQL documents table
```

---

## Accessing the Data

### View PostgreSQL Metadata
```powershell
# Connect to PostgreSQL
psql -U postgres -d document_processor

# View documents
SELECT id, filename, status, created_at FROM documents;

# View specific document
SELECT * FROM documents WHERE id = 1;

# Export to JSON
SELECT jsonb_pretty(layout_data) FROM documents WHERE id = 1;
```

### Search Embeddings (Programmatically)
```python
from app.services.qdrant_service import QdrantService

service = QdrantService()
results = service.search_similar(
    query_embedding=[0.1]*768,  # Your query vector
    document_id=1,
    limit=5
)
# Results: [{"id": ..., "score": ..., "payload": {...}}, ...]
```

---

## What Gets Backed Up

✅ **Backed Up (Persistent):**
- PostgreSQL database (documents.db or PostgreSQL server)
- Uploaded files (./uploads/)
- Application code

❌ **NOT Backed Up (Temporary):**
- Qdrant embeddings (in-memory, lost on restart)
- Cache entries (2-hour TTL)

---

## To Make Embeddings Persistent

Currently embeddings are in-memory (lost on restart). To make permanent:

1. **Stop the application**
2. **Run Qdrant server separately** (Docker or local)
3. **Update `app/services/qdrant_service.py`:**
   ```python
   # Change from:
   self.client = QdrantClient(":memory:")
   
   # To:
   self.client = QdrantClient(
       host="localhost",
       port=6333,
       api_key="your_api_key"
   )
   ```
4. **Set environment variables:**
   ```env
   QDRANT_HOST=localhost
   QDRANT_PORT=6333
   ```
5. **Restart application**

---

## Summary

| Question | Answer |
|----------|--------|
| Where are embeddings? | Qdrant (RAM) |
| Where is metadata? | PostgreSQL database |
| How long do embeddings last? | Until app restart |
| How long does metadata last? | Forever |
| Can I search embeddings? | Yes, via search_similar() |
| Can I backup embeddings? | Only with Qdrant server mode |
| Can I query metadata with SQL? | Yes, via psql |
| What's the database connection? | postgresql://postgres:1234@localhost:5432/document_processor |

---
