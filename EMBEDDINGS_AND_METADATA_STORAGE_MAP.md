# Embeddings and Metadata Storage Map

## Quick Summary

```
EMBEDDINGS:
  ├─ Stored in: Qdrant (in-memory vector database)
  ├─ Format: 768-dimensional vectors (Lists of floats)
  ├─ Key: MD5(document_id + chunk_index)
  └─ Payload: {document_id, chunk_index, text, element_id, element_type, page}

METADATA:
  ├─ Document metadata: SQLite database (documents.db)
  ├─ Chunk metadata: Qdrant payload (inline with vectors)
  ├─ Layout data: SQLite JSON field (documents.layout_data)
  ├─ Graph data: SQLite JSON field (documents.graph_data)
  ├─ Processed JSON: SQLite JSON field (documents.processed_json)
  └─ Cache: Redis/Memory cache (7200s TTL)
```

---

## Detailed Storage Breakdown

### 1. EMBEDDINGS STORAGE

#### Where: Qdrant Vector Database
**Location in Code:** `app/services/qdrant_service.py`

**Storage Process:**
```python
# In celery_app.py (line 283-291)
chunks = []
for node in graph_dict.get('nodes', []):
    if node.get('text'):
        chunks.append({
            "text": node.get('text', ''),
            "element_id": node.get('id', ''),
            "element_type": node.get('type', ''),
            "page": node.get('page', 1)
        })

if chunks:
    embeddings = []
    for chunk in chunks[:50]:
        embedding = generate_simple_embedding(chunk['text'], dim=768)
        embeddings.append(embedding)
    
    qdrant_service = QdrantService()
    qdrant_service.store_chunks(document_id, chunks[:50], embeddings)
```

**Embedding Generation:**
- Function: `generate_simple_embedding()` (lines 52-68 in celery_app.py)
- Dimension: 768
- Algorithm: Deterministic bag-of-words hashing
- Input: Text from extracted document elements
- Output: Normalized vector [0.0 - 1.0]

**Vector Storage:**
```python
# In qdrant_service.py - store_chunks() method
for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
    point_id = int(hashlib.md5(f"{document_id}_{idx}".encode()).hexdigest()[:8], 16)
    
    points.append(
        PointStruct(
            id=point_id,
            vector=embedding,  # 768-dim vector stored here
            payload={
                "document_id": document_id,
                "chunk_index": idx,
                "text": chunk.get("text", ""),
                "element_id": chunk.get("element_id", ""),
                "element_type": chunk.get("element_type", ""),
                "page": chunk.get("page", 1)
            }
        )
    )

self.client.upsert(
    collection_name=self.collection_name,
    points=points,
    wait=True
)
```

**Qdrant Configuration:**
- Collection Name: "documents"
- Vector Size: 768 dimensions
- Distance Metric: COSINE similarity
- Storage Mode: In-memory (`:memory:`)
- Collection Auto-created: Yes (on first use)

**Limits:**
- Max chunks stored: 50 per document (line 291 in celery_app.py)
- Vector ID: MD5 hash (unique per document + chunk index)
- Retention: Until application restart (in-memory mode)

---

### 2. METADATA STORAGE - DATABASE

#### Where: SQLite Database (`documents.db`)

**Location in Code:** `app/models/document.py`

**Document Table Structure:**
```sql
CREATE TABLE documents (
    id INTEGER PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    file_size INTEGER NOT NULL,
    status ENUM (pending|processing|completed|failed),
    
    -- Metadata JSON fields:
    layout_data JSON,           -- Raw layout extraction
    graph_data JSON,            -- Network graph structure
    processed_json JSON,        -- Post-processed elements
    
    error_message TEXT,
    created_at DATETIME,
    updated_at DATETIME,
    processed_at DATETIME
);
```

**Stored Metadata Details:**

#### a) layout_data (JSON)
**What it contains:**
```json
{
  "page_number": 1,
  "layout": {
    "elements": [
      {
        "id": "element_0",
        "type": "paragraph|table|chart|image",
        "text": "element content",
        "bbox": [x1, y1, x2, y2],
        "confidence": 0.95,
        "is_chart": false,
        "table_data": "if table",
        "chart_details": "if chart"
      }
    ],
    "relationships": [
      {"from": "e1", "to": "e2", "type": "describes"}
    ],
    "chart_count": 0
  },
  "chart_details": []
}
```

**Source:** Vision API extraction (VisionService.extract_layout)
**Stored in:** `doc.layout_data` (line 305)

#### b) graph_data (JSON)
**What it contains:**
```json
{
  "nodes": [
    {
      "id": "node_0",
      "type": "element_type",
      "text": "node content",
      "page": 1,
      "bbox": [x1, y1, x2, y2],
      "metadata": {...},
      "embeddings": {
        "content_embedding": true,
        "context_embedding": true,
        "combined_embedding": true
      },
      "chart_details": {...}
    }
  ],
  "edges": [
    {"from": "n1", "to": "n2", "type": "describes"}
  ],
  "node_count": 42,
  "edge_count": 38
}
```

