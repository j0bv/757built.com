#!/bin/bash
# Setup script for 757Built primary server (server1) with H100 cluster integration
# Specifically for AlmaLinux 8 cPanel environment

set -e

echo "Setting up 757Built.com primary server (server1) with H100 cluster integration..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
  echo "Please run as root"
  exit 1
fi

# Configuration variables
PUBLIC_HTML="/home/YOUR_CPANEL_USERNAME/public_html"  # CHANGE THIS to your cPanel username
STORAGE_DIR="/home/YOUR_CPANEL_USERNAME/757built_data"  # CHANGE THIS to your cPanel username
MODELS_DIR="/home/YOUR_CPANEL_USERNAME/757built_models"  # CHANGE THIS to your cPanel username
SCRIPTS_DIR="/home/YOUR_CPANEL_USERNAME/757built_scripts"  # CHANGE THIS to your cPanel username

# Create directories outside the public web root
mkdir -p $STORAGE_DIR
mkdir -p $MODELS_DIR
mkdir -p $SCRIPTS_DIR
mkdir -p $STORAGE_DIR/temp_queue
mkdir -p $SCRIPTS_DIR/h100-cluster

# SECURITY: Move scripts out of public_html
if [ -d "$PUBLIC_HTML/server1" ]; then
  echo "Moving server scripts out of public web directory for security..."
  cp -r $PUBLIC_HTML/server1/* $SCRIPTS_DIR/
  rm -rf $PUBLIC_HTML/server1
  echo "WARNING: Server scripts have been moved from public_html/server1 to $SCRIPTS_DIR for security."
fi

# Check for existing repository
if [ -d "$PUBLIC_HTML/757built.com" ]; then
  echo "Found existing repository in $PUBLIC_HTML/757built.com. Using it."
  REPO_DIR="$PUBLIC_HTML/757built.com"
else
  echo "Repository not found. Will use files in public_html."
  REPO_DIR="$PUBLIC_HTML"
fi

# Install system dependencies (use yum for AlmaLinux)
echo "Installing system dependencies..."
yum update -y
yum install -y python3 python3-pip redis git cmake make gcc gcc-c++ kernel-devel

# Configure Redis for distributed processing
echo "Configuring Redis..."
cat > /etc/redis.conf << EOF
bind 0.0.0.0
port 6379
protected-mode no
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
EOF

# Safety check for production server
if ! systemctl status redis &>/dev/null; then
  # Redis not running or not installed via systemd
  if command -v redis-server &>/dev/null; then
    systemctl enable redis
    systemctl restart redis
  else 
    # Fallback to manual redis installation
    echo "Redis not found via systemd, starting manually..."
    redis-server /etc/redis.conf --daemonize yes
    # Add to rc.local for startup
    echo "redis-server /etc/redis.conf --daemonize yes" >> /etc/rc.d/rc.local
    chmod +x /etc/rc.d/rc.local
  fi
fi

# Install IPFS (using precompiled binary for AlmaLinux compatibility)
echo "Installing IPFS..."
if ! command -v ipfs &> /dev/null; then
    cd /tmp
    wget https://dist.ipfs.tech/kubo/v0.22.0/kubo_v0.22.0_linux-amd64.tar.gz
    tar -xvzf kubo_v0.22.0_linux-amd64.tar.gz
    cd kubo
    bash install.sh
    cd ..
    rm -rf kubo kubo_v0.22.0_linux-amd64.tar.gz
fi

# Initialize IPFS if not already initialized
if [ ! -d ~/.ipfs ]; then
    ipfs init --profile server
fi

# Enable IPFS API for remote connections
ipfs config --json API.HTTPHeaders.Access-Control-Allow-Origin '["*"]'
ipfs config --json API.HTTPHeaders.Access-Control-Allow-Methods '["PUT", "POST", "GET"]'

# Install llama.cpp (without using systemd since cPanel may handle services differently)
echo "Installing llama.cpp..."
if [ ! -d "$SCRIPTS_DIR/llama.cpp" ]; then
    git clone https://github.com/ggerganov/llama.cpp.git $SCRIPTS_DIR/llama.cpp
    cd $SCRIPTS_DIR/llama.cpp
    make
    cd -
fi

# Set up Python environment using virtual environments
echo "Setting up Python environment..."
python3 -m venv $SCRIPTS_DIR/757built_env
source $SCRIPTS_DIR/757built_env/bin/activate

# Install Python dependencies
echo "Installing Python requirements..."
cd $REPO_DIR
if [ -f "Agent/requirements.txt" ]; then
    pip install -r Agent/requirements.txt
else
    # Fallback if repo structure is different
    pip install requests beautifulsoup4 python-dotenv schedule ipfshttpclient textract numpy
fi
pip install redis ipfshttpclient flask flask-cors gunicorn requests schedule numpy

# Create IPFS daemon script (use cPanel service management if available)
echo "Setting up IPFS daemon script..."
cat > $SCRIPTS_DIR/run_ipfs.sh << 'EOF'
#!/bin/bash
export IPFS_PATH=~/.ipfs
ipfs daemon --enable-pubsub-experiment
EOF

chmod +x $SCRIPTS_DIR/run_ipfs.sh

# Create document processor script
echo "Setting up document processor script..."
cat > $SCRIPTS_DIR/run_processor.sh << EOF
#!/bin/bash
source $SCRIPTS_DIR/757built_env/bin/activate
cd $REPO_DIR
python Agent/enhanced_document_processor.py \\
  --model-path $MODELS_DIR/phi3-q3_k_l.gguf \\
  --llama-path $SCRIPTS_DIR/llama.cpp/main \\
  --threads 8 \\
  --ctx-size 8192 \\
  --redis-url redis://localhost:6379/0 \\
  --storage-path $STORAGE_DIR/temp_storage \\
  --replication 2
EOF

chmod +x $SCRIPTS_DIR/run_processor.sh

# Create API server script
echo "Setting up API server script..."
cat > $SCRIPTS_DIR/run_api.sh << EOF
#!/bin/bash
source $SCRIPTS_DIR/757built_env/bin/activate
cd $REPO_DIR
STORAGE_PATH=$STORAGE_DIR/temp_storage \\
REDIS_URL=redis://localhost:6379/0 \\
REPLICATION_FACTOR=2 \\
STORAGE_CAPACITY_GB=50.0 \\
gunicorn -w 4 -b 0.0.0.0:5000 api.app:app
EOF

chmod +x $SCRIPTS_DIR/run_api.sh

# Create IPFS pinning service script for cPanel
echo "Creating IPFS pinning service..."
cat > $SCRIPTS_DIR/ipfs_pin_service.sh << EOF
#!/bin/bash
TEMP_QUEUE="$STORAGE_DIR/temp_queue"
PINATA_SERVICE="pinata"

# Process pending files
for file in "\$TEMP_QUEUE"/*.json; do
  if [ -f "\$file" ]; then
    echo "Pinning \$(basename "\$file") to IPFS pinning service..."
    CID=\$(ipfs add -Q "\$file")
    if [ -n "\$CID" ]; then
      # If Pinata is configured, pin there
      if ipfs pin remote ls --service="\$PINATA_SERVICE" &>/dev/null; then
        ipfs pin remote add --service="\$PINATA_SERVICE" "\$CID"
        echo "Pinned \$CID to \$PINATA_SERVICE"
      else
        echo "Pinning service not configured, only storing locally."
      fi
      
      # Mark as processed
      mkdir -p "\$TEMP_QUEUE/processed"
      mv "\$file" "\$TEMP_QUEUE/processed/\$(basename "\$file")"
    else
      echo "Failed to add \$(basename "\$file") to IPFS"
    fi
  fi
done

# Update usage statistics
curl -s -X POST http://localhost:5000/api/storage/status > /dev/null
EOF

chmod +x $SCRIPTS_DIR/ipfs_pin_service.sh

# Add cron job for regular pinning
(crontab -l 2>/dev/null; echo "*/10 * * * * $SCRIPTS_DIR/ipfs_pin_service.sh") | crontab -

