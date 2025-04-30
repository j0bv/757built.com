#!/bin/bash
# Setup script for 757Built primary server (server1) with H100 cluster integration
# This script configures the main coordinator node that will use H100 cluster for compute

set -e

echo "Setting up 757Built.com primary server (server1) with H100 cluster integration..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
  echo "Please run as root"
  exit 1
fi

# Install system dependencies
apt-get update
apt-get install -y nginx python3 python3-pip python3-venv redis-server git build-essential cmake

# Create directories
mkdir -p /var/www/757built.com
mkdir -p /root/models
mkdir -p /root/757built.com/data/temp_queue
mkdir -p /root/h100-cluster

# Clone repository
echo "Fetching content from repository..."
if [ -d "/var/www/757built.com" ]; then
  cd /var/www/757built.com
  git pull
else
  cd /var/www
  git clone https://github.com/your-username/757built.com.git 757built.com
fi

# Configure Redis for distributed processing
echo "Configuring Redis..."
cat > /etc/redis/redis.conf << EOF
bind 0.0.0.0
port 6379
protected-mode no
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
EOF

systemctl restart redis-server
systemctl enable redis-server

# Install IPFS
echo "Installing IPFS..."
if ! command -v ipfs &> /dev/null; then
    wget https://dist.ipfs.tech/kubo/v0.22.0/kubo_v0.22.0_linux-amd64.tar.gz
    tar -xvzf kubo_v0.22.0_linux-amd64.tar.gz
    cd kubo
    bash install.sh
    cd ..
    rm -rf kubo kubo_v0.22.0_linux-amd64.tar.gz
fi

# Initialize IPFS
if [ ! -d ~/.ipfs ]; then
    ipfs init --profile server
fi

# Enable IPFS API for remote connections
ipfs config --json API.HTTPHeaders.Access-Control-Allow-Origin '["*"]'
ipfs config --json API.HTTPHeaders.Access-Control-Allow-Methods '["PUT", "POST", "GET"]'

# Install llama.cpp
echo "Installing llama.cpp..."
if [ ! -d "/root/llama.cpp" ]; then
    git clone https://github.com/ggerganov/llama.cpp.git /root/llama.cpp
    cd /root/llama.cpp
    make
    cd -
fi

# Create virtual environment for Python
python3 -m venv /root/757built_env
source /root/757built_env/bin/activate

# Install Python dependencies
echo "Installing Python requirements..."
cd /var/www/757built.com
pip install -r Agent/requirements.txt
pip install redis ipfshttpclient flask flask-cors gunicorn requests schedule numpy

# Create IPFS service
echo "Setting up IPFS service..."
cat > /etc/systemd/system/ipfs.service << EOF
[Unit]
Description=IPFS Daemon Service
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/ipfs daemon --enable-pubsub-experiment
Restart=always
RestartSec=10
Environment=IPFS_PATH=/root/.ipfs

[Install]
WantedBy=multi-user.target
EOF

# Create document processor service
echo "Setting up document processor service..."
cat > /etc/systemd/system/document-processor.service << EOF
[Unit]
Description=757Built Document Processor Service
After=network.target ipfs.service redis-server.service
Wants=ipfs.service redis-server.service

[Service]
Type=simple
User=root
WorkingDirectory=/var/www/757built.com
ExecStart=/root/757built_env/bin/python /var/www/757built.com/Agent/enhanced_document_processor.py --model-path /root/models/phi3-q3_k_l.gguf --llama-path /root/llama.cpp/main --threads 8 --ctx-size 8192 --redis-url redis://localhost:6379/0 --storage-path /root/757built.com/data/temp_storage --replication 2
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# Create API service
echo "Setting up API service..."
cat > /etc/systemd/system/757built-api.service << EOF
[Unit]
Description=757Built API Service
After=network.target redis-server.service
Wants=redis-server.service

