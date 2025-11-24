# Embeddings & Metadata Storage - Documentation Index

## 📖 Quick Navigation

### I need to understand:
- **Where embeddings are saved** → Read `EMBEDDINGS_AND_METADATA_STORAGE_MAP.md` (Section 1)
- **Where metadata is saved** → Read `EMBEDDINGS_AND_METADATA_STORAGE_MAP.md` (Section 2)
- **How data flows** → Read `STORAGE_ARCHITECTURE_DIAGRAM.md`
- **Complete technical details** → Read `COMPLETE_STORAGE_ANALYSIS.md`
- **Visual diagrams** → Read `STORAGE_ARCHITECTURE_DIAGRAM.md`

---

## 🎯 Quick Facts

### Embeddings
```
WHERE:     Qdrant Vector Database
FORMAT:    768-dimensional float vectors
METRIC:    COSINE similarity (0-1)
LIMIT:     50 chunks per document
PERMANENT: ❌ No (in-memory, restart loses data)
SPEED:     ~2ms per search
INDEXED:   Yes (by document_id via filter)
```

### Metadata
```
WHERE:     SQLite Database (documents.db)
FORMAT:    JSON fields in documents table
PERMANENT: ✅ Yes (survives restart)
FIELDS:    layout_data, graph_data, processed_json
QUERYABLE: Yes (by document_id)
INDEXED:   ❌ No (full table scan)
SPEED:     ~5-10ms per query
```

### Cache
```
WHERE:     Redis or In-memory
TTL:       2 hours (7200 seconds)
SPEED:     ~1ms (hit), ~10ms (miss + DB fetch)
KEY:       document:{document_id}
PERMANENT: ❌ No (expires after 2 hours)
```

---

## 📋 Documentation Files

### Main Documents

1. **EMBEDDINGS_AND_METADATA_STORAGE_MAP.md** (14 KB)
   - Complete mapping of all storage locations
   - Detailed breakdown by data type
   - Processing pipeline flow
   - Data retrieval paths
   - Configuration details
   - **Best for:** Understanding the complete architecture

2. **STORAGE_ARCHITECTURE_DIAGRAM.md** (8 KB)
   - Visual diagrams of data flow
   - High-level architecture
   - Detailed processing flow
   - Storage layer access patterns
   - Size estimates
   - **Best for:** Visual learners

3. **COMPLETE_STORAGE_ANALYSIS.md** (10 KB)
   - Executive summary
   - Quick answers
   - Complete breakdown with examples
   - Configuration instructions
   - Making embeddings persistent
   - **Best for:** Quick reference

---

## 🔍 Finding Information

### By Storage Type

**Where are embeddings saved?**
→ Qdrant Vector Database
→ See: EMBEDDINGS_AND_METADATA_STORAGE_MAP.md, Section 1

**Where is metadata saved?**
→ SQLite Database
→ See: EMBEDDINGS_AND_METADATA_STORAGE_MAP.md, Section 2

**Where is cache?**
→ Redis/Memory
→ See: EMBEDDINGS_AND_METADATA_STORAGE_MAP.md, Section 3

### By Processing Stage

**1. Document Upload** → STORAGE_ARCHITECTURE_DIAGRAM.md, "1. FILE UPLOAD"
**2. Extraction** → STORAGE_ARCHITECTURE_DIAGRAM.md, "2. DOCUMENT EXTRACTION"
**3. Layout Detection** → STORAGE_ARCHITECTURE_DIAGRAM.md, "3. LAYOUT EXTRACTION"
**4. Graph Building** → STORAGE_ARCHITECTURE_DIAGRAM.md, "4. GRAPH CONSTRUCTION"
**5. Embedding Generation** → STORAGE_ARCHITECTURE_DIAGRAM.md, "5. EMBEDDING GENERATION"
**6. Chunk Storage** → STORAGE_ARCHITECTURE_DIAGRAM.md, "6. CHUNK STORAGE IN QDRANT"
**7. Post-Processing** → STORAGE_ARCHITECTURE_DIAGRAM.md, "7. POST-PROCESSING"
**8. Caching** → STORAGE_ARCHITECTURE_DIAGRAM.md, "8. CACHE POPULATION"
**9. Database Update** → STORAGE_ARCHITECTURE_DIAGRAM.md, "9. DATABASE UPDATE"

### By Use Case

**I want to query embeddings** 
→ See: COMPLETE_STORAGE_ANALYSIS.md, "DATA RETRIEVAL" section

**I want to retrieve document metadata**
→ See: EMBEDDINGS_AND_METADATA_STORAGE_MAP.md, "Get Document with All Metadata"

**I want to make embeddings persistent**
→ See: COMPLETE_STORAGE_ANALYSIS.md, "MAKING EMBEDDINGS PERSISTENT"

**I need configuration details**
→ See: COMPLETE_STORAGE_ANALYSIS.md, "CONFIGURATION" section

---

## 📊 Quick Reference Tables

### Storage Locations

| Data | Location | Format | Size | Permanent |
|------|----------|--------|------|-----------|
| Embeddings | Qdrant | 768-dim vectors | ~3 KB/chunk | ❌ |
| Chunk metadata | Qdrant payload | JSON | ~500 B | ❌ |
| Document info | SQLite | JSON | ~450 KB | ✅ |
| layout_data | SQLite JSON | JSON | 10-100 KB | ✅ |
| graph_data | SQLite JSON | JSON | 20-200 KB | ✅ |
| processed_json | SQLite JSON | JSON | 15-150 KB | ✅ |
| Cache | Redis/Mem | JSON | 20-200 KB | ❌ (2hr) |

