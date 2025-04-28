from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import json
import os
import ipfshttpclient
from graph_db.schema import NodeType, EdgeType

app = Flask(__name__)
CORS(app)

GRAPH_DATA_PATH = 'data/graph_data.json'
IPFS_GATEWAY = os.getenv('IPFS_GATEWAY', 'http://localhost:8080')
IPNS_KEY = os.getenv('GRAPH_IPNS_KEY', 'self')

# Import our Git visualization blueprint
from endpoints.git_visualization import git_viz_bp

# Register blueprints
app.register_blueprint(git_viz_bp, url_prefix='/api')

# Set simple caching headers (5 minutes) for GET requests
@app.after_request
def add_cache_headers(response):
    if request.method == 'GET':
        response.cache_control.max_age = 300
        response.cache_control.public = True
    return response

# Helper functions
def load_graph_data():
    """Load graph data from file or IPFS"""
    try:
        with open(GRAPH_DATA_PATH, 'r') as f:
            return json.load(f)
    except:
        return {"nodes": [], "edges": [], "projects": [], "locations": []}

def get_node_by_id(graph_data, node_id):
    """Find node by ID in graph data"""
    return next((node for node in graph_data['nodes'] if node['id'] == node_id), None)

def get_edges_for_node(graph_data, node_id):
    """Get all edges connected to a node"""
    return [edge for edge in graph_data['edges'] 
            if edge['source'] == node_id or edge['target'] == node_id]

def get_neighbors(graph_data, node_id):
    """Get all neighbor nodes of a node"""
    edges = get_edges_for_node(graph_data, node_id)
    neighbor_ids = set()
    for edge in edges:
        if edge['source'] == node_id:
            neighbor_ids.add(edge['target'])
        else:
            neighbor_ids.add(edge['source'])
    
    return [get_node_by_id(graph_data, nid) for nid in neighbor_ids if nid]

# Routes
@app.route('/api/projects', methods=['GET'])
def get_projects():
    """Get all projects"""
    graph_data = load_graph_data()
    return jsonify(graph_data.get('projects', []))

@app.route('/api/projects/<project_id>', methods=['GET'])
def get_project(project_id):
    """Get a single project by ID"""
    graph_data = load_graph_data()
    project = next((p for p in graph_data.get('projects', []) if p['id'] == project_id), None)
    if not project:
        abort(404, description="Project not found")
    return jsonify(project)

@app.route('/api/projects/<project_id>/documents', methods=['GET'])
def get_project_documents(project_id):
    """Get all documents related to a project"""
    graph_data = load_graph_data()
    
    # Find all edges that connect project to documents
    doc_edges = [edge for edge in graph_data.get('edges', []) 
                if edge['source'] == project_id and edge['relationship'] == 'contains_document']
    
    # Get the document nodes
    doc_nodes = []
    for edge in doc_edges:
        doc_node = get_node_by_id(graph_data, edge['target'])
        if doc_node and doc_node['type'] == 'document':
            doc_nodes.append(doc_node)
    
    return jsonify(doc_nodes)

@app.route('/api/documents/<document_id>/related', methods=['GET'])
def get_related_docs(document_id):
    """Get documents related to this document"""
    graph_data = load_graph_data()
    
    # Get all edges for this document
    doc_edges = get_edges_for_node(graph_data, document_id)
    
    # Get all nodes connected to this document
    related = []
    for edge in doc_edges:
        # Get the other end of the edge
        other_id = edge['target'] if edge['source'] == document_id else edge['source']
        other_node = get_node_by_id(graph_data, other_id)
        
        if other_node:
            related.append({
                'node': other_node,
                'relationship': edge['relationship']
            })
    
    return jsonify(related)

@app.route('/api/graph/subgraph/<node_id>', methods=['GET'])
def get_subgraph(node_id):
    """Get a subgraph centered on a specific node"""
    graph_data = load_graph_data()
    depth = int(request.args.get('depth', 1))
    
    # Start with the center node
    center_node = get_node_by_id(graph_data, node_id)
    if not center_node:
        abort(404, description="Node not found")
    
    # Build the subgraph
    subgraph = {
        'nodes': [center_node],
        'edges': []
    }
    
    # We'll do a simple BFS to the requested depth
    visited = {node_id}
    frontier = [node_id]
    
    for _ in range(depth):
        next_frontier = []
        for current_id in frontier:
            # Get all edges for this node
            edges = get_edges_for_node(graph_data, current_id)
            
            for edge in edges:
                # Add edge to subgraph if not already there
                if edge not in subgraph['edges']:
                    subgraph['edges'].append(edge)
                
                # Add the neighbor to the next frontier if not visited
                neighbor_id = edge['target'] if edge['source'] == current_id else edge['source']
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    next_frontier.append(neighbor_id)
                    
                    # Add neighbor node to subgraph
                    neighbor_node = get_node_by_id(graph_data, neighbor_id)
                    if neighbor_node and neighbor_node not in subgraph['nodes']:
                        subgraph['nodes'].append(neighbor_node)
        
        frontier = next_frontier
        if not frontier:  # No more nodes to explore
            break
    
    return jsonify(subgraph)

