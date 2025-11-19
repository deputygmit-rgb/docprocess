from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from app.core.config import get_settings
from typing import List, Dict, Any
import hashlib

settings = get_settings()


class QdrantService:
    def __init__(self):
        self.client = QdrantClient(":memory:")
        self.collection_name = settings.QDRANT_COLLECTION
        self._init_collection()
    
    def _init_collection(self):
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=768, distance=Distance.COSINE)
                )
        except Exception as e:
            print(f"Qdrant collection init warning: {e}")
    
    def store_chunks(self, document_id: int, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks must match number of embeddings")
        
        points = []
        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            point_id = int(hashlib.md5(f"{document_id}_{idx}".encode()).hexdigest()[:8], 16)
            
            points.append(
                PointStruct(
                    id=point_id,
                    vector=embedding,
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
    
    def search_similar(self, query_embedding: List[float], document_id: int = None, limit: int = 5):
        query_filter = None
        
        if document_id:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id)
                    )
                ]
            )
        
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            query_filter=query_filter,
            limit=limit
        )
        
        return [
            {
                "id": result.id,
                "score": result.score,
                "payload": result.payload
            }
            for result in results
        ]
    
    def delete_document_chunks(self, document_id: int):
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id)
                    )
                ]
            )
        )
