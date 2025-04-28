#!/bin/bash
set -e

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
  echo "Please run as root"
  exit 1
fi

# Install system dependencies
apt-get update
apt-get install -y python3.11 python3.11-venv python3-pip git build-essential cmake

# Install IPFS if not present
if ! command -v ipfs &> /dev/null; then
    wget https://dist.ipfs.tech/kubo/v0.22.0/kubo_v0.22.0_linux-amd64.tar.gz
    tar -xvzf kubo_v0.22.0_linux-amd64.tar.gz
    cd kubo
    bash install.sh
    cd ..
    rm -rf kubo kubo_v0.22.0_linux-amd64.tar.gz
fi

# Initialize IPFS if not already initialized
if [ ! -d ~/.ipfs ]; then
    ipfs init
fi

# Install llama.cpp
if [ ! -d "/root/llama.cpp" ]; then
    git clone https://github.com/ggerganov/llama.cpp.git /root/llama.cpp
    cd /root/llama.cpp
    make
    cd -
fi

# Create and activate virtual environment
python3.11 -m venv /root/757built_env
source /root/757built_env/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Copy systemd service file
cp phi3-document-processor.service /etc/systemd/system/
systemctl daemon-reload

# Create necessary directories
mkdir -p /root/757built.com/crawler
mkdir -p /root/models

# Copy files to their locations
cp -r . /root/757built.com/crawler/

# Start services
systemctl enable ipfs
systemctl start ipfs
systemctl enable phi3-document-processor
systemctl start phi3-document-processor

echo "Backend deployment complete!"
echo "Please ensure you have:"
echo "1. Downloaded the phi3 model to /root/models/phi3-q3_k_l.gguf"
echo "2. Set up your IPNS keys using: ipfs key gen --type=rsa --size=2048 YOUR_KEY_NAME"
echo "3. Updated the IPFS_API and GRAPH_IPNS_KEY in GitHub repository secrets" 