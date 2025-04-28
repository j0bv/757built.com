<?php
// API endpoint to receive IPFS hashes from the AI Processing server
header('Content-Type: application/json');

// Load environment variables
if (file_exists('../.env')) {
    $env = parse_ini_file('../.env');
    foreach ($env as $key => $value) {
        putenv("$key=$value");
    }
}

// Verify API key - use a secure method in production
$api_key = getenv('API_KEY');
$provided_key = isset($_SERVER['HTTP_X_API_KEY']) ? $_SERVER['HTTP_X_API_KEY'] : '';

if (!$api_key || $provided_key !== $api_key) {
    http_response_code(401);
    echo json_encode(['error' => 'Unauthorized']);
    exit;
}

// Get request data
$data = json_decode(file_get_contents('php://input'), true);

if (!$data || !isset($data['ipfs_hash']) || !isset($data['document_name'])) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid request data']);
    exit;
}

// Connect to database
$db_host = getenv('DB_HOST') ?: 'localhost';
$db_name = getenv('DB_NAME') ?: 'ybqiflhd_757built';
$db_user = getenv('DB_USER') ?: 'ybqiflhd_admin';
$db_pass = getenv('DB_PASSWORD');

try {
    $conn = new PDO("mysql:host=$db_host;dbname=$db_name", $db_user, $db_pass);
    $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    
    // Create ipfs_hashes table if it doesn't exist
    $conn->exec("CREATE TABLE IF NOT EXISTS ipfs_hashes (
        id INT AUTO_INCREMENT PRIMARY KEY,
        ipfs_hash VARCHAR(255) NOT NULL,
        document_name VARCHAR(255) NOT NULL,
        document_type VARCHAR(100),
        technology_area_id INT,
        metadata TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (technology_area_id) REFERENCES technology_areas(id)
    )");
    
    // Insert the IPFS hash
    $stmt = $conn->prepare("
        INSERT INTO ipfs_hashes 
        (ipfs_hash, document_name, document_type, technology_area_id, metadata) 
        VALUES (?, ?, ?, ?, ?)
    ");
    
    $stmt->execute([
        $data['ipfs_hash'],
        $data['document_name'],
        $data['document_type'] ?? 'document',
        $data['technology_area_id'] ?? null,
        isset($data['metadata']) ? json_encode($data['metadata']) : null
    ]);
    
    echo json_encode([
        'success' => true,
        'message' => 'IPFS hash recorded',
        'id' => $conn->lastInsertId()
    ]);
    
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Database error', 'message' => $e->getMessage()]);
}
?> 