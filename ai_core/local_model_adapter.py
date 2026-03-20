"""
Local Model Adapter for Testing

Supports running local models like Llama 3.2 via Ollama for testing
without consuming Gemini API quota.
"""

import requests
import json
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class LocalModelAdapter:
    """
    Adapter for local LLM models (Ollama, LM Studio, etc.)
    
    Provides same interface as Gemini API for seamless testing.
    """
    
    def __init__(self, model_name: str = "llama3.2:3b", base_url: str = "http://localhost:11434"):
        """
        Initialize local model adapter.
        
        Args:
            model_name: Name of the local model (e.g., "llama3.2:3b", "llama3.2:1b")
            base_url: Base URL for Ollama API (default: http://localhost:11434)
        """
        self.model_name = model_name
        self.base_url = base_url
        self.api_endpoint = f"{base_url}/api/generate"
        
    def check_availability(self) -> bool:
        """
        Check if local model is available.
        
        Returns:
            True if model is available, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return any(m['name'] == self.model_name for m in models)
            return False
        except:
            return False
    
    def generate_content(self, prompt: str, temperature: float = 0.1) -> Dict[str, Any]:
        """
        Generate content using local model.
        
        Args:
            prompt: Input prompt
            temperature: Temperature for generation
            
        Returns:
            Response dictionary compatible with Gemini API format
        """
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": 2000  # Max tokens
                }
            }
            
            response = requests.post(
                self.api_endpoint,
                json=payload,
                timeout=60  # Local models can be slow
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'text': result.get('response', ''),
                    'model': self.model_name,
                    'local': True
                }
            else:
                raise Exception(f"Local model error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Local model generation failed: {e}")
            raise
    
    def assess_student_personality(self, observations: str, reference_sheet: str) -> str:
        """
        Assess student personality using local model.
        
        Args:
            observations: Student observations
            reference_sheet: Reference sheet for assessment
            
        Returns:
            Assessment text
        """
        prompt = f"""You are an educational psychologist assessing student personality traits.

Reference Sheet:
{reference_sheet}

Student Observations:
{observations}

Based on the observations and reference sheet, provide a detailed personality assessment.
For each quality, determine the level (HIGH, MIDDLE, LOW, or NOT OBSERVED) and provide reasoning.

Format your response as:
Quality: LEVEL
  (Reasoning based on observations)

Assess all 20 qualities from the reference sheet."""

        response = self.generate_content(prompt, temperature=0.1)
        return response['text']


def get_local_model_info() -> Dict[str, Any]:
    """
    Get information about available local models.
    
    Returns:
        Dictionary with model information
    """
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json().get('models', [])
            return {
                'available': True,
                'models': [
                    {
                        'name': m['name'],
                        'size': m.get('size', 0),
                        'modified': m.get('modified_at', '')
                    }
                    for m in models
                ],
                'recommended': [
                    'llama3.2:1b',  # Fastest, good for testing
                    'llama3.2:3b',  # Balanced
                    'llama3.1:8b',  # Best quality
                ]
            }
        return {'available': False, 'error': 'Ollama not responding'}
    except Exception as e:
        return {'available': False, 'error': str(e)}


def setup_instructions() -> str:
    """
    Get setup instructions for local models.
    
    Returns:
        Setup instructions as string
    """
    return """
# Setup Local Model for Testing

## Option 1: Ollama (Recommended)

### Install Ollama:
1. Download from: https://ollama.com/download
2. Install for your OS (Windows/Mac/Linux)
3. Ollama will start automatically

### Pull Llama 3.2 Model:
```bash
# Smallest/Fastest (1B parameters) - Good for testing
ollama pull llama3.2:1b

# Medium (3B parameters) - Balanced
ollama pull llama3.2:3b

# Larger (8B parameters) - Best quality
ollama pull llama3.1:8b
```

### Verify Installation:
```bash
ollama list
```

### Test Model:
```bash
ollama run llama3.2:3b "Hello, how are you?"
```

## Option 2: LM Studio

1. Download from: https://lmstudio.ai/
2. Install and open LM Studio
3. Search for "Llama 3.2" in the model browser
4. Download llama-3.2-3b-instruct
5. Start local server (default: http://localhost:1234)

## Using in the App

Once Ollama is running:
1. Go to sidebar in Streamlit app
2. Look for "Local Model (Testing)" option
3. Select your local model
4. Process assessments without using API quota!

## Benefits

- **No API quota usage** - Test unlimited
- **Faster for testing** - No network latency
- **Privacy** - Data stays local
- **Free** - No costs

## Performance

- llama3.2:1b - ~2-3 seconds per assessment
- llama3.2:3b - ~5-7 seconds per assessment
- llama3.1:8b - ~10-15 seconds per assessment

## Note

Local models may not be as accurate as Gemini for production use,
but they're perfect for testing UI features and workflows!
"""


if __name__ == "__main__":
    # Test local model availability
    print("Checking for local models...")
    info = get_local_model_info()
    
    if info['available']:
        print(f"\n✓ Ollama is running!")
        print(f"\nAvailable models:")
        for model in info['models']:
            print(f"  • {model['name']}")
        
        print(f"\nRecommended for testing:")
        for model in info['recommended']:
            print(f"  • {model}")
    else:
        print(f"\n✗ Ollama not available: {info.get('error')}")
        print("\nSetup instructions:")
        print(setup_instructions())
