"""Generate Git-like visualization data for projects and their lineage.

This module creates a Git-like representation of project lineage,
showing how research papers and patents connect to projects.
"""
import networkx as nx
from datetime import datetime
from graph_db.schema import NodeType, EdgeType

# Define Hampton Roads localities for highlighting
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

def build_git_history_for_project(G, project_id):
    """Build a Git-like history for a specific project.
    
    Returns data structure that can be visualized as a Git graph.
    """
    # Get all ancestors that contributed to this project
    subgraph = nx.DiGraph()
    
    # Add the project node
    project_data = G.nodes[project_id]
    subgraph.add_node(project_id, **project_data)
    
    # Recursively trace back to all research and patents
    nodes_to_process = [project_id]
    while nodes_to_process:
        current = nodes_to_process.pop(0)
        
        # Find all direct ancestors (papers, patents that influenced)
        ancestors = []
        for predecessor, edge_data in G.pred[current].items():
            edge_type = edge_data.get('type')
            if edge_type in (EdgeType.DERIVES_FROM.value, EdgeType.IMPLEMENTS.value, 
                            EdgeType.INFLUENCED.value):
                ancestors.append((predecessor, edge_data))
        
        # Add them to our subgraph
        for ancestor_id, edge_data in ancestors:
            if ancestor_id not in subgraph:
                # Only process nodes we haven't seen
                subgraph.add_node(ancestor_id, **G.nodes[ancestor_id])
                nodes_to_process.append(ancestor_id)
            
            # Add the connection
            subgraph.add_edge(ancestor_id, current, **edge_data)
    
    # Add relevant locality nodes
    add_localities_to_subgraph(G, subgraph)
    
    # Now convert to Git-like format with commits
    git_commits = []
    for node_id in nx.topological_sort(subgraph):  # Ensure ancestors come first
        node_type = subgraph.nodes[node_id].get('type')
        
        # Skip locality nodes in commits list (they're in separate metadata)
        if node_type == NodeType.LOCALITY.value or node_type == NodeType.REGION.value:
            continue
            
        timestamp = get_node_timestamp(subgraph, node_id)
        
        # Get locality information
        locality_info = get_node_locality_info(G, node_id)
        
        # Build a Git-like commit object
        commit = {
            'id': node_id,
            'timestamp': timestamp,
            'type': node_type,
            'message': subgraph.nodes[node_id].get('title', f"Unnamed {node_type}"),
            'parents': [p for p in subgraph.predecessors(node_id) 
                       if subgraph.nodes[p].get('type') not in [NodeType.LOCALITY.value, NodeType.REGION.value]],
            'cid': subgraph.nodes[node_id].get('cid', ''),  # Include IPFS CID
            'author': subgraph.nodes[node_id].get('author', 'Unknown'),
            'locality': locality_info.get('primary_locality', ''),
            'localities': locality_info.get('localities', []),
            'coordinates': locality_info.get('coordinates', None),
            'in_seven_cities': locality_info.get('in_seven_cities', False)
        }
        git_commits.append(commit)
    
    return git_commits

def add_localities_to_subgraph(G, subgraph):
    """Add locality nodes and edges to the subgraph."""
    # Find nodes that have locality edges
    locality_edges = []
    for node_id in list(subgraph.nodes()):
        if G.has_node(node_id):  # Safety check
            # Find outgoing edges to localities
            for _, target, edge_data in G.out_edges(node_id, data=True):
                if (edge_data.get('type') == EdgeType.LOCATED_IN.value and
                    G.nodes[target].get('type') == NodeType.LOCALITY.value):
                    locality_edges.append((node_id, target, edge_data))
    
    # Add localities and edges to subgraph
    for source, target, edge_data in locality_edges:
        if not subgraph.has_node(target):
            subgraph.add_node(target, **G.nodes[target])
        if not subgraph.has_edge(source, target):
            subgraph.add_edge(source, target, **edge_data)

