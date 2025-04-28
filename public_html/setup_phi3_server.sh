#!/bin/bash

# Setup script for Server 2 (root@server1)
# This script installs Microsoft's Phi-3 model via Ollama
# and sets up the crawler for document processing

echo "Setting up Phi-3 AI processing server..."

# Update system and install dependencies
apt-get update && apt-get upgrade -y
apt-get install -y git python3 python3-pip ipfs-go python3-venv libmysqlclient-dev

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Set up workspace directory
mkdir -p /opt/757built
cd /opt/757built

# Clone the repository
git clone https://github.com/j0bv/757built.com.git .

# Set up Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python requirements
cd crawler
pip install -r requirements.txt
pip install mysql-connector-python python-dateutil

# Configure IPFS
ipfs init
systemctl enable --now ipfs
ipfs config Addresses.Gateway /ip4/0.0.0.0/tcp/8080
ipfs config --json API.HTTPHeaders.Access-Control-Allow-Origin '["*"]'
ipfs config --json API.HTTPHeaders.Access-Control-Allow-Methods '["GET", "POST"]'

# Download Phi-3 model with Ollama
echo "Downloading Phi-3 model - this may take some time..."
ollama pull phi3

# Create .env file for crawler settings
cat > .env << EOF
OLLAMA_ENDPOINT=http://localhost:11434/api/generate
DB_HOST=server250.web-hosting.com
DB_NAME=ybqiflhd_757built
DB_USER=ybqiflhd_admin
DB_PASSWORD=YOUR_PASSWORD_HERE
IPFS_GATEWAY=http://localhost:8080
EOF

# Test the Phi-3 model
python test_phi3.py

# Set up cron job for periodic crawling
(crontab -l 2>/dev/null; echo "0 */4 * * * cd /opt/757built/crawler && /opt/757built/venv/bin/python direct_crawler.py && /opt/757built/venv/bin/python upload_to_db.py") | crontab -

# Create a hash document upload service
cat > /etc/systemd/system/ipfs-hash-service.service << EOF
[Unit]
Description=IPFS Document Hash Service
After=network.target

[Service]
User=root
WorkingDirectory=/opt/757built/crawler
ExecStart=/opt/757built/venv/bin/python document_hasher.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create document hashing script
cat > /opt/757built/crawler/document_hasher.py << EOF
#!/usr/bin/env python3
import os
import glob
import json
import subprocess
import time
import requests
from datetime import datetime

def hash_document(document_path):
    """Add document to IPFS and return the hash"""
    try:
        result = subprocess.run(['ipfs', 'add', '-q', document_path], 
                                capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error hashing document: {e}")
        return None

def update_hash_database(document_path, ipfs_hash):
    """Record the hash in a local database"""
    data_dir = os.path.dirname(document_path)
    db_path = os.path.join(data_dir, 'ipfs_hashes.json')
    
    # Load existing database or create new one
    if os.path.exists(db_path):
        with open(db_path, 'r') as f:
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
    with open(db_path, 'w') as f:
        json.dump(db, f, indent=2)
    
    return True

def sync_with_web_server(ipfs_hash, metadata):
    """Send IPFS hash to the web server"""
    # Load .env file for API endpoint and credentials
    # Implementation depends on how you want to authenticate
    # with the web server
    pass

def monitor_data_directory():
    """Monitor the data directory for new documents"""
    while True:
        # Find all JSON files in the data directory
        data_files = glob.glob('data/*.json')
        hashes_db_path = 'data/ipfs_hashes.json'
        
        # Load hash database
        if os.path.exists(hashes_db_path):
            with open(hashes_db_path, 'r') as f:
                hashes_db = json.load(f)
                processed_files = [entry['document'] for entry in hashes_db['documents']]
        else:
            hashes_db = {'documents': []}
            processed_files = []
        
        # Process new files
        for file_path in data_files:
            filename = os.path.basename(file_path)
            if filename == 'ipfs_hashes.json' or filename in processed_files:
                continue
            
            print(f"Adding new document to IPFS: {filename}")
            
            # Hash document
            ipfs_hash = hash_document(file_path)
            if ipfs_hash:
                # Update hash database
                update_hash_database(file_path, ipfs_hash)
                
                # Extract metadata
                with open(file_path, 'r') as f:
                    try:
                        metadata = json.load(f)
                        # Optionally sync with web server
                        # sync_with_web_server(ipfs_hash, metadata)
                    except json.JSONDecodeError:
                        print(f"Error parsing JSON from {filename}")
        
        # Wait before next scan
        time.sleep(60)

if __name__ == "__main__":
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    # Start monitoring
    monitor_data_directory()
EOF

# Make script executable
chmod +x /opt/757built/crawler/document_hasher.py

# Enable and start the service
systemctl enable ipfs-hash-service
systemctl start ipfs-hash-service

echo "Phi-3 AI processing server setup complete!" 