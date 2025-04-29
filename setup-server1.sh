#!/bin/bash
# Setup script for 757Built API server

set -e

echo "Setting up 757Built.com API server..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
  echo "Please run as root"
  exit 1
fi

# Install system dependencies
apt-get update
apt-get install -y nginx python3 python3-pip python3-venv 

# Set up directories
mkdir -p /var/www/api.757built.com
mkdir -p /var/www/757built.com

# Clone or pull content if needed
echo "Fetching content from repository..."
SRC="https://github.com/your-username/757built.com.git"

if [ -d "/var/www/757built.com" ]; then
  cd /var/www/757built.com
  git pull
else
  cd /var/www
  git clone $SRC 757built.com
fi

# Set up API environment
cd /var/www/757built.com/api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create systemd service
cat > /etc/systemd/system/757built-api.service << EOF
[Unit]
Description=757Built API Service
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/757built.com/api
Environment="PATH=/var/www/757built.com/api/venv/bin"
ExecStart=/var/www/757built.com/api/venv/bin/python api_server.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx
cat > /etc/nginx/sites-available/757built.com << EOF
server {
    listen 80;
    server_name 757built.com www.757built.com;

    root /var/www/757built.com/public_html;
    index index.html;

    location / {
        try_files \$uri \$uri/ =404;
    }
}

server {
    listen 80;
    server_name api.757built.com;

    location / {
        proxy_pass http://localhost:5000/api/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

# Enable sites
ln -sf /etc/nginx/sites-available/757built.com /etc/nginx/sites-enabled/

# Set permissions
chown -R www-data:www-data /var/www/757built.com

# Reload services
systemctl daemon-reload
systemctl enable 757built-api
systemctl start 757built-api
systemctl restart nginx

echo "Setup complete! 757Built API server is now running."
echo "You should set up SSL certificates with Certbot for production use." 