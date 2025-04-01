<?php
// Database connection
require_once '../config/database.php';
$db = getDbConnection();

// Get the specific city if provided
$city = isset($path_parts[1]) ? $path_parts[1] : null;
$subResource = isset($path_parts[2]) ? $path_parts[2] : null;

if (!$city) {
    // List all cities
    try {
        $stmt = $db->prepare("
            SELECT DISTINCT event_location, COUNT(id) as technology_count
            FROM consolidated_developments
            WHERE event_location IS NOT NULL
            GROUP BY event_location
            ORDER BY event_location
        ");
        $stmt->execute();
        $cities = $stmt->fetchAll(PDO::FETCH_ASSOC);
        
        echo json_encode([
            'status' => 'success',
            'count' => count($cities),
            'data' => $cities
        ]);
    } catch (PDOException $e) {
        http_response_code(500);
        echo json_encode([
            'status' => 'error',
            'message' => 'Database error',
            'details' => DEBUG_MODE ? $e->getMessage() : null
        ]);
    }
} elseif ($city && $subResource === 'technologies') {
    // Get technologies for a specific city
    try {
        $stmt = $db->prepare("
            SELECT c.*, t.name as technology_area_name, t.slug, t.description
            FROM consolidated_developments c
            JOIN technology_areas t ON c.technology_area_id = t.id
            WHERE c.event_location LIKE :location
            ORDER BY c.consolidation_date DESC
        ");
        $stmt->execute(['location' => '%' . $city . '%']);
        $technologies = $stmt->fetchAll(PDO::FETCH_ASSOC);
        
        if ($technologies) {
            echo json_encode([
                'status' => 'success',
                'count' => count($technologies),
                'data' => $technologies
            ]);
        } else {
            http_response_code(404);
            echo json_encode([
                'status' => 'error',
                'message' => 'No technologies found for this city'
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
} else {
    // Invalid sub-resource
    http_response_code(404);
    echo json_encode([
        'status' => 'error',
        'message' => 'Endpoint not found'
    ]);
}
?> 