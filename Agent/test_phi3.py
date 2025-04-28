import requests
import json

def test_phi3():
    # Prepare the request to Ollama
    endpoint = "http://localhost:11434/api/generate"
    payload = {
        "model": "phi3",
        "prompt": "What are the key technology sectors in Hampton Roads, Virginia?",
        "stream": False
    }
    
    try:
        # Send the request
        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        
        # Parse the response
        result = response.json()
        
        # Print the result
        print("Phi3 Response:")
        print(result['response'])
        
        return True
    except Exception as e:
        print(f"Error testing Phi3: {e}")
        return False

if __name__ == "__main__":
    test_phi3() 