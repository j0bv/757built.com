<?php
// Database connection
require_once '../config/database.php';
$db = getDbConnection();

// Get the specific technology slug if provided
$slug = isset($path_parts[1]) ? $path_parts[1] : null;

if (!$slug) {
    // List all technology areas
    try {
        $stmt = $db->prepare("SELECT id, name, slug, description FROM technology_areas");
        $stmt->execute();
        $technologies = $stmt->fetchAll(PDO::FETCH_ASSOC);
        
        echo json_encode([
            'status' => 'success',
            'count' => count($technologies),
            'data' => $technologies
        ]);
    } catch (PDOException $e) {
        http_response_code(500);
        echo json_encode([
            'status' => 'error',
            'message' => 'Database error',
            'details' => DEBUG_MODE ? $e->getMessage() : null
        ]);
    }
} else {
    // Get details for specific technology area
    try {
        $stmt = $db->prepare("
            SELECT c.*, t.name as technology_area_name, t.description
            FROM consolidated_developments c
            JOIN technology_areas t ON c.technology_area_id = t.id
            WHERE t.slug = :slug
            ORDER BY c.consolidation_date DESC
            LIMIT 1
        ");
        $stmt->execute(['slug' => $slug]);
        $result = $stmt->fetch(PDO::FETCH_ASSOC);
        
        if ($result) {
            echo json_encode([
                'status' => 'success',
                'data' => $result
            ]);
        } else {
            http_response_code(404);
            echo json_encode([
                'status' => 'error',
                'message' => 'Technology area not found'
            ]);
        }
    } catch (PDOException $e) {
        http_response_code(500);
        echo json_encode([
            'status' => 'error',
            'message' => 'Database error',
            'details' => DEBUG_MODE ? $e->getMessage() : null
        ]);
    }
}
?> 