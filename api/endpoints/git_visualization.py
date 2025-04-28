"""API endpoints for Git-like visualizations of project lineage."""
from flask import jsonify, Blueprint
from graph_db.graph_builder import dict_to_nx
from visualization.git_graph import build_git_history_for_project, export_git_visualization
import json
import os

# Create a blueprint for these endpoints
git_viz_bp = Blueprint('git_visualization', __name__)

def load_current_graph():
    """Load the current knowledge graph from file."""
    graph_path = os.environ.get('GRAPH_PATH', 'data/graph_data.json')
    try:
        with open(graph_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Return empty graph if file doesn't exist or is invalid
        return {"nodes": [], "edges": []}

@git_viz_bp.route('/projects/<project_id>/git-history', methods=['GET'])
def get_project_git_visualization(project_id):
    """API endpoint to get Git-like visualization data."""
    # Load the current graph
    graph_data = load_current_graph()
    G = dict_to_nx(graph_data)
    
    # Check if project exists
    if project_id not in G.nodes:
        return jsonify({"error": f"Project {project_id} not found"}), 404
    
    # Generate Git history
    git_commits = build_git_history_for_project(G, project_id)
    visualization_data = export_git_visualization(project_id, git_commits)
    
    return jsonify(visualization_data)

# How to register in the main Flask app:
# from api.endpoints.git_visualization import git_viz_bp
# app.register_blueprint(git_viz_bp, url_prefix='/api') 