### Performance

| Operation | Time | Location |
|-----------|------|----------|
| Search embedding | ~2ms | Qdrant |
| Fetch document | ~5ms | SQLite |
| Cache hit | ~1ms | Redis/Memory |
| Cache miss | ~10ms | DB fetch |
| Store 50 embeddings | ~50ms | Qdrant |
| Generate embeddings | ~100ms | CPU |

### Limits

| Limit | Value | Note |
|-------|-------|------|
| Chunks per document | 50 max | Configurable |
| Embedding dimensions | 768 fixed | Not configurable |
| Cache TTL | 2 hours | Configurable |
| Database file | Unlimited | Until disk full |
| Qdrant memory | RAM limited | ~5 GB typical |

---

## 🔧 Configuration Files

**Qdrant:**
- Location: `app/services/qdrant_service.py`
- File: `app/core/config.py`
- Current: In-memory mode
- Changeable: Yes (see "Making Embeddings Persistent")

**Database:**
- Location: `app/models/document.py`
- File: `app/core/config.py`
- Default: `sqlite:///./documents.db`

**Cache:**
- Location: `app/services/cache_service.py`
- File: `app/core/config.py`
- Default: In-memory with Redis fallback

---

## 🚀 Getting Started

### 1. Understand the Architecture
   - Read: STORAGE_ARCHITECTURE_DIAGRAM.md
   - Time: ~5 minutes

### 2. Learn the Details
   - Read: EMBEDDINGS_AND_METADATA_STORAGE_MAP.md
   - Time: ~10 minutes

### 3. Reference When Needed
   - Use: COMPLETE_STORAGE_ANALYSIS.md
   - Time: As needed

### 4. Implement (if needed)
   - To make embeddings persistent:
     - See: COMPLETE_STORAGE_ANALYSIS.md, "MAKING EMBEDDINGS PERSISTENT"
     - Time: ~30 minutes setup

---

## 💡 Key Takeaways

1. **Embeddings stored in Qdrant** (fast, temporary)
2. **Metadata stored in SQLite** (permanent, all documents)
3. **Cache layer for performance** (2-hour TTL)
4. **Three separate storage systems** working together
5. **50 chunks max** per document stored as embeddings
6. **768-dimensional vectors** using COSINE distance
7. **No embedding persistence** in current in-memory mode
8. **Complete metadata persistence** in SQLite

---

## 📞 Troubleshooting

**Q: Where are my embeddings saved?**
A: Qdrant vector database (in-memory). They're lost on restart.
   To persist: See "MAKING EMBEDDINGS PERSISTENT"

**Q: Can I search embeddings?**
A: Yes, via `qdrant.search_similar(query_vec, doc_id, limit=5)`
   Returns top-5 chunks with similarity scores.

**Q: Will my data survive a restart?**
A: SQLite metadata: YES. Qdrant embeddings: NO (unless switched to server mode).

**Q: How fast is it?**
A: Embedding search: ~2ms. Document fetch: ~5ms. Cache hit: ~1ms.

**Q: Can I change the vector dimension?**
A: No, it's hardcoded to 768. Would need code changes.

**Q: How many documents can I store?**
A: SQLite: Millions. Qdrant: RAM-limited (~5 GB typical).

---

## 📚 All Document Maps

```
EMBEDDINGS_AND_METADATA_STORAGE_MAP.md
├─ Section 1: Embeddings Storage (Qdrant)
├─ Section 2: Metadata Storage (SQLite)
├─ Section 3: Cache Storage (Redis)
├─ Processing Pipeline Flow
├─ Data Retrieval Paths
├─ Storage Summary by Type
├─ Key Points
├─ Configuration
├─ Querying Data
└─ Performance & Retention

STORAGE_ARCHITECTURE_DIAGRAM.md
├─ High-Level Architecture
├─ Detailed Data Flow
├─ Storage Layer Access Patterns
├─ Storage Size Estimates
└─ Data Access Patterns

COMPLETE_STORAGE_ANALYSIS.md
├─ Quick Answer
├─ Complete Storage Breakdown
├─ Metadata Details
├─ Processing Pipeline
├─ Data Retrieval
├─ Summary Table
├─ Key Insights
├─ Making Embeddings Persistent
└─ API Endpoints
```

---

## 🎓 Learning Path

### Beginner
1. Read: Quick Facts (this page)
2. Read: STORAGE_ARCHITECTURE_DIAGRAM.md (visual overview)
3. You now understand the basic architecture

### Intermediate
1. Read: EMBEDDINGS_AND_METADATA_STORAGE_MAP.md
2. Understand: Where each piece of data is stored
3. Reference: API endpoints and query methods

### Advanced
1. Read: COMPLETE_STORAGE_ANALYSIS.md
2. Understand: Detailed configurations
3. Implement: Custom changes if needed

---

## 📝 Last Updated

- **Date:** November 24, 2025
- **Status:** Complete mapping
- **All locations:** Documented
- **Verified:** All components tested

---

## 🔗 Related Documentation

- **Qdrant Status:** See `QDRANT_CHECK_FINAL_REPORT.md`
- **Chart Extraction:** See `MULTI_CHART_FIX_SUMMARY.md`
- **API Endpoints:** See `app/main.py`
- **Database Model:** See `app/models/document.py`

---

**This is your one-stop reference for understanding where embeddings and metadata are stored!**

Choose your starting document based on your needs above. 👆
