#!/bin/bash
# Setup script for Phi-3 document processing pipeline on Server1

set -e

echo "Setting up document processing pipeline on Server1..."

# Configuration - Edit these variables as needed
PHI3_MODEL_PATH="/opt/models/phi3-q3_k_l.gguf"
REPO_DIR="/root/757built.com"
DATA_DIR="${REPO_DIR}/data"
LOG_DIR="${REPO_DIR}/logs"
WEB_API_ENDPOINT="https://api.757built.com/ipfs_hashes.php"
SERVER250_IP="SERVER250_IP_PLACEHOLDER" # Replace with actual IP in production

# Load secrets from environment file if it exists
if [ -f "/etc/757built.env" ]; then
    echo "Loading environment variables from /etc/757built.env"
    set -a
    source /etc/757built.env
    set +a
fi

# Create directories
mkdir -p "${DATA_DIR}/raw"
mkdir -p "${DATA_DIR}/processed"
mkdir -p "${LOG_DIR}"

# Ensure repo is up to date
if [ -d "$REPO_DIR" ]; then
    echo "Updating existing repository..."
    cd "$REPO_DIR"
    git pull
else
    echo "Cloning repository..."
    git clone https://github.com/j0bv/757built.com.git "$REPO_DIR"
    cd "$REPO_DIR"
fi

# Install dependencies
echo "Installing dependencies..."
apt-get update
apt-get install -y python3 python3-pip redis-server ufw jq moreutils

# Install Python requirements
echo "Installing Python requirements..."
pip3 install -r Agent/requirements.txt
pip3 install flask-limiter clamd

# Ensure IPFS is installed
if ! command -v ipfs &> /dev/null; then
    echo "Installing IPFS..."
    wget https://dist.ipfs.io/go-ipfs/v0.18.1/go-ipfs_v0.18.1_linux-amd64.tar.gz
    tar -xvzf go-ipfs_v0.18.1_linux-amd64.tar.gz
    cd go-ipfs
    bash install.sh
    cd ..
    rm -rf go-ipfs go-ipfs_v0.18.1_linux-amd64.tar.gz
    ipfs init
fi

# Download Phi-3 model if not exists
if [ ! -f "$PHI3_MODEL_PATH" ]; then
    echo "Downloading Phi-3 Q3_K_L model..."
    mkdir -p "$(dirname "$PHI3_MODEL_PATH")"
    wget -O "$PHI3_MODEL_PATH" "https://huggingface.co/microsoft/phi-3-mini-4k-instruct-gguf/resolve/main/phi-3-mini-4k-instruct-q3_k_l.gguf"
fi

# Create enhanced_document_processor patch
echo "Creating processor patch..."
mkdir -p "$REPO_DIR/Agent"
cat > "$REPO_DIR/Agent/enhanced_document_processor_patch.py" << 'EOF'
# Patch for enhanced_document_processor.py
# Add this inside process_document function after processed_data is ready

import json
import hashlib
from pathlib import Path

# List of trusted document sources - add your trusted sources here
TRUSTED_SOURCES = ["official_crawler", "manual_upload", "verified_contributor"]

def validate_document(document_path, metadata=None):
    """
    Validate a document before processing it.
    
    Args:
        document_path (str): Path to the document
        metadata (dict): Document metadata including source
        
    Returns:
        bool: True if document is valid, False otherwise
    """
    # Check if source is trusted
    if metadata and "source" in metadata:
        if metadata["source"] not in TRUSTED_SOURCES:
            print(f"Untrusted source: {metadata['source']}")
            return False
    
    # Perform basic file validation
    try:
        file_size = Path(document_path).stat().st_size
        if file_size > 100 * 1024 * 1024:  # 100MB limit
            print(f"File too large: {file_size} bytes")
            return False
            
        # Calculate file hash for validation or logging
        sha256 = hashlib.sha256()
        with open(document_path, 'rb') as f:
            for block in iter(lambda: f.read(4096), b''):
                sha256.update(block)
        file_hash = sha256.hexdigest()
        
        # Could check against allow-list of hashes
        # if file_hash not in ALLOWED_DOCUMENT_HASHES:
        #     return False
        
        print(f"Document validated: {document_path} (SHA256: {file_hash})")
        return True
    except Exception as e:
        print(f"Validation error: {str(e)}")
        return False

