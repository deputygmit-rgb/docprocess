# Storage Architecture Diagram

## High-Level Storage Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                         DOCUMENT UPLOAD                            │
└────────────────────────────────────────────┬───────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────┐
│                      EXTRACTION & PROCESSING                       │
│  • PDF/Image/DOCX/PPTX/XLSX extraction                           │
│  • Vision API layout detection                                    │
│  • Graph construction                                             │
│  • Embedding generation                                           │
└────────────────────────────────────────────┬───────────────────────┘
                                            │
                    ┌───────────────────────┼───────────────────────┐
                    ▼                       ▼                       ▼
        ┌─────────────────────┐  ┌──────────────────┐  ┌──────────────────┐
        │  PostgreSQL DB      │  │ Qdrant Vector DB │  │  Cache Layer     │
        │ (localhost:5432)    │  │  (in-memory)     │  │  (Redis/Memory)  │
        ├─────────────────────┤  ├──────────────────┤  ├──────────────────┤
        │ ✅ Permanent        │  │ ⚠️ Temporary*    │  │ ⏱️ 2-hour TTL   │
        │ ✅ Full metadata    │  │ ✅ Searchable    │  │ ✅ Fast lookup   │
        │ ✅ Always available │  │ ✅ High perf     │  │ ⚠️ Optional      │
        └─────────────────────┘  └──────────────────┘  └──────────────────┘
            │       │ │ │             │  │ │             │
            │       │ │ │             │  │ │             │
        ┌───┴──┬────┴─┼─┴─────┐     │  │ │             │
        ▼      ▼      ▼       ▼     │  ▼ ▼             ▼
    Document layout_data  graph_data processed_json  Embeddings  Chunks  Document
    metadata JSON        JSON       JSON            (768-dim)   Metadata Cache
    (indexed)            (full)     (processed)
```

## Detailed Data Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│ 1. FILE UPLOAD                                                       │
│    File: document.pdf (10 MB)                                       │
│    → Saved to: ./uploads/[timestamp]_document.pdf                   │
│    │ → DB Entry: PostgreSQL documents table (PENDING status)          │
└──────────────┬───────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│ 2. DOCUMENT EXTRACTION (celery_app.py)                              │
│    Extracts text, tables, images from file                          │
│    ↓                                                                 │
│    ├─ PDF → Pages → Images → Vision API                           │
│    ├─ DOCX → Paragraphs + Tables                                   │
│    ├─ PPTX → Slides                                                │
│    ├─ XLSX → Sheet data                                            │
│    └─ Images → Direct to Vision API                                │
└──────────────┬───────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│ 3. LAYOUT EXTRACTION (vision_service.py)                            │
│    Output: layout_data JSON                                         │
│    {                                                                │
│      "page_number": 1,                                             │
│      "elements": [                                                 │
│        {"id": "e1", "type": "paragraph", "text": "...", "bbox": ...}
│      ],                                                            │
│      "chart_details": [...]                                       │
│    }                                                               │
│    ↓                                                               │
│    ✅ Stored in: doc.layout_data (PostgreSQL JSON field)          │
└──────────────┬───────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│ 4. GRAPH CONSTRUCTION (graph_service.py)                            │
│    Builds network graph from layout elements                        │
│    Output: graph_data JSON                                         │
│    {                                                               │
│      "nodes": [                                                    │
│        {                                                           │
│          "id": "n1",                                              │
│          "type": "paragraph",                                     │
│          "text": "extracted text",                                │
│          "embeddings": {                                          │
│            "content_embedding": true,  ← Generated here           │
│            "context_embedding": true   ← Generated here           │
│          }                                                         │
│        }                                                           │
│      ],                                                            │
│      "edges": [...]                                               │
│    }                                                               │
│    ↓                                                               │
│    ✅ Stored in: doc.graph_data (PostgreSQL JSON field)           │
└──────────────┬───────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│ 5. EMBEDDING GENERATION (celery_app.py)                             │
│    For each node in graph with text:                               │
│    1. Extract chunks (text, element_id, element_type, page)      │
│    2. Generate 768-dim embeddings using generate_simple_embedding │
│    3. Store up to 50 chunks                                       │
│                                                                   │
│    Embedding = [0.123, 0.456, ..., 0.789] (768 values)          │
│    ↓                                                              │
│    ✅ Stored in: Qdrant (vector database)                        │
└──────────────┬───────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│ 6. CHUNK STORAGE IN QDRANT (qdrant_service.py)                      │
│    For each chunk:                                                  │
│    {                                                               │
│      "point_id": MD5(doc_id + chunk_idx),                         │
│      "vector": [0.123, 0.456, ..., 0.789],  ← 768-dim embedding  │
│      "payload": {                            ← Metadata           │
│        "document_id": 1,                                          │
│        "chunk_index": 0,                                          │
│        "text": "chunk content",                                   │
│        "element_id": "e1",                                        │
│        "element_type": "paragraph",                               │
│        "page": 1                                                  │
│      }                                                            │
│    }                                                              │
│    ↓                                                              │
│    ✅ Stored in: Qdrant collection "documents" (in-memory)       │
└──────────────┬───────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│ 7. POST-PROCESSING (post_processor.py)                              │
│    Formats graph data into user-friendly JSON                       │
│    Output: processed_json JSON                                      │
│    {                                                                │
│      "elements": [...],   ← Formatted elements                     │
│      "statistics": {...}  ← Element counts by type                │
│    }                                                                │
│    ↓                                                                │
│    ✅ Stored in: doc.processed_json (PostgreSQL JSON field)       │
└──────────────┬───────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│ 8. CACHE POPULATION (cache_service.py)                              │
│    Stores document data for fast retrieval                          │
│    Key: "document:1"                                               │
│    Value: {layout_data, graph_data, processed_json}                │
│    TTL: 7200 seconds (2 hours)                                     │
│    ↓                                                                │
│    ✅ Stored in: Redis/Memory cache                                │
└──────────────┬───────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│ 9. DATABASE UPDATE                                                   │
│    Update document record with all metadata                         │
│    ↓                                                                │
│    doc.layout_data = layout_data JSON                              │
│    doc.graph_data = graph_data JSON                                │
│    doc.processed_json = processed_json JSON                        │
│    doc.status = "COMPLETED"                                        │
│    doc.processed_at = datetime.now()                               │
│    ↓                                                                │
│    ✅ Stored in: PostgreSQL documents table                        │
└──────────────┬───────────────────────────────────────────────────────┘
```

