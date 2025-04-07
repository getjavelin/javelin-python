from javelin_sdk import JavelinClient, JavelinConfig
import os
from typing import Dict, Any
import json
import dotenv

dotenv.load_dotenv()


# Helper function to pretty print responses
def print_response(provider: str, response: Dict[str, Any]) -> None:
    print(f"=== Response from {provider} ===")
    print(json.dumps(response, indent=2))


# Setup client configuration
config = JavelinConfig(
    base_url=os.getenv("JAVELIN_BASE_URL"),
    javelin_api_key=os.getenv("JAVELIN_API_KEY"),
    timeout=120,
)

client = JavelinClient(config)
custom_headers = {
    "Content-Type": "application/json",
    "x-javelin-route": "claude_univ",
    "x-api-key": os.getenv("ANTHROPIC_API_KEY"),
    "x-javelin-model": "claude-3-5-sonnet-20240620",
    "x-javelin-provider": "https://api.anthropic.com/v1",
}
client.set_headers(custom_headers)

# Example messages in OpenAI format
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What are the three primary colors?"},
]

try:
    openai_response = client.chat.completions.create(
        messages=messages,
        temperature=0.7,
        max_tokens=150,
        model="claude-3-5-sonnet-20240620",
        stream=True,
        endpoint_type="messages",
        anthropic_version="bedrock-2023-05-31",
    )
    for chunk in openai_response:
        print(chunk, end="", flush=True)
    print()  # Add a newline at the end
except Exception as e:
    print(f"Anthropic query failed: {str(e)}")
