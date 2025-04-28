#!/bin/bash
set -e

echo "=== Setting up 757Built backend on server1 ==="

# Install dependencies
echo "Installing dependencies..."
apt-get update
apt-get install -y python3 python3-venv python3-pip redis-server nginx

# Enable and start Redis
systemctl enable --now redis

# Pull content from server250 if needed
if [ "$1" == "--pull" ]; then
  echo "Pulling content from server250..."
  SRC="ybqiflhd@server250:~/757built.com"
  DST="~/757built.com"
  mkdir -p $DST
  rsync -av --delete \
      --include='Agent/***' \
      --include='api/***'   \
      --include='data/***'  \
      --exclude='*'         \
      $SRC/ $DST/
fi

# Set up Python environment
echo "Setting up Python environment..."
cd ~/757built.com/Agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt llama-cpp-python redis ipfshttpclient flask flask-cors gunicorn

# Install systemd service files
echo "Installing service files..."
cp ~/757built.com/Agent/document-processor.service /etc/systemd/system/
cp ~/757built.com/api/api-server.service /etc/systemd/system/
systemctl daemon-reload

# Create lightweight web folder (optional IPFS gateway fallback page)
echo "Creating web directory..."
mkdir -p /var/www/757built
echo '<h1>Agent node running</h1>' > /var/www/757built/index.html

# Configure Nginx as reverse proxy
echo "Configuring Nginx..."
cat > /etc/nginx/sites-available/757built << 'EOF'
server {
    listen 80;
    server_name _;

    location / {
        root /var/www/757built;
        index index.html;
    }

    location /api/ {
        proxy_pass http://localhost:5000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

ln -sf /etc/nginx/sites-available/757built /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# Enable and start services
echo "Starting services..."
systemctl enable document-processor api-server
systemctl start document-processor
systemctl start api-server

echo "=== Setup complete ==="
echo "You can check service status with:"
echo "  systemctl status document-processor"
echo "  systemctl status api-server"
echo "  journalctl -u document-processor -f"
echo "  journalctl -u api-server -f"
echo
echo "API endpoints available at:"
echo "  http://server1:5000/api/projects"
echo "  http://server1:5000/api/graph/subgraph/root" 