[Service]
Type=simple
User=root
WorkingDirectory=/var/www/757built.com
ExecStart=/root/757built_env/bin/gunicorn -w 4 -b 0.0.0.0:5000 api.app:app
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1
Environment=REDIS_URL=redis://localhost:6379/0
Environment=STORAGE_PATH=/root/757built.com/data/temp_storage
Environment=REPLICATION_FACTOR=2
Environment=STORAGE_CAPACITY_GB=50.0

[Install]
WantedBy=multi-user.target
EOF

# Create IPFS pinning service script
echo "Creating IPFS pinning service..."
cat > /root/ipfs_pin_service.sh << 'EOF'
#!/bin/bash
TEMP_QUEUE="/root/757built.com/data/temp_queue"
PINATA_SERVICE="pinata"

# Process pending files
for file in "$TEMP_QUEUE"/*.json; do
  if [ -f "$file" ]; then
    echo "Pinning $(basename "$file") to IPFS pinning service..."
    CID=$(ipfs add -Q "$file")
    if [ -n "$CID" ]; then
      # If Pinata is configured, pin there
      if ipfs pin remote ls --service="$PINATA_SERVICE" &>/dev/null; then
        ipfs pin remote add --service="$PINATA_SERVICE" "$CID"
        echo "Pinned $CID to $PINATA_SERVICE"
      else
        echo "Pinning service not configured, only storing locally."
      fi
      
      # Mark as processed
      mkdir -p "$TEMP_QUEUE/processed"
      mv "$file" "$TEMP_QUEUE/processed/$(basename "$file")"
    else
      echo "Failed to add $(basename "$file") to IPFS"
    fi
  fi
done

# Update usage statistics
curl -s -X POST http://localhost:5000/api/storage/status > /dev/null
EOF

chmod +x /root/ipfs_pin_service.sh

# Add cron job for regular pinning
(crontab -l 2>/dev/null; echo "*/10 * * * * /root/ipfs_pin_service.sh") | crontab -

# Create H100 cluster setup script
echo "Creating H100 cluster setup script..."
cat > /root/h100-cluster/setup_h100_node.sh << 'EOF'
#!/bin/bash
# Setup script for H100 worker nodes in Prime Intellect cluster
set -e

# Configuration
SERVER1_IP="REPLACE_WITH_SERVER1_IP"  # Replace this with your server1 IP
REDIS_URL="redis://${SERVER1_IP}:6379/0"
STORAGE_PATH="/workspace/storage"
REPLICATION_FACTOR=2

# Install dependencies
apt-get update
apt-get install -y python3-pip git build-essential cmake

# Create work directory
mkdir -p /workspace/757built
mkdir -p ${STORAGE_PATH}
cd /workspace/757built

# Clone repository
git clone https://github.com/your-username/757built.com.git .

# Install Python requirements
pip install -r Agent/requirements.txt
pip install redis torch==2.1.0 transformers==4.34.0 ipfshttpclient flask flask-cors gunicorn requests

# Create worker service file
cat > /etc/systemd/system/757built-worker.service << EOT
[Unit]
Description=757Built H100 Worker Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/workspace/757built
ExecStart=/usr/bin/python3 /workspace/757built/Agent/agent.py --server ${SERVER1_IP} --redis-url ${REDIS_URL} --worker-id \$(hostname) --storage-path ${STORAGE_PATH}
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOT

# Create storage service file
cat > /etc/systemd/system/757built-storage.service << EOT
[Unit]
Description=757Built Storage Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/workspace/757built
ExecStart=/usr/bin/python3 -m gunicorn -w 2 -b 0.0.0.0:5000 api.storage_app:app
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1
Environment=REDIS_URL=${REDIS_URL}
Environment=STORAGE_PATH=${STORAGE_PATH}
Environment=REPLICATION_FACTOR=${REPLICATION_FACTOR}
Environment=STORAGE_CAPACITY_GB=100.0

[Install]
WantedBy=multi-user.target
EOT

# Enable and start services
systemctl daemon-reload
systemctl enable 757built-worker
systemctl enable 757built-storage
systemctl start 757built-worker
systemctl start 757built-storage

