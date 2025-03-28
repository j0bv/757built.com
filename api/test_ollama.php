<?php
require_once 'helpers/ai_client.php';

// Simple test
$client = new OllamaClient();
$result = $client->generateResponse("What is Hampton Roads known for in technology development?");

if ($result && isset($result['response'])) {
    echo "<h2>Ollama Connection Successful</h2>";
    echo "<p><strong>Test Query:</strong> What is Hampton Roads known for in technology development?</p>";
    echo "<p><strong>Response:</strong></p>";
    echo "<pre>" . htmlspecialchars($result['response']) . "</pre>";
} else {
    echo "<h2>Ollama Connection Failed</h2>";
    echo "<p>Could not connect to the Ollama server or receive a valid response.</p>";
    echo "<p>Check your OLLAMA_ENDPOINT setting and ensure the server is running.</p>";
}
?> 