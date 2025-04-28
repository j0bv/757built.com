"""Spatial helper for adding nearest-neighbour edges to the graph.

Usage::

    from graph_db.geospatial import add_nearest_edges
    add_nearest_edges(G, k=3, max_km=15)
"""
from __future__ import annotations

import math
from typing import List, Tuple, Callable

import networkx as nx
from sklearn.neighbors import BallTree  # type: ignore

from .schema import EdgeType, EDGE_DISTANCE

EARTH_R = 6371.0088  # km – mean Earth radius (WGS-84)


def _to_rad(latlon: Tuple[float, float]) -> Tuple[float, float]:
    """Convert (lat, lon) degrees to radians."""
    lat, lon = latlon
    return math.radians(lat), math.radians(lon)


def add_nearest_edges(
    G: nx.DiGraph,
    *,
    node_filter: Callable[[str, dict], bool] | None = None,
    k: int = 3,
    max_km: float = 15.0,
) -> None:
    """Add 'nearby' edges between spatially close nodes.

    Parameters
    ----------
    G : nx.DiGraph
        The target graph (modified in place).
    node_filter : callable, optional
        Function (node_id, attrs) -> bool selecting nodes to include.
        Defaults to nodes having a 'coordinates' attribute.
    k : int
        Number of nearest neighbours to connect (default 3).
    max_km : float
        Maximum great-circle distance in kilometres for an edge.
    """
    if node_filter is None:
        node_filter = lambda n, d: "coordinates" in d  # noqa: E731

    # Collect candidate nodes
    nodes: List[str] = [n for n, d in G.nodes(data=True) if node_filter(n, d)]
    if len(nodes) < 2:
        return  # nothing to connect

    # Build BallTree in radians
    coords_rad = [_to_rad(G.nodes[n]["coordinates"]) for n in nodes]
    tree = BallTree(coords_rad, metric="haversine")

    # Query k+1 because first neighbour is the node itself (distance=0)
    dists, idxs = tree.query(coords_rad, k=min(k + 1, len(nodes)))

    for i, src in enumerate(nodes):
        for dist, j in zip(dists[i][1:], idxs[i][1:]):
            km = dist * EARTH_R
            if km <= max_km:
                dst = nodes[j]
                # Avoid duplicating reverse edge
                if G.has_edge(src, dst) or G.has_edge(dst, src):
                    continue
                G.add_edge(
                    src,
                    dst,
                    type=EdgeType.NEARBY.value,
                    **{EDGE_DISTANCE: round(km, 2)},
                )
