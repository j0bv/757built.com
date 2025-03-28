import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import schedule
import time
from dotenv import load_dotenv
import openai  # You'll need to install this package

# Load environment variables
load_dotenv()

class AIEnhancedCrawler:
    def __init__(self):
        self.data_dir = 'data'
        self.ensure_data_directory()
        # Initialize OpenAI API with key from environment variables
        openai.api_key = os.getenv('OPENAI_API_KEY')
        
    def ensure_data_directory(self):
        """Create data directory if it doesn't exist"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def fetch_page(self, url):
        """Fetch a webpage and return its content"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    def parse_content(self, html_content, technology_area):
        """Parse HTML content using BeautifulSoup"""
        if not html_content:
            return None
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract basic page content
        text_content = soup.get_text(strip=True)
        title = soup.title.string if soup.title else ''
        
        # Use AI to analyze and extract structured information
        structured_data = self.analyze_with_ai(text_content, title, technology_area)
        
        return structured_data

    def analyze_with_ai(self, text_content, title, technology_area):
        """Use AI to extract structured information about technology development"""
        try:
            # Formulate a prompt for the AI
            prompt = f"""
            Utilize the following web content to extract information about {technology_area}:
            
            Title: {title}
            
            Content: {text_content[:4000]}  # Limiting content length for API constraints
            
            Extract the following information:
            1. Key Role Players: Identify individuals, organizations, or companies leading or contributing to the development, research, or project.
            2. Technological Development: Gather information about specific technological advancements, innovations, or breakthroughs.
            3. Project Cost: Provide details on funding, project costs, or financial investments.
            4. Date of Information Release: Include the latest date of project updates, publications, or announcements.
            5. Event Location: Specify the geographical location where the development or research is taking place.
            6. Contact Information: Extract publicly accessible contact details for key role players.
            
            Format the response as a structured JSON object with these fields.
            """
            
            # Call the AI API
            response = openai.ChatCompletion.create(
                model="gpt-4",  # Use the appropriate model
                messages=[{"role": "system", "content": "You extract structured information about technology developments."},
                          {"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            # Parse the AI response
            ai_analysis = json.loads(response.choices[0].message.content)
            
            # Add metadata
            ai_analysis["meta"] = {
                "source_title": title,
                "extraction_date": datetime.now().isoformat(),
                "technology_area": technology_area
            }
            
            return ai_analysis
            
        except Exception as e:
            print(f"Error using AI for analysis: {e}")
            # Return basic structured data if AI processing fails
            return {
                "meta": {
                    "source_title": title,
                    "extraction_date": datetime.now().isoformat(),
                    "technology_area": technology_area,
                    "error": str(e)
                }
            }

    def save_data(self, data, filename):
        """Save scraped data to a JSON file"""
        filepath = os.path.join(self.data_dir, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"AI-enhanced data saved to {filepath}")
        except Exception as e:
            print(f"Error saving data: {e}")

    def crawl_website(self, url, technology_area, filename=None):
        """Main crawling function with AI analysis for specific technology areas"""
        print(f"Crawling {url} for information about {technology_area}...")
        
        if filename is None:
            # Generate filename based on technology area and timestamp
            safe_tech_name = technology_area.replace(" ", "_").lower()
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"{safe_tech_name}_{timestamp}.json"
        
        html_content = self.fetch_page(url)
        if html_content:
            data = self.parse_content(html_content, technology_area)
            if data:
                self.save_data(data, filename)
                return data
        return None

    def crawl_multiple_sources(self, technology_area, urls):
        """Crawl multiple sources for a given technology area and consolidate results"""
        print(f"Starting comprehensive search for: {technology_area}")
        all_results = []
        
        for url in urls:
            result = self.crawl_website(url, technology_area)
            if result:
                all_results.append(result)
        
        # Consolidate results using AI
        if all_results:
            consolidated = self.consolidate_findings(all_results, technology_area)
            # Save consolidated findings
            safe_tech_name = technology_area.replace(" ", "_").lower()
            timestamp = datetime.now().strftime("%Y%m%d")
            self.save_data(consolidated, f"{safe_tech_name}_consolidated_{timestamp}.json")
            return consolidated
        
        return None
    
    def consolidate_findings(self, results, technology_area):
        """Use AI to consolidate findings from multiple sources"""
        try:
            # Convert results to a string representation for the prompt
            results_str = json.dumps(results, indent=2)
            
            prompt = f"""
            Consolidate the following research findings about {technology_area} from multiple sources:
            
            {results_str[:7000]}  # Limit content length for API constraints
            
            Create a comprehensive summary that reconciles any conflicts in the data and provides the most accurate, up-to-date information about:
            1. Key Role Players
            2. Technological Development
            3. Project Cost
            4. Date of Information Release
            5. Event Location
            6. Contact Information
            
            Format the response as a structured JSON object with these fields.
            """
            
            # Call the AI API
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "system", "content": "You consolidate research findings from multiple sources."},
                          {"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            # Parse the AI response
            consolidated = json.loads(response.choices[0].message.content)
            
            # Add metadata
            consolidated["meta"] = {
                "consolidation_date": datetime.now().isoformat(),
                "technology_area": technology_area,
                "number_of_sources": len(results)
            }
            
            return consolidated
            
        except Exception as e:
            print(f"Error consolidating findings: {e}")
            return {
                "error": "Failed to consolidate findings",
                "message": str(e),
                "raw_results": results
            }

def main():
    # Initialize the AI-enhanced crawler
    crawler = AIEnhancedCrawler()
    
    # Define your target technology areas and relevant websites
    technology_search_mapping = {
        "Quantum Computing in Hampton Roads": [
            "https://www.jeffersonlab.org",
            "https://www.odu.edu/physics",
            "https://www.nasa.gov/langley"
        ],
        "Renewable Energy Projects in Virginia Beach": [
            "https://virginiabeach.gov/departments/public-utilities/sustainable-energy",
            "https://www.dominionenergy.com/projects-and-facilities/offshore-wind-facilities"
        ],
        # Add more technology areas and sources as needed
    }
    
    def crawl_job():
        for tech_area, urls in technology_search_mapping.items():
            crawler.crawl_multiple_sources(tech_area, urls)
    
    # Schedule the crawler to run daily
    schedule.every().day.at("02:00").do(crawl_job)  # Run at 2 AM
    
    # Run the crawler immediately if needed
    # crawl_job()
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main() 