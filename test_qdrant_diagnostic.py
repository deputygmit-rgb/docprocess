"""Diagnostic script to test Qdrant connectivity and functionality."""

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.qdrant_service import QdrantService
from app.core.config import get_settings


def test_qdrant_connection():
    """Test if Qdrant service initializes and connects."""
    print("=" * 80)
    print("QDRANT DIAGNOSTIC TEST")
    print("=" * 80)
    
    settings = get_settings()
    
    print("\n[CONFIG]")
    print(f"  QDRANT_HOST: {settings.QDRANT_HOST}")
    print(f"  QDRANT_PORT: {settings.QDRANT_PORT}")
    print(f"  QDRANT_COLLECTION: {settings.QDRANT_COLLECTION}")
    print(f"  QDRANT_API_KEY: {'(set)' if settings.QDRANT_API_KEY else '(not set)'}")
    
    print("\n[INITIALIZATION]")
    try:
        qdrant_service = QdrantService()
        print("  ✓ QdrantService initialized successfully")
    except Exception as e:
        print(f"  ✗ Failed to initialize QdrantService: {e}")
        return False
    
    print("\n[COLLECTION CHECK]")
    try:
        collections = qdrant_service.client.get_collections()
        collection_names = [col.name for col in collections.collections]
        print(f"  ✓ Collections retrieved: {collection_names}")
        
        if settings.QDRANT_COLLECTION in collection_names:
            print(f"  ✓ Collection '{settings.QDRANT_COLLECTION}' exists")
        else:
            print(f"  ⚠ Collection '{settings.QDRANT_COLLECTION}' not found")
    except Exception as e:
        print(f"  ✗ Failed to get collections: {e}")
        return False
    
    print("\n[STORAGE TEST]")
    try:
        # Test storing chunks
        test_chunks = [
            {"text": "Sample chunk 1", "element_id": "elem_1", "element_type": "paragraph", "page": 1},
            {"text": "Sample chunk 2", "element_id": "elem_2", "element_type": "paragraph", "page": 1},
        ]
        
        # Create simple embeddings (768 dimensions)
        test_embeddings = [
            [0.1] * 768,  # Simple test embedding
            [0.2] * 768,  # Another test embedding
        ]
        
        qdrant_service.store_chunks(
            document_id=1,
            chunks=test_chunks,
            embeddings=test_embeddings
        )
        print("  ✓ Chunks stored successfully")
    except Exception as e:
        print(f"  ✗ Failed to store chunks: {e}")
        return False
    
    print("\n[SEARCH TEST]")
    try:
        # Test searching
        test_query = [0.15] * 768
        results = qdrant_service.search_similar(test_query, document_id=1, limit=2)
        
        if results:
            print(f"  ✓ Search returned {len(results)} results")
            for i, result in enumerate(results, 1):
                print(f"    Result {i}:")
                print(f"      ID: {result['id']}")
                print(f"      Score: {result['score']:.4f}")
                print(f"      Text: {result['payload'].get('text', '')[:50]}...")
        else:
            print("  ⚠ Search returned no results")
    except Exception as e:
        print(f"  ✗ Search failed: {e}")
        return False
    
    print("\n[DELETION TEST]")
    try:
        qdrant_service.delete_document_chunks(document_id=1)
        print("  ✓ Document chunks deleted successfully")
        
        # Verify deletion
        results = qdrant_service.search_similar([0.15] * 768, document_id=1, limit=2)
        if len(results) == 0:
            print("  ✓ Deletion verified - no chunks found")
        else:
            print(f"  ⚠ Deletion incomplete - {len(results)} chunks still found")
    except Exception as e:
        print(f"  ✗ Deletion failed: {e}")
        return False
    
    print("\n" + "=" * 80)
    print("✓ ALL QDRANT TESTS PASSED")
    print("=" * 80)
    return True


if __name__ == "__main__":
    try:
        success = test_qdrant_connection()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
