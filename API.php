<?php
// api/technology-data.php

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *'); // Allow cross-origin requests
header('Access-Control-Allow-Methods: 'GET, OPTIONS');
header('Access-Control-Allow-Headers: 'Content-Type');

// Database connection
$db_host = getenv('DB_HOST') ?: 'localhost';
$db_name = getenv('DB_NAME') ?: '757built_db';
$db_user = getenv('DB_USER') ?: 'db_user';
$db_pass = getenv('DB_PASSWORD') ?: 'password';

try {
    $db = new PDO("mysql:host=$db_host;dbname=$db_name", $db_user, $db_pass);
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch(PDOException $e) {
    echo json_encode(['error' => 'Database connection failed: ' . $e->getMessage()]);
    exit;
}

// Get technology area from request
$area = isset($_GET['area']) ? $_GET['area'] : null;

if (!$area) {
    // Return list of all technology areas
    $stmt = $db->prepare("SELECT id, name, slug, description FROM technology_areas");
    $stmt->execute();
    echo json_encode(['technology_areas' => $stmt->fetchAll(PDO::FETCH_ASSOC)]);
} else {
    // Get consolidated data for the specific technology area
    $stmt = $db->prepare("
        SELECT c.*, t.name as technology_area_name 
        FROM consolidated_developments c
        JOIN technology_areas t ON c.technology_area_id = t.id
        WHERE t.slug = :slug OR t.name = :name
        ORDER BY c.consolidation_date DESC
        LIMIT 1
    ");
    $stmt->execute(['slug' => strtolower(str_replace(' ', '-', $area)), 'name' => $area]);
    $result = $stmt->fetch(PDO::FETCH_ASSOC);
    
    if ($result) {
        echo json_encode($result);
    } else {
        echo json_encode(['error' => 'Technology area not found']);
    }
}
?>
