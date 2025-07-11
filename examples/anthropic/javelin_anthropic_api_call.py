import os
import json
from typing import Dict, Any
from javelin_sdk import JavelinClient, JavelinConfig
from dotenv import load_dotenv

load_dotenv()

# Helper for pretty print


def print_response(provider: str, response: Dict[str, Any]) -> None:
    print(f"=== Response from {provider} ===")
    print(json.dumps(response, indent=2))


# Javelin client config
config = JavelinConfig(
    base_url=os.getenv("JAVELIN_BASE_URL"),
    javelin_api_key=os.getenv("JAVELIN_API_KEY"),
    llm_api_key=os.getenv("ANTHROPIC_API_KEY"),
    timeout=120,
)
client = JavelinClient(config)

# Proper headers (must match Anthropic's expectations)
custom_headers = {
    "Content-Type": "application/json",
    "x-javelin-route": "anthropic_univ",
    "x-javelin-model": "claude-3-5-sonnet-20240620",
    "x-javelin-provider": "https://api.anthropic.com/v1",
    "x-api-key": os.getenv("ANTHROPIC_API_KEY"),  # For Anthropic model
    "anthropic-version": "2023-06-01",
}
client.set_headers(custom_headers)

# Claude-compatible messages format
query_body = {
    "model": "claude-3-5-sonnet-20240620",
    "max_tokens": 300,
    "temperature": 0.7,
    "system": "You are a helpful assistant.",
    "messages": [
        {
            "role": "user",
            "content": [{"type": "text", "text": "What are the three primary colors?"}],
        }
    ],
}

# Invoke
try:
    response = client.query_unified_endpoint(
        provider_name="anthropic",
        endpoint_type="messages",
        query_body=query_body,
    )
    print_response("Anthropic", response)
except Exception as e:
    print(f"Anthropic query failed: {str(e)}")
