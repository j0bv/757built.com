#!/usr/bin/env python3
import os
import json
import subprocess
import logging
import re
from typing import Dict, List, Optional, Tuple, Union, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("phi3_analysis.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("phi3_wrapper")

class Phi3Processor:
    """
    Wrapper for the quantized Phi-3 model using llama.cpp
    """
    def __init__(
        self, 
        model_path: str = "./path/to/phi3-q3_k_l.gguf", 
        threads: int = 6, 
        gpu_layers: int = 0, 
        ctx_size: int = 4096,
        llama_executable: str = "./main"
    ):
        self.model_path = model_path
        self.threads = threads
        self.gpu_layers = gpu_layers
        self.ctx_size = ctx_size
        self.llama_executable = llama_executable
        
        # Validate model path exists
        if not os.path.exists(model_path):
            logger.warning(f"Model path does not exist: {model_path}")

    def _run_model(self, prompt: str, max_tokens: int = 1024) -> str:
        """
        Run the quantized Phi-3 model with a prompt and return the response
        """
        try:
            # Prepare the command
            cmd = [
                self.llama_executable,
                "-m", self.model_path,
                "-t", str(self.threads),
                "--n-gpu-layers", str(self.gpu_layers),
                "--ctx-size", str(self.ctx_size),
                "-n", str(max_tokens),
                "-p", prompt
            ]
            
            logger.info(f"Running Phi-3 with prompt: {prompt[:100]}...")
            
            # Execute the command
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            # Process the output - remove the prompt from the response
            output = result.stdout
            if prompt in output:
                output = output.split(prompt, 1)[1]
            
            return output.strip()
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running Phi-3 model: {e}")
            logger.error(f"stderr: {e.stderr}")
            return ""
        except Exception as e:
            logger.error(f"Unexpected error running Phi-3 model: {e}")
            return ""

    def extract_coordinates(self, text: str) -> List[Dict[str, Union[str, float]]]:
        """
        Extract geographic coordinates from text using Phi-3
        
        Returns a list of locations with coordinates:
        [
            {"name": "Hampton University", "lat": 37.0209, "lng": -76.3367},
            ...
        ]
        """
        prompt = f"""
Extract all geographic locations and their coordinates from the following text, focusing only on locations in Southeastern Virginia (757 area code). 
If coordinates aren't directly mentioned, don't invent them; just extract the location names.
Return the results as a JSON array of objects with "name", "lat", and "lng" fields.

Text: {text}

JSON Result:
"""
        
        try:
            response = self._run_model(prompt)
            
            # Try to extract JSON array from the response
            json_match = re.search(r'\[.*?\]', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                locations = json.loads(json_str)
                return locations
            else:
                logger.warning("No JSON array found in the response")
                return []
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            logger.error(f"Response: {response}")
            return []
        except Exception as e:
            logger.error(f"Error extracting coordinates: {e}")
            return []

    def extract_funding_info(self, text: str) -> Dict[str, Any]:
        """
        Extract funding information from text using Phi-3
        
        Returns a dictionary with total funding, sources, periods, and grant numbers
        """
        prompt = f"""
Extract comprehensive funding data from the following text.

Return a JSON object with this schema:
{{
  "award_number": "",
  "program_name": "",            // immediate program name (e.g., BUILD Grants 2024)
  "parent_fund": "",              // overarching fund or legislation (e.g., IIJA, ARPA-H)
  "amount_usd": 0,
  "fiscal_year": "",
  "related_awards": [              // other awards from the same program in the 757 region
    {{"award_number": "", "recipient": "", "amount_usd": 0}}
  ]
}}
If an item is unknown, leave it blank or 0.  Do not invent data.

Text: {text}

JSON Result:
"""
        
        try:
            response = self._run_model(prompt)
            
            # Try to extract JSON object from the response
            json_match = re.search(r'\{.*?\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                funding = json.loads(json_str)
                return funding
            else:
                logger.warning("No JSON object found in the response")
                return {
                    "award_number": "",
                    "program_name": "",
                    "parent_fund": "",
                    "amount_usd": 0,
                    "fiscal_year": "",
                    "related_awards": []
                }
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            logger.error(f"Response: {response}")
            return {
                "award_number": "",
                "program_name": "",
                "parent_fund": "",
                "amount_usd": 0,
                "fiscal_year": "",
                "related_awards": []
            }
        except Exception as e:
            logger.error(f"Error extracting funding info: {e}")
            return {
                "award_number": "",
                "program_name": "",
                "parent_fund": "",
                "amount_usd": 0,
                "fiscal_year": "",
                "related_awards": []
            }

    def extract_key_entities(self, text: str) -> Dict[str, List[Dict[str, str]]]:
        """
        Extract key entities from text using Phi-3
        
        Returns a dictionary with categorized entities:
        {
            "people": [{"name": "Dr. John Smith", "role": "Principal Investigator"}],
            "organizations": [{"name": "Old Dominion University", "role": "Research Institution"}],
            "companies": [{"name": "Newport News Shipbuilding", "role": "Contractor"}]
        }
        """
        prompt = f"""
Extract all key entities from the following text, focusing on those related to Southeastern Virginia (757 area code).
Categorize each entity and identify their role in the project:

1. People (researchers, officials, contractors)
2. Organizations (universities, government agencies)
3. Companies (contractors, subcontractors)

Return the results as a JSON object with "people", "organizations", and "companies" arrays, each containing objects with "name" and "role" fields.

Text: {text}

JSON Result:
"""
        
        try:
            response = self._run_model(prompt)
            
            # Try to extract JSON object from the response
            json_match = re.search(r'\{.*?\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                entities = json.loads(json_str)
                return entities
            else:
                logger.warning("No JSON object found in the response")
                return {
                    "people": [],
                    "organizations": [],
                    "companies": []
                }
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            logger.error(f"Response: {response}")
            return {
                "people": [],
                "organizations": [],
                "companies": []
            }
        except Exception as e:
            logger.error(f"Error extracting key entities: {e}")
            return {
                "people": [],
                "organizations": [],
                "companies": []
            }
    
    def classify_document_type(self, text: str) -> str:
        """
        Classify the document type using Phi-3
        
        Returns a document type string:
        - "research_paper"
        - "patent"
        - "construction_document"
        - "government_report"
        - "grant_proposal"
        - "other"
        """
        prompt = f"""
Classify the following document into one of these categories:
- research_paper
- patent
- construction_document
- government_report
- grant_proposal
- other

Return ONLY the category name without explanation.

Text: {text[:2000]}

Category:
"""
        
        try:
            response = self._run_model(prompt, max_tokens=100)
            # Clean up response to only return the category
            for category in ["research_paper", "patent", "construction_document", 
                            "government_report", "grant_proposal", "other"]:
                if category.lower() in response.lower():
                    return category
            
            return "other"
        except Exception as e:
            logger.error(f"Error classifying document: {e}")
            return "other"
    
    def extract_project_summary(self, text: str) -> Dict[str, str]:
        """
        Extract a concise project summary using Phi-3
        
        Returns a dictionary with project details:
        {
            "title": "Hampton Roads Bridge-Tunnel Expansion",
            "summary": "...",
            "start_date": "2023-01",
            "end_date": "2025-12",
            "status": "In Progress"
        }
        """
        prompt = f"""
Extract a concise summary of the project or research described in the following text.
Focus on:
1. Project title
2. Brief summary (2-3 sentences)
3. Start date (if mentioned)
4. End date or expected completion (if mentioned)
5. Current status (Not Started, In Progress, Completed, etc.)

Return the results as a JSON object with "title", "summary", "start_date", "end_date", and "status" fields.

Text: {text[:3000]}

JSON Result:
"""
        
        try:
            response = self._run_model(prompt)
            
            # Try to extract JSON object from the response
            json_match = re.search(r'\{.*?\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                summary = json.loads(json_str)
                return summary
            else:
                logger.warning("No JSON object found in the response")
                return {
                    "title": "",
                    "summary": "",
                    "start_date": "",
                    "end_date": "",
                    "status": ""
                }
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            logger.error(f"Response: {response}")
            return {
                "title": "",
                "summary": "",
                "start_date": "",
                "end_date": "",
                "status": ""
            }
        except Exception as e:
            logger.error(f"Error extracting project summary: {e}")
            return {
                "title": "",
                "summary": "",
                "start_date": "",
                "end_date": "",
                "status": ""
            }
    
    def identify_relationships(self, text: str) -> List[Dict[str, str]]:
        """
        Identify relationships between entities mentioned in the text
        
        Returns a list of relationships:
        [
            {"source": "ODU", "target": "NASA Langley", "relationship": "research_partnership"},
            ...
        ]
        """
        prompt = f"""
Identify all relationships between entities (people, organizations, companies) mentioned in the following text.
For each relationship, specify:
1. Source entity
2. Target entity
3. Type of relationship (funding, partnership, contractor, employment, etc.)

Return the results as a JSON array of objects with "source", "target", and "relationship" fields.

Text: {text}

JSON Result:
"""
        
        try:
            response = self._run_model(prompt)
            
            # Try to extract JSON array from the response
            json_match = re.search(r'\[.*?\]', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                relationships = json.loads(json_str)
                return relationships
            else:
                logger.warning("No JSON array found in the response")
                return []
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            logger.error(f"Response: {response}")
            return []
        except Exception as e:
            logger.error(f"Error identifying relationships: {e}")
            return []

    def extract_classifications(self, text: str) -> Dict[str, Any]:
        """Classify industry, subsector, NAICS, and technology areas."""
        prompt = f"""
You are an expert industry analyst. For the following text, identify:
1. Industry sectors (high-level, e.g., Construction, Transportation, Renewable Energy)
2. Subsectors (e.g., Highway Construction, Offshore Wind)
3. NAICS codes (as 6-digit strings) that best apply
4. Technology areas or research domains mentioned (short phrases)

Return a JSON object:
{{
  "industry": [],
  "subsector": [],
  "naics_codes": [],
  "technology_area": []
}}

Text: {text}

JSON Result:
"""
        try:
            response = self._run_model(prompt)
            json_match = re.search(r'\{.*?\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
        except Exception:
            pass
        return {"industry": [], "subsector": [], "naics_codes": [], "technology_area": []}

    def process_document(self, document_path: str) -> Dict:
        """
        Process a document using all extraction functions
        """
        try:
            # Read the document
            with open(document_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Get the basic document metadata
            doc_type = self.classify_document_type(text)
            project_summary = self.extract_project_summary(text)
            
            # Extract structured information
            locations = self.extract_coordinates(text)
            funding = self.extract_funding_info(text)
            entities = self.extract_key_entities(text)
            classifications = self.extract_classifications(text)
            relationships = self.identify_relationships(text)
            
            # Combine all information
            document_analysis = {
                "document_path": document_path,
                "document_type": doc_type,
                "project": project_summary,
                "locations": locations,
                "funding": funding,
                "entities": entities,
                "classifications": classifications,
                "relationships": relationships
            }
            
            logger.info(f"Completed analysis of {document_path}")
            return document_analysis
            
        except Exception as e:
            logger.error(f"Error processing document {document_path}: {e}")
            return {
                "document_path": document_path,
                "error": str(e)
            }

if __name__ == "__main__":
    # Example usage
    processor = Phi3Processor(
        model_path="/path/to/phi3-q3_k_l.gguf",
        threads=6,
        gpu_layers=0,
        ctx_size=4096
    )
    
    # Test with a sample file
    result = processor.process_document("sample_document.txt")
    print(json.dumps(result, indent=2))
