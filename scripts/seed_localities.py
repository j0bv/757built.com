#!/usr/bin/env python3
"""Seed Hampton Roads locality nodes in the knowledge graph.

This script creates nodes for each Hampton Roads locality with appropriate
attributes and GeoJSON references. Run this once to initialize the graph
with region data.
"""
import os
import json
import networkx as nx
from datetime import datetime
import ipfshttpclient
import sys

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from graph_db.schema import NodeType, EdgeType, EDGE_TIMESTAMP
from ipfs_storage.ipfs_client import add_or_reuse

# Constants
GRAPH_DATA_PATH = os.path.join('data', 'graph_data.json')
GEOJSON_DIR = os.path.join('data', 'geojson')
HAMPTON_ROADS_REGION_ID = "region_hampton_roads"

# Hampton Roads localities
HAMPTON_ROADS_LOCALITIES = [
    "NORFOLK", "VIRGINIA BEACH", "CHESAPEAKE", "PORTSMOUTH", 
    "SUFFOLK", "HAMPTON", "NEWPORT NEWS", "WILLIAMSBURG",
    "JAMES CITY", "GLOUCESTER", "YORK", "POQUOSON",
    "ISLE OF WIGHT", "SURRY", "SOUTHAMPTON", "SMITHFIELD"
]

# The Seven Cities (subset of Hampton Roads)
SEVEN_CITIES = [
    "CHESAPEAKE", "HAMPTON", "NEWPORT NEWS", "NORFOLK", 
    "PORTSMOUTH", "SUFFOLK", "VIRGINIA BEACH"
]

# Approximate centroid coordinates for localities (for visualization)
LOCALITY_COORDINATES = {
    "NORFOLK": [36.8508, -76.2859],
    "VIRGINIA BEACH": [36.8529, -75.9780],
    "CHESAPEAKE": [36.7682, -76.2874],
    "PORTSMOUTH": [36.8354, -76.2983],
    "SUFFOLK": [36.7282, -76.5836],
    "HAMPTON": [37.0311, -76.3452],
    "NEWPORT NEWS": [37.0871, -76.4730],
    "WILLIAMSBURG": [37.2707, -76.7075],
    "JAMES CITY": [37.3136, -76.7681],
    "GLOUCESTER": [37.4098, -76.5250],
    "YORK": [37.2419, -76.5125],
    "POQUOSON": [37.1224, -76.3193],
    "ISLE OF WIGHT": [36.9087, -76.7048],
    "SURRY": [37.1374, -76.8850],
    "SOUTHAMPTON": [36.7787, -77.1025],
    "SMITHFIELD": [36.9824, -76.6322]
}

def normalize_locality_name(name):
    """Normalize a locality name to a consistent format for IDs."""
    return name.lower().replace(' ', '_')

def load_graph():
    """Load existing graph or create a new one."""
    if os.path.exists(GRAPH_DATA_PATH):
        with open(GRAPH_DATA_PATH, 'r') as f:
            graph_dict = json.load(f)
        G = nx.DiGraph()
        
        # Add nodes
        for node in graph_dict.get('nodes', []):
            attrs = {k: v for k, v in node.items() if k != 'id'}
            G.add_node(node['id'], **attrs)
        
        # Add edges
        for edge in graph_dict.get('edges', []):
            attrs = {k: v for k, v in edge.items() if k not in ['source', 'target']}
            G.add_edge(edge['source'], edge['target'], **attrs)
            
        return G
    else:
        return nx.DiGraph()

def save_graph(G):
    """Save graph to JSON file."""
    os.makedirs(os.path.dirname(GRAPH_DATA_PATH), exist_ok=True)
    
    # Convert to dict format
    nodes = []
    for node_id, attrs in G.nodes(data=True):
        node_data = {'id': node_id}
        node_data.update(attrs)
        nodes.append(node_data)
    
    edges = []
    for u, v, attrs in G.edges(data=True):
        edge_data = {'source': u, 'target': v}
        edge_data.update(attrs)
        edges.append(edge_data)
    
    graph_dict = {
        'nodes': nodes,
        'edges': edges
    }
    
    with open(GRAPH_DATA_PATH, 'w') as f:
        json.dump(graph_dict, f, indent=2)

def create_geojson_for_locality(locality, coordinates):
    """Create a simple GeoJSON Point feature for a locality."""
    geojson = {
        "type": "Feature",
        "properties": {
            "name": locality,
            "is_seven_cities": locality in SEVEN_CITIES
        },
        "geometry": {
            "type": "Point",
            "coordinates": [coordinates[1], coordinates[0]]  # GeoJSON is [lng, lat]
        }
    }
    
    # Create directory if it doesn't exist
    os.makedirs(GEOJSON_DIR, exist_ok=True)
    
    # Save to file
    file_path = os.path.join(GEOJSON_DIR, f"{normalize_locality_name(locality)}.geojson")
    with open(file_path, 'w') as f:
        json.dump(geojson, f, indent=2)
    
    return file_path

def add_locality_to_graph(G, locality, coordinates, is_seven_cities=False):
    """Add a locality node to the graph."""
    locality_id = f"loc_{normalize_locality_name(locality)}"
    
    # Create GeoJSON file
    geojson_path = create_geojson_for_locality(locality, coordinates)
    
    # Add to IPFS
    geojson_cid = None
    try:
        geojson_cid = add_or_reuse(geojson_path)
        print(f"Added GeoJSON for {locality} to IPFS with CID: {geojson_cid}")
    except Exception as e:
        print(f"Warning: Could not add GeoJSON to IPFS: {e}")
    
    # Add node
    G.add_node(
        locality_id,
        type=NodeType.LOCALITY.value,
        label=locality,
        name=locality,
        region="hampton_roads",
        is_seven_cities=is_seven_cities,
        coordinates=coordinates,
        geojson_cid=geojson_cid
    )
    
    return locality_id

def add_region_to_graph(G):
    """Add Hampton Roads region node to the graph."""
    # Add region node
    G.add_node(
        HAMPTON_ROADS_REGION_ID,
        type=NodeType.REGION.value,
        label="Hampton Roads",
        name="Hampton Roads",
        description="Hampton Roads region in southeastern Virginia"
    )
    
    return HAMPTON_ROADS_REGION_ID

def main():
    """Main function to seed localities."""
    # Load or create graph
    G = load_graph()
    
    # Add Hampton Roads region
    region_id = add_region_to_graph(G)
    
    # Current timestamp
    now_iso = datetime.now().isoformat()
    
    # Add localities
    for locality in HAMPTON_ROADS_LOCALITIES:
        coordinates = LOCALITY_COORDINATES.get(locality, [0, 0])
        is_seven_cities = locality in SEVEN_CITIES
        
        # Add locality node
        locality_id = add_locality_to_graph(G, locality, coordinates, is_seven_cities)
        
        # Connect to region
        G.add_edge(
            locality_id,
            region_id,
            type=EdgeType.LOCATED_IN.value,
            timestamp=now_iso
        )
    
    # Save graph
    save_graph(G)
    
    print(f"Successfully added {len(HAMPTON_ROADS_LOCALITIES)} localities and Hampton Roads region to the graph")

if __name__ == "__main__":
    main() 