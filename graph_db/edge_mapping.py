"""Edge mapping utilities for the 757Built knowledge graph.

This module provides tools to map free-text relationship descriptions
to canonical EdgeType enum values. It loads a YAML mapping file and
provides helper functions to normalize relationship texts.
"""
import yaml
import pathlib
import logging
from typing import Dict, Optional, Set
from threading import Lock

from .schema import EdgeType

logger = logging.getLogger(__name__)

_MAPPING_FILE = pathlib.Path(__file__).with_suffix('.yaml')
_mapping_cache: Dict[str, str] = {}
_mapping_lock = Lock()
_last_mtime = 0

def _load_mapping() -> Dict[str, str]:
    """Load the edge mapping from YAML file."""
    global _mapping_cache, _last_mtime
    
    try:
        current_mtime = _MAPPING_FILE.stat().st_mtime
        
        with _mapping_lock:
            # Check if file has been modified since last load
            if not _mapping_cache or current_mtime > _last_mtime:
                logger.info(f"Loading edge mapping from {_MAPPING_FILE}")
                mapping = yaml.safe_load(_MAPPING_FILE.read_text())
                
                # Store normalized keys (lowercase, stripped)
                _mapping_cache = {k.lower().strip(): v for k, v in mapping.items()}
                _last_mtime = current_mtime
                logger.info(f"Loaded {len(_mapping_cache)} edge mappings")
            
        return _mapping_cache
    except Exception as e:
        logger.error(f"Error loading edge mapping: {e}")
        return {}

def canonical_edge(text: str) -> Optional[EdgeType]:
    """Convert a free-text relationship description to a canonical EdgeType.
    
    Args:
        text: The relationship text to normalize (e.g., "collaborated with")
        
    Returns:
        The corresponding EdgeType enum value, or None if no match found
    """
    if not text:
        return None
        
    text = text.lower().strip()
    mapping = _load_mapping()
    
    enum_name = mapping.get(text)
    if enum_name:
        try:
            return EdgeType[enum_name]
        except KeyError:
            logger.warning(f"Invalid EdgeType enum name in mapping: {enum_name}")
            return None
    return None

def get_all_relation_texts() -> Set[str]:
    """Get all recognized relation texts from the mapping file.
    
    Returns:
        A set of all relationship strings that can be mapped
    """
    mapping = _load_mapping()
    return set(mapping.keys())

def reload_mapping() -> int:
    """Force reload of the edge mapping file.
    
    Returns:
        The number of mappings loaded
    """
    global _mapping_cache, _last_mtime
    
    with _mapping_lock:
        _mapping_cache = {}
        _last_mtime = 0
        
    mapping = _load_mapping()
    return len(mapping)

def get_mapping_file_path() -> str:
    """Get the absolute path to the edge mapping file.
    
    Returns:
        The absolute path as a string
    """
    return str(_MAPPING_FILE.absolute()) 