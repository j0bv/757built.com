#!/usr/bin/env python3
import os
import json
import time
import logging
import argparse
import subprocess
import glob
from datetime import datetime
from dotenv import load_dotenv
import hashlib
import ipfshttpclient

# Import our custom modules
from phi3_wrapper import Phi3Processor
from job_queue import dequeue_document

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("document_processor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("document_processor")

# Load environment variables
load_dotenv()

# Configuration
WEB_API_ENDPOINT = os.getenv('WEB_API_ENDPOINT', 'https://server250.web-hosting.com/api/ipfs_hashes.php')
API_KEY = os.getenv('API_KEY')
DATA_DIR = 'data'
ANALYSIS_DIR = os.path.join(DATA_DIR, 'analysis')
DB_PATH = os.path.join(DATA_DIR, 'ipfs_hashes.json')
GRAPH_DATA_PATH = os.path.join(DATA_DIR, 'graph_data.json')
DOCUMENT_EXTENSIONS = ['.txt', '.pdf', '.docx', '.doc', '.rtf', '.json', '.csv']
GRAPH_IPNS_KEY = os.getenv('GRAPH_IPNS_KEY', 'self')

def extract_text_from_document(document_path):
    """Extract text from various document formats"""
    extension = os.path.splitext(document_path)[1].lower()
    
    try:
        if extension == '.txt':
            with open(document_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        elif extension == '.json':
            with open(document_path, 'r', encoding='utf-8', errors='ignore') as f:
                data = json.load(f)
                # Handle different JSON structures
                if isinstance(data, dict):
                    # Try common keys that might contain text
                    for key in ['text', 'content', 'body', 'description', 'abstract']:
                        if key in data and isinstance(data[key], str):
                            return data[key]
                    # If no specific key found, convert whole JSON to string
                    return json.dumps(data)
                elif isinstance(data, list):
                    # Join list items if they're strings
                    text_items = [item for item in data if isinstance(item, str)]
                    if text_items:
                        return ' '.join(text_items)
                    # Otherwise convert whole JSON to string
                    return json.dumps(data)
        elif extension == '.pdf':
            # Use pdftotext if available
            try:
                result = subprocess.run(['pdftotext', document_path, '-'], 
                                     capture_output=True, text=True, check=True)
                return result.stdout
            except:
                logger.warning(f"pdftotext not available for {document_path}. Install poppler-utils.")
                return ""
        elif extension in ['.docx', '.doc']:
            # Try using textract if available
            try:
                import textract
                return textract.process(document_path).decode('utf-8', errors='ignore')
            except ImportError:
                logger.warning("textract not available. Install with: pip install textract")
                return ""
        elif extension == '.csv':
            import csv
            text_content = []
            with open(document_path, 'r', encoding='utf-8', errors='ignore') as f:
                csv_reader = csv.reader(f)
                for row in csv_reader:
                    text_content.append(' '.join(row))
            return '\n'.join(text_content)
        else:
            logger.warning(f"Unsupported file format: {extension}")
            return ""
    except Exception as e:
        logger.error(f"Error extracting text from {document_path}: {e}")
        return ""

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

def is_hash_processed(ipfs_hash):
    """Check if this ipfs_hash already exists in the local database."""
    if not ipfs_hash or not os.path.exists(DB_PATH):
        return False
    try:
        with open(DB_PATH, "r") as f:
            db = json.load(f)
        return any(entry.get("ipfs_hash") == ipfs_hash for entry in db.get("documents", []))
    except Exception:
        return False

def compute_content_hash(text):
    """Return SHA-256 hex digest of the given text (UTF-8)."""
    return hashlib.sha256(text.encode('utf-8', errors='ignore')).hexdigest()

def is_content_hash_processed(content_hash):
    if not content_hash or not os.path.exists(DB_PATH):
        return False
    try:
        with open(DB_PATH, "r") as f:
            db = json.load(f)
        return any(entry.get("content_hash") == content_hash for entry in db.get("documents", []))
    except Exception:
        return False

def update_hash_database(document_path, ipfs_hash=None, analysis=None, content_hash=None):
    """Record the hash and analysis in a local database"""
    try:
        # Load existing database or create new one
        if os.path.exists(DB_PATH):
            with open(DB_PATH, 'r') as f:
                db = json.load(f)
        else:
            db = {'documents': []}
        
        # Add new entry with analysis
        entry = {
            'document': os.path.basename(document_path),
            'timestamp': datetime.now().isoformat()
        }
        
        if ipfs_hash:
            entry['ipfs_hash'] = ipfs_hash
        if content_hash:
            entry['content_hash'] = content_hash
        
        # Add analysis if available
        if analysis:
            entry['analysis'] = analysis
        
        # Avoid duplicates; enrich existing record if necessary
        found = False
        for existing in db['documents']:
            if (ipfs_hash and existing.get('ipfs_hash') == ipfs_hash) or (content_hash and existing.get('content_hash') == content_hash):
                found = True
                if analysis and 'analysis' not in existing:
                    existing['analysis'] = analysis
                    existing['timestamp'] = datetime.now().isoformat()
                break
        
        if not found:
            db['documents'].append(entry)
        
        # Save updated database
        with open(DB_PATH, 'w') as f:
            json.dump(db, f, indent=2)
        
        logger.info(f"Updated local hash database with {os.path.basename(document_path)}")
        return True
    except Exception as e:
        logger.error(f"Error updating hash database: {e}")
        return False

def update_graph_database(analysis):
    """Update the graph database with new entity and relationship data"""
    try:
        # Load existing graph data or create new
        if os.path.exists(GRAPH_DATA_PATH):
            with open(GRAPH_DATA_PATH, 'r') as f:
                graph = json.load(f)
        else:
            graph = {
                'nodes': [],
                'edges': [],
                'projects': [],
                'locations': []
            }
        
        if not analysis:
            return False
            
        # Extract document path for reference
        doc_path = analysis.get('document_path', '')
        doc_name = os.path.basename(doc_path)
        
        # Add project as a node
        project = analysis.get('project', {})
        if project and project.get('title'):
            project_id = f"project_{len(graph['projects'])}"
            project_data = {
                'id': project_id,
                'type': 'project',
                'title': project.get('title', ''),
                'summary': project.get('summary', ''),
                'start_date': project.get('start_date', ''),
                'end_date': project.get('end_date', ''),
                'status': project.get('status', ''),
                'document': doc_name
            }
            graph['projects'].append(project_data)
            graph['nodes'].append({
                'id': project_id,
                'label': project.get('title', ''),
                'type': 'project',
                'properties': project_data
            })
            
        # Add locations
        for location in analysis.get('locations', []):
            loc_name = location.get('name', '')
            if not loc_name:
                continue
                
            # Check if location already exists
            existing_loc = next((l for l in graph['locations'] if l.get('name') == loc_name), None)
            if not existing_loc:
                loc_id = f"location_{len(graph['locations'])}"
                loc_data = {
                    'id': loc_id,
                    'name': loc_name,
                    'lat': location.get('lat'),
                    'lng': location.get('lng'),
                    'documents': [doc_name]
                }
                graph['locations'].append(loc_data)
                graph['nodes'].append({
                    'id': loc_id,
                    'label': loc_name,
                    'type': 'location',
                    'properties': {
                        'lat': location.get('lat'),
                        'lng': location.get('lng')
                    }
                })
                
                # Link project to location if available
                if project and project.get('title'):
                    graph['edges'].append({
                        'source': project_id,
                        'target': loc_id,
                        'relationship': 'located_at',
                        'document': doc_name
                    })
            else:
                # Update existing location
                if doc_name not in existing_loc.get('documents', []):
                    existing_loc['documents'].append(doc_name)
                
                # Link project to existing location
                if project and project.get('title'):
                    graph['edges'].append({
                        'source': project_id,
                        'target': existing_loc['id'],
                        'relationship': 'located_at',
                        'document': doc_name
                    })
        
        # Add entities
        entities = analysis.get('entities', {})
        
        # Process people
        for person in entities.get('people', []):
            person_name = person.get('name', '')
            if not person_name:
                continue
                
            # Check if person already exists
            existing_person = next((n for n in graph['nodes'] if n.get('type') == 'person' and n.get('label') == person_name), None)
            if not existing_person:
                person_id = f"person_{len([n for n in graph['nodes'] if n.get('type') == 'person'])}"
                graph['nodes'].append({
                    'id': person_id,
                    'label': person_name,
                    'type': 'person',
                    'properties': {
                        'role': person.get('role', ''),
                        'documents': [doc_name]
                    }
                })
                
                # Link to project if available
                if project and project.get('title'):
                    graph['edges'].append({
                        'source': person_id,
                        'target': project_id,
                        'relationship': person.get('role', 'involved_in'),
                        'document': doc_name
                    })
            else:
                # Update existing person
                person_id = existing_person['id']
                if 'documents' not in existing_person['properties']:
                    existing_person['properties']['documents'] = []
                if doc_name not in existing_person['properties']['documents']:
                    existing_person['properties']['documents'].append(doc_name)
                
                # Link to project if available
                if project and project.get('title'):
                    graph['edges'].append({
                        'source': person_id,
                        'target': project_id,
                        'relationship': person.get('role', 'involved_in'),
                        'document': doc_name
                    })
        
        # Process organizations
        for org in entities.get('organizations', []):
            org_name = org.get('name', '')
            if not org_name:
                continue
                
            # Check if organization already exists
            existing_org = next((n for n in graph['nodes'] if n.get('type') == 'organization' and n.get('label') == org_name), None)
            if not existing_org:
                org_id = f"org_{len([n for n in graph['nodes'] if n.get('type') == 'organization'])}"
                graph['nodes'].append({
                    'id': org_id,
                    'label': org_name,
                    'type': 'organization',
                    'properties': {
                        'role': org.get('role', ''),
                        'documents': [doc_name]
                    }
                })
                
                # Link to project if available
                if project and project.get('title'):
                    graph['edges'].append({
                        'source': org_id,
                        'target': project_id,
                        'relationship': org.get('role', 'involved_in'),
                        'document': doc_name
                    })
            else:
                # Update existing organization
                org_id = existing_org['id']
                if 'documents' not in existing_org['properties']:
                    existing_org['properties']['documents'] = []
                if doc_name not in existing_org['properties']['documents']:
                    existing_org['properties']['documents'].append(doc_name)
                
                # Link to project if available
                if project and project.get('title'):
                    graph['edges'].append({
                        'source': org_id,
                        'target': project_id,
                        'relationship': org.get('role', 'involved_in'),
                        'document': doc_name
                    })
        
        # Process companies
        for company in entities.get('companies', []):
            company_name = company.get('name', '')
            if not company_name:
                continue
                
            # Check if company already exists
            existing_company = next((n for n in graph['nodes'] if n.get('type') == 'company' and n.get('label') == company_name), None)
            if not existing_company:
                company_id = f"company_{len([n for n in graph['nodes'] if n.get('type') == 'company'])}"
                graph['nodes'].append({
                    'id': company_id,
                    'label': company_name,
                    'type': 'company',
                    'properties': {
                        'role': company.get('role', ''),
                        'documents': [doc_name]
                    }
                })
                
                # Link to project if available
                if project and project.get('title'):
                    graph['edges'].append({
                        'source': company_id,
                        'target': project_id,
                        'relationship': company.get('role', 'involved_in'),
                        'document': doc_name
                    })
            else:
                # Update existing company
                company_id = existing_company['id']
                if 'documents' not in existing_company['properties']:
                    existing_company['properties']['documents'] = []
                if doc_name not in existing_company['properties']['documents']:
                    existing_company['properties']['documents'].append(doc_name)
                
                # Link to project if available
                if project and project.get('title'):
                    graph['edges'].append({
                        'source': company_id,
                        'target': project_id,
                        'relationship': company.get('role', 'involved_in'),
                        'document': doc_name
                    })
        
        # Add explicit relationships from analysis
        for rel in analysis.get('relationships', []):
            source_name = rel.get('source', '')
            target_name = rel.get('target', '')
            relationship = rel.get('relationship', '')
            
            if not source_name or not target_name or not relationship:
                continue
                
            # Find source and target nodes
            source_node = next((n for n in graph['nodes'] if n.get('label') == source_name), None)
            target_node = next((n for n in graph['nodes'] if n.get('label') == target_name), None)
            
            if source_node and target_node:
                # Check if relationship already exists
                existing_edge = next((e for e in graph['edges'] 
                                     if e.get('source') == source_node['id'] 
                                     and e.get('target') == target_node['id']
                                     and e.get('relationship') == relationship), None)
                
                if not existing_edge:
                    graph['edges'].append({
                        'source': source_node['id'],
                        'target': target_node['id'],
                        'relationship': relationship,
                        'document': doc_name
                    })
        
        # Save updated graph data
        with open(GRAPH_DATA_PATH, 'w') as f:
            json.dump(graph, f, indent=2)
        
        # Publish to IPNS
        publish_graph_to_ipns()
        
        logger.info(f"Updated graph database with data from {doc_name}")
        return True
    except Exception as e:
        logger.error(f"Error updating graph database: {e}")
        return False

def publish_graph_to_ipns():
    """Pin latest graph_data.json to IPFS and publish CID via IPNS."""
    try:
        client = ipfshttpclient.connect()
        res = client.add(GRAPH_DATA_PATH)
        cid = res['Hash'] if isinstance(res, dict) else res[-1]['Hash']
        client.name.publish(f"/ipfs/{cid}", key=GRAPH_IPNS_KEY)
        logger.info(f"Published graph {cid} to IPNS key '{GRAPH_IPNS_KEY}'")
        return cid
    except Exception as e:
        logger.error(f"Failed to publish graph to IPNS: {e}")
        return None

def sync_with_web_server(ipfs_hash, document_path, analysis=None):
    """Send IPFS hash and analysis to the web server"""
    if not API_KEY:
        logger.warning("API_KEY not set, skipping sync with web server")
        return False
    
    try:
        # Prepare core payload
        payload = {
            'ipfs_hash': ipfs_hash,
            'document_name': os.path.basename(document_path),
            'document_type': 'unknown'
        }
        
        # Add analysis data if available
        if analysis:
            # Document type
            if 'document_type' in analysis:
                payload['document_type'] = analysis['document_type']
            
            # Project data
            if 'project' in analysis:
                payload['project'] = analysis['project']
                
            # Location data - map coordinates to geoJSON format
            if 'locations' in analysis and analysis['locations']:
                payload['geojson'] = {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "properties": {
                                "name": loc.get('name', ''),
                                "document": os.path.basename(document_path)
                            },
                            "geometry": {
                                "type": "Point",
                                "coordinates": [loc.get('lng', 0), loc.get('lat', 0)]
                            }
                        } for loc in analysis['locations'] if 'lat' in loc and 'lng' in loc
                    ]
                }
            
            # Funding data
            if 'funding' in analysis:
                payload['funding'] = analysis['funding']
                
            # Entity data
            if 'entities' in analysis:
                payload['entities'] = analysis['entities']
        
        # Send to web server
        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': API_KEY
        }
        
        import requests
        response = requests.post(WEB_API_ENDPOINT, json=payload, headers=headers)
        response.raise_for_status()
        
        logger.info(f"Successfully synced {os.path.basename(document_path)} with web server")
        return True
    except Exception as e:
        logger.error(f"Error syncing with web server: {e}")
        return False

