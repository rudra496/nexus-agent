import json
import networkx as nx
from typing import Dict, Any, List
import os

class GraphMemory:
    """
    A lightweight GraphRAG implementation for local, persistent memory.
    """
    def __init__(self, storage_path: str = ".nexus/memory.json"):
        self.storage_path = storage_path
        self.graph = nx.DiGraph()
        self._load()

    def _load(self):
        """Loads the graph from local storage if it exists."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                    self.graph = nx.node_link_graph(data)
            except Exception:
                self.graph = nx.DiGraph()

    def _save(self):
        """Saves the current graph to local storage."""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        data = nx.node_link_data(self.graph)
        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2)

    def add_node(self, node_id: str, attributes: Dict[str, Any]):
        """Adds a concept/node to the graph."""
        self.graph.add_node(node_id, **attributes)
        self._save()

    def add_edge(self, source: str, target: str, relationship: str):
        """Adds a relationship between two nodes."""
        self.graph.add_edge(source, target, relation=relationship)
        self._save()

    def retrieve_context(self, query: str) -> str:
        """
        Naive retrieval: Searches graph nodes for keyword matches.
        In a full implementation, this would use vector embeddings.
        """
        keywords = query.lower().split()
        relevant_nodes = []
        for node, data in self.graph.nodes(data=True):
            if any(k in node.lower() or k in str(data).lower() for k in keywords):
                relevant_nodes.append(f"{node}: {data}")
        
        if not relevant_nodes:
            return "No prior context found in local memory."
        return "Relevant context:\n" + "\n".join(relevant_nodes)

    def get_stats(self) -> Dict[str, int]:
        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges()
        }
