"""Utilities to convert between the existing JSON graph format and
an in-memory NetworkX graph.
"""
from typing import Dict, Any
import networkx as nx
from .schema import EdgeType, EDGE_TIMESTAMP, EDGE_CONFIDENCE, EDGE_MESSAGE

NODE_KEYS = {"id", "label", "type", "properties"}


def dict_to_nx(graph_dict: Dict[str, Any]) -> nx.DiGraph:
    """Convert JSON (as produced by enhanced_document_processor) to NetworkX."""
    G = nx.DiGraph()
    for node in graph_dict.get("nodes", []):
        attrs = {k: v for k, v in node.items() if k not in NODE_KEYS}
        attrs.update(node.get("properties", {}))
        G.add_node(node["id"], label=node.get("label"), type=node.get("type"), **attrs)

    for edge in graph_dict.get("edges", []):
        G.add_edge(edge["source"], edge["target"], **{k: v for k, v in edge.items() if k not in {"source", "target"}})
    return G


def nx_to_dict(G: nx.DiGraph) -> Dict[str, Any]:
    nodes = []
    for nid, data in G.nodes(data=True):
        props = {k: v for k, v in data.items() if k not in {"label", "type"}}
        nodes.append({"id": nid, "label": data.get("label", nid), "type": data.get("type", "unknown"), "properties": props})

    edges = []
    for u, v, data in G.edges(data=True):
        edge_entry = {"source": u, "target": v}
        edge_entry.update(data)
        edges.append(edge_entry)

    return {"nodes": nodes, "edges": edges}


# ---------------------------------------------------------------------------
# Helper utilities for lineage handling
# ---------------------------------------------------------------------------

def add_lineage_edge(G: nx.DiGraph, src: str, dst: str, edge_type: EdgeType, timestamp: str, **meta) -> None:
    """Add a schema-compliant lineage edge to *G*.

    Parameters
    ----------
    src, dst : str
        Node IDs.
    edge_type : EdgeType
        One of DERIVES_FROM / IMPLEMENTS / INFLUENCED / SUPERSEDES.
    timestamp : str
        ISO-8601 timestamp string.
    **meta : any
        Additional edge attributes (e.g. confidence, message).
    """
    attr = {EDGE_TIMESTAMP: timestamp, **meta}
    G.add_edge(src, dst, type=edge_type.value if isinstance(edge_type, EdgeType) else str(edge_type), **attr)


def get_lineage(G: nx.DiGraph, node_id: str, direction: str = "backward"):
    """Return a list of (neighbor_id, edge_data) along lineage relations.

    direction = "backward"  → predecessors (ancestors)
    direction = "forward"   → successors (descendants)
    """
    neighbors = G.pred[node_id].items() if direction == "backward" else G.succ[node_id].items()
    lineage_types = {t.value for t in (EdgeType.DERIVES_FROM, EdgeType.IMPLEMENTS, EdgeType.INFLUENCED, EdgeType.SUPERSEDES)}
    return [(n, d) for n, d in neighbors if d.get("type") in lineage_types]
