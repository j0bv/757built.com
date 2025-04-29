import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import schedule
import time
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
import sys
import logging

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

class AIEnhancedCrawler:
    def __init__(self):
        # Ollama endpoint configuration
        self.ollama_endpoint = os.getenv('OLLAMA_ENDPOINT', 'http://localhost:11434/api/generate')
        
        # Database configuration
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'your_database_name'),
            'user': os.getenv('DB_USER', 'your_database_user'),
            'password': os.getenv('DB_PASSWORD')
        }
        
        # Validate configuration
        if not self.db_config['password']:
            logger.error("Database password not set. Please configure DB_PASSWORD environment variable.")
            sys.exit(1)
        
        # Ensure database tables exist
        self.init_database()
        
    def init_database(self):
        """Initialize database connection and ensure tables exist"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Check if tables exist and create them if needed
            # (The actual CREATE TABLE statements would be here)
            
            cursor.close()
            conn.close()
            print("Database initialized successfully")
        except Error as e:
            print(f"Database initialization error: {e}")
    
    def get_db_connection(self):
        """Get a database connection"""
        try:
            return mysql.connector.connect(**self.db_config)
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            return None
    
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
        """Use Phi3 via API to extract structured information"""
        try:
            # API endpoint on your web server that connects to Ollama
            api_url = "https://757built.com/api/ai_analysis"
            
            # Prepare data for the request
            data = {
                "text": text_content[:3000],  # Limit text length
                "technology_area": technology_area
            }
            
            # Make the request
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {os.getenv('AI_API_KEY')}"
            }
            
            response = requests.post(api_url, json=data, headers=headers)
            response.raise_for_status()
            
            # Parse the response
            result = response.json()
            
            if result['status'] == 'success':
                # Add metadata
                result['data']["meta"] = {
                    "source_title": title,
                    "extraction_date": datetime.now().isoformat(),
                    "technology_area": technology_area
                }
                return result['data']
            else:
                raise Exception(f"API error: {result.get('message', 'Unknown error')}")
            
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

    def save_to_database(self, data, url, technology_area_name):
        """Save the extracted data to MySQL database"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return False
                
            cursor = conn.cursor()
            
            # Get technology area ID (or create if doesn't exist)
            cursor.execute(
                "SELECT id FROM technology_areas WHERE name = %s", 
                (technology_area_name,)
            )
            result = cursor.fetchone()
            
            if result:
                tech_area_id = result[0]
            else:
                # Create new technology area
                tech_slug = technology_area_name.lower().replace(' ', '-')
                cursor.execute(
                    "INSERT INTO technology_areas (name, slug) VALUES (%s, %s)",
                    (technology_area_name, tech_slug)
                )
                tech_area_id = cursor.lastrowid
            
            # Check if we already have data for this URL and technology
            cursor.execute(
                "SELECT id FROM technology_developments WHERE source_url = %s AND technology_area_id = %s",
                (url, tech_area_id)
            )
            result = cursor.fetchone()
            
            # Parse dates (handle various formats)
            info_date = None
            if data.get("Date of Information Release") and data["Date of Information Release"] != "Not found in source":
                try:
                    # Try to parse date in various formats
                    from dateutil import parser
                    info_date = parser.parse(data["Date of Information Release"]).strftime('%Y-%m-%d')
                except:
                    info_date = None
            
            if result:
                # Update existing record
                dev_id = result[0]
                cursor.execute("""
                    UPDATE technology_developments 
                    SET key_players = %s, technological_development = %s, 
                        project_cost = %s, information_date = %s,
                        event_location = %s, contact_information = %s,
                        source_title = %s, extraction_date = %s,
                        last_updated = NOW()
                    WHERE id = %s
                """, (
                    data.get("Key Role Players", ""),
                    data.get("Technological Development", ""),
                    data.get("Project Cost", ""),
                    info_date,
                    data.get("Event Location", ""),
                    data.get("Contact Information", ""),
                    data["meta"]["source_title"],
                    data["meta"]["extraction_date"],
                    dev_id
                ))
            else:
                # Insert new record
                cursor.execute("""
                    INSERT INTO technology_developments (
                        technology_area_id, source_url, source_title,
                        key_players, technological_development, project_cost,
                        information_date, event_location, contact_information,
                        extraction_date
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    tech_area_id, url, data["meta"]["source_title"],
                    data.get("Key Role Players", ""),
                    data.get("Technological Development", ""),
                    data.get("Project Cost", ""),
                    info_date,
                    data.get("Event Location", ""),
                    data.get("Contact Information", ""),
                    data["meta"]["extraction_date"]
                ))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
            
        except Error as e:
            print(f"Database error while saving data: {e}")
            return False

    def save_consolidated_to_database(self, data, technology_area_name, source_count):
        """Save consolidated findings to database"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return False
                
            cursor = conn.cursor()
            
            # Get technology area ID
            cursor.execute(
                "SELECT id FROM technology_areas WHERE name = %s", 
                (technology_area_name,)
            )
            result = cursor.fetchone()
            
            if not result:
                return False  # Technology area should exist
                
            tech_area_id = result[0]
            
            # Parse dates
            info_date = None
            if data.get("Date of Information Release") and data["Date of Information Release"] != "Not found":
                try:
                    from dateutil import parser
                    info_date = parser.parse(data["Date of Information Release"]).strftime('%Y-%m-%d')
                except:
                    info_date = None
            
            # Check if we already have consolidated data for this technology area
            cursor.execute(
                "SELECT id FROM consolidated_developments WHERE technology_area_id = %s",
                (tech_area_id,)
            )
            result = cursor.fetchone()
            
            if result:
                # Update existing record
                cons_id = result[0]
                cursor.execute("""
                    UPDATE consolidated_developments 
                    SET key_players = %s, technological_development = %s, 
                        project_cost = %s, information_date = %s,
                        event_location = %s, contact_information = %s,
                        number_of_sources = %s, consolidation_date = %s
                    WHERE id = %s
                """, (
                    data.get("Key Role Players", ""),
                    data.get("Technological Development", ""),
                    data.get("Project Cost", ""),
                    info_date,
                    data.get("Event Location", ""),
                    data.get("Contact Information", ""),
                    source_count,
                    data["meta"]["consolidation_date"],
                    cons_id
                ))
            else:
                # Insert new record
                cursor.execute("""
                    INSERT INTO consolidated_developments (
                        technology_area_id, key_players, technological_development,
                        project_cost, information_date, event_location, 
                        contact_information, number_of_sources, consolidation_date
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    tech_area_id,
                    data.get("Key Role Players", ""),
                    data.get("Technological Development", ""),
                    data.get("Project Cost", ""),
                    info_date,
                    data.get("Event Location", ""),
                    data.get("Contact Information", ""),
                    source_count,
                    data["meta"]["consolidation_date"]
                ))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
            
        except Error as e:
            print(f"Database error while saving consolidated data: {e}")
            return False

    def crawl_website(self, url, technology_area):
        """Main crawling function with AI analysis for specific technology areas"""
        print(f"Crawling {url} for information about {technology_area}...")
        
        html_content = self.fetch_page(url)
        if html_content:
            data = self.parse_content(html_content, technology_area)
            if data:
                self.save_to_database(data, url, technology_area)
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
            # Save consolidated findings to database
            if consolidated:
                self.save_consolidated_to_database(consolidated, technology_area, len(all_results))
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
            response = requests.post(self.ollama_endpoint, json={"prompt": prompt})
            response.raise_for_status()
            consolidated = response.json()
            
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