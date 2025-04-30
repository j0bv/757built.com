"""
API module for 757Built platform.

This module contains the Flask API routes and endpoints
for the 757Built knowledge graph platform.
"""

from flask import Flask
from .search_routes import init_app as init_search_routes

__version__ = '0.1.0'

def create_app(config=None):
    """
    Create and configure the Flask application.
    
    Args:
        config: Configuration dictionary or object
        
    Returns:
        Configured Flask application
    """
    app = Flask(__name__)
    
    # Apply configuration
    if config:
        app.config.update(config)
    
    # Register blueprints
    init_search_routes(app)
    
    # Add a basic index route
    @app.route('/')
    def index():
        return {
            'name': '757Built API',
            'version': __version__,
            'endpoints': {
                'search': '/api/search',
                'multi-step': '/api/search/multi',
                'suggestions': '/api/search/suggest'
            }
        }
    
    return app 