@app.route('/api/search', methods=['GET'])
def search():
    """Search nodes by label/name"""
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify([])
    
    graph_data = load_graph_data()
    
    # Search all nodes
    results = []
    for node in graph_data.get('nodes', []):
        if query in node.get('label', '').lower():
            results.append(node)
    
    # Also search projects
    for project in graph_data.get('projects', []):
        if (query in project.get('title', '').lower() or 
            query in project.get('summary', '').lower()):
            # Convert project to node format if not already in results
            if not any(r.get('id') == project.get('id') for r in results):
                results.append({
                    'id': project.get('id'),
                    'label': project.get('title', ''),
                    'type': 'project',
                    'properties': project
                })
    
    return jsonify(results)

@app.route('/api/ipfs/<hash>', methods=['GET'])
def get_ipfs_content(hash):
    """Fetch content from IPFS by hash"""
    try:
        client = ipfshttpclient.connect()
        content = client.cat(hash)
        
        # Determine content type
        if hash.endswith('.json'):
            return jsonify(json.loads(content))
        elif hash.endswith('.txt'):
            return content.decode('utf-8')
        else:
            return content
    except:
        abort(404, description="IPFS content not found")

@app.route('/api/localities', methods=['GET'])
def list_localities():
    """Get all localities in the knowledge graph."""
    graph_data = load_graph_data()
    localities = []
    
    for node in graph_data.get('nodes', []):
        if node.get('type') == NodeType.LOCALITY.value:
            localities.append({
                'id': node.get('id'),
                'name': node.get('name', ''),
                'label': node.get('label', ''),
                'coordinates': node.get('coordinates', []),
                'is_seven_cities': node.get('is_seven_cities', False),
                'geojson_cid': node.get('geojson_cid', '')
            })
    
    return jsonify(localities)

@app.route('/api/projects/by-locality/<locality_name>', methods=['GET'])
def projects_by_locality(locality_name):
    """Get projects located in a specific locality."""
    locality_name = locality_name.upper()  # Normalize to uppercase
    graph_data = load_graph_data()
    
    # Find the locality node
    locality_id = None
    for node in graph_data.get('nodes', []):
        if (node.get('type') == NodeType.LOCALITY.value and 
            node.get('name', '').upper() == locality_name):
            locality_id = node.get('id')
            break
    
    if not locality_id:
        abort(404, description=f"Locality '{locality_name}' not found")
    
    # Find all edges from projects to this locality
    project_edges = []
    for edge in graph_data.get('edges', []):
        if (edge.get('target') == locality_id and 
            edge.get('type') == EdgeType.LOCATED_IN.value):
            source_id = edge.get('source')
            source_node = get_node_by_id(graph_data, source_id)
            if source_node and source_node.get('type') == NodeType.PROJECT.value:
                project_edges.append({
                    'project': source_node,
                    'relation': edge
                })
    
    # Extract just the project nodes
    projects = [item['project'] for item in project_edges]
    
    return jsonify(projects)

@app.route('/api/graph/map-data', methods=['GET'])
def get_map_data():
    """Get data formatted for map visualization."""
    graph_data = load_graph_data()
    
    # Collect nodes with coordinates for map display
    map_nodes = []
    for node in graph_data.get('nodes', []):
        if 'coordinates' in node:
            # Only include nodes with coordinates
            map_nodes.append({
                'id': node.get('id'),
                'type': node.get('type'),
                'label': node.get('label', ''),
                'coordinates': node.get('coordinates'),
                'locality': node.get('primary_locality', ''),
                'is_seven_cities': node.get('primary_locality', '') in SEVEN_CITIES
            })
    
    # Get all localities
    localities = []
    for node in graph_data.get('nodes', []):
        if node.get('type') == NodeType.LOCALITY.value:
            localities.append({
                'id': node.get('id'),
                'name': node.get('name', ''),
                'coordinates': node.get('coordinates', []),
                'is_seven_cities': node.get('is_seven_cities', False)
            })
    
    # Count projects per locality
    projects_by_locality = {}
    for node in graph_data.get('nodes', []):
        if node.get('type') == NodeType.PROJECT.value:
            locality = node.get('primary_locality', '')
            if locality:
                if locality not in projects_by_locality:
                    projects_by_locality[locality] = 0
                projects_by_locality[locality] += 1
    
    return jsonify({
        'map_nodes': map_nodes,
        'localities': localities,
        'projects_by_locality': projects_by_locality
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