# Create H100 cluster setup script
echo "Creating H100 cluster setup script..."
cat > $SCRIPTS_DIR/h100-cluster/setup_h100_node.sh << 'EOF'
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

chmod +x $SCRIPTS_DIR/h100-cluster/setup_h100_node.sh

# Create H100 deployment guide
cat > $SCRIPTS_DIR/h100-cluster/README.md << 'EOF'
# H100 Cluster Deployment Guide

This guide explains how to deploy the 757Built system to Prime Intellect H100 cluster.

## Prerequisites

1. A running server1 instance (AlmaLinux 8 with cPanel) with this setup script completed
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
      scp SCRIPTS_DIR/h100-cluster/setup_h100_node.sh ubuntu@H100_NODE_IP:/tmp/
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

# Generate IPNS key for publishing (if not already done)
if ! ipfs key list | grep -q "757built_graph_key"; then
    ipfs key gen --type=rsa --size=2048 757built_graph_key
fi

# Create monitoring script
cat > $SCRIPTS_DIR/monitor_cluster.sh << 'EOF'
#!/bin/bash
echo "===== 757Built System Status ====="
echo "IPFS Status:"
ps aux | grep "ipfs daemon" | grep -v grep
echo "Document Processor Status:"
ps aux | grep "enhanced_document_processor.py" | grep -v grep
echo "API Status:"
ps aux | grep "gunicorn" | grep -v grep
echo "Redis Queue Status:"
redis-cli info | grep connected_clients
redis-cli llen document_queue
echo "Worker Nodes:"
redis-cli smembers active_workers
echo "Storage Nodes:"
redis-cli hkeys storage_nodes
echo "=============================="
EOF

