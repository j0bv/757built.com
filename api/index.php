<?php
// Load Composer autoloader if it exists
if (file_exists(__DIR__ . '/../vendor/autoload.php')) {
    require __DIR__ . '/../vendor/autoload.php';
}

// Load rate limiter middleware
require_once __DIR__ . '/middleware/rate_limiter.php';
checkRateLimit();

// Main API entry point
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *'); // Allow cross-origin requests
header('Access-Control-Allow-Methods: GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

// Basic route handling
$request_uri = $_SERVER['REQUEST_URI'];
$path = parse_url($request_uri, PHP_URL_PATH);
$path_parts = explode('/', trim($path, '/'));

// Remove 'api' from the path if it's the first part
if ($path_parts[0] === 'api') {
    array_shift($path_parts);
}

// Route the request
if (empty($path_parts[0])) {
    // API root - show available endpoints
    echo json_encode([
        'status' => 'success',
        'message' => '757Built API',
        'version' => '1.0',
        'endpoints' => [
            '/api/technologies' => 'List all technology areas',
            '/api/technologies/{slug}' => 'Get details for a specific technology area',
            '/api/cities' => 'List all cities in Hampton Roads',
            '/api/cities/{name}/technologies' => 'Get technologies for a specific city'
        ]
    ]);
} elseif ($path_parts[0] === 'technologies') {
    include_once 'endpoints/technologies.php';
} elseif ($path_parts[0] === 'cities') {
    include_once 'endpoints/cities.php';
} else {
    // Unknown endpoint
    http_response_code(404);
    echo json_encode([
        'status' => 'error',
        'message' => 'Endpoint not found'
    ]);
}
?> 