def process_document(document_path, phi3_processor):
    """Process a single document with Phi-3 analysis and IPFS hashing"""
    try:
        logger.info(f"Processing document: {document_path}")
        
        # Check if document exists
        if not os.path.exists(document_path):
            logger.error(f"Document not found: {document_path}")
            return False
        
        # Extract text content from document first
        text_content = extract_text_from_document(document_path)
        if not text_content:
            logger.warning(f"Could not extract text from {document_path}")
            # Still proceed with hashing even if text extraction fails
        
        # Compute content hash for deduplication
        content_hash = compute_content_hash(text_content)
        
        if is_content_hash_processed(content_hash):
            logger.info(f"Document already processed (content hash match). Skipping.")
            return True
        
        # Process with Phi-3 if text was extracted
        analysis = None
        if text_content:
            # Create a temporary file with the text content
            text_file_path = os.path.join(
                ANALYSIS_DIR, 
                f"{os.path.splitext(os.path.basename(document_path))[0]}_text.txt"
            )
            os.makedirs(ANALYSIS_DIR, exist_ok=True)
            
            with open(text_file_path, 'w', encoding='utf-8') as f:
                f.write(text_content)
            
            # Analyze with Phi-3
            logger.info(f"Analyzing document with Phi-3: {document_path}")
            analysis = phi3_processor.process_document(text_file_path)
            
            # Save analysis to file
            analysis_file_path = os.path.join(
                ANALYSIS_DIR, 
                f"{os.path.splitext(os.path.basename(document_path))[0]}_analysis.json"
            )
            with open(analysis_file_path, 'w') as f:
                json.dump(analysis, f, indent=2)
                
            logger.info(f"Saved analysis to {analysis_file_path}")
        
        # After successful analysis, hash the original document with IPFS
        ipfs_hash = hash_document(document_path)
        if not ipfs_hash:
            logger.error(f"Failed to hash document after analysis: {document_path}")
            return False
        
        # Update hash database with analysis
        updated_db = update_hash_database(document_path, ipfs_hash, analysis, content_hash)
        if not updated_db:
            logger.warning(f"Failed to update hash database for {document_path}")
        
        # Update graph database with analysis
        if analysis:
            updated_graph = update_graph_database(analysis)
            if not updated_graph:
                logger.warning(f"Failed to update graph database for {document_path}")
        
        # Sync with web server
        synced = sync_with_web_server(ipfs_hash, document_path, analysis)
        if not synced:
            logger.warning(f"Failed to sync {document_path} with web server")
        
        logger.info(f"Successfully processed document: {document_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error processing document {document_path}: {e}")
        return False

