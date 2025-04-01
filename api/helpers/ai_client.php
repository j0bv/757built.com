<?php
class OllamaClient {
    private $endpoint;
    private $model;
    private $timeout;
    
    public function __construct($model = 'phi3', $timeout = 30) {
        // Get Ollama endpoint from environment variable or use default
        $this->endpoint = getenv('OLLAMA_ENDPOINT') ?: 'http://your-ollama-server-ip:11434/api/generate';
        $this->model = $model;
        $this->timeout = $timeout;
    }
    
    /**
     * Send a prompt to Ollama and get the response
     * 
     * @param string $prompt The text prompt to send to the model
     * @param array $options Additional options for the model
     * @return array|bool The JSON response or false on failure
     */
    public function generateResponse($prompt, $options = []) {
        // Set default options
        $defaultOptions = [
            'temperature' => 0.1,
            'top_p' => 0.9,
            'max_tokens' => 1024
        ];
        
        // Merge with provided options
        $options = array_merge($defaultOptions, $options);
        
        // Prepare the request payload
        $payload = [
            'model' => $this->model,
            'prompt' => $prompt,
            'stream' => false,
            'options' => $options
        ];
        
        // Initialize cURL
        $ch = curl_init($this->endpoint);
        
        // Set cURL options
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($payload));
        curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
        curl_setopt($ch, CURLOPT_TIMEOUT, $this->timeout);
        
        // Execute the request
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        
        // Check for errors
        if (curl_errno($ch)) {
            error_log('Ollama API error: ' . curl_error($ch));
            curl_close($ch);
            return false;
        }
        
        curl_close($ch);
        
        // Check HTTP response code
        if ($httpCode !== 200) {
            error_log('Ollama API returned HTTP code ' . $httpCode . ': ' . $response);
            return false;
        }
        
        // Parse the JSON response
        $responseData = json_decode($response, true);
        if (json_last_error() !== JSON_ERROR_NONE) {
            error_log('Failed to parse Ollama response: ' . json_last_error_msg());
            return false;
        }
        
        return $responseData;
    }
    
    /**
     * Extract structured data from text using Phi3
     * 
     * @param string $text The text to analyze
     * @param string $technology_area The technology area to focus on
     * @return array|bool The structured data or false on failure
     */
    public function extractStructuredData($text, $technology_area) {
        $prompt = "You are an AI assistant specialized in extracting structured information about technology developments.
        
Task: Analyze the following web content about {$technology_area} and extract specific information.

Content: " . substr($text, 0, 3000) . "

Extract and format the following information as JSON:
1. Key Role Players: Identify individuals, organizations, or companies leading the development.
2. Technological Development: Describe specific technological advancements or innovations.
3. Project Cost: Provide details on funding or financial investments if available.
4. Date of Information Release: Include the latest date of updates or announcements.
5. Event Location: Specify the geographical location of the development.
6. Contact Information: Extract publicly accessible contact details if available.

If information for a category is not found, indicate with \"Not found in source\".
Format your response STRICTLY as a valid JSON object with these fields and nothing else.";

        $response = $this->generateResponse($prompt);
        
        if (!$response || !isset($response['response'])) {
            return false;
        }
        
        // Try to extract JSON from the response
        try {
            $jsonData = json_decode($response['response'], true);
            
            // Check if we got valid JSON
            if (json_last_error() !== JSON_ERROR_NONE) {
                // Try to extract JSON using regex
                preg_match('/(\{.*\})/s', $response['response'], $matches);
                if (isset($matches[0])) {
                    $jsonData = json_decode($matches[0], true);
                    if (json_last_error() !== JSON_ERROR_NONE) {
                        throw new Exception("Could not parse JSON from response");
                    }
                } else {
                    throw new Exception("Could not find JSON in response");
                }
            }
            
            return $jsonData;
            
        } catch (Exception $e) {
            error_log('Error extracting structured data: ' . $e->getMessage());
            return false;
        }
    }
}
?> 