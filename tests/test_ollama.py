import requests
import json

url = "http://ollama:11434/api/chat"
payload = {
    "model": "mistral",
    "messages": [{"role": "user", "content": "hi"}],
    "stream": False
}

try:
    print(f"Testing {url} with payload: {payload}")
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:200]}...")
except Exception as e:
    print(f"Error: {e}")
