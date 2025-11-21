from celery import Celery
from app.core.config import get_settings
from app.core.database import get_db_context
from app.models.document import ProcessingStatus
from app.utils.document_processor import DocumentProcessor
from app.services.vision_service import VisionService
from app.services.graph_service import GraphService
from app.services.post_processor import PostProcessorService
from app.services.cache_service import CacheService
from app.services.qdrant_service import QdrantService
from datetime import datetime
import os
import hashlib
import time

settings = get_settings()

try:
    if settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY:
        try:
            from langfuse import Langfuse
            langfuse_client = Langfuse(
                public_key=settings.LANGFUSE_PUBLIC_KEY,
                secret_key=settings.LANGFUSE_SECRET_KEY,
                host=settings.LANGFUSE_HOST
            )
            LANGFUSE_ENABLED = True
        except ImportError:
            print("Langfuse decorators not available, tracing disabled")
            langfuse_client = None
            LANGFUSE_ENABLED = False
    else:
        LANGFUSE_ENABLED = False
except Exception as e:
    print(f"Langfuse initialization warning: {e}")
    LANGFUSE_ENABLED = False

celery_app = Celery(
    "document_processor",
    broker=settings.CELERY_BROKER_URL if "redis" in settings.CELERY_BROKER_URL else "memory://",
    backend=settings.CELERY_RESULT_BACKEND if "redis" in settings.CELERY_RESULT_BACKEND else "cache+memory://"
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_always_eager=True,
    task_eager_propagates=True,
)


def generate_simple_embedding(text: str, dim: int = 768) -> list:
    import numpy as np
    import hashlib
    
    words = text.lower().split()
    if not words:
        return [0.0] * dim
    
    embedding = np.zeros(dim)
    for word in words[:100]:
        word_hash = int(hashlib.md5(word.encode()).hexdigest(), 16)
        idx = word_hash % dim
        embedding[idx] += 1.0
    
    norm = np.linalg.norm(embedding)
    if norm > 0:
        embedding = embedding / norm
    
    return embedding.tolist()


