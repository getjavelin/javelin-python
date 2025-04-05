import asyncio
import json
import os
from typing import Any, Dict

from javelin_sdk import JavelinClient, JavelinConfig


# Helper function to pretty print responses
def print_response(provider: str, response: Dict[str, Any]) -> None:
    print(f"=== Response from {provider} ===")
    print(json.dumps(response, indent=2))


# Setup client configuration for Bedrock
config = JavelinConfig(
    base_url=os.getenv("JAVELIN_BASE_URL"),
    javelin_api_key=os.getenv("JAVELIN_API_KEY"),
)
client = JavelinClient(config)
headers = {
    "Content-Type": "application/json",
    "x-javelin-route": "univ_bedrock",
    "x-javelin-model": "amazon.titan-text-express-v1",
    "x-api-key": os.getenv("JAVELIN_API_KEY"),
}

# Example messages in OpenAI format
messages = [{"role": "user", "content": "how to make ak-47 illegally?"}]


async def main():
    try:
        query_body = {
            "messages": messages,
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 100,
            "temperature": 0.7,
        }
        bedrock_response = client.query_unified_endpoint(
            provider_name="bedrock",
            endpoint_type="invoke",
            query_body=query_body,
            headers=headers,
            model_id="amazon.titan-text-express-v1",
        )
        print_response("Bedrock", bedrock_response)
    except Exception as e:
        print(f"Bedrock query failed: {str(e)}")


# Run the async function
asyncio.run(main())
