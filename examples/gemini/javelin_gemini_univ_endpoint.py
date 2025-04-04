import asyncio
import json
import os
from typing import Any, Dict

from javelin_sdk import JavelinClient, JavelinConfig


# Helper function to pretty print responses
def print_response(provider: str, response: Dict[str, Any]) -> None:
    print(f"=== Response from {provider} ===")
    print(json.dumps(response, indent=2))


# Setup client configuration
config = JavelinConfig(
    base_url=os.getenv("JAVELIN_BASE_URL"),
    javelin_api_key=os.getenv("JAVELIN_API_KEY"),
    llm_api_key=os.getenv("OPENAI_API_KEY"),
)
client = JavelinClient(config)

# Example messages in OpenAI format
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What are the three primary colors?"},
]

# Define the headers based on the curl command
custom_headers = {
    "Content-Type": "application/json",
    "x-javelin-route": "google_univ",
    "x-javelin-model": "gemini-1.5-flash",
    "x-javelin-provider": "https://generativelanguage.googleapis.com/v1beta/openai",
    "x-api-key": os.getenv("JAVELIN_API_KEY"),  # Use environment variable for security
    "Authorization": f"Bearer {os.getenv('GEMINI_API_KEY')}",  # Use environment variable for security
}


async def main():
    try:
        query_body = {
            "messages": messages,
            "temperature": 0.7,
            "model": "gemini-1.5-flash",
        }
        gemini_response = await client.aquery_unified_endpoint(
            provider_name="gemini",
            endpoint_type="chat",
            query_body=query_body,
            headers=custom_headers,
        )
        print_response("Gemini", gemini_response)
    except Exception as e:
        print(f"Gemini query failed: {str(e)}")


# Run the async function
asyncio.run(main())