def ensure_processed_output(document_path, processed_data, output_dir='data/processed'):
    """
    Ensure the processed document is saved to the output directory.
    
    Args:
        document_path (str): Path to the original document
        processed_data (dict): Processed document data
        output_dir (str): Directory to save processed files
    """
    # Create output directory if it doesn't exist
    processed_out = Path(output_dir)
    processed_out.mkdir(parents=True, exist_ok=True)
    
    # Create output filename using the original document's stem
    out_file = processed_out / (Path(document_path).stem + '.json')
    
    # Write the processed data to the output file
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(processed_data, f, indent=2, ensure_ascii=False)
    
    print(f"Saved processed document to {out_file}")
    return out_file
EOF

# Create empty ipfs/__init__.py to make it a proper package
mkdir -p "$REPO_DIR/ipfs"
cat > "$REPO_DIR/ipfs/__init__.py" << 'EOF'
# IPFS utilities package for 757Built document processing
"""
This package contains tools for verifying and uploading processed documents to IPFS.
"""
EOF

# Create systemd service for document processor
echo "Creating systemd service for document processor..."
cat > /etc/systemd/system/phi3-processor.service << EOF
[Unit]
Description=Phi-3 Document Processor
After=network.target redis-server.service

[Service]
Type=simple
WorkingDirectory=${REPO_DIR}
ExecStart=/usr/bin/python3 ${REPO_DIR}/Agent/enhanced_document_processor.py --model-path ${PHI3_MODEL_PATH} --queue --output-dir ${DATA_DIR}/processed --web-api ${WEB_API_ENDPOINT}
Restart=always
RestartSec=10
User=root
Environment="PYTHONPATH=${REPO_DIR}"
EnvironmentFile=/etc/757built.env

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for ingestion orchestrator
echo "Creating systemd service for ingestion orchestrator..."
cat > /etc/systemd/system/ingestion-orchestrator.service << EOF
[Unit]
Description=Document Ingestion Orchestrator
After=network.target redis-server.service

[Service]
Type=simple
WorkingDirectory=${REPO_DIR}
ExecStart=/usr/bin/python3 -m ingestion.orchestrator --out ${DATA_DIR}/raw
Restart=always
RestartSec=10
User=root
Environment="PYTHONPATH=${REPO_DIR}"
EnvironmentFile=/etc/757built.env

[Install]
WantedBy=multi-user.target
EOF

# ------------------------------------------------
# IPFS Security Hardening
# ------------------------------------------------
echo "Hardening IPFS configuration..."

# Create environment file for secrets if it doesn't exist
if [ ! -f "/etc/757built.env" ]; then
    echo "Creating environment file for secrets..."
    API_SECRET_KEY=$(openssl rand -hex 32)
    cat > /etc/757built.env << EOF
# 757Built environment variables - KEEP SECURE
API_SECRET_KEY=${API_SECRET_KEY}
REDIS_PASSWORD=$(openssl rand -hex 16)
TRUSTED_SOURCES=official_crawler,manual_upload,verified_contributor
EOF
    chmod 600 /etc/757built.env
fi

# Configure IPFS with private network
echo "Configuring IPFS private network..."

# Create swarm.key if it doesn't exist (DO NOT store in repo)
if [ ! -f "$HOME/.ipfs/swarm.key" ]; then
    echo "Generating private swarm key..."
    # Install swarm key generator if needed
    go get -u github.com/Kubuxu/go-ipfs-swarm-key-gen/ipfs-swarm-key-gen 2>/dev/null || echo "Manual key generation needed"
    if command -v ipfs-swarm-key-gen &> /dev/null; then
        ipfs-swarm-key-gen > "$HOME/.ipfs/swarm.key"
    else
        # Fallback manual key generation
        echo "/key/swarm/psk/1.0.0/" > "$HOME/.ipfs/swarm.key"
        echo "/base16/" >> "$HOME/.ipfs/swarm.key"
        openssl rand -hex 32 >> "$HOME/.ipfs/swarm.key"
    fi
    chmod 600 "$HOME/.ipfs/swarm.key"
    echo "Private swarm key created. IMPORTANT: Manually copy this to Server250."