def _process_document_impl(document_id: int):
    langfuse_trace = None
    
    with get_db_context() as db:
        from app.models.document import Document
        
        doc = db.query(Document).filter(Document.id == document_id).first()
        
        if not doc:
            return {"error": "Document not found"}
        
        doc.status = ProcessingStatus.PROCESSING
        db.commit()
        
        if LANGFUSE_ENABLED:
            try:
                # Initialize Langfuse trace for this document processing
                langfuse_trace = langfuse_client.trace(
                    name="process_document",
                    input={
                        "document_id": document_id,
                        "file_name": doc.file_name,
                        "file_type": doc.file_type,
                        "file_path": doc.file_path
                    },
                    metadata={
                        "document_id": str(document_id),
                        "file_type": doc.file_type
                    }
                )
            except Exception as e:
                print(f"Langfuse trace initialization warning: {e}")
                langfuse_trace = None
        
        try:
            if not settings.OPENROUTER_API_KEY:
                doc.status = ProcessingStatus.FAILED
                doc.error_message = "OPENROUTER_API_KEY not configured. Vision processing requires API key."
                db.commit()
                if langfuse_trace:
                    try:
                        langfuse_trace.event(name="api_key_missing", input={"error": "OPENROUTER_API_KEY not set"})
                    except Exception as e:
                        print(f"Langfuse event warning: {e}")
                return {
                    "document_id": document_id,
                    "status": "failed",
                    "error": "API key required"
                }
            
            file_ext = doc.file_type.lower()
            processor = DocumentProcessor()
            vision_service = VisionService()
            graph_service = GraphService()
            post_processor = PostProcessorService()
            cache_service = CacheService()
            
            layout_data = []
            
            # Track extraction phase
            if langfuse_trace:
                try:
                    extraction_span = langfuse_trace.span(
                        name="document_extraction",
                        input={"file_type": file_ext}
                    )
                except Exception as e:
                    print(f"Langfuse span warning: {e}")
                    extraction_span = None
            else:
                extraction_span = None
            
            if file_ext == '.pdf':
                pages = processor.pdf_extract_pages(doc.file_path)
                
                for page in pages[:5]:
                    img_base64 = processor.image_to_base64(page['image'])
                    
                    layout_result = vision_service.extract_layout(
                        img_base64,
                        page['page_number']
                    )
                    layout_data.append(layout_result)
            
            elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                # Handle image files directly
                img_base64 = processor.image_to_base64_from_file(doc.file_path)
                
                layout_result = vision_service.extract_layout(
                    img_base64,
                    page_number=1
                )
                layout_data.append(layout_result)
            
            elif file_ext in ['.pptx', '.ppt', '.odp']:
                slides = processor.ppt_to_images(doc.file_path)
                layout_data = [{
                    "page_number": slide['slide_number'],
                    "layout": {
                        "elements": [{
                            "id": f"text_{slide['slide_number']}",
                            "type": "paragraph",
                            "text": slide['text'],
                            "bbox": [0, 0, 100, 100]
                        }],
                        "relationships": []
                    }
                } for slide in slides[:5]]
            
            elif file_ext in ['.xlsx', '.xls', '.ods']:
                sheets = processor.xlsx_extract_data(doc.file_path)
                layout_data = []
                for idx, sheet in enumerate(sheets):
                    # Normalize Excel sheet data to column structure
                    from app.utils.document_processor import normalize_table
                    normalized = normalize_table(str(sheet['data']))
                    
                    layout_data.append({
                        "page_number": idx + 1,
                        "layout": {
                            "elements": [{
                                "id": f"table_{idx}",
                                "type": "table",
                                "text": f"Table: {sheet['sheet_name']}",
                                "bbox": [0, 0, 100, 100],
                                "table_data": normalized
                            }],
                            "relationships": []
                        }
                    })
            
            elif file_ext in ['.docx', '.doc', '.odt']:
                docx_data = processor.docx_extract_text(doc.file_path)
                from app.utils.document_processor import normalize_table
                
                elements = [
                    {
                        "id": f"para_{idx}",
                        "type": "paragraph",
                        "text": para,
                        "bbox": [0, idx * 20, 100, (idx + 1) * 20]
                    }
                    for idx, para in enumerate(docx_data['paragraphs'][:20])
                ]
                
                # Add normalized tables
                for t_idx, table in enumerate(docx_data.get('tables', [])[:5]):
                    normalized = normalize_table('\n'.join(str(row) for row in table))
                    elements.append({
                        "id": f"table_{t_idx}",
                        "type": "table",
                        "text": f"Table {t_idx + 1}",
                        "bbox": [0, 0, 100, 100],
                        "table_data": normalized
                    })
                
                layout_data = [{
                    "page_number": 1,
                    "layout": {
                        "elements": elements,
                        "relationships": []
                    }
                }]
            
            graph = graph_service.build_document_graph(layout_data, document_id=document_id)
            graph_dict = graph_service.graph_to_dict(graph)
            
            if langfuse_trace:
                try:
                    langfuse_trace.event(
                        name="graph_built",
                        input={
                            "nodes": graph_dict.get('node_count', 0),
                            "edges": graph_dict.get('edge_count', 0)
                        }
                    )
                except Exception as e:
                    print(f"Langfuse graph event warning: {e}")
            
            # Time the JSON generation
            json_start_time = time.time()
            processed_result = post_processor.process_graph_data(graph_dict)
            json_generation_time = time.time() - json_start_time
            
            # Add timing information to processed result
            if isinstance(processed_result.get('processed_data'), dict):
                processed_result['processed_data']['generation_time_seconds'] = round(json_generation_time, 2)
                processed_result['processed_data']['generated_at'] = datetime.utcnow().isoformat()
            
            if langfuse_trace:
                try:
                    langfuse_trace.event(
                        name="processing_complete",
                        input={
                            "generation_time_seconds": round(json_generation_time, 2),
                            "elements_processed": len(processed_result.get('processed_data', {}).get('elements', []))
                        }
                    )
                except Exception as e:
                    print(f"Langfuse processing event warning: {e}")
            
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
                try:
                    embeddings = []
                    for chunk in chunks[:50]:
                        embedding = generate_simple_embedding(chunk['text'], dim=768)
                        embeddings.append(embedding)
                    
                    qdrant_service = QdrantService()
                    qdrant_service.store_chunks(document_id, chunks[:50], embeddings)
                except Exception as e:
                    print(f"Qdrant storage warning: {e}")
            
            doc.layout_data = layout_data
            doc.graph_data = graph_dict
            doc.processed_json = processed_result['processed_data']
            doc.status = ProcessingStatus.COMPLETED
            doc.processed_at = datetime.utcnow()
            doc.error_message = None
            
            cache_service.set(f"document:{document_id}", {
                "layout_data": layout_data,
                "graph_data": graph_dict,
                "processed_json": processed_result['processed_data']
            }, ttl=7200)
            
            db.commit()
            
            if langfuse_trace:
                try:
                    langfuse_trace.end(
                        output={
                            "status": "completed",
                            "elements_extracted": graph_dict.get('node_count', 0),
                            "document_id": document_id
                        }
                    )
                    langfuse_client.flush()
                except Exception as e:
                    print(f"Langfuse trace end warning: {e}")
            
            return {
                "document_id": document_id,
                "status": "completed",
                "elements_extracted": graph_dict['node_count']
            }
            
        except Exception as e:
            if langfuse_trace:
                try:
                    langfuse_trace.end(
                        output={
                            "status": "failed",
                            "error": str(e),
                            "document_id": document_id
                        }
                    )
                    langfuse_client.flush()
                except Exception as trace_e:
                    print(f"Langfuse trace error logging warning: {trace_e}")
            
            doc.status = ProcessingStatus.FAILED
            doc.error_message = str(e)
            db.commit()
            
            return {
                "document_id": document_id,
                "status": "failed",
                "error": str(e)
            }


if LANGFUSE_ENABLED:
    try:
        process_document_task = celery_app.task(name="process_document")(_process_document_impl)
    except Exception as e:
        print(f"Langfuse task decoration failed: {e}")
        process_document_task = celery_app.task(name="process_document")(_process_document_impl)
else:
    process_document_task = celery_app.task(name="process_document")(_process_document_impl)
