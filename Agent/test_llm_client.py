#!/usr/bin/env python3
"""Test script for the LLM client.

This script tests the LLM client with different backend configurations:
1. Phi-3 via llama.cpp
2. Llama-3 via OpenAI-compatible API

Usage:
    python test_llm_client.py --type phi3 --model-path /path/to/phi3.gguf --llama-path /path/to/llama.cpp
    python test_llm_client.py --type openai_compatible --api-base http://localhost:8000/v1 --model llama-3-70b-instruct
"""

import os
import argparse
import json
import logging
from llm_client import LLMClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_llm_client")

# Test prompts
SIMPLE_PROMPT = "What is the capital of Virginia? Keep your answer brief."

ENTITY_EXTRACTION_PROMPT = """
Extract key organizations mentioned in the following text. Return the result as a JSON array of objects, each with "name" and "type" fields.

Text: William & Mary's Virginia Institute of Marine Science (VIMS) received a $1.2M grant from the National Science Foundation (NSF) to study coastal resilience in Hampton Roads. The project is in partnership with Old Dominion University (ODU) and will focus on sea level rise impacts in Norfolk and Virginia Beach.

Expected format:
[
  {"name": "William & Mary's Virginia Institute of Marine Science", "type": "research_institution"},
  {"name": "National Science Foundation", "type": "funding_agency"}
]
"""

RELATIONSHIP_PROMPT = """
Identify relationships between entities in this text. Return the result as a JSON array with "source", "target", and "relationship" fields.

Text: Newport News Shipbuilding, a division of Huntington Ingalls Industries, partnered with Dominion Energy on offshore wind projects. The shipyard will supply steel components for turbine foundations that will be installed off the coast of Virginia Beach by 2026.

Expected format:
[
  {"source": "Newport News Shipbuilding", "target": "Huntington Ingalls Industries", "relationship": "division_of"},
  {"source": "Newport News Shipbuilding", "target": "Dominion Energy", "relationship": "partnered_with"}
]
"""

def main():
    parser = argparse.ArgumentParser(description="Test the LLM client with different backends")
    
    # Add arguments
    parser.add_argument("--type", choices=["phi3", "openai", "openai_compatible"], 
                        default=os.getenv("LLM_TYPE", "phi3"),
                        help="LLM backend type")
    parser.add_argument("--model-path", default=os.getenv("MODEL_PATH", ""),
                        help="Path to the model file (for phi3)")
    parser.add_argument("--llama-path", default=os.getenv("LLAMA_PATH", ""),
                        help="Path to the llama.cpp executable (for phi3)")
    parser.add_argument("--api-key", default=os.getenv("OPENAI_API_KEY", ""),
                        help="API key (for OpenAI)")
    parser.add_argument("--api-base", default=os.getenv("OPENAI_API_BASE", ""),
                        help="API base URL")
    parser.add_argument("--model", default=os.getenv("LLM_MODEL", "gpt-3.5-turbo"),
                        help="Model identifier (for OpenAI/compatible)")
    parser.add_argument("--temperature", type=float, default=0.2,
                        help="Sampling temperature")
    
    args = parser.parse_args()
    
    # Create the client
    llm_client = LLMClient(
        llm_type=args.type,
        model_path=args.model_path,
        llama_executable=args.llama_path,
        api_key=args.api_key,
        api_base=args.api_base,
        model=args.model,
        temperature=args.temperature
    )
    
    # Run tests
    run_test(llm_client, "Simple Question", SIMPLE_PROMPT)
    run_test(llm_client, "Entity Extraction", ENTITY_EXTRACTION_PROMPT)
    run_test(llm_client, "Relationship Extraction", RELATIONSHIP_PROMPT)

def run_test(client, test_name, prompt):
    """Run a test with the given client and prompt."""
    logger.info(f"Running test: {test_name}")
    logger.info(f"Prompt: {prompt.strip()[:100]}...")
    
    # Generate response
    response = client.generate(prompt)
    
    logger.info(f"Response: {response}")
    logger.info("-" * 80)
    
    # For JSON responses, try to validate the JSON
    if "Expected format:" in prompt and "[" in response:
        try:
            json_start = response.find("[")
            json_end = response.rfind("]") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                parsed = json.loads(json_str)
                logger.info(f"Successfully parsed JSON response: {len(parsed)} items")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")

if __name__ == "__main__":
    main() 