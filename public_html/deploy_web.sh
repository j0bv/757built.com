#!/bin/bash
# Web deployment script for 757built.com

# Configuration - Fill these with your actual values
DEPLOY_USER="your_username"
DEPLOY_HOST="your_hostname"
DEPLOY_PORT="22"  # Standard SSH port
REMOTE_DIR="public_html"

# SSH command
SSH_CMD="ssh -p $DEPLOY_PORT $DEPLOY_USER@$DEPLOY_HOST"

# Local files to deploy
SOURCE_DIR="./public_html/"

echo "Deploying 757built.com website..."

# Create deployment archive
echo "Creating deployment archive..."
tar -czf deploy.tar.gz $SOURCE_DIR

# Copy files
echo "Uploading files to server..."
scp -P $DEPLOY_PORT deploy.tar.gz "$DEPLOY_USER@$DEPLOY_HOST:~/"

# Extract on remote server
echo "Extracting files on server..."
$SSH_CMD "cd ~/ && tar -xzf deploy.tar.gz -C $REMOTE_DIR --strip-components=1 && rm deploy.tar.gz"

# Clean up local archive
rm deploy.tar.gz

echo "Deployment completed!" 