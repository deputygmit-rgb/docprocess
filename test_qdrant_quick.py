"""Quick Qdrant diagnostic test."""

print("\n" + "=" * 80)
print("QDRANT QUICK DIAGNOSTIC")
print("=" * 80)

# Test 1: Import
print("\n[TEST 1] Import qdrant_client...")
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams
    print("  ✓ Import successful")
except ImportError as e:
    print(f"  ✗ Import failed: {e}")
    exit(1)

# Test 2: In-memory client
print("\n[TEST 2] Create in-memory client...")
try:
    client = QdrantClient(":memory:")
    print("  ✓ In-memory client created")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    exit(1)

# Test 3: Collection creation
print("\n[TEST 3] Create collection...")
try:
    client.create_collection(
        collection_name="test_collection",
        vectors_config=VectorParams(size=768, distance=Distance.COSINE)
    )
    print("  ✓ Collection created")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    exit(1)

# Test 4: Store vectors
print("\n[TEST 4] Store vectors...")
try:
    from qdrant_client.models import PointStruct
    
    points = [
        PointStruct(
            id=1,
            vector=[0.1] * 768,
            payload={"text": "sample 1"}
        ),
        PointStruct(
            id=2,
            vector=[0.2] * 768,
            payload={"text": "sample 2"}
        )
    ]
    
    client.upsert(
        collection_name="test_collection",
        points=points,
        wait=True
    )
    print("  ✓ Vectors stored")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    exit(1)

# Test 5: Search
print("\n[TEST 5] Search vectors...")
try:
    results = client.query_points(
        collection_name="test_collection",
        query=[0.15] * 768,
        limit=2
    )
    print(f"  ✓ Search returned {len(results.points)} results")
    for i, result in enumerate(results.points, 1):
        print(f"    [{i}] ID: {result.id}, Score: {result.score:.4f}")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    exit(1)

# Test 6: Delete
print("\n[TEST 6] Delete vectors...")
try:
    client.delete(
        collection_name="test_collection",
        points_selector=[1, 2]
    )
    
    results = client.query_points(
        collection_name="test_collection",
        query=[0.15] * 768,
        limit=2
    )
    
    if len(results.points) == 0:
        print("  ✓ Delete successful - no results found")
    else:
        print(f"  ✗ Delete failed - {len(results.points)} vectors still exist")
        exit(1)
except Exception as e:
    print(f"  ✗ Failed: {e}")
    exit(1)

print("\n" + "=" * 80)
print("✓ ALL QDRANT TESTS PASSED - WORKING CORRECTLY")
print("=" * 80)
print("\nQDRANT STATUS: ✓ OPERATIONAL (in-memory mode)")
print("  - Client: QdrantClient (in-memory)")
print("  - Collections: Supported")
print("  - Operations: Create, Store, Search, Delete - All working")
print("\n")