def get_node_locality_info(G, node_id):
    """Get locality information for a node (document, project, etc.)."""
    result = {
        'primary_locality': '',
        'localities': [],
        'coordinates': None,
        'in_seven_cities': False
    }
    
    # Direct locality attribute from node
    if 'primary_locality' in G.nodes[node_id]:
        primary = G.nodes[node_id]['primary_locality']
        result['primary_locality'] = primary
        result['localities'] = G.nodes[node_id].get('localities', [primary])
        result['coordinates'] = G.nodes[node_id].get('coordinates')
        result['in_seven_cities'] = primary in SEVEN_CITIES
        return result
    
    # Look for LOCATED_IN edges
    localities = []
    for _, target, edge_data in G.out_edges(node_id, data=True):
        if (edge_data.get('type') == EdgeType.LOCATED_IN.value and
            G.nodes[target].get('type') == NodeType.LOCALITY.value):
            name = G.nodes[target].get('name', '')
            if name:
                localities.append({
                    'name': name,
                    'confidence': edge_data.get('confidence', 0.5),
                    'coordinates': G.nodes[target].get('coordinates'),
                    'in_seven_cities': name in SEVEN_CITIES
                })
    
    # Sort by confidence
    localities.sort(key=lambda x: x['confidence'], reverse=True)
    
    if localities:
        primary = localities[0]
        result['primary_locality'] = primary['name']
        result['localities'] = [loc['name'] for loc in localities]
        result['coordinates'] = primary['coordinates']
        result['in_seven_cities'] = primary['in_seven_cities']
    
    return result

def get_node_timestamp(G, node_id):
    """Extract or estimate timestamp for a node based on its connections."""
    # First try to get node's own timestamp
    if 'date' in G.nodes[node_id]:
        return G.nodes[node_id]['date']
    
    # Otherwise use earliest edge timestamp
    timestamps = []
    for _, _, edge_data in G.in_edges(node_id, data=True):
        if 'timestamp' in edge_data:
            timestamps.append(edge_data['timestamp'])
    
    return min(timestamps) if timestamps else datetime.now().isoformat()

def export_git_visualization(project_id, git_commits):
    """Export the Git visualization to JSON format for rendering."""
    # Group commits by locality for map visualization
    commits_by_locality = {}
    for commit in git_commits:
        if commit['locality']:
            if commit['locality'] not in commits_by_locality:
                commits_by_locality[commit['locality']] = []
            commits_by_locality[commit['locality']].append(commit['id'])
    
    return {
        'project_id': project_id,
        'commits': git_commits,
        'branches': extract_branches(git_commits),
        'localities': {
            'commits_by_locality': commits_by_locality,
            'seven_cities': SEVEN_CITIES,
            'hampton_roads': HAMPTON_ROADS_LOCALITIES
        }
    }

def extract_branches(git_commits):
    """Identify logical branches in the commit history.
    
    For example:
    - Research papers form initial branches
    - Patents that implement multiple papers are merge points
    - Final project implementation is the master branch head
    """
    # Group by node type to form logical branches
    branches = {}
    
    # Sort commits by timestamp
    sorted_commits = sorted(git_commits, key=lambda c: c['timestamp'])
    
    # Research papers form the earliest branches
    research_branches = []
    for commit in sorted_commits:
        if commit['type'] == NodeType.RESEARCH_PAPER.value:
            branch_name = f"research/{commit['id']}"
            branches[branch_name] = [commit['id']]
            research_branches.append(branch_name)
    
    # Patents typically merge research branches
    patent_branches = []
    for commit in sorted_commits:
        if commit['type'] == NodeType.PATENT.value:
            # Find which research branches this patent comes from
            parent_branches = []
            for parent in commit['parents']:
                for branch_name, commits in branches.items():
                    if parent in commits:
                        parent_branches.append(branch_name)
            
            # Create patent branch
            branch_name = f"patent/{commit['id']}"
            branches[branch_name] = [commit['id']]
            patent_branches.append(branch_name)
            
            # Record merge information
            for parent_branch in parent_branches:
                branches[parent_branch].append(commit['id'])
    
    # Project is the master branch
    project_branches = []
    for commit in sorted_commits:
        if commit['type'] == NodeType.PROJECT.value:
            branch_name = f"project/{commit['id']}"
            branches[branch_name] = [commit['id']]
            project_branches.append(branch_name)
    
    return {
        'research': research_branches,
        'patent': patent_branches, 
        'project': project_branches,
        'branch_commits': branches
    } 