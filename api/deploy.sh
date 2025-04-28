#!/bin/bash
set -e

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
  echo "Please run as root"
  exit 1
fi

# Install system dependencies
apt-get update
apt-get install -y apache2 php8.1 php8.1-mysql php8.1-mbstring php8.1-xml php8.1-curl mariadb-server

# Enable required Apache modules
a2enmod rewrite
a2enmod ssl

# Configure Apache virtual host
cat > /etc/apache2/sites-available/757built-api.conf << 'EOF'
<VirtualHost *:443>
    ServerName api.757built.com
    DocumentRoot /var/www/757built-api

    SSLEngine on
    SSLCertificateFile /etc/ssl/certs/757built-api.crt
    SSLCertificateKeyFile /etc/ssl/private/757built-api.key

    <Directory /var/www/757built-api>
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>

    ErrorLog ${APACHE_LOG_DIR}/757built-api_error.log
    CustomLog ${APACHE_LOG_DIR}/757built-api_access.log combined
</VirtualHost>
EOF

# Create web directory
mkdir -p /var/www/757built-api

# Copy API files
cp -r . /var/www/757built-api/
chown -R www-data:www-data /var/www/757built-api

# Set up database
mysql -e "CREATE DATABASE IF NOT EXISTS 757built;"
mysql -e "CREATE USER IF NOT EXISTS '757built'@'localhost' IDENTIFIED BY 'CHANGE_THIS_PASSWORD';"
mysql -e "GRANT ALL PRIVILEGES ON 757built.* TO '757built'@'localhost';"
mysql -e "FLUSH PRIVILEGES;"
mysql 757built < dbtable.sql

# Create config file from template
cat > /var/www/757built-api/config/database.php << 'EOF'
<?php
return [
    'host' => 'localhost',
    'dbname' => '757built',
    'username' => '757built',
    'password' => 'CHANGE_THIS_PASSWORD'
];
EOF

# Enable site and restart Apache
a2ensite 757built-api
systemctl restart apache2

echo "API deployment complete!"
echo "Please ensure you:"
echo "1. Update the database password in /var/www/757built-api/config/database.php"
echo "2. Install SSL certificates in /etc/ssl/certs/757built-api.crt and /etc/ssl/private/757built-api.key"
echo "3. Update DNS records to point api.757built.com to this server"
echo "4. Update the frontend configuration to use the new API endpoint" 