<?php
// Database setup script for 757built.com
// This will create the necessary tables for storing development data

// Load environment variables from .env file
$env_file = __DIR__ . '/.env';
if (file_exists($env_file)) {
    $env = parse_ini_file($env_file);
    if ($env) {
        foreach ($env as $key => $value) {
            putenv("$key=$value");
        }
    }
}

// Database connection details
$db_host = getenv('DB_HOST') ?: 'localhost';
$db_name = getenv('DB_NAME') ?: 'your_database_name';
$db_user = getenv('DB_USER') ?: 'your_database_user';
$db_pass = getenv('DB_PASSWORD');

if (!$db_pass) {
    die("Error: DB_PASSWORD environment variable must be set.");
}

try {
    // Connect to database
    $conn = new PDO("mysql:host=$db_host;dbname=$db_name", $db_user, $db_pass);
    $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    
    echo "Connected to database successfully.\n";
    
    // Create technology_areas table
    $conn->exec("CREATE TABLE IF NOT EXISTS technology_areas (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        slug VARCHAR(255) NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    )");
    echo "Table 'technology_areas' created or already exists.\n";
    
    // Create consolidated_developments table
    $conn->exec("CREATE TABLE IF NOT EXISTS consolidated_developments (
        id INT AUTO_INCREMENT PRIMARY KEY,
        technology_area_id INT NOT NULL,
        key_players TEXT,
        technological_development TEXT,
        project_cost TEXT,
        event_location VARCHAR(255),
        information_date DATE,
        contact_information TEXT,
        number_of_sources INT DEFAULT 0,
        consolidation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (technology_area_id) REFERENCES technology_areas(id)
    )");
    echo "Table 'consolidated_developments' created or already exists.\n";
    
    // Create sources table
    $conn->exec("CREATE TABLE IF NOT EXISTS sources (
        id INT AUTO_INCREMENT PRIMARY KEY,
        development_id INT NOT NULL,
        source_url VARCHAR(255),
        source_date DATE,
        source_content TEXT,
        FOREIGN KEY (development_id) REFERENCES consolidated_developments(id)
    )");
    echo "Table 'sources' created or already exists.\n";
    
    // Create table for geographic coordinates
    $conn->exec("CREATE TABLE IF NOT EXISTS development_locations (
        id INT AUTO_INCREMENT PRIMARY KEY,
        development_id INT NOT NULL,
        latitude DECIMAL(10, 8) NOT NULL,
        longitude DECIMAL(11, 8) NOT NULL,
        location_name VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (development_id) REFERENCES consolidated_developments(id)
    )");
    echo "Table 'development_locations' created or already exists.\n";
    
    echo "All tables created successfully!\n";
    
} catch(PDOException $e) {
    echo "Error: " . $e->getMessage() . "\n";
}

// Create .htaccess file for API security
file_put_contents('api/.htaccess', "
RewriteEngine On
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^(.*)$ index.php [QSA,L]

# Prevent directory listing
Options -Indexes

# Basic security headers
<IfModule mod_headers.c>
    Header set X-Content-Type-Options \"nosniff\"
    Header set X-Frame-Options \"SAMEORIGIN\"
    Header set X-XSS-Protection \"1; mode=block\"
</IfModule>
");

echo "API security configured.\n";
?> 