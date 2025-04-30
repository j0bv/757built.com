#!/usr/bin/env python3
"""
Run script for the 757Built API server.

This script starts the Flask development server for the 757Built API.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add the parent directory to the path so we can import the api package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Load environment variables from .env file if present
load_dotenv()

# Import the application factory
from api import create_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_config_from_env():
    """
    Get configuration from environment variables.
    
    Returns:
        Dictionary of configuration values
    """
    return {
        'DEBUG': os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't'),
        'TESTING': os.environ.get('FLASK_TESTING', 'False').lower() in ('true', '1', 't'),
        'SECRET_KEY': os.environ.get('FLASK_SECRET_KEY', 'dev-key-change-in-production'),
        'GRAPH_DATA_PATH': os.environ.get('GRAPH_DATA_PATH', '../data/knowledge_graph.json'),
        'PHI3_MODEL_PATH': os.environ.get('PHI3_MODEL_PATH', None),
    }

if __name__ == '__main__':
    # Get configuration from environment
    config = get_config_from_env()
    
    # Create the application
    app = create_app(config)
    
    # Get host and port from environment or use defaults
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    
    logger.info(f"Starting 757Built API server on {host}:{port}")
    
    # Run the application
    app.run(host=host, port=port) 