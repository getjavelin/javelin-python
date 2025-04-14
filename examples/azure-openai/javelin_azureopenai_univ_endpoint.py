import asyncio
import json
import os
from typing import Any, Dict

from javelin_sdk import JavelinClient, JavelinConfig
from dotenv import load_dotenv

load_dotenv()

# Helper function to pretty print responses
def print_response(provider: str, response: Dict[str, Any]) -> None:
    print(f"=== Response from {provider} ===")
    print(json.dumps(response, indent=2))


# Setup client configuration
config = JavelinConfig(
    base_url=os.getenv("JAVELIN_BASE_URL"),
    javelin_api_key=os.getenv("JAVELIN_API_KEY"),
    default_headers={
        "Content-Type": "application/json",
        "x-javelin-provider": "https://javelinpreview.openai.azure.com/openai",
        "x-api-key": os.getenv("JAVELIN_API_KEY"),
        "api-key": os.getenv("AZURE_OPENAI_API_KEY"),
    },
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
    "x-javelin-route": "azureopenai_univ",
    "x-javelin-provider": "https://javelinpreview.openai.azure.com/openai",
    "x-api-key": os.getenv("JAVELIN_API_KEY"),  # Use environment variable for security
    "api-key": os.getenv(
        "AZURE_OPENAI_API_KEY"
    ),  # Use environment variable for security
}


async def main():
    try:
        query_body = {"messages": messages, "temperature": 0.7}
        query_params = {"api-version": "2023-07-01-preview"}
        openai_response = client.query_unified_endpoint(
            provider_name="azureopenai",
            endpoint_type="chat",
            query_body=query_body,
            headers=custom_headers,
            query_params=query_params,
            deployment="gpt-4",
        )
        print_response("Azure OpenAI", openai_response)
    except Exception as e:
        print(f"OpenAI query failed: {str(e)}")


# Run the async function
asyncio.run(main())