def monitor_data_directory(phi3_processor):
    """Monitor the data directory for new documents"""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(ANALYSIS_DIR, exist_ok=True)
    
    logger.info("Starting document monitoring service")
    
    # Load existing database to check which files have been processed
    if os.path.exists(DB_PATH):
        with open(DB_PATH, 'r') as f:
            db = json.load(f)
            processed_files = [entry['document'] for entry in db.get('documents', [])]
    else:
        db = {'documents': []}
        processed_files = []
    
    while True:
        # Find all documents in the data directory
        all_files = []
        for ext in DOCUMENT_EXTENSIONS:
            all_files.extend(glob.glob(os.path.join(DATA_DIR, f"*{ext}")))
        
        # Process new files
        for file_path in all_files:
            filename = os.path.basename(file_path)
            if filename in processed_files or filename == 'ipfs_hashes.json' or filename == 'graph_data.json':
                continue
            
            logger.info(f"Found new document: {filename}")
            success = process_document(file_path, phi3_processor)
            
            if success:
                processed_files.append(filename)
            
            # Short pause between processing documents
            time.sleep(1)
        
        # Wait before next scan
        logger.info("Sleeping for 60 seconds before next scan")
        time.sleep(60)

def queue_worker(phi3_processor):
    """Continuously consume document paths from Redis queue and process them."""
    logger.info("Starting queue worker mode – waiting for jobs…")
    while True:
        job = dequeue_document()
        if not job:
            continue  # timeout, loop back
        
        path = job.get('path')
        if not path:
            logger.warning("Received job without path: %s", job)
            continue
        
        process_document(path, phi3_processor)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Process documents with Phi-3 and IPFS')
    parser.add_argument('--model-path', required=True, help='Path to the Phi-3 model GGUF file')
    parser.add_argument('--llama-path', default='./main', help='Path to the llama.cpp executable')
    parser.add_argument('--threads', type=int, default=6, help='Number of threads to use')
    parser.add_argument('--gpu-layers', type=int, default=0, help='Number of GPU layers to use')
    parser.add_argument('--ctx-size', type=int, default=4096, help='Context size for the model')
    parser.add_argument('--single-file', help='Process a single file instead of monitoring directory')
    parser.add_argument('--queue', action='store_true', help='Run as queue consumer instead of directory monitor')
    
    args = parser.parse_args()
    
    # Initialize Phi-3 processor
    phi3_processor = Phi3Processor(
        model_path=args.model_path,
        threads=args.threads,
        gpu_layers=args.gpu_layers,
        ctx_size=args.ctx_size,
        llama_executable=args.llama_path
    )
    
    # Process a single file or monitor directory
    if args.single_file:
        process_document(args.single_file, phi3_processor)
    elif args.queue:
        queue_worker(phi3_processor)
    else:
        monitor_data_directory(phi3_processor)

if __name__ == "__main__":
    main()