**Source:** GraphService.build_document_graph()
**Structure:** NetworkX graph converted to dict
**Stored in:** `doc.graph_data` (line 306)

#### c) processed_json (JSON)
**What it contains:**
```json
{
  "elements": [
    {
      "id": "processed_0",
      "type": "paragraph",
      "content": "extracted text",
      "metadata": {
        "page": 1,
        "bbox": [x1, y1, x2, y2],
        "confidence": 0.95
      },
      "relationships": [...]
    }
  ],
  "statistics": {
    "total_elements": 42,
    "by_type": {"paragraph": 20, "table": 5, "chart": 2}
  },
  "generation_time_seconds": 1.23,
  "generated_at": "2025-11-24T10:30:00Z"
}
```

**Source:** PostProcessorService.process_graph_data()
**Stored in:** `doc.processed_json` (line 307)

**Document Status Fields:**
- status: One of {PENDING, PROCESSING, COMPLETED, FAILED}
- created_at: When document uploaded
- processed_at: When processing completed
- error_message: If processing failed

**Storage Location:**
```
File: documents.db (SQLite)
Path: Same directory as application
Size: Grows with number of documents
```

---

### 3. CACHE STORAGE

#### Where: Redis/Memory Cache
**Location in Code:** `app/services/cache_service.py`

**Cache Entry:**
```python
# In celery_app.py (line 309-314)
cache_service.set(
    f"document:{document_id}",
    {
        "layout_data": layout_data,
        "graph_data": graph_dict,
        "processed_json": processed_result['processed_data']
    },
    ttl=7200  # 2 hours
)
```

**Key Format:** `document:{document_id}`
**Value:** Dict with layout_data, graph_data, processed_json
**TTL:** 7200 seconds (2 hours)
**Storage:** Redis (if configured) or in-memory cache
**Purpose:** Fast retrieval of frequently accessed documents

---

## Processing Pipeline Flow

```
File Upload
    ↓
Document created in DB (status: PENDING)
    ↓
Celery task triggered
    ↓
File extracted based on type (.pdf, .docx, .pptx, .xlsx, .jpg, etc.)
    ↓
Vision API extracts layout (VisionService)
    → Stores in: layout_data
    ↓
Graph built from layout (GraphService)
    → Generates embeddings for each node
    → Stores in: graph_data
    ↓
Embeddings generated (generate_simple_embedding)
    ↓
Chunks created from graph nodes
    ↓
Embeddings stored in Qdrant (QdrantService.store_chunks)
    → Stores in: Qdrant vector DB
    ↓
Post-processing (PostProcessorService)
    → Stores in: processed_json
    ↓
Database updated
    → layout_data (JSON)
    → graph_data (JSON)
    → processed_json (JSON)
    → status: COMPLETED
    ↓
Cache populated (CacheService)
    → 2-hour TTL
    ↓
Processing complete
```

---

## Data Retrieval Paths

### Get Document with All Metadata
```python
# app/main.py - GET /documents/{document_id}
doc = db.query(Document).filter(Document.id == document_id).first()

# Returns all fields including:
# - layout_data (JSON)
# - graph_data (JSON)
# - processed_json (JSON)
# - All other metadata
```

### Get Embeddings
```python
# app/services/qdrant_service.py - search_similar
results = client.query_points(
    collection_name="documents",
    query=query_embedding,
    query_filter=Filter(document_id=doc_id),
    limit=5
)

# Returns:
# [{id, score, payload}, ...]
# payload contains: text, element_id, element_type, page, document_id
```

### Get from Cache
```python
# app/services/cache_service.py
cached_data = self.cache_client.get(f"document:{document_id}")

# Returns: {layout_data, graph_data, processed_json}
# Or None if expired/not cached
```

---

## Storage Summary by Type

| Data Type | Storage Location | Format | Size | Permanent | Indexed |
|-----------|-----------------|--------|------|-----------|---------|
| **Embeddings** | Qdrant (in-memory) | 768-dim float vectors | ~3KB per chunk | ❌ (restart loses) | ✅ COSINE |
| **Chunk metadata** | Qdrant payload | JSON object | ~500B per chunk | ❌ (with vectors) | ✅ (doc_id filter) |
| **Document metadata** | SQLite JSON | JSON object | 10-500KB | ✅ Permanent | ⚠️ (no index) |
| **Layout data** | SQLite JSON | JSON object | 10-100KB | ✅ Permanent | ❌ |
| **Graph data** | SQLite JSON | JSON object | 20-200KB | ✅ Permanent | ❌ |
| **Processed JSON** | SQLite JSON | JSON object | 15-150KB | ✅ Permanent | ❌ |
| **Raw file** | File system | Binary | Original size | ✅ Permanent | ❌ |
| **Cache** | Redis/Memory | JSON object | 20-200KB | ❌ (2hr TTL) | ✅ (key lookup) |

