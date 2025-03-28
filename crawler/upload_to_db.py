import mysql.connector
from mysql.connector import Error
import json
import os
import glob
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def connect_to_database():
    """Connect to the cPanel MySQL database"""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None

def upload_consolidated_data():
    """Upload consolidated data from JSON files to MySQL database"""
    # Connect to database
    connection = connect_to_database()
    if not connection:
        return
    
    cursor = connection.cursor()
    
    # Get all consolidated JSON files
    consolidated_files = glob.glob('data/*_consolidated_*.json')
    
    for file_path in consolidated_files:
        try:
            # Read JSON file
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract technology area from filename
            filename = os.path.basename(file_path)
            tech_area = filename.split('_consolidated_')[0].replace('_', ' ')
            
            # Check if technology area exists in database, create if not
            cursor.execute("SELECT id FROM technology_areas WHERE LOWER(name) = LOWER(%s)", (tech_area,))
            result = cursor.fetchone()
            
            if result:
                tech_area_id = result[0]
            else:
                # Create new technology area
                tech_slug = tech_area.lower().replace(' ', '-')
                cursor.execute(
                    "INSERT INTO technology_areas (name, slug, description) VALUES (%s, %s, %s)",
                    (tech_area.title(), tech_slug, f"Information about {tech_area} in Hampton Roads")
                )
                tech_area_id = cursor.lastrowid
            
            # Parse date if available
            info_date = None
            if data.get("Date of Information Release") and data["Date of Information Release"] != "Not found":
                try:
                    from dateutil import parser
                    info_date = parser.parse(data["Date of Information Release"]).strftime('%Y-%m-%d')
                except:
                    info_date = None
            
            # Check if consolidated entry already exists
            cursor.execute(
                "SELECT id FROM consolidated_developments WHERE technology_area_id = %s",
                (tech_area_id,)
            )
            result = cursor.fetchone()
            
            consolidation_date = data.get("meta", {}).get("consolidation_date", datetime.now().isoformat())
            number_of_sources = data.get("meta", {}).get("number_of_sources", 1)
            
            if result:
                # Update existing record
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
                    number_of_sources,
                    consolidation_date,
                    result[0]
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
                    number_of_sources,
                    consolidation_date
                ))
            
            connection.commit()
            print(f"Uploaded data for {tech_area}")
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    cursor.close()
    connection.close()

if __name__ == "__main__":
    upload_consolidated_data() 