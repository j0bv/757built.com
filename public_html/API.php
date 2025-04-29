<?php
// api/technology-data.php

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *'); // Allow cross-origin requests
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

// Load environment variables from .env file if it exists
$env_file = __DIR__ . '/.env';
if (file_exists($env_file)) {
    $env = parse_ini_file($env_file);
    if ($env) {
        foreach ($env as $key => $value) {
            putenv("$key=$value");
        }
    }
}

// Database connection
$db_host = getenv('DB_HOST') ?: 'localhost';
$db_name = getenv('DB_NAME') ?: 'your_database_name';
$db_user = getenv('DB_USER') ?: 'your_database_user';
$db_pass = getenv('DB_PASSWORD');

// Check if required credentials are available
if (!$db_pass) {
    header('HTTP/1.1 500 Internal Server Error');
    echo json_encode(['error' => 'Database configuration incomplete. Please set environment variables.']);
    exit;
}

try {
    // Connect to database
    $db = new PDO("mysql:host=$db_host;dbname=$db_name", $db_user, $db_pass);
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    
    // Get request path
    $request_uri = $_SERVER['REQUEST_URI'];
    $path = parse_url($request_uri, PHP_URL_PATH);
    $path_parts = explode('/', trim($path, '/'));
    
    // API endpoint handling
    $endpoint = $path_parts[count($path_parts) - 1];
    
    // Rate limiting - simple implementation
    $client_ip = $_SERVER['REMOTE_ADDR'];
    $rate_limit_key = "rate_limit:$client_ip";
    $current_time = time();
    $rate_limit_period = 60; // 1 minute
    $rate_limit_max = 60; // requests per minute
    
    // Check if rate limit file exists
    $rate_limit_file = sys_get_temp_dir() . "/rate_limits.json";
    $rate_limits = [];
    if (file_exists($rate_limit_file)) {
        $rate_limits = json_decode(file_get_contents($rate_limit_file), true);
    }
    
    // Check rate limit
    if (isset($rate_limits[$rate_limit_key])) {
        $limit_data = $rate_limits[$rate_limit_key];
        if ($current_time - $limit_data['timestamp'] > $rate_limit_period) {
            // Reset count if period expired
            $rate_limits[$rate_limit_key] = [
                'count' => 1,
                'timestamp' => $current_time
            ];
        } else if ($limit_data['count'] >= $rate_limit_max) {
            // Rate limit exceeded
            header('HTTP/1.1 429 Too Many Requests');
            echo json_encode(['error' => 'Rate limit exceeded. Please try again later.']);
            exit;
        } else {
            // Increment count
            $rate_limits[$rate_limit_key]['count']++;
        }
    } else {
        // First request
        $rate_limits[$rate_limit_key] = [
            'count' => 1,
            'timestamp' => $current_time
        ];
    }
    
    // Save rate limits
    file_put_contents($rate_limit_file, json_encode($rate_limits));
    
    // Route API requests
    switch ($endpoint) {
        case 'technology_areas':
            $stmt = $db->query("SELECT * FROM technology_areas");
            $result = $stmt->fetchAll(PDO::FETCH_ASSOC);
            echo json_encode(['technology_areas' => $result]);
            break;
            
        case 'technology_area':
            if (isset($_GET['slug'])) {
                $slug = $_GET['slug'];
                $stmt = $db->prepare("SELECT * FROM technology_areas WHERE slug = :slug");
                $stmt->bindParam(':slug', $slug);
                $stmt->execute();
                $technology_area = $stmt->fetch(PDO::FETCH_ASSOC);
                
                if ($technology_area) {
                    $area_id = $technology_area['id'];
                    $stmt = $db->prepare("SELECT * FROM consolidated_developments WHERE technology_area_id = :area_id");
                    $stmt->bindParam(':area_id', $area_id);
                    $stmt->execute();
                    $developments = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
                    $technology_area['developments'] = $developments;
                    echo json_encode($technology_area);
    } else {
        echo json_encode(['error' => 'Technology area not found']);
    }
            } else {
                echo json_encode(['error' => 'Missing slug parameter']);
            }
            break;
            
        default:
            echo json_encode([
                'api' => '757Built API',
                'version' => '1.0',
                'endpoints' => [
                    'technology_areas' => 'GET /api/technology_areas',
                    'technology_area' => 'GET /api/technology_area?slug={slug}'
                ]
            ]);
    }
} catch (PDOException $e) {
    header('HTTP/1.1 500 Internal Server Error');
    echo json_encode(['error' => 'Database error', 'details' => $e->getMessage()]);
}
?>
