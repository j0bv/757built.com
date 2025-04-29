#!/bin/bash
# Setup script for Phi-3 inference engine for document processing

# Exit on errors
set -e

echo "Starting setup for 757Built document processing server..."

# Install system dependencies
echo "Installing system dependencies..."
apt-get update
apt-get install -y python3 python3-pip python3-venv git nginx

# Create a directory for the application
APP_DIR="/opt/757built-processor"
mkdir -p $APP_DIR

# Clone the repository
echo "Cloning the repository..."
git clone https://github.com/yourusername/757built.com.git $APP_DIR

# Set up Python virtual environment
echo "Setting up Python environment..."
cd $APP_DIR
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r Agent/requirements.txt
pip install torch torchvision torchaudio

# Create .env file
echo "Creating environment configuration..."
cat > $APP_DIR/.env << EOF
# Database Configuration
DB_HOST=your_db_host
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=

# IPFS Configuration
IPFS_API=/ip4/127.0.0.1/tcp/5001
GRAPH_IPNS_KEY=your_ipns_key_name

# Web API Integration
WEB_API_ENDPOINT=https://example.com/api/ipfs_hashes.php

# Log Configuration
LOG_LEVEL=INFO
EOF

# Create systemd service
echo "Setting up systemd service..."
cat > /etc/systemd/system/phi3-document-processor.service << 'EOF'
[Unit]
Description=757Built Phi-3 Document Processor
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/757built-processor
Environment="PATH=/opt/757built-processor/venv/bin"
EnvironmentFile=/opt/757built-processor/.env
ExecStart=/opt/757built-processor/venv/bin/python /opt/757built-processor/Agent/phi3_processor.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Set permissions
chown -R www-data:www-data $APP_DIR
chmod -R 755 $APP_DIR

# Start and enable the service
systemctl daemon-reload
systemctl enable phi3-document-processor.service
systemctl start phi3-document-processor.service

echo "Installation complete!"
echo
echo "IMPORTANT: Please update the .env file with your database credentials and API keys:"
echo "nano $APP_DIR/.env"
echo
echo "Then restart the service with: systemctl restart phi3-document-processor.service" 