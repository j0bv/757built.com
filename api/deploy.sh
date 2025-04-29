#!/bin/bash
# Deployment script for 757Built API server

# Exit on error
set -e 

echo "Starting 757Built API server deployment..."

# Ensure root privileges
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 
   exit 1
fi

# Install required packages
apt-get update
apt-get install -y apache2 php mysql-server php-mysql libapache2-mod-php php-curl php-xml php-gd php-mbstring

# Enable Apache modules
a2enmod rewrite
a2enmod ssl
a2enmod proxy
a2enmod proxy_http

# Create Apache configuration
cat > /etc/apache2/sites-available/757built-api.conf << 'EOF'
<VirtualHost *:443>
    ServerName api.757built.com
    ServerAdmin webmaster@757built.com
    DocumentRoot /var/www/757built-api

    <Directory /var/www/757built-api>
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>

    ErrorLog ${APACHE_LOG_DIR}/757built-api-error.log
    CustomLog ${APACHE_LOG_DIR}/757built-api-access.log combined

    SSLEngine on
    SSLCertificateFile /etc/ssl/certs/757built-api.crt
    SSLCertificateKeyFile /etc/ssl/private/757built-api.key

    ProxyPreserveHost On

    # API endpoints
    ProxyPass /api/ http://localhost:5000/api/
    ProxyPassReverse /api/ http://localhost:5000/api/
</VirtualHost>
EOF

# Set up MySQL database and user
echo "Setting up MySQL database..."
mysql -e "CREATE DATABASE IF NOT EXISTS 757built_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -e "CREATE USER IF NOT EXISTS '757built'@'localhost' IDENTIFIED BY '';"
mysql -e "GRANT ALL PRIVILEGES ON 757built_db.* TO '757built'@'localhost';"
mysql -e "FLUSH PRIVILEGES;"

# Create directory structure
mkdir -p /var/www/757built-api/config

# Create database configuration
cat > /var/www/757built-api/config/database.php << 'EOF'
<?php
return [
    'host' => 'localhost',
    'database' => '757built_db',
    'user' => '757built',
    'password' => ''
];
EOF

# Set permissions
chown -R www-a:www-data /var/www/757built-api
chmod -R 755 /var/www/757built-api

# Enable site and restart Apache
a2ensite 757built-api.conf
systemctl restart apache2

echo "Deployment completed!"
echo "Please complete the following manual steps:"
echo "1. Update the database password in /var/www/757built-api/config/database.php"
echo "2. Install SSL certificates in /etc/ssl/certs/757built-api.crt and /etc/ssl/private/757built-api.key"
echo "3. Copy the API files to /var/www/757built-api/" 