## Storage Layer Diagram

```
REQUEST TO GET DOCUMENT DATA
           │
           ▼
    ┌─────────────────────┐
    │ Cache Layer?        │ ──── Miss ───┐
    │ (2-hr TTL)          │              │
    └─────────────────────┘              │
           │ Hit                      │
           ▼                          ▼
      RETURN        ┌─────────────────────────┐
     (fast!)        │ PostgreSQL Database     │
                    │ localhost:5432          │
                    └────────┬────────────────┘
                             │
                             ▼
                    ┌─────────────────────────┐
                    │ Return Document Record  │
                    │ + All JSON fields:      │
                    │ - layout_data           │
                    │ - graph_data            │
                    │ - processed_json        │
                    └────────┬────────────────┘
                             │
                             ▼
                    ┌─────────────────────────┐
                    │ Cache for 2 hours       │
                    │ (future requests)       │
                    └────────┬────────────────┘
                             │
                             ▼
                        RETURN TO CLIENT


REQUEST TO SEARCH EMBEDDINGS
           │
           ▼
    ┌─────────────────────────┐
    │ Embedding Search Query  │
    │ [0.123, 0.456, ...]    │ 768-dim vector
    └────────┬────────────────┘
             │
             ▼
    ┌─────────────────────────┐
    │ Qdrant Vector Search    │
    │ - COSINE distance       │
    │ - Filter by doc_id      │
    │ - Limit 5 results       │
    └────────┬────────────────┘
             │
             ▼
    ┌─────────────────────────┐
    │ Return Top-5 Results:   │
    │ [{                      │
    │   "id": 12345,          │
    │   "score": 0.95,        │ ← Similarity (0-1)
    │   "payload": {          │
    │     "text": "...",      │
    │     "doc_id": 1         │
    │   }                     │
    │ }, ...]                 │
    └────────┬────────────────┘
             │
             ▼
        RETURN TO CLIENT
```

## Storage Size Estimates

```
Typical Document (10 pages):
├─ Raw file: 10 MB
├─ Extracted text: ~50 KB
├─ Layout data JSON: ~100 KB
├─ Graph data JSON: ~150 KB
├─ Processed JSON: ~100 KB
├─ PostgreSQL record: ~450 KB total
├─ Embeddings (50 chunks × 768-dim): ~3 MB in Qdrant
└─ Cache entry: ~350 KB (2-hour TTL)

Total memory per document:
├─ Database: ~450 KB (permanent, PostgreSQL)
├─ Qdrant: ~3 MB (temporary, restart loses)
└─ Cache: ~350 KB (expires 2hr)

For 100 documents:
├─ PostgreSQL: ~45 MB database
├─ Qdrant: ~300 MB RAM (in-memory)
└─ Cache: ~35 MB (varies with TTL)
```

## Data Access Patterns

```
Pattern 1: Get Full Document Info
    ↓
    Request to DB
    ↓
    Return: {file_info, layout_data, graph_data, processed_json}
    ↓
    Fast (cached) or medium (DB query)

Pattern 2: Search by Content
    ↓
    Embed query text → 768-dim vector
    ↓
    Search in Qdrant
    ↓
    Return: Top-5 chunks with scores
    ↓
    Very fast (~2ms)

Pattern 3: Browse Document
    ↓
    Request from cache/DB
    ↓
    Return: processed_json (user-friendly)
    ↓
    Fast if cached, medium if not

Pattern 4: Delete Document
    ↓
    Delete from DB
    ↓
    Delete from Qdrant
    ↓
    Invalidate cache
    ↓
    Complete
```

---

**Note:** * Qdrant is in-memory mode currently. To make embeddings persistent, 
switch to server mode (see QDRANT_IMPLEMENTATION_SUMMARY.md).
