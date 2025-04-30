"""Unit tests for the edge mapping module."""
import os
import pathlib
import tempfile
import pytest
from unittest.mock import patch

from graph_db.edge_mapping import (
    canonical_edge, 
    reload_mapping, 
    get_all_relation_texts,
    get_mapping_file_path
)
from graph_db.schema import EdgeType

# Sample mapping for testing
TEST_MAPPING_CONTENT = """
# Test mapping
worked with: WORKED_WITH
collaborated with: WORKED_WITH
partnered with: PARTNERED_WITH
acquired: ACQUIRED
bought: ACQUIRED
invalid relation: INVALID_EDGE_TYPE
"""

@pytest.fixture
def temp_mapping_file():
    """Create a temporary mapping file for testing."""
    # Save original mapping file path
    original_file = pathlib.Path(get_mapping_file_path())
    original_content = original_file.read_text() if original_file.exists() else ""
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
        temp_file.write(TEST_MAPPING_CONTENT)
        temp_path = temp_file.name
    
    # Patch the _MAPPING_FILE path
    with patch('graph_db.edge_mapping._MAPPING_FILE', pathlib.Path(temp_path)):
        # Force reload with the new path
        reload_mapping()
        yield temp_path
    
    # Clean up
    os.unlink(temp_path)
    
    # Restore original mapping if needed (only for tests that modified it)
    if original_file.exists() and original_content:
        reload_mapping()

def test_canonical_edge_basic(temp_mapping_file):
    """Test basic mapping of text to EdgeType."""
    # Test exact matches
    assert canonical_edge("worked with") == EdgeType.WORKED_WITH
    assert canonical_edge("acquired") == EdgeType.ACQUIRED
    
    # Test case insensitivity
    assert canonical_edge("Worked With") == EdgeType.WORKED_WITH
    assert canonical_edge("ACQUIRED") == EdgeType.ACQUIRED
    
    # Test whitespace handling
    assert canonical_edge("  worked with  ") == EdgeType.WORKED_WITH
    
    # Test mapping of synonyms
    assert canonical_edge("collaborated with") == EdgeType.WORKED_WITH
    assert canonical_edge("bought") == EdgeType.ACQUIRED

def test_canonical_edge_invalid(temp_mapping_file):
    """Test handling of invalid relations."""
    # Non-existent relation
    assert canonical_edge("unknown relation") is None
    
    # Empty input
    assert canonical_edge("") is None
    assert canonical_edge(None) is None
    
    # Relation mapped to invalid enum (should return None, not error)
    assert canonical_edge("invalid relation") is None

def test_get_all_relation_texts(temp_mapping_file):
    """Test retrieving all relation texts."""
    relations = get_all_relation_texts()
    
    # Check expected relations are present
    assert "worked with" in relations
    assert "collaborated with" in relations
    assert "acquired" in relations
    assert "bought" in relations
    
    # Check count matches expected (5 valid + 1 invalid in test data)
    assert len(relations) == 6

def test_reload_mapping(temp_mapping_file):
    """Test forced reload of mapping."""
    # Initial load
    count = reload_mapping()
    assert count == 6  # 5 valid + 1 invalid relations
    
    # Modify the file and reload
    with open(temp_mapping_file, 'a') as f:
        f.write("new relation: ACQUIRED\n")
    
    # Reload and verify count increased
    count = reload_mapping()
    assert count == 7
    
    # Verify new relation is available
    assert canonical_edge("new relation") == EdgeType.ACQUIRED 