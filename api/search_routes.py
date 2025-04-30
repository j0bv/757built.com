"""
API routes for the 757Built search functionality.

This module provides the API endpoints for searching the knowledge graph.
"""

import os
import json
import logging
from typing import Dict, Any, List
from flask import Blueprint, request, jsonify, current_app

from Agent.search.query_processor import create_processor
from Agent.search.knowledge_graph_search import create_searcher

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a Blueprint for search routes
search_bp = Blueprint('search', __name__, url_prefix='/api/search')

# Path to Phi-3 model (if available)
PHI3_MODEL_PATH = os.environ.get('PHI3_MODEL_PATH', None)

# Initialize query processor and searcher
query_processor = create_processor(model_path=PHI3_MODEL_PATH)
graph_searcher = create_searcher()

@search_bp.route('/', methods=['POST'])
def search():
    """
    Main search endpoint.
    
    Expected JSON body:
    {
        "query": "Text of natural language query",
        "max_results": 20,  // optional
        "entity_type": "project"  // optional filter
    }
    
    Returns:
        JSON response with search results
    """
    # Get search parameters from request
    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({
            'error': 'Missing query parameter',
            'status': 'error'
        }), 400
    
    query = data.get('query')
    max_results = data.get('max_results', 20)
    entity_type_filter = data.get('entity_type')
    
    # Log search query
    logger.info(f"Search query: {query}")
    
    try:
        # Process the query
        processed_query = query_processor.process_query(query)
        
        # Apply entity_type override if provided in the request
        if entity_type_filter:
            processed_query['entity_type'] = entity_type_filter
        
        # Search the knowledge graph
        results = graph_searcher.search(processed_query, max_results=max_results)
        
        # Return formatted results
        return jsonify({
            'query': query,
            'processed_query': processed_query,
            'results': results,
            'result_count': len(results),
            'status': 'success'
        })
    
    except Exception as e:
        logger.error(f"Error processing search: {str(e)}", exc_info=True)
        return jsonify({
            'error': f"Error processing search: {str(e)}",
            'status': 'error'
        }), 500

@search_bp.route('/multi', methods=['POST'])
def multi_step_search():
    """
    Handle complex multi-step search queries.
    
    Expected JSON body:
    {
        "query": "Find projects in Norfolk and then filter those by funding over $1M",
        "max_results": 20
    }
    
    Returns:
        JSON response with search results from multi-step processing
    """
    # Get search parameters from request
    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({
            'error': 'Missing query parameter',
            'status': 'error'
        }), 400
    
    query = data.get('query')
    max_results = data.get('max_results', 20)
    
    # Log search query
    logger.info(f"Multi-step search query: {query}")
    
    try:
        # Decompose the complex query
        query_steps = query_processor.decompose_complex_query(query)
        
        # If there's only one step, redirect to the main search
        if len(query_steps) == 1:
            processed_query = query_steps[0]
            results = graph_searcher.search(processed_query, max_results=max_results)
            
            return jsonify({
                'query': query,
                'processed_query': processed_query,
                'results': results,
                'result_count': len(results),
                'is_multi_step': False,
                'status': 'success'
            })
        
        # Process multi-step query
        all_results = []
        step_results = []
        
        # Execute each step
        context = {}
        for i, step_query in enumerate(query_steps):
            # First step - normal search
            if i == 0:
                results = graph_searcher.search(step_query, max_results=100)  # Get more results for filtering
                
                # Save context for next steps
                context['previous_results'] = [r['id'] for r in results]
                context['previous_entity_type'] = step_query.get('entity_type')
                
                step_results.append({
                    'step': i + 1,
                    'query': step_query.get('original_query', ''),
                    'processed_query': step_query,
                    'results': results[:max_results],  # Limit results for response
                    'result_count': len(results)
                })
                
                all_results = results
                
            # Subsequent steps - filter previous results
            else:
                # Filter existing results based on new criteria
                filtered_results = []
                
                for result in all_results:
                    # Calculate a new score based on the current step query
                    node_id = result['id']
                    new_score = graph_searcher._calculate_relevance(node_id, step_query)
                    
                    if new_score > 0:
                        # Update the result with the new score
                        updated_result = result.copy()
                        updated_result['score'] = new_score
                        filtered_results.append(updated_result)
                
                # Sort by the new score
                filtered_results.sort(key=lambda x: x['score'], reverse=True)
                
                step_results.append({
                    'step': i + 1,
                    'query': step_query.get('original_query', ''),
                    'processed_query': step_query,
                    'results': filtered_results[:max_results],
                    'result_count': len(filtered_results)
                })
                
                all_results = filtered_results
        
        # Return results from all steps
        return jsonify({
            'query': query,
            'steps': step_results,
            'final_results': all_results[:max_results],
            'final_result_count': len(all_results),
            'is_multi_step': True,
            'status': 'success'
        })
    
    except Exception as e:
        logger.error(f"Error processing multi-step search: {str(e)}", exc_info=True)
        return jsonify({
            'error': f"Error processing multi-step search: {str(e)}",
            'status': 'error'
        }), 500

@search_bp.route('/suggest', methods=['GET'])
def suggest():
    """
    Provide search suggestions based on partial input.
    
    Query parameters:
    - q: Partial query text
    - limit: Maximum number of suggestions (default: 5)
    
    Returns:
        JSON response with suggestions
    """
    query = request.args.get('q', '')
    limit = int(request.args.get('limit', 5))
    
    if not query or len(query) < 2:
        return jsonify({
            'query': query,
            'suggestions': []
        })
    
    try:
        # This is a simplified suggestion algorithm
        # A more sophisticated approach would use knowledge graph entity names
        # or maintain a search history
        
        # Example suggestions (in a real implementation, these would come from the graph)
        common_entities = [
            "Norfolk waterfront development",
            "Hampton Roads Development Corp",
            "renewable energy research",
            "Naval Station Norfolk projects",
            "Virginia Beach tourism",
            "Old Dominion University patents",
            "Newport News Shipbuilding contracts",
            "Chesapeake Bay environmental studies",
            "Virginia Tech research in 757 area",
            "Norfolk Innovation Corridor"
        ]
        
        # Filter by prefix match
        query_lower = query.lower()
        matches = [s for s in common_entities if query_lower in s.lower()]
        
        return jsonify({
            'query': query,
            'suggestions': matches[:limit]
        })
    
    except Exception as e:
        logger.error(f"Error generating suggestions: {str(e)}")
        return jsonify({
            'query': query,
            'suggestions': [],
            'error': str(e)
        }), 500

def init_app(app):
    """
    Initialize the search blueprint with a Flask app.
    
    Args:
        app: Flask application instance
    """
    app.register_blueprint(search_bp)
    logger.info("Search routes registered") 