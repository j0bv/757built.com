#!/bin/bash

# Deploy 757built.com to cPanel server
# This script should be run locally to deploy to Server 1

echo "Deploying 757built.com to web server..."

# SSH command with key authentication
SSH_CMD="ssh -p 21098 ybqiflhd@server250.web-hosting.com"

# Create necessary directories
$SSH_CMD "mkdir -p ~/public_html"

# Clone the GitHub repository
$SSH_CMD "cd ~/public_html && git clone https://github.com/j0bv/757built.com.git ."

# Set up MySQL database tables
$SSH_CMD "cd ~/public_html && php create_tables.php"

# Set up cron job for auto updates
$SSH_CMD "crontab -l > mycron"
$SSH_CMD "echo '0 */6 * * * cd ~/public_html && git pull origin main' >> mycron"
$SSH_CMD "crontab mycron"
$SSH_CMD "rm mycron"

echo "Deployment complete!" 