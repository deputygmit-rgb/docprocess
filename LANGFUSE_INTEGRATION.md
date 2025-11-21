# Langfuse Integration Guide

## Overview

Langfuse v2 tracing has been fully integrated into the document processor. The system now automatically creates detailed traces for each document processing task, including:

- **Document Processing Trace**: Main trace capturing the entire document lifecycle
- **Extraction Events**: Tracks when documents are extracted by file type
- **Graph Building Events**: Logs when the knowledge graph is constructed
- **Processing Events**: Records JSON generation and element processing metrics
- **Completion/Error Events**: Final status with outputs or error details
- **API Key Validation Events**: Tracks when API keys are missing

## Configuration

### Environment Variables

Add these to your `.env` file (already configured):

```
LANGFUSE_PUBLIC_KEY=pk-lf-1b11da6a-37ec-4b59-8650-55a8a0cd92ea
LANGFUSE_SECRET_KEY=sk-lf-1ad1386e-00d5-4242-81f0-d9d797cfc930
LANGFUSE_HOST=https://cloud.langfuse.com
```

**To get your own Langfuse credentials:**
1. Visit https://cloud.langfuse.com
2. Sign up for a free account
3. Create a new project
4. Copy your public key (starts with `pk-lf-`)
5. Copy your secret key (starts with `sk-lf-`)
6. Add them to your `.env` file
7. Restart the application

### Disabling Langfuse

To disable Langfuse tracing, simply leave the credentials empty in `.env`:

```
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
```

The system gracefully degrades and continues to work without tracing.

## How It Works

### Document Processing Flow with Tracing

1. **Trace Initialization** (`_process_document_impl`)
   - Creates main trace with document metadata
   - Includes: document_id, file_name, file_type, file_path
   - Status: PROCESSING

2. **Extraction Phase** (`document_extraction` span)
   - Extracts content based on file type (PDF, PPTX, XLSX, DOCX)
   - Events logged for each phase

3. **Graph Building** (`graph_built` event)
   - Records number of nodes and edges created
   - Logs relationship graph structure

4. **Processing & Generation** (`processing_complete` event)
   - Tracks JSON generation time
   - Records number of elements processed

5. **Completion** (trace end)
   - Final trace output with status: "completed"
   - Includes element count and timing metrics
   - `langfuse_client.flush()` ensures data is sent immediately

6. **Error Handling**
   - Exceptions are caught and logged as trace output
   - Trace ends with status: "failed" and error message
   - Database transaction rolled back properly

## Viewing Traces

1. Log in to https://cloud.langfuse.com
2. Select your project
3. Go to "Traces" section
4. You'll see traces named "process_document" with nested events and spans
5. Click on any trace to see:
   - Input data (document metadata)
   - All events and spans
   - Output data (status, elements_extracted)
   - Generation time and timestamps
   - Any errors that occurred

## API Usage in Code

### Creating a Trace

```python
trace = langfuse_client.trace(
    name="process_document",
    input={...},
    metadata={...}
)
```

### Adding Events

```python
trace.event(
    name="graph_built",
    input={"nodes": 42, "edges": 53}
)
```

### Creating Spans (for nested operations)

```python
span = trace.span(
    name="document_extraction",
    input={"file_type": ".pdf"}
)
# ... do work ...
span.end(output={...})
```

### Ending the Trace

```python
trace.end(output={"status": "completed", ...})
```

### Flushing Data

```python
langfuse_client.flush()  # Send all traces immediately
```

## Integration Points

### In `celery_app.py`

1. **Initialization** (lines 17-36)
   - Langfuse client instantiated with credentials
   - LANGFUSE_ENABLED flag set based on credentials presence

2. **Trace Creation** (lines 93-108)
   - Langfuse trace created at start of `_process_document_impl`
   - Document metadata captured

3. **API Key Validation** (lines 115-124)
   - Event logged if OPENROUTER_API_KEY missing
   - Graceful exit with trace logging

4. **Extraction Tracking** (lines 130-137)
   - Extraction span created for file type processing

5. **Graph Building** (lines 251-259)
   - Event logs graph statistics

6. **Processing Completion** (lines 261-270)
   - Final processing metrics captured

7. **Success & Failure** (lines 295-320)
   - Traces properly ended with final output
   - Error traces include exception details
   - Flush ensures immediate transmission

## Performance Considerations

- Langfuse tracing is **non-blocking** - doesn't slow down document processing
- All Langfuse operations are wrapped in try-except blocks
- Missing/invalid credentials silently disable tracing (graceful degradation)
- Traces are flushed immediately after completion for real-time dashboard updates

## Troubleshooting

### "Langfuse trace initialization warning"

**Cause**: Invalid credentials or network issue
**Solution**: 
- Verify LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY in `.env`
- Check internet connection
- Restart application

### Traces not appearing in dashboard

**Possible causes**:
1. Langfuse credentials not set
2. Network connectivity issue
3. Langfuse project not selected correctly
4. Check application logs for warnings

**Solutions**:
- Verify credentials: `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` are non-empty
- Check .env file is properly loaded
- Restart application after credential changes
- Check application console for error messages

### "Langfuse event warning" or "Langfuse trace warning"

**Solution**: These are non-blocking warnings. Check:
- Application logs for details
- Langfuse dashboard for partially sent traces
- Network connectivity

## Example Dashboard View

When you process a document with Langfuse enabled, you'll see in the dashboard:

```
Trace: process_document
├── Input: {document_id: 1, file_name: "report.pdf", ...}
├── Events:
│   ├── extraction phase completed
│   ├── graph_built: nodes=42, edges=53
│   └── processing_complete: generation_time_seconds=2.34, elements_processed=42
└── Output: {status: "completed", elements_extracted: 42, document_id: 1}
```

## Next Steps

1. **Ensure credentials are in `.env`** (already done)
2. **Restart the application** to load Langfuse configuration
3. **Upload a test document** via the API
4. **Check Langfuse dashboard** at https://cloud.langfuse.com to see traces appear
5. **Iterate**: Use trace data to optimize processing

---

**Version**: Langfuse v2 integration
**Status**: Production Ready ✅
**Last Updated**: November 2025
