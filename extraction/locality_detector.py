"""Utility to detect Hampton Roads localities in text.

This module provides simple functions to detect mentions of Hampton Roads
localities in document text and extract location information.
"""
import re
from graph_db.schema import NodeType, EdgeType
from datetime import datetime

# Hampton Roads localities (used for locality detection)
HAMPTON_ROADS_LOCALITIES = [
    "NORFOLK", "VIRGINIA BEACH", "CHESAPEAKE", "PORTSMOUTH", 
    "SUFFOLK", "HAMPTON", "NEWPORT NEWS", "WILLIAMSBURG",
    "JAMES CITY", "GLOUCESTER", "YORK", "POQUOSON",
    "ISLE OF WIGHT", "SURRY", "SOUTHAMPTON", "SMITHFIELD"
]

# Regular expressions for locality detection
# Include common variations and abbreviations
LOCALITY_PATTERNS = {
    "NORFOLK": [r"\bNorfolk\b", r"\bNFK\b"],
    "VIRGINIA BEACH": [r"\bVirginia Beach\b", r"\bVA Beach\b", r"\bVB\b"],
    "CHESAPEAKE": [r"\bChesapeake\b"],
    "PORTSMOUTH": [r"\bPortsmouth\b"],
    "SUFFOLK": [r"\bSuffolk\b"],
    "HAMPTON": [r"\bHampton\b"],
    "NEWPORT NEWS": [r"\bNewport News\b", r"\bNN\b"],
    "WILLIAMSBURG": [r"\bWilliamsburg\b"],
    "JAMES CITY": [r"\bJames City\b", r"\bJames City County\b", r"\bJCC\b"],
    "GLOUCESTER": [r"\bGloucester\b", r"\bGloucester County\b"],
    "YORK": [r"\bYork\b", r"\bYork County\b"],
    "POQUOSON": [r"\bPoquoson\b"],
    "ISLE OF WIGHT": [r"\bIsle of Wight\b", r"\bIOW\b", r"\bIsle of Wight County\b"],
    "SURRY": [r"\bSurry\b", r"\bSurry County\b"],
    "SOUTHAMPTON": [r"\bSouthampton\b", r"\bSouthampton County\b"],
    "SMITHFIELD": [r"\bSmithfield\b"]
}

# Region regex patterns
REGION_PATTERNS = [
    r"\bHampton Roads\b",
    r"\bHR\b",
    r"\bSeven Cities\b",
    r"\bSoutheast Virginia\b",
    r"\bTidewater\b"
]


def normalize_locality_name(name):
    """Normalize a locality name to a consistent format for IDs."""
    return name.lower().replace(' ', '_')


def detect_localities(text):
    """Detect mentions of Hampton Roads localities in text.
    
    Returns a dictionary with the locality names as keys and
    the number of mentions as values.
    """
    if not text:
        return {}
    
    results = {}
    
    # Check for each locality
    for locality, patterns in LOCALITY_PATTERNS.items():
        count = 0
        for pattern in patterns:
            count += len(re.findall(pattern, text, re.IGNORECASE))
        
        if count > 0:
            results[locality] = count
    
    return results


def detect_region(text):
    """Detect mentions of Hampton Roads region.
    
    Returns True if the text mentions the Hampton Roads region.
    """
    if not text:
        return False
    
    for pattern in REGION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    return False


def add_locality_relations_to_graph(G, document_id, text):
    """Add locality relationships to the graph for a document.
    
    Args:
        G: NetworkX graph
        document_id: ID of the document node
        text: Text content of the document
    
    Returns:
        List of locality IDs that were associated with the document
    """
    # Detect localities in the text
    localities = detect_localities(text)
    if not localities:
        return []
    
    # Current timestamp
    now_iso = datetime.now().isoformat()
    
    # Add edges for each detected locality
    locality_ids = []
    for locality, count in localities.items():
        locality_id = f"loc_{normalize_locality_name(locality)}"
        
        # Skip if locality node doesn't exist
        if locality_id not in G:
            continue
        
        # Add edge from document to locality
        G.add_edge(
            document_id,
            locality_id,
            type=EdgeType.LOCATED_IN.value,
            timestamp=now_iso,
            confidence=min(1.0, count / 10),  # Higher count = higher confidence, max 1.0
            mentions=count
        )
        
        locality_ids.append(locality_id)
    
    # Check for region mentions
    if detect_region(text):
        region_id = "region_hampton_roads"
        if region_id in G:
            G.add_edge(
                document_id,
                region_id,
                type=EdgeType.LOCATED_IN.value,
                timestamp=now_iso,
                subtype="explicit_mention"
            )
    
    return locality_ids 