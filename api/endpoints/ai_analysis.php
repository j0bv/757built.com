<?php
// Include helper classes
require_once __DIR__ . '/../helpers/ai_client.php';
require_once __DIR__ . '/../config/database.php';

// Handle request
$request_method = $_SERVER['REQUEST_METHOD'];
$content_type = isset($_SERVER['CONTENT_TYPE']) ? $_SERVER['CONTENT_TYPE'] : '';

// Only allow POST requests
if ($request_method !== 'POST') {
    http_response_code(405);
    echo json_encode([
        'status' => 'error',
        'message' => 'Method not allowed. Use POST.'
    ]);
    exit;
}

// Check content type
if (strpos($content_type, 'application/json') === false) {
    http_response_code(400);
    echo json_encode([
        'status' => 'error',
        'message' => 'Content-Type must be application/json'
    ]);
    exit;
}

// Get JSON input
$input = json_decode(file_get_contents('php://input'), true);

// Validate required fields
if (!isset($input['text']) || !isset($input['technology_area'])) {
    http_response_code(400);
    echo json_encode([
        'status' => 'error',
        'message' => 'Missing required fields: text and technology_area'
    ]);
    exit;
}

// Initialize Ollama client
$ai_client = new OllamaClient();

// Process the request
$result = $ai_client->extractStructuredData($input['text'], $input['technology_area']);

if (!$result) {
    http_response_code(500);
    echo json_encode([
        'status' => 'error',
        'message' => 'Failed to process text with AI model'
    ]);
    exit;
}

// Add metadata
$result['meta'] = [
    'technology_area' => $input['technology_area'],
    'analysis_date' => date('c'),
    'model' => 'phi3'
];

// Return the structured data
echo json_encode([
    'status' => 'success',
    'data' => $result
]);
?> 