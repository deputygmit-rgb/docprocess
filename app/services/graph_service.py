import networkx as nx
from typing import List, Dict, Any
import json


class GraphService:
    def __init__(self):
        self.graph = None
    
    def build_document_graph(self, layout_data: List[Dict[str, Any]]) -> nx.DiGraph:
        G = nx.DiGraph()
        
        for page_data in layout_data:
            page_num = page_data.get("page_number", 1)
            layout = page_data.get("layout", {})
            
            elements = layout.get("elements", [])
            relationships = layout.get("relationships", [])
            
            for element in elements:
                element_id = f"p{page_num}_{element.get('id', 'unknown')}"
                
                G.add_node(
                    element_id,
                    page=page_num,
                    type=element.get("type", "unknown"),
                    text=element.get("text", ""),
                    bbox=element.get("bbox", []),
                    confidence=element.get("confidence", 0.0)
                )
            
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
            nodes.append({
                "id": node_id,
                **data
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
