<?php
// Simple rate limiter based on IP address
function checkRateLimit() {
    $ip = $_SERVER['REMOTE_ADDR'];
    $cacheDir = sys_get_temp_dir() . '/757built_ratelimit';
    
    // Create cache directory if it doesn't exist
    if (!file_exists($cacheDir)) {
        mkdir($cacheDir, 0755, true);
    }
    
    $cacheFile = $cacheDir . '/' . md5($ip);
    
    // Check if file exists
    if (file_exists($cacheFile)) {
        $data = json_decode(file_get_contents($cacheFile), true);
        
        // Reset count if the hour has changed
        if (date('YmdH') > $data['timestamp']) {
            $data = [
                'count' => 1,
                'timestamp' => date('YmdH')
            ];
        } else {
            // Increment count
            $data['count']++;
            
            // Check if over limit
            if ($data['count'] > 100) { // 100 requests per hour
                http_response_code(429);
                header('Retry-After: ' . (3600 - (time() % 3600)));
                echo json_encode([
                    'status' => 'error',
                    'message' => 'Rate limit exceeded. Try again later.'
                ]);
                exit;
            }
        }
    } else {
        // First request in this hour
        $data = [
            'count' => 1,
            'timestamp' => date('YmdH')
        ];
    }
    
    // Save the data
    file_put_contents($cacheFile, json_encode($data));

    $cacheDir = sys_get_temp_dir() . '/757built_ratelimit';
    
    // Create cache directory if it doesn't exist
    if (!file_exists($cacheDir)) {
        mkdir($cacheDir, 0755, true);
    }
    
    $cacheFile = $cacheDir . '/' . md5($ip);
    
    // Add headers
    header('X-RateLimit-Limit: 100');
    header('X-RateLimit-Remaining: ' . (100 - $data['count']));
    header('X-RateLimit-Reset: ' . (3600 - (time() % 3600)));
    
}

// Include this at the top of index.php
checkRateLimit();
?> 