<?php
// Define constants
define('DEBUG_MODE', filter_var(getenv('DEBUG_MODE') ?: false, FILTER_VALIDATE_BOOLEAN));

// Load environment variables if dotenv is available
if (file_exists(__DIR__ . '/../../.env')) {
    if (class_exists('Dotenv\Dotenv')) {
        $dotenv = Dotenv\Dotenv::createImmutable(__DIR__ . '/../..');
        $dotenv->load();
    }
}

// Database connection function
function getDbConnection() {
    // Load configuration from environment variables
    $db_host = getenv('DB_HOST') ?: 'localhost';
    $db_name = getenv('DB_NAME');
    $db_user = getenv('DB_USER');
    $db_pass = getenv('DB_PASSWORD');
    
    // Check if credentials are available
    if (!$db_name || !$db_user || !$db_pass) {
        error_log('Database credentials not found in environment variables');
        return false;
    }
    
    try {
        $db = new PDO("mysql:host=$db_host;dbname=$db_name;charset=utf8mb4", $db_user, $db_pass);
        $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        $db->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
        $db->setAttribute(PDO::ATTR_EMULATE_PREPARES, false);
        return $db;
    } catch(PDOException $e) {
        if (DEBUG_MODE) {
            throw $e; // Re-throw in debug mode
        } else {
            // Log error silently in production
            error_log('Database connection error: ' . $e->getMessage());
            return false;
        }
    }
}
?> 