chmod +x $SCRIPTS_DIR/monitor_cluster.sh

# Create startup script for cPanel environment
cat > $SCRIPTS_DIR/start_services.sh << EOF
#!/bin/bash

# Start IPFS daemon
$SCRIPTS_DIR/run_ipfs.sh &
sleep 5  # Wait for IPFS to start

# Start document processor
$SCRIPTS_DIR/run_processor.sh &

# Start API server
$SCRIPTS_DIR/run_api.sh &

echo "Services started"
echo "Check status with $SCRIPTS_DIR/monitor_cluster.sh"
EOF

chmod +x $SCRIPTS_DIR/start_services.sh

# Create a php info file in public_html to show API status
cat > $PUBLIC_HTML/757built_status.php << 'EOF'
<?php
header('Content-Type: application/json');

// Define services to check
$services = [
    'redis' => ['port' => 6379, 'host' => '127.0.0.1'],
    'ipfs_api' => ['port' => 5001, 'host' => '127.0.0.1'],
    'api_server' => ['port' => 5000, 'host' => '127.0.0.1']
];

$results = [];

// Check each service
foreach ($services as $name => $config) {
    $socket = @fsockopen($config['host'], $config['port'], $errno, $errstr, 1);
    $results[$name] = [
        'status' => $socket ? 'running' : 'offline',
        'error' => $socket ? null : "$errno: $errstr"
    ];
    if ($socket) {
        fclose($socket);
    }
}

// Check cluster status via API if available
if ($results['api_server']['status'] === 'running') {
    $api_result = @file_get_contents('http://localhost:5000/api/cluster/status');
    if ($api_result) {
        $results['cluster'] = json_decode($api_result, true);
    } else {
        $results['cluster'] = ['error' => 'Could not connect to cluster API'];
    }
}

// Output results
echo json_encode([
    'system' => 'AlmaLinux 8 cPanel',
    'timestamp' => date('Y-m-d H:i:s'),
    'services' => $results
], JSON_PRETTY_PRINT);
EOF

echo "===== 757Built Server1 Setup Complete ====="
echo "IMPORTANT: Next steps:"
echo "1. Download the Phi-3 model:"
echo "   wget -O $MODELS_DIR/phi3-q3_k_l.gguf https://huggingface.co/microsoft/phi-3-mini-4k-instruct-gguf/resolve/main/phi-3-mini-4k-instruct.Q4_K_M.gguf"
echo ""
echo "2. Configure IPFS pinning service (optional):"
echo "   ipfs pin remote service add pinata https://api.pinata.cloud/psa YOUR_PINATA_JWT_TOKEN"
echo ""
echo "3. Start the services:"
echo "   $SCRIPTS_DIR/start_services.sh"
echo ""
echo "4. Deploy H100 cluster from Prime Intellect:"
echo "   Follow instructions in $SCRIPTS_DIR/h100-cluster/README.md"
echo ""
echo "5. Monitor the system:"
echo "   $SCRIPTS_DIR/monitor_cluster.sh"
echo ""
echo "6. Access system status page:"
echo "   https://yourdomain.com/757built_status.php"
echo ""
echo "7. Configure GitHub secrets for CI/CD automation:"
echo "   - IPFS_API: /ip4/127.0.0.1/tcp/5001"
echo "   - GRAPH_IPNS_KEY: 757built_graph_key"
echo "==============================" 