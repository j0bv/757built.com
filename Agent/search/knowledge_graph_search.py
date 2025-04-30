"""
Knowledge graph search module for 757Built platform.

This module provides functionality to search the knowledge graph based on
processed query parameters and return relevant results.
"""

import os
import json
import logging
import networkx as nx
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

logger = logging.getLogger(__name__)

# Node types in the knowledge graph
class NodeType:
    DOCUMENT = "document"
    PROJECT = "project"
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    PATENT = "patent"
    RESEARCH = "research"

class KnowledgeGraphSearch:
    """Search interface for the 757Built knowledge graph."""
    
    def __init__(self, graph_path: Optional[str] = None):
        """
        Initialize the knowledge graph search.
        
        Args:
            graph_path: Path to the graph data file (JSON or pickle)
        """
        self.graph_path = graph_path or os.environ.get(
            "GRAPH_DATA_PATH", 
            os.path.join(os.path.dirname(__file__), "..", "..", "data", "knowledge_graph.json")
        )
        self.graph = self._load_graph()
    
    def _load_graph(self) -> nx.Graph:
        """
        Load the knowledge graph from disk.
        
        Returns:
            NetworkX graph object
        """
        graph_path = Path(self.graph_path)
        
        if not graph_path.exists():
            logger.warning(f"Graph file not found at {graph_path}. Creating new graph.")
            return nx.DiGraph()
        
        try:
            # Determine file type and load accordingly
            if graph_path.suffix == '.json':
                with open(graph_path, 'r') as f:
                    data = json.load(f)
                return nx.node_link_graph(data)
            else:
                return nx.read_gpickle(graph_path)
        except Exception as e:
            logger.error(f"Error loading graph: {e}")
            return nx.DiGraph()
    
    def search(self, query_params: Dict[str, Any], 
               max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Search the knowledge graph based on processed query parameters.
        
        Args:
            query_params: Dictionary of processed query parameters
            max_results: Maximum number of results to return
            
        Returns:
            List of result dictionaries with node data and relevance score
        """
        if not self.graph or self.graph.number_of_nodes() == 0:
            logger.warning("Empty knowledge graph, no results to return")
            return []
        
        # Extract query parameters
        entity_type = query_params.get('entity_type')
        time_range = query_params.get('time_range')
        location = query_params.get('location')
        keywords = query_params.get('keywords', [])
        relationships = query_params.get('relationships', {})
        
        # Filter nodes by entity type
        candidate_nodes = set()
        for node, attrs in self.graph.nodes(data=True):
            node_type = attrs.get('type')
            
            # If entity type is specified, filter by it
            if entity_type and node_type != entity_type:
                continue
                
            # Add all nodes of requested types or all if no type specified
            candidate_nodes.add(node)
        
        # Score and rank candidates
        scored_results = []
        for node_id in candidate_nodes:
            score = self._calculate_relevance(node_id, query_params)
            if score > 0:
                node_data = dict(self.graph.nodes[node_id])
                # Add connected entities as context
                node_data['connections'] = self._get_node_connections(node_id)
                scored_results.append({
                    'id': node_id,
                    'data': node_data,
                    'score': score,
                    'highlights': self._generate_highlights(node_id, query_params)
                })
        
        # Sort by score and limit results
        scored_results.sort(key=lambda x: x['score'], reverse=True)
        return scored_results[:max_results]
    
    def _calculate_relevance(self, node_id: str, 
                             query_params: Dict[str, Any]) -> float:
        """
        Calculate relevance score of a node for the given query.
        
        Args:
            node_id: ID of the node to score
            query_params: Query parameters
            
        Returns:
            Relevance score (higher is more relevant)
        """
        node_data = self.graph.nodes[node_id]
        score = 0.0
        
        # Check time range if specified
        if query_params.get('time_range'):
            # Check if node has a date
            node_date = self._extract_node_date(node_data)
            if node_date:
                time_range = query_params['time_range']
                # Apply time range filter - if outside range, return 0
                if time_range.get('start') and node_date < time_range['start']:
                    return 0.0
                if time_range.get('end') and node_date > time_range['end']:
                    return 0.0
                # Nodes closer to search date get higher score
                if time_range.get('start') and time_range.get('end'):
                    midpoint = (time_range['start'] + time_range['end']) / 2
                    recency_score = 1.0 - abs(node_date - midpoint) / (time_range['end'] - time_range['start'] + 1)
                    score += recency_score
        
        # Check location if specified
        if query_params.get('location'):
            location_match = self._check_location_match(node_id, query_params['location'])
            if location_match:
                score += 2.0
        
        # Check keywords
        if query_params.get('keywords'):
            keyword_score = self._calculate_keyword_score(node_data, query_params['keywords'])
            score += keyword_score
        
        # Check relationships
        if query_params.get('relationships'):
            relationship_score = self._calculate_relationship_score(
                node_id, 
                query_params['relationships']
            )
            score += relationship_score
        
        # A small boost based on node connectivity (more connected = more important)
        connectivity_score = min(1.0, len(list(self.graph.neighbors(node_id))) / 10)
        score += connectivity_score * 0.5
        
        return score
    
    def _extract_node_date(self, node_data: Dict[str, Any]) -> Optional[int]:
        """
        Extract a date from node data for time-based filtering.
        
        Args:
            node_data: Node attributes
            
        Returns:
            Year as integer or None if no date found
        """
        # Try different date fields
        for field in ['date', 'year', 'start_date', 'end_date', 'created']:
            if field in node_data:
                value = node_data[field]
                # Handle ISO date strings
                if isinstance(value, str):
                    # Try to extract just the year
                    import re
                    year_match = re.search(r'(\d{4})', value)
                    if year_match:
                        return int(year_match.group(1))
                # Handle numeric year
                elif isinstance(value, int):
                    return value
        return None
    
    def _check_location_match(self, node_id: str, location: str) -> bool:
        """
        Check if node is related to the specified location.
        
        Args:
            node_id: Node to check
            location: Location string from query
            
        Returns:
            True if there's a match, False otherwise
        """
        node_data = self.graph.nodes[node_id]
        
        # Check direct location attributes
        for field in ['location', 'address', 'city', 'region']:
            if field in node_data:
                if isinstance(node_data[field], str) and location.lower() in node_data[field].lower():
                    return True
        
        # Check for connected location nodes
        for neighbor in self.graph.neighbors(node_id):
            neighbor_data = self.graph.nodes[neighbor]
            if neighbor_data.get('type') == NodeType.LOCATION:
                for field in ['name', 'label']:
                    if field in neighbor_data:
                        if isinstance(neighbor_data[field], str) and location.lower() in neighbor_data[field].lower():
                            return True
        
        return False
    
    def _calculate_keyword_score(self, node_data: Dict[str, Any], 
                                 keywords: List[str]) -> float:
        """
        Calculate node score based on keyword matches.
        
        Args:
            node_data: Node attributes
            keywords: List of keywords from query
            
        Returns:
            Keyword match score
        """
        if not keywords:
            return 0.0
        
        score = 0.0
        
        # Check all text fields for keyword matches
        text_fields = ['name', 'label', 'description', 'summary', 'title', 'content']
        
        for field in text_fields:
            if field in node_data and isinstance(node_data[field], str):
                field_text = node_data[field].lower()
                for keyword in keywords:
                    if keyword.lower() in field_text:
                        # Weight by field importance
                        if field in ['name', 'label', 'title']:
                            score += 1.0  # Higher weight for title fields
                        else:
                            score += 0.5  # Lower weight for description fields
        
        # Normalize by number of keywords
        score = score / len(keywords) if keywords else 0
        return min(3.0, score)  # Cap at 3.0
    
    def _calculate_relationship_score(self, node_id: str, 
                                     relationships: Dict[str, str]) -> float:
        """
        Calculate score based on relationship matches.
        
        Args:
            node_id: Node to check
            relationships: Dictionary of relationship types and target entities
            
        Returns:
            Relationship match score
        """
        if not relationships:
            return 0.0
        
        score = 0.0
        
        # Check each specified relationship
        for rel_type, target in relationships.items():
            # Check edges for matching relationship types
            for _, target_id, edge_data in self.graph.out_edges(node_id, data=True):
                # Match relationship type
                if edge_data.get('type', '').lower() == rel_type.lower():
                    target_node = self.graph.nodes[target_id]
                    # Check if target matches
                    if (target_node.get('name', '').lower() == target.lower() or
                        target_node.get('label', '').lower() == target.lower()):
                        score += 2.0  # Strong match
                        break
        
        return score
    
    def _get_node_connections(self, node_id: str, 
                             max_connections: int = 5) -> List[Dict[str, Any]]:
        """
        Get important connections for a node to provide context.
        
        Args:
            node_id: Node to get connections for
            max_connections: Maximum number of connections to return
            
        Returns:
            List of connection information dictionaries
        """
        connections = []
        
        # Get both incoming and outgoing connections
        for direction, edge_function in [
            ('outgoing', self.graph.out_edges),
            ('incoming', self.graph.in_edges)
        ]:
            for edge in edge_function(node_id, data=True):
                if direction == 'outgoing':
                    _, target, edge_data = edge
                    connection_id = target
                else:
                    source, _, edge_data = edge
                    connection_id = source
                
                # Skip if this is the same node
                if connection_id == node_id:
                    continue
                
                # Get basic node info
                if connection_id in self.graph.nodes:
                    conn_data = self.graph.nodes[connection_id]
                    connections.append({
                        'id': connection_id,
                        'name': conn_data.get('name', '') or conn_data.get('label', ''),
                        'type': conn_data.get('type', 'unknown'),
                        'relationship': edge_data.get('type', ''),
                        'direction': direction
                    })
        
        # Sort by node importance (could use PageRank or other centrality measure)
        # For now, just return the first max_connections
        return connections[:max_connections]
    
    def _generate_highlights(self, node_id: str, 
                            query_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate text highlights for search results.
        
        Args:
            node_id: Node ID
            query_params: Query parameters
            
        Returns:
            Dictionary with highlight information
        """
        node_data = self.graph.nodes[node_id]
        highlights = {}
        
        # Only generate highlights if we have keywords
        if query_params.get('keywords'):
            keywords = query_params['keywords']
            
            # Look for matches in description or content fields
            for field in ['description', 'summary', 'content']:
                if field in node_data and isinstance(node_data[field], str):
                    text = node_data[field]
                    
                    # Find best snippet containing keywords
                    best_snippet = self._find_best_snippet(text, keywords)
                    if best_snippet:
                        highlights[field] = best_snippet
        
        return highlights
    
    def _find_best_snippet(self, text: str, keywords: List[str], 
                          context_size: int = 100) -> Optional[str]:
        """
        Find the best text snippet containing the most keywords.
        
        Args:
            text: Text to search in
            keywords: List of keywords to look for
            context_size: Character context around matches
            
        Returns:
            Best matching snippet or None if no match
        """
        if not text or not keywords:
            return None
            
        text_lower = text.lower()
        
        # Find positions of all keywords
        positions = []
        for keyword in keywords:
            keyword_lower = keyword.lower()
            start = 0
            while start < len(text_lower):
                pos = text_lower.find(keyword_lower, start)
                if pos == -1:
                    break
                positions.append((pos, keyword))
                start = pos + 1
        
        if not positions:
            return None
            
        # Sort positions
        positions.sort(key=lambda x: x[0])
        
        # Find best cluster of positions
        best_score = 0
        best_start = 0
        best_end = 0
        
        for i, (pos, _) in enumerate(positions):
            # Consider a window starting at this position
            window_end = pos + context_size
            
            # Count keywords in this window
            keywords_in_window = set()
            for j in range(i, len(positions)):
                if positions[j][0] <= window_end:
                    keywords_in_window.add(positions[j][1])
                else:
                    break
                    
            # Score is number of unique keywords
            score = len(keywords_in_window)
            
            if score > best_score:
                best_score = score
                best_start = max(0, pos - context_size//2)
                best_end = min(len(text), window_end + context_size//2)
        
        # Extract the snippet
        snippet = text[best_start:best_end]
        
        # Add ellipsis if needed
        if best_start > 0:
            snippet = f"...{snippet}"
        if best_end < len(text):
            snippet = f"{snippet}..."
            
        return snippet


# Factory function for easy instantiation
def create_searcher(graph_path: Optional[str] = None) -> KnowledgeGraphSearch:
    """
    Create and return a KnowledgeGraphSearch instance.
    
    Args:
        graph_path: Optional path to the graph data
        
    Returns:
        Configured KnowledgeGraphSearch instance
    """
    return KnowledgeGraphSearch(graph_path=graph_path) 