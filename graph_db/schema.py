"""Centralised schema constants and helpers for the 757Built knowledge graph.

This module defines
• NodeType – allowed node categories
• EdgeType – allowed edge relations
plus helper attribute keys shared across the codebase.
"""
from enum import Enum

# Current schema version - increment on breaking changes
SCHEMA_VERSION = 3

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

    # collaboration / bibliometrics / business relations
    WORKED_WITH = "worked_with"       # A worked_with B (collaborative relation)
    CITED_BY = "cited_by"             # A cited_by B (bibliographic citation)
    CONTRACTED_BY = "contracted_by"   # A contracted_by B (service or subcontract)
    MERGED_WITH = "merged_with"       # company A merged_with B
    ACQUIRED = "acquired"             # company A acquired B

    # new relations
    PARTNERED_WITH = "partnered_with"   # strategic partnership
    INVESTED_IN = "invested_in"       # investor → project/company
    SUPPLIES_TO = "supplies_to"       # supplier → organisation
    PROVIDES_SERVICE_TO = "provides_service_to" # service provider → client
    HOSTS_AT = "hosts_at"             # event → venue/locality
    LOCATED_NEAR = "located_near"     # proximity relation
    ORIGINATED_FROM = "originated_from" # company/startup → locality


# Common attribute keys for edges
EDGE_TIMESTAMP = "timestamp"   # ISO-8601 string
EDGE_CONFIDENCE = "confidence" # float 0-1
EDGE_MESSAGE = "message"       # free-text description
EDGE_SUBTYPE = "subtype"       # further classification of edge
EDGE_DISTANCE = "distance_km"  # numeric distance for 'nearby' edges

# Standard node coordinate keys
NODE_LAT = "lat"
NODE_LON = "lng"

__all__ = [
    "NodeType",
    "EdgeType",
    "EDGE_TIMESTAMP",
    "EDGE_CONFIDENCE",
    "EDGE_MESSAGE",
    "EDGE_SUBTYPE",
    "EDGE_DISTANCE",
    "NODE_LAT",
    "NODE_LON",
    "SCHEMA_VERSION",
]
