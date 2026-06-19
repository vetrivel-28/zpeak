import requests
import json
import logging

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:1.5b"
TIMEOUT_SECONDS = 30

def generate(prompt, format_json=False):
    """
    Sends a prompt to the local Ollama API.
    Returns the response string if successful, or None if failed.
    """
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }
    
    if format_json:
        payload["format"] = "json"
        
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        result = response.json()
        return result.get("response", "").strip()
    except requests.exceptions.RequestException as e:
        logger.error(f"LLM API Error: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding LLM response: {e}")
        return None
