#!/usr/bin/env python3
"""LLM Client for calling various backend models through a unified interface.

This module provides a client for interacting with different LLM backends:
1. Local Phi-3 models via llama.cpp
2. Llama-3 via TGI/vLLM OpenAI-compatible API
3. OpenAI's API

The client auto-detects which API to use based on environment variables.
"""

import os
import json
import logging
import subprocess
import requests
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("llm_client")

class LLMType(str, Enum):
    PHI3 = "phi3"            # Local Phi-3 via llama.cpp
    OPENAI = "openai"        # OpenAI API
    OPENAI_COMPATIBLE = "openai_compatible"  # OpenAI-compatible API (TGI/vLLM)

class ChatMessage(BaseModel):
    """Chat message in OpenAI format."""
    role: str = Field(..., description="Role of the message sender (system/user/assistant)")
    content: str = Field(..., description="Content of the message")

class LLMClient:
    """Unified client for interacting with different LLM backends."""
    
    def __init__(
        self,
        llm_type: Optional[str] = None,
        model_path: Optional[str] = None,
        llama_executable: Optional[str] = None,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        model: Optional[str] = None,
        threads: int = 6,
        gpu_layers: int = 0,
        ctx_size: int = 4096,
        temperature: float = 0.2
    ):
        """Initialize the LLM client.
        
        Args:
            llm_type: Type of LLM to use (phi3, openai, openai_compatible)
            model_path: Path to the local model file (for phi3)
            llama_executable: Path to the llama.cpp executable (for phi3)
            api_key: API key for OpenAI or compatible API
            api_base: Base URL for API calls
            model: Model identifier (for OpenAI/compatible APIs)
            threads: Number of CPU threads to use (for phi3)
            gpu_layers: Number of layers to offload to GPU (for phi3)
            ctx_size: Context size in tokens (for phi3)
            temperature: Sampling temperature
        """
        # Get config from environment or parameters
        self.llm_type = llm_type or os.getenv("LLM_TYPE", "phi3").lower()
        self.model_path = model_path or os.getenv("MODEL_PATH", "./path/to/phi3-model.gguf")
        self.llama_executable = llama_executable or os.getenv("LLAMA_PATH", "./main")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.api_base = api_base or os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        self.model = model or os.getenv("LLM_MODEL", "gpt-3.5-turbo")
        
        # Runtime parameters
        self.threads = threads
        self.gpu_layers = gpu_layers
        self.ctx_size = ctx_size
        self.temperature = temperature
        
        # Convert to enum
        try:
            self.llm_type_enum = LLMType(self.llm_type)
        except ValueError:
            logger.warning(f"Unknown LLM type: {self.llm_type}, defaulting to phi3")
            self.llm_type_enum = LLMType.PHI3
        
        # Check if we have the necessary config
        self._validate_config()
        
        logger.info(f"Initialized LLM client with type: {self.llm_type}")
    
    def _validate_config(self):
        """Validate the configuration."""
        if self.llm_type_enum == LLMType.PHI3:
            if not os.path.exists(self.model_path):
                logger.warning(f"Model path does not exist: {self.model_path}")
            if not os.path.exists(self.llama_executable):
                logger.warning(f"llama.cpp executable not found: {self.llama_executable}")
        
        elif self.llm_type_enum in [LLMType.OPENAI, LLMType.OPENAI_COMPATIBLE]:
            if not self.api_key and self.llm_type_enum == LLMType.OPENAI:
                logger.warning("OpenAI API key not provided")
            if not self.api_base:
                logger.warning("API base URL not provided")
    
    def generate(self, prompt: str, max_tokens: int = 1024) -> str:
        """Generate a response to a single prompt.
        
        Args:
            prompt: The text prompt to send to the LLM
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            The generated text response
        """
        if self.llm_type_enum == LLMType.PHI3:
            return self._generate_phi3(prompt, max_tokens)
        
        # For OpenAI-style APIs, convert the prompt to a chat format
        messages = [{"role": "user", "content": prompt}]
        return self.chat(messages, max_tokens)
    
    def chat(self, messages: List[Dict[str, str]], max_tokens: int = 1024) -> str:
        """Generate a response using chat-style inputs.
        
        Args:
            messages: List of message dictionaries with role and content
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            The generated text response
        """
        if self.llm_type_enum == LLMType.PHI3:
            # Convert chat format to a single prompt for Phi-3
            prompt = self._convert_messages_to_prompt(messages)
            return self._generate_phi3(prompt, max_tokens)
        
        elif self.llm_type_enum in [LLMType.OPENAI, LLMType.OPENAI_COMPATIBLE]:
            return self._generate_openai_style(messages, max_tokens)
    
    def _generate_phi3(self, prompt: str, max_tokens: int = 1024) -> str:
        """Generate text using local Phi-3 model via llama.cpp.
        
        Args:
            prompt: Text prompt
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        try:
            # Prepare the command
            cmd = [
                self.llama_executable,
                "-m", self.model_path,
                "-t", str(self.threads),
                "--n-gpu-layers", str(self.gpu_layers),
                "--ctx-size", str(self.ctx_size),
                "-n", str(max_tokens),
                "--temp", str(self.temperature),
                "-p", prompt
            ]
            
            logger.info(f"Running Phi-3 with prompt: {prompt[:100]}...")
            
            # Execute the command
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            # Process the output - remove the prompt from the response
            output = result.stdout
            if prompt in output:
                output = output.split(prompt, 1)[1]
            
            return output.strip()
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running Phi-3 model: {e}")
            logger.error(f"stderr: {e.stderr}")
            return ""
        except Exception as e:
            logger.error(f"Unexpected error running Phi-3 model: {e}")
            return ""
    
    def _generate_openai_style(self, messages: List[Dict[str, str]], max_tokens: int = 1024) -> str:
        """Generate text using OpenAI or compatible API.
        
        Args:
            messages: List of message dictionaries
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        try:
            headers = {
                "Content-Type": "application/json"
            }
            
            # Add Authorization header for OpenAI API
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": self.temperature
            }
            
            # Build the API endpoint URL
            endpoint = f"{self.api_base}/chat/completions"
            if not endpoint.startswith(("http://", "https://")):
                endpoint = f"https://{endpoint}"
            
            logger.info(f"Calling OpenAI-style API at {endpoint}")
            response = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=120  # 2-minute timeout
            )
            
            # Raise exception for 4xx/5xx errors
            response.raise_for_status()
            
            data = response.json()
            logger.debug(f"API response: {data}")
            
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            else:
                logger.error(f"Unexpected API response format: {data}")
                return ""
            
        except requests.RequestException as e:
            logger.error(f"API request error: {e}")
            return ""
        except Exception as e:
            logger.error(f"Unexpected error with OpenAI-style API: {e}")
            return ""
    
    def _convert_messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert chat messages to a single prompt for Phi-3.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            A formatted prompt string
        """
        formatted_messages = []
        
        for msg in messages:
            role = msg.get("role", "").lower()
            content = msg.get("content", "")
            
            if role == "system":
                formatted_messages.append(f"<System>\n{content}\n</System>")
            elif role == "user":
                formatted_messages.append(f"<User>\n{content}\n</User>")
            elif role == "assistant":
                formatted_messages.append(f"<Assistant>\n{content}\n</Assistant>")
            else:
                # Unknown role, just add the content
                formatted_messages.append(content)
        
        # Add the final assistant prompt
        formatted_messages.append("<Assistant>")
        
        return "\n".join(formatted_messages)

# Example usage
if __name__ == "__main__":
    # Test with Phi-3
    phi3_client = LLMClient(
        llm_type="phi3",
        model_path="/path/to/phi3.gguf",
        llama_executable="/path/to/llama.cpp/main"
    )
    
    # Test with OpenAI-compatible API (e.g., vLLM server)
    openai_compatible_client = LLMClient(
        llm_type="openai_compatible",
        api_base="http://localhost:8000/v1",
        model="llama-3-70b-instruct"
    )
    
    # Test with a prompt
    prompt = "What is the capital of France?"
    response = phi3_client.generate(prompt)
    print(f"Phi-3 response: {response}")
    
    # Test with chat format
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France?"}
    ]
    response = openai_compatible_client.chat(messages)
    print(f"OpenAI-compatible response: {response}") 