echo "H100 node setup complete!"
EOF

chmod +x /root/h100-cluster/setup_h100_node.sh

# Create H100 deployment instructions
cat > /root/h100-cluster/README.md << 'EOF'
# H100 Cluster Deployment Guide

This guide explains how to deploy the 757Built system to Prime Intellect H100 cluster.

## Prerequisites

1. A running server1 instance with this setup script completed
2. Access to the Prime Intellect dashboard
3. The IP address of your server1 instance

## Deployment Steps

1. Log in to the Prime Intellect dashboard: https://app.primeintellect.ai/dashboard/clusters

2. Launch H100 cluster:
   - Select Ubuntu 22 image
   - Choose United States location
   - Select H100_80GB GPU type
   - Set quantity as needed (recommended: 4+)

3. After the cluster launches, execute these commands on each node:
   
   a. Copy the setup script to each node:
      ```
      scp /root/h100-cluster/setup_h100_node.sh ubuntu@H100_NODE_IP:/tmp/
      ```
   
   b. SSH into each node:
      ```
      ssh ubuntu@H100_NODE_IP
      ```
   
   c. Edit the setup script to set your server1 IP:
      ```
      sudo sed -i 's/REPLACE_WITH_SERVER1_IP/YOUR_SERVER1_IP/' /tmp/setup_h100_node.sh
      ```
   
   d. Run the setup script:
      ```
      sudo bash /tmp/setup_h100_node.sh
      ```

4. Verify the setup from server1:
   ```
   curl http://localhost:5000/api/storage/status
   ```

## Monitoring

Check the status of all nodes:
```
redis-cli smembers active_workers
redis-cli hgetall storage_nodes
```

## Adding More Nodes

Simply repeat the deployment steps for any additional nodes.
EOF

# Generate IPNS key for publishing 
ipfs key gen --type=rsa --size=2048 757built_graph_key

# Enable and start services
systemctl daemon-reload
systemctl enable ipfs
systemctl enable document-processor
systemctl enable 757built-api

systemctl start ipfs
sleep 5  # Wait for IPFS to start
systemctl start document-processor
systemctl start 757built-api

# Create monitoring script
cat > /root/monitor_cluster.sh << 'EOF'
#!/bin/bash
echo "===== 757Built System Status ====="
echo "IPFS Status:"
systemctl status ipfs | grep Active
echo "Document Processor Status:"
systemctl status document-processor | grep Active
echo "API Status:"
systemctl status 757built-api | grep Active
echo "Redis Queue Status:"
redis-cli info | grep connected_clients
redis-cli llen document_queue
echo "Worker Nodes:"
redis-cli smembers active_workers
echo "Storage Nodes:"
redis-cli hkeys storage_nodes
echo "=============================="
EOF

chmod +x /root/monitor_cluster.sh

echo "===== 757Built Server1 Setup Complete ====="
echo "IMPORTANT: Next steps:"
echo "1. Download the Phi-3 model:"
echo "   wget -O /root/models/phi3-q3_k_l.gguf https://huggingface.co/microsoft/phi-3-mini-4k-instruct-gguf/resolve/main/phi-3-mini-4k-instruct.Q4_K_M.gguf"
echo ""
echo "2. Configure IPFS pinning service (optional):"
echo "   ipfs pin remote service add pinata https://api.pinata.cloud/psa YOUR_PINATA_JWT_TOKEN"
echo ""
echo "3. Deploy H100 cluster from Prime Intellect:"
echo "   Follow instructions in /root/h100-cluster/README.md"
echo ""
echo "4. Monitor the system:"
echo "   /root/monitor_cluster.sh"
echo ""
echo "5. Configure GitHub secrets for CI/CD automation:"
echo "   - IPFS_API: /ip4/127.0.0.1/tcp/5001"
echo "   - GRAPH_IPNS_KEY: 757built_graph_key"
echo "==============================" 