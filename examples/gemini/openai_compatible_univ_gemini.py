# This example demonstrates how Javelin uses OpenAI's schema as a standardized interface for different LLM providers.
# By adopting OpenAI's widely-used request/response format, Javelin enables seamless integration with various LLM providers
# (like Anthropic, Bedrock, Mistral, etc.) while maintaining a consistent API structure. This allows developers to use the
# same code pattern regardless of the underlying model provider, with Javelin handling the necessary translations and adaptations behind the scenes.

from javelin_sdk import JavelinClient, JavelinConfig
import os
from typing import Dict, Any
import json


# Helper function to pretty print responses
def print_response(provider: str, response: Dict[str, Any]) -> None:
    print(f"=== Response from {provider} ===")
    print(json.dumps(response, indent=2))


# Setup client configuration
config = JavelinConfig(
    base_url="https://api-dev.javelin.live",
    javelin_api_key=os.getenv("JAVELIN_API_KEY"),
    llm_api_key=os.getenv("OPENAI_API_KEY"),
    timeout=120,
)

client = JavelinClient(config)
custom_headers = {
    "Content-Type": "application/json",
    "x-javelin-route": "google_univ",
    "x-javelin-provider": "https://generativelanguage.googleapis.com/v1beta/openai",
    "x-api-key": os.getenv("JAVELIN_API_KEY"),  # Use environment variable for security
    "Authorization": f"Bearer {os.getenv('GEMINI_API_KEY')}",  # Use environment variable for security
}
client.set_headers(custom_headers)

# Example messages in OpenAI format
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What are the three primary colors?"},
]

try:
    gemini_response = client.chat.completions.create(
        messages=messages, temperature=0.7, max_tokens=150, model="gemini-1.5-flash"
    )
    print_response("Gemini", gemini_response)
except Exception as e:
    print(f"Gemini query failed: {str(e)}")
