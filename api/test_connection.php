<?php
// Define whether we're in debug mode for this test
define('DEBUG_MODE', true);

// Include the database configuration
require_once 'config/database.php';

// Try to connect
$db = getDbConnection();

if ($db) {
    echo "Connection successful!";
    
    // Try a simple query
    try {
        $stmt = $db->query("SHOW TABLES");
        $tables = $stmt->fetchAll(PDO::FETCH_COLUMN);
        
        echo "<br><br>Tables in database:<br>";
        foreach ($tables as $table) {
            echo "- $table<br>";
        }
    } catch (PDOException $e) {
        echo "<br><br>Query error: " . $e->getMessage();
    }
} else {
    echo "Connection failed!";
}
?> 