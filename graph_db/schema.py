"""Centralised schema constants and helpers for the 757Built knowledge graph.

This module defines
• NodeType – allowed node categories
• EdgeType – allowed edge relations
plus helper attribute keys shared across the codebase.
"""
from enum import Enum


class NodeType(str, Enum):
    RESEARCH_PAPER = "research_paper"
    PATENT = "patent"
    PROJECT = "project"
    BUILDING = "building"
    DATASET = "dataset"
    PERSON = "person"
    FUNDING = "funding"
    DOCUMENT = "document"
    LOCALITY = "locality"
    REGION = "region"


class EdgeType(str, Enum):
    # lineage / derivation
    DERIVES_FROM = "derives_from"   # A derives_from B   (paper → patent)
    IMPLEMENTS = "implements"       # A implements B     (project → patent)
    INFLUENCED = "influenced"       # A influenced B     (paper → project)
    SUPERSEDES = "supersedes"       # versioning         (v2 supersedes v1)

    # misc relations (examples)
    AUTHORED_BY = "authored_by"
    FUNDED_BY = "funded_by"
    
    # spatial relations
    LOCATED_IN = "located_in"       # document/project → locality
    SERVES_REGION = "serves_region" # project → region


# Common attribute keys for edges
EDGE_TIMESTAMP = "timestamp"   # ISO-8601 string
EDGE_CONFIDENCE = "confidence" # float 0-1
EDGE_MESSAGE = "message"       # free-text description
EDGE_SUBTYPE = "subtype"       # further classification of edge
EDGE_DISTANCE = "distance_km"  # numeric distance for 'nearby' edges


__all__ = [
    "NodeType",
    "EdgeType",
    "EDGE_TIMESTAMP",
    "EDGE_CONFIDENCE",
    "EDGE_MESSAGE",
    "EDGE_SUBTYPE",
    "EDGE_DISTANCE",
]
