#!/usr/bin/env python3
import os
import glob
import json
import subprocess
import time
import requests
from datetime import datetime
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("document_hasher.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("document_hasher")

# Load environment variables
load_dotenv()

# Configuration
WEB_API_ENDPOINT = os.getenv('WEB_API_ENDPOINT', 'https://example.com/api/ipfs_hashes.php')
API_KEY = os.getenv('API_KEY')
DATA_DIR = 'data'
DB_PATH = os.path.join(DATA_DIR, 'ipfs_hashes.json')

def hash_document(document_path):
    """Add document to IPFS and return the hash"""
    try:
        logger.info(f"Adding document to IPFS: {document_path}")
        result = subprocess.run(['ipfs', 'add', '-q', document_path], 
                             capture_output=True, text=True, check=True)
        ipfs_hash = result.stdout.strip()
        logger.info(f"Document added to IPFS with hash: {ipfs_hash}")
        return ipfs_hash
    except subprocess.CalledProcessError as e:
        logger.error(f"Error hashing document: {e}")
        return None

def update_hash_database(document_path, ipfs_hash):
    """Record the hash in a local database"""
    try:
        # Load existing database or create new one
        if os.path.exists(DB_PATH):
            with open(DB_PATH, 'r') as f:
                db = json.load(f)
        else:
            db = {'documents': []}
        
        # Add new entry
        db['documents'].append({
            'document': os.path.basename(document_path),
            'ipfs_hash': ipfs_hash,
            'timestamp': datetime.now().isoformat()
        })
        
        # Save updated database
        with open(DB_PATH, 'w') as f:
            json.dump(db, f, indent=2)
        
        logger.info(f"Updated local hash database with {os.path.basename(document_path)}")
        return True
    except Exception as e:
        logger.error(f"Error updating hash database: {e}")
        return False

def extract_technology_area(document_path):
    """Extract technology area from consolidated document filename"""
    try:
        filename = os.path.basename(document_path)
        if '_consolidated_' in filename:
            tech_area = filename.split('_consolidated_')[0].replace('_', ' ')
            return tech_area
        return None
    except Exception:
        return None

def sync_with_web_server(ipfs_hash, document_path):
    """Send IPFS hash to the web server"""
    if not API_KEY:
        logger.warning("API_KEY not set, skipping sync with web server")
        return False
    
    try:
        # Extract document metadata
        with open(document_path, 'r') as f:
            metadata = json.load(f)
        
        # Extract technology area from filename
        tech_area = extract_technology_area(document_path)
        
        # Prepare payload
        payload = {
            'ipfs_hash': ipfs_hash,
            'document_name': os.path.basename(document_path),
            'document_type': 'consolidated_data' if '_consolidated_' in os.path.basename(document_path) else 'raw_data',
            'metadata': metadata.get('meta', {})
        }
        
        # Add technology area if available
        if tech_area:
            payload['technology_area'] = tech_area
        
        # Send to web server
        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': API_KEY
        }
        
        response = requests.post(WEB_API_ENDPOINT, json=payload, headers=headers)
        response.raise_for_status()
        
        logger.info(f"Successfully synced {os.path.basename(document_path)} with web server")
        return True
    except Exception as e:
        logger.error(f"Error syncing with web server: {e}")
        return False

def retry_failed_syncs():
    """Retry any failed syncs from previous runs"""
    if not os.path.exists(DB_PATH):
        return
    
    try:
        with open(DB_PATH, 'r') as f:
            db = json.load(f)
        
        for doc in db.get('documents', []):
            if not doc.get('synced'):
                document_name = doc.get('document')
                ipfs_hash = doc.get('ipfs_hash')
                document_path = os.path.join(DATA_DIR, document_name)
                
                if os.path.exists(document_path) and ipfs_hash:
                    logger.info(f"Retrying sync for {document_name}")
                    synced = sync_with_web_server(ipfs_hash, document_path)
                    
                    # Update sync status
                    if synced:
                        doc['synced'] = True
                        doc['sync_timestamp'] = datetime.now().isoformat()
        
        # Save updated database
        with open(DB_PATH, 'w') as f:
            json.dump(db, f, indent=2)
            
    except Exception as e:
        logger.error(f"Error retrying failed syncs: {e}")

def monitor_data_directory():
    """Monitor the data directory for new documents"""
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Initial retry of failed syncs
    retry_failed_syncs()
    
    while True:
        # Find all JSON files in the data directory
        data_files = glob.glob(os.path.join(DATA_DIR, '*.json'))
        
        # Load hash database
        if os.path.exists(DB_PATH):
            with open(DB_PATH, 'r') as f:
                hashes_db = json.load(f)
                processed_files = [entry['document'] for entry in hashes_db.get('documents', [])]
        else:
            hashes_db = {'documents': []}
            processed_files = []
        
        # Process new files
        for file_path in data_files:
            filename = os.path.basename(file_path)
            if filename == 'ipfs_hashes.json' or filename in processed_files:
                continue
            
            logger.info(f"Processing new document: {filename}")
            
            # Hash document
            ipfs_hash = hash_document(file_path)
            if ipfs_hash:
                # Update hash database
                update_hash_database(file_path, ipfs_hash)
                
                # Sync with web server
                synced = sync_with_web_server(ipfs_hash, file_path)
                
                # Update sync status in database
                if synced and os.path.exists(DB_PATH):
                    with open(DB_PATH, 'r') as f:
                        db = json.load(f)
                    
                    for doc in db.get('documents', []):
                        if doc.get('document') == filename and doc.get('ipfs_hash') == ipfs_hash:
                            doc['synced'] = True
                            doc['sync_timestamp'] = datetime.now().isoformat()
                    
                    with open(DB_PATH, 'w') as f:
                        json.dump(db, f, indent=2)
        
        # Retry any failed syncs
        retry_failed_syncs()
        
        # Wait before next scan
        logger.info("Sleeping for 60 seconds before next scan")
        time.sleep(60)

if __name__ == "__main__":
    logger.info("Starting IPFS document hasher service")
    monitor_data_directory() 