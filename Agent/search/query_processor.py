"""
Query processor for natural language search queries.

This module handles parsing, understanding and processing of natural language
search queries, breaking them into structured components for knowledge graph queries.
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class QueryProcessor:
    """Processes natural language queries for the 757Built search system."""
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the query processor.
        
        Args:
            model_path: Optional path to Phi-3 model for enhanced query understanding
        """
        self.model_path = model_path
        self.entity_types = ["project", "organization", "person", "location", "patent", "research"]
        self.time_patterns = [
            r"since\s+(\d{4})",
            r"before\s+(\d{4})",
            r"in\s+(\d{4})",
            r"between\s+(\d{4})\s+and\s+(\d{4})"
        ]
        
        # Load Phi-3 model if path provided
        self.phi3_processor = None
        if model_path:
            try:
                from ..phi3_wrapper import Phi3Processor
                self.phi3_processor = Phi3Processor(model_path=model_path)
                logger.info(f"Loaded Phi-3 model from {model_path}")
            except Exception as e:
                logger.warning(f"Could not load Phi-3 model: {e}")
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a natural language query into structured components.
        
        Args:
            query: The natural language query string
            
        Returns:
            Dictionary containing extracted search parameters
        """
        # Default to basic processing
        if not self.phi3_processor:
            return self._basic_query_processing(query)
        
        # Use advanced Phi-3 based processing
        return self._advanced_query_processing(query)
    
    def _basic_query_processing(self, query: str) -> Dict[str, Any]:
        """
        Basic rule-based query processing without ML.
        
        Args:
            query: The natural language query string
            
        Returns:
            Dictionary containing extracted search parameters
        """
        # Normalize query
        query = query.lower().strip()
        
        # Extract potential entity types
        entity_type = None
        for etype in self.entity_types:
            if etype in query or f"{etype}s" in query:
                entity_type = etype
                break
        
        # Extract time constraints
        time_range = None
        for pattern in self.time_patterns:
            matches = re.search(pattern, query)
            if matches:
                if len(matches.groups()) == 1:
                    year = int(matches.group(1))
                    if "since" in query:
                        time_range = {"start": year, "end": None}
                    elif "before" in query:
                        time_range = {"start": None, "end": year}
                    else:  # "in"
                        time_range = {"start": year, "end": year}
                elif len(matches.groups()) == 2:
                    time_range = {
                        "start": int(matches.group(1)),
                        "end": int(matches.group(2))
                    }
                break
        
        # Extract locations
        location = None
        location_patterns = [
            r"in\s+([A-Za-z\s]+)",
            r"near\s+([A-Za-z\s]+)",
            r"around\s+([A-Za-z\s]+)"
        ]
        
        for pattern in location_patterns:
            matches = re.search(pattern, query)
            if matches and matches.group(1).lower() not in ["the", "a", "an"]:
                location = matches.group(1).strip()
                break
        
        # Extract keywords (remaining significant terms)
        stop_words = ["the", "and", "or", "in", "near", "with", "by", "to", 
                     "from", "since", "before", "between", "related", "about"]
        
        keywords = query.split()
        keywords = [word for word in keywords 
                   if word not in stop_words 
                   and not any(p in word for p in [".", ",", "!", "?"])]
        
        return {
            "original_query": query,
            "entity_type": entity_type,
            "time_range": time_range,
            "location": location,
            "keywords": keywords
        }
    
    def _advanced_query_processing(self, query: str) -> Dict[str, Any]:
        """
        Advanced query processing using Phi-3 model.
        
        Args:
            query: The natural language query string
            
        Returns:
            Dictionary containing extracted search parameters with higher accuracy
        """
        # Prepare prompt for Phi-3
        prompt = f"""
        You are an AI assistant that extracts structured search parameters from natural language queries.
        
        Analyze the following search query and extract the key components in JSON format:
        
        Query: {query}
        
        Extract and return a JSON object with these fields:
        - entity_type: The type of entity being searched for (project, organization, person, location, patent, research)
        - time_range: A JSON object with "start" and "end" years if specified
        - location: Any geographic location mentioned in the query
        - keywords: Important search terms
        - relationships: Any relationships between entities (e.g., "funded by", "connected to")
        
        Only include fields if they are present in the query. Return valid JSON only.
        """
        
        # Get Phi-3 response
        response = self.phi3_processor.run_inference(prompt)
        
        # Parse the JSON response
        try:
            # Extract JSON from response (handling potential markdown/code blocks)
            json_match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", response)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response.strip()
            
            result = json.loads(json_str)
            
            # Add original query for reference
            result["original_query"] = query
            return result
            
        except json.JSONDecodeError:
            logger.warning(f"Could not parse Phi-3 response as JSON: {response}")
            # Fall back to basic processing
            return self._basic_query_processing(query)

    def decompose_complex_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Decompose a complex multi-part query into separate sub-queries.
        
        Args:
            query: A potentially complex query that might need multiple search steps
            
        Returns:
            List of structured query components that should be executed in sequence
        """
        # Check if this is potentially a multi-step query
        if "and then" in query.lower() or ";" in query or "after that" in query.lower():
            parts = re.split(r";\s*|and then|after that", query, flags=re.IGNORECASE)
            return [self.process_query(part.strip()) for part in parts]
        
        # This is a single query
        return [self.process_query(query)]


# Factory function for easy instantiation
def create_processor(model_path: Optional[str] = None) -> QueryProcessor:
    """
    Create and return a QueryProcessor instance.
    
    Args:
        model_path: Optional path to Phi-3 model
        
    Returns:
        Configured QueryProcessor instance
    """
    return QueryProcessor(model_path=model_path) 