fi

# Modify IPFS config to harden security
echo "Updating IPFS configuration..."
ipfs bootstrap rm --all
jq '.API.HTTPHeaders["Access-Control-Allow-Methods"]=["POST","GET"] | .Swarm.EnableRelayHop=false' \
   ~/.ipfs/config | sponge ~/.ipfs/config

# Configure firewall
echo "Configuring firewall..."
ufw allow ssh
ufw allow from ${SERVER250_IP} to any port 4001 proto tcp
ufw allow from ${SERVER250_IP} to any port 5000 proto tcp
ufw deny 4001/tcp
ufw deny 5001/tcp # API port - only accessible locally
ufw --force enable

# Secure Redis to only listen on localhost
echo "Securing Redis..."
if grep -q "^bind " /etc/redis/redis.conf; then
    sed -i 's/^bind .*/bind 127.0.0.1/' /etc/redis/redis.conf
else
    echo "bind 127.0.0.1" >> /etc/redis/redis.conf
fi

# Set Redis password if not already set
if ! grep -q "^requirepass " /etc/redis/redis.conf && [ -f "/etc/757built.env" ]; then
    REDIS_PASS=$(grep "REDIS_PASSWORD" /etc/757built.env | cut -d= -f2)
    if [ -n "$REDIS_PASS" ]; then
        echo "requirepass $REDIS_PASS" >> /etc/redis/redis.conf
    fi
fi

# Enable and start services
echo "Enabling and starting services..."
systemctl daemon-reload
systemctl restart redis-server
systemctl enable redis-server
systemctl enable phi3-processor.service
systemctl enable ingestion-orchestrator.service

# Start IPFS daemon
echo "Starting IPFS daemon..."
ipfs daemon --enable-gc &

# Modify enhanced_document_processor to support output directory and validation
echo "Patching enhanced_document_processor.py..."
PROCESSOR_FILE="${REPO_DIR}/Agent/enhanced_document_processor.py"

# Check if the file exists before trying to patch it
if [ -f "$PROCESSOR_FILE" ]; then
    # Add validation import
    sed -i '1s/^/from enhanced_document_processor_patch import ensure_processed_output, validate_document\n/' "$PROCESSOR_FILE"
    
    # Add output_dir parameter to the process_document function
    sed -i 's/def process_document(self, document_path, model)/def process_document(self, document_path, model, output_dir=None, metadata=None)/g' "$PROCESSOR_FILE"
    
    # Add validation call
    sed -i '/def process_document/a\\        # Validate document before processing\n        if not validate_document(document_path, metadata):\n            return {"error": "Document validation failed", "status": "rejected"}' "$PROCESSOR_FILE"
    
    # Add output_dir argument parser
    sed -i '/parser.add_argument.*--queue/a\    parser.add_argument("--output-dir", help="Directory to save processed documents as JSON files")' "$PROCESSOR_FILE"
    
    # Add saving logic
    sed -i '/# Return the processed data/i\        # Save to output directory if specified\n        if output_dir:\n            ensure_processed_output(document_path, processed_data, output_dir)' "$PROCESSOR_FILE"
    
    # Pass output_dir to process_document
    sed -i 's/processor.process_document(document_path, model)/processor.process_document(document_path, model, output_dir=args.output_dir)/g' "$PROCESSOR_FILE"
    
    echo "Enhanced document processor patched successfully"
else
    echo "Warning: Could not find $PROCESSOR_FILE to patch. Please apply the changes manually."
fi

# Configure fail2ban
echo "Setting up Fail2Ban..."
apt-get install -y fail2ban
systemctl enable fail2ban
systemctl start fail2ban

echo "Starting services..."
systemctl start phi3-processor.service
systemctl start ingestion-orchestrator.service

echo "Setup completed successfully!"
echo "Document processor is running as a service: phi3-processor.service"
echo "Ingestion orchestrator is running as a service: ingestion-orchestrator.service"
echo "Check logs with: journalctl -u phi3-processor -f"
echo ""
echo "IMPORTANT: You must manually copy the swarm.key to Server250 and securely store your environment file"
echo "Private swarm key location: $HOME/.ipfs/swarm.key"
echo "Environment file: /etc/757built.env" 