---

## Key Points About Storage

### Embeddings (Qdrant)
✅ **Fast** - COSINE distance search in ~2ms
✅ **Searchable** - Vector similarity queries
❌ **Temporary** - Lost on application restart (in-memory mode)
❌ **Scalable** - Limited to RAM size (typically < 5GB)

### Metadata (SQLite)
✅ **Permanent** - Survives application restarts
✅ **Full data** - Complete extraction results stored
✅ **Queryable** - Can retrieve by document ID
❌ **Not searchable** - JSON fields not indexed
⚠️ **Large files** - Can be hundreds of KB per document

### Cache (Redis/Memory)
✅ **Fast** - In-memory or Redis cache
✅ **2-hour TTL** - Balances freshness and performance
❌ **Temporary** - Expires after 2 hours
⚠️ **Optional** - Falls back to database if not available

---

## Configuration for Storage

### Qdrant Configuration (`app/core/config.py`)
```python
QDRANT_HOST: str = "localhost"
QDRANT_PORT: int = 6333
QDRANT_API_KEY: str = ""
QDRANT_COLLECTION: str = "documents"
# Currently using: QdrantClient(":memory:")
```

### Database Configuration
```python
DATABASE_URL: str = "sqlite:///./documents.db"
# Can be switched to PostgreSQL: "postgresql://..."
```

### Cache Configuration
```python
REDIS_URL: str = "redis://localhost:6379/0"
CELERY_BROKER_URL: str = "memory://"
CELERY_RESULT_BACKEND: str = "cache+memory://"
```

---

## Querying Stored Data

### By Document ID
```python
# Get all metadata for a document
db.query(Document).filter(Document.id == 1).first()
# Returns: Complete document with all JSON fields

# Get embeddings for a document
qdrant.search_similar(query_vec, document_id=1, limit=5)
# Returns: Top 5 similar chunks with scores
```

### By Type
```python
# Get all completed documents
db.query(Document).filter(Document.status == ProcessingStatus.COMPLETED).all()

# Get failed documents
db.query(Document).filter(Document.status == ProcessingStatus.FAILED).all()
```

### By Content
```python
# Find similar chunks via embedding search
results = qdrant.search_similar(query_embedding=[...])
# Returns: List of chunks with similarity scores
```

---

## Performance Characteristics

| Operation | Time | Location |
|-----------|------|----------|
| Store 50 embeddings | ~50ms | Qdrant |
| Search embedding | ~2ms | Qdrant |
| Fetch document metadata | ~5ms | SQLite |
| Cache hit | ~1ms | Redis/Memory |
| Cache miss + DB fetch | ~10ms | Database |
| Generate embeddings | ~100ms | CPU (50 chunks) |

---

## Retention Policy

| Data | Duration | Retention |
|------|----------|-----------|
| Embeddings | Until restart | Qdrant in-memory |
| Database metadata | Forever | SQLite persistent |
| Cache | 2 hours | TTL expiry |
| Raw files | Until deleted | File system |

---

## Backup & Persistence

### What Gets Backed Up (Persistent)
✅ SQLite database (documents.db)
✅ Raw uploaded files (./uploads/)
✅ Application code

### What's Lost on Restart (In-Memory)
❌ Qdrant embeddings (if using in-memory mode)
❌ Cache entries (Redis/Memory)

### To Make Embeddings Persistent
Would need to:
1. Run Qdrant as separate server
2. Update `QdrantClient(":memory:")` to use server connection
3. Regular Qdrant snapshots/backups

---

## Summary Table

```
┌─────────────────────────────────────────────────────────┐
│ STORAGE LOCATION MAP                                    │
├──────────────────┬──────────────────┬──────────────────┤
│ Data Type        │ Storage          │ Persistence      │
├──────────────────┼──────────────────┼──────────────────┤
│ Embeddings       │ Qdrant           │ Temporary*       │
│ Chunk Metadata   │ Qdrant Payload   │ Temporary*       │
│ Document Info    │ SQLite           │ Permanent        │
│ Layout Data      │ SQLite JSON      │ Permanent        │
│ Graph Data       │ SQLite JSON      │ Permanent        │
│ Processed JSON   │ SQLite JSON      │ Permanent        │
│ Raw Files        │ Filesystem       │ Permanent        │
│ Cache            │ Redis/Memory     │ 2-hour TTL       │
└──────────────────┴──────────────────┴──────────────────┘
* Temporary in current setup (in-memory). Can be made permanent
  by switching Qdrant to server mode.
```

---

**Generated:** November 24, 2025
**Current Mode:** In-memory (Qdrant), SQLite (Metadata)
**All embeddings:** max 50 per document, 768 dimensions each
