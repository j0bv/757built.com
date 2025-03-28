import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DirectPhiCrawler:
    def __init__(self):
        # Local Ollama endpoint
        self.ollama_endpoint = os.getenv('OLLAMA_ENDPOINT', 'http://localhost:11434/api/generate')
        self.data_dir = 'data'
        
        # Ensure data directory exists
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def fetch_page(self, url):
        """Fetch a webpage and return its content"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    def analyze_with_phi3(self, text_content, title, technology_area):
        """Use local Phi3 to extract structured information"""
        try:
            # Prepare the prompt
            prompt = f"""
            You are an AI assistant specialized in extracting structured information about technology developments.
            
            Task: Analyze the following web content about {technology_area} and extract specific information.
            
            Title: {title}
            
            Content: {text_content[:3000]}
            
            Extract and format the following information as JSON:
            1. Key Role Players: Identify individuals, organizations, or companies leading the development.
            2. Technological Development: Describe specific technological advancements or innovations.
            3. Project Cost: Provide details on funding or financial investments if available.
            4. Date of Information Release: Include the latest date of updates or announcements.
            5. Event Location: Specify the geographical location of the development.
            6. Contact Information: Extract publicly accessible contact details if available.
            
            If information for a category is not found, indicate with "Not found in source".
            Format your response STRICTLY as a valid JSON object with these fields and nothing else.
            """
            
            # Prepare the request payload
            payload = {
                "model": "phi3",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9
                }
            }
            
            # Send the request
            response = requests.post(self.ollama_endpoint, json=payload)
            response.raise_for_status()
            
            # Parse the response
            result = response.json()
            
            # Try to extract JSON from the response
            try:
                json_data = json.loads(result['response'])
            except json.JSONDecodeError:
                # Try to extract JSON using regex if the response isn't pure JSON
                import re
                json_match = re.search(r'(\{.*\})', result['response'], re.DOTALL)
                if json_match:
                    json_data = json.loads(json_match.group(1))
                else:
                    raise Exception("Could not extract JSON from model response")
            
            # Add metadata
            json_data["meta"] = {
                "source_title": title,
                "extraction_date": datetime.now().isoformat(),
                "technology_area": technology_area,
                "model": "phi3"
            }
            
            return json_data
            
        except Exception as e:
            print(f"Error using Phi3 for analysis: {e}")
            # Return basic structured data if AI processing fails
            return {
                "Key Role Players": "Error during extraction",
                "Technological Development": "Error during extraction",
                "Project Cost": "Error during extraction",
                "Date of Information Release": "Error during extraction",
                "Event Location": "Error during extraction",
                "Contact Information": "Error during extraction",
                "meta": {
                    "source_title": title,
                    "extraction_date": datetime.now().isoformat(),
                    "technology_area": technology_area,
                    "error": str(e),
                    "model": "phi3"
                }
            }

    def consolidate_findings(self, results, technology_area):
        """Use Phi3 to consolidate findings from multiple sources"""
        try:
            # Simplify results to avoid token limits
            simplified_results = []
            for result in results:
                simplified = {
                    "Key Role Players": result.get("Key Role Players", "Not found"),
                    "Technological Development": result.get("Technological Development", "Not found"),
                    "Project Cost": result.get("Project Cost", "Not found"),
                    "Date of Information Release": result.get("Date of Information Release", "Not found"),
                    "Event Location": result.get("Event Location", "Not found"),
                    "Contact Information": result.get("Contact Information", "Not found"),
                    "Source": result.get("meta", {}).get("source_title", "Unknown source")
                }
                simplified_results.append(simplified)
            
            results_str = json.dumps(simplified_results, indent=2)
            
            # Prepare the prompt for consolidation
            prompt = f"""
            You are an AI assistant specialized in consolidating research findings from multiple sources.
            
            Task: Analyze the following research findings about {technology_area} extracted from multiple sources.
            
            Sources Data:
            {results_str}
            
            Create a comprehensive summary that reconciles any conflicts and provides the most accurate information about:
            1. Key Role Players
            2. Technological Development
            3. Project Cost
            4. Date of Information Release
            5. Event Location
            6. Contact Information
            
            Format your response STRICTLY as a valid JSON object with these fields and nothing else.
            For each field, include all relevant information from all sources without redundancy.
            """
            
            # Prepare the request payload
            payload = {
                "model": "phi3",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9
                }
            }
            
            # Send the request
            response = requests.post(self.ollama_endpoint, json=payload)
            response.raise_for_status()
            
            # Parse the response
            result = response.json()
            
            # Try to extract JSON from the response
            try:
                consolidated = json.loads(result['response'])
            except json.JSONDecodeError:
                # Try to extract JSON using regex
                import re
                json_match = re.search(r'(\{.*\})', result['response'], re.DOTALL)
                if json_match:
                    consolidated = json.loads(json_match.group(1))
                else:
                    raise Exception("Could not extract JSON from model response")
            
            # Add metadata
            consolidated["meta"] = {
                "consolidation_date": datetime.now().isoformat(),
                "technology_area": technology_area,
                "number_of_sources": len(results),
                "model": "phi3"
            }
            
            return consolidated
            
        except Exception as e:
            print(f"Error consolidating findings with Phi3: {e}")
            return {
                "error": "Failed to consolidate findings",
                "message": str(e),
                "model": "phi3"
            }

    def save_data(self, data, filename):
        """Save the data to a JSON file"""
        filepath = os.path.join(self.data_dir, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Data saved to {filepath}")
            return True
        except Exception as e:
            print(f"Error saving data: {e}")
            return False

    def crawl_website(self, url, technology_area):
        """Crawl a website and extract information using Phi3"""
        print(f"Crawling {url} for information about {technology_area}...")
        
        # Generate filename based on URL and technology area
        domain = url.replace('https://', '').replace('http://', '').split('/')[0]
        safe_tech_name = technology_area.replace(' ', '_').lower()
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{safe_tech_name}_{domain}_{timestamp}.json"
        
        # Fetch and analyze the content
        html_content = self.fetch_page(url)
        if html_content:
            soup = BeautifulSoup(html_content, 'html.parser')
            text_content = soup.get_text(strip=True)
            title = soup.title.string if soup.title else domain
            
            # Analyze with Phi3
            data = self.analyze_with_phi3(text_content, title, technology_area)
            if data:
                # Save the data
                self.save_data(data, filename)
                return data
        
        return None

    def crawl_multiple_sources(self, technology_area, urls):
        """Crawl multiple sources and consolidate results"""
        print(f"Starting comprehensive search for: {technology_area}")
        all_results = []
        
        for url in urls:
            result = self.crawl_website(url, technology_area)
            if result:
                all_results.append(result)
                # Small delay to avoid overloading local resources
                time.sleep(2)
        
        # Consolidate results if we have any
        if all_results:
            print(f"Consolidating {len(all_results)} results for {technology_area}...")
            consolidated = self.consolidate_findings(all_results, technology_area)
            
            # Save consolidated findings
            if consolidated:
                safe_tech_name = technology_area.replace(' ', '_').lower()
                timestamp = datetime.now().strftime("%Y%m%d")
                filename = f"{safe_tech_name}_consolidated_{timestamp}.json"
                self.save_data(consolidated, filename)
            
            return consolidated
        
        return None


def main():
    # Initialize the crawler
    crawler = DirectPhiCrawler()
    
    # Define technology areas and sources to crawl
    technology_search_mapping = {
        "Quantum Computing in Hampton Roads": [
            "https://www.jeffersonlab.org",
            "https://www.odu.edu/physics/research",
            "https://www.nasa.gov/langley-research-center"
        ],
        "Renewable Energy Projects in Virginia Beach": [
            "https://www.virginiabeach.gov/services/sustainability-environment",
            "https://www.dominionenergy.com/projects-and-facilities/offshore-wind-facilities"
        ],
        "Cybersecurity Initiatives in Norfolk": [
            "https://www.norfolk.gov",
            "https://www.nrfk.navy.mil",
            "https://securityboulevard.com/tag/hampton-roads/"
        ],
        "Maritime Technology in Hampton Roads": [
            "https://www.hrp.org",
            "https://www.marinelink.com/news/virginia",
            "https://hrmffa.org/maritime-innovation"
        ]
    }
    
    # Run the crawling process
    for tech_area, urls in technology_search_mapping.items():
        print(f"\n=== Processing: {tech_area} ===")
        crawler.crawl_multiple_sources(tech_area, urls)
        print(f"=== Completed: {tech_area} ===\n")
        time.sleep(5)  # Pause between technology areas


if __name__ == "__main__":
    main() 