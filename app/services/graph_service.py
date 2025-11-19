import networkx as nx
from typing import List, Dict, Any
import json
import hashlib
import numpy as np
from app.utils.document_processor import clean_element_text


def generate_simple_embedding(text: str, dim: int = 768) -> list:
    """Generate deterministic embedding from text"""
    if not text:
        return [0.0] * dim
    
    words = text.lower().split()
    embedding = np.zeros(dim)
    
    for word in words[:100]:
        word_hash = int(hashlib.md5(word.encode()).hexdigest(), 16)
        idx = word_hash % dim
        embedding[idx] += 1.0
    
    norm = np.linalg.norm(embedding)
    if norm > 0:
        embedding = embedding / norm
    
    return embedding.tolist()


class GraphService:
    def __init__(self):
        self.graph = None
    
    def build_document_graph(self, layout_data: List[Dict[str, Any]], document_id: int = None) -> nx.DiGraph:
        G = nx.DiGraph()
        
        for page_data in layout_data:
            page_num = page_data.get("page_number", 1)
            layout = page_data.get("layout", {})
            
            elements = layout.get("elements", [])
            relationships = layout.get("relationships", [])
            
            for element in elements:
                element_id = f"p{page_num}_{element.get('id', 'unknown')}"
                raw_text = element.get("text", "")
                
                # Clean the text
                text = clean_element_text(raw_text) if raw_text else ""
                element_type = element.get("type", "")
                
                # Generate embeddings only if text exists
                content_embedding_created = False
                context_embedding_created = False
                combined_embedding_created = False
                
                combined_embedding = None
                
                if text:
                    try:
                        content_embedding = generate_simple_embedding(text)
                        content_embedding_created = True
                    except Exception as e:
                        print(f"Content embedding generation failed for element {element_id}: {e}")
                        content_embedding_created = False
                
                if element_type:
                    try:
                        context_embedding = generate_simple_embedding(element_type)
                        context_embedding_created = True
                    except Exception as e:
                        print(f"Context embedding generation failed for element {element_id}: {e}")
                        context_embedding_created = False
                
                # Combined embedding only if both exist
                if content_embedding_created and context_embedding_created:
                    try:
                        combined_embedding = [
                            (c + ctx) / 2.0 for c, ctx in zip(content_embedding, context_embedding)
                        ]
                        
                        # Normalize combined embedding
                        norm = np.linalg.norm(combined_embedding)
                        if norm > 0:
                            combined_embedding = [x / norm for x in combined_embedding]
                        
                        combined_embedding_created = True
                    except Exception as e:
                        print(f"Combined embedding generation failed for element {element_id}: {e}")
                        combined_embedding_created = False
                
                node_data = {
                    "document_id": document_id,
                    "element_id": element_id,
                    "page": page_num,
                    "page_number": page_num,
                    "type": element_type,
                    "text": text,
                    "bbox": element.get("bbox", []),
                    "confidence": element.get("confidence", 0.0),
                    "extraction_confidence": element.get("confidence", 0.0),
                    "content_embedding": content_embedding_created,
                    "context_embedding": context_embedding_created,
                    "combined_embedding": combined_embedding_created
                }
                
                G.add_node(element_id, **node_data)
            
            for rel in relationships:
                from_id = f"p{page_num}_{rel.get('from', '')}"
                to_id = f"p{page_num}_{rel.get('to', '')}"
                rel_type = rel.get("type", "related")
                
                if G.has_node(from_id) and G.has_node(to_id):
                    G.add_edge(from_id, to_id, relationship=rel_type)
            
            for i in range(len(elements) - 1):
                elem1_id = f"p{page_num}_{elements[i].get('id', 'unknown')}"
                elem2_id = f"p{page_num}_{elements[i+1].get('id', 'unknown')}"
                
                if G.has_node(elem1_id) and G.has_node(elem2_id):
                    if not G.has_edge(elem1_id, elem2_id):
                        G.add_edge(elem1_id, elem2_id, relationship="follows")
        
        self.graph = G
        return G
    
    def graph_to_dict(self, graph: nx.DiGraph = None) -> Dict[str, Any]:
        if graph is None:
            graph = self.graph
        
        if graph is None:
            return {}
        
        nodes = []
        for node_id, data in graph.nodes(data=True):
            # Get relationships (predecessors and successors)
            predecessors = list(graph.predecessors(node_id))
            successors = list(graph.successors(node_id))
            
            # Get edge relationships with types
            relationships = []
            for pred in predecessors:
                edge_data = graph.get_edge_data(pred, node_id)
                relationships.append({
                    "from": pred,
                    "to": node_id,
                    "type": edge_data.get("relationship", "related") if edge_data else "related"
                })
            for succ in successors:
                edge_data = graph.get_edge_data(node_id, succ)
                relationships.append({
                    "from": node_id,
                    "to": succ,
                    "type": edge_data.get("relationship", "related") if edge_data else "related"
                })
            
            # Create page summary
            page_num = data.get("page_number", data.get("page", 1))
            page_summary = f"Page {page_num}: {data.get('type', 'unknown')} element"
            
            nodes.append({
                "id": node_id,
                **data,
                "relationships": relationships,
                "parent_element": predecessors[0] if predecessors else None,
                "child_elements": successors,
                "page_summary": page_summary
            })
        
        edges = []
        for source, target, data in graph.edges(data=True):
            edges.append({
                "source": source,
                "target": target,
                **data
            })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "node_count": graph.number_of_nodes(),
            "edge_count": graph.number_of_edges()
        }
    
    def get_connected_elements(self, element_id: str, depth: int = 1) -> List[str]:
        if self.graph is None:
            return []
        
        if not self.graph.has_node(element_id):
            return []
        
        connected = set()
        current_level = {element_id}
        
        for _ in range(depth):
            next_level = set()
            for node in current_level:
                successors = set(self.graph.successors(node))
                predecessors = set(self.graph.predecessors(node))
                next_level.update(successors)
                next_level.update(predecessors)
            
            connected.update(next_level)
            current_level = next_level
        
        return list(connected)
    
    def get_element_context(self, element_id: str, depth: int = 1) -> Dict[str, Any]:
        if self.graph is None or not self.graph.has_node(element_id):
            return {}
        
        element_data = self.graph.nodes[element_id]
        connected_ids = self.get_connected_elements(element_id, depth)
        
        context_elements = []
        for conn_id in connected_ids:
            if self.graph.has_node(conn_id):
                context_elements.append({
                    "id": conn_id,
                    **self.graph.nodes[conn_id]
                })
        
        return {
            "element": {
                "id": element_id,
                **element_data
            },
            "context": context_elements
        }
