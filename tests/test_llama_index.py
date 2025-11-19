from llama_index.llms.ollama import Ollama
import logging
import sys

# Setup logging to see debug info
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

print("Initializing Ollama...")
try:
    llm = Ollama(
        model="mistral",
        base_url="http://ollama:11434",
        request_timeout=300.0,
        temperature=0.2,
    )
    
    print("Sending completion request...")
    resp = llm.complete("Hello, are you there?")
    print(f"Response: {resp}")

    print("Sending chat request...")
    from llama_index.core.llms import ChatMessage
    messages = [ChatMessage(role="user", content="Hi")]
    resp_chat = llm.chat(messages)
    print(f"Chat Response: {resp_chat}")

except Exception as e:
    print(f"Error: {e}")
