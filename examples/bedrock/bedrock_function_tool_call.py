#!/usr/bin/env python
import asyncio
import json
import os
from typing import Dict, Any

from javelin_sdk import JavelinClient, JavelinConfig

# Load ENV
from dotenv import load_dotenv
load_dotenv()

# Print response utility
def print_response(provider: str, response: Dict[str, Any]) -> None:
    print(f"\n=== Response from {provider} ===")
    print(json.dumps(response, indent=2))


# Setup Bedrock Javelin client
config = JavelinConfig(
    base_url=os.getenv("JAVELIN_BASE_URL"),
    javelin_api_key=os.getenv("JAVELIN_API_KEY"),
)
client = JavelinClient(config)

headers = {
    "Content-Type": "application/json",
    "x-javelin-route": "amazon_univ",
    "x-javelin-model": "amazon.titan-text-express-v1",  # replace if needed
    "x-api-key": os.getenv("JAVELIN_API_KEY"),
}


async def test_function_call():
    print("\n==== Bedrock Function Calling Test ====")
    try:
        query_body = {
            "messages": [{"role": "user", "content": "Get weather for Paris in Celsius"}],
            "functions": [
                {
                    "name": "get_weather",
                    "description": "Returns weather info for a city",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {"type": "string"},
                            "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
                        },
                        "required": ["city"]
                    }
                }
            ],
            "function_call": "auto",
            "max_tokens": 100,
            "temperature": 0.7,
        }

        response = client.query_unified_endpoint(
            provider_name="bedrock",
            endpoint_type="invoke",
            query_body=query_body,
            headers=headers,
            model_id="amazon.titan-text-express-v1",
        )
        print_response("Bedrock Function Call", response)
    except Exception as e:
        print(f"Function call failed: {str(e)}")


async def test_tool_call():
    print("\n==== Bedrock Tool Calling Test ====")
    try:
        query_body = {
            "messages": [{"role": "user", "content": "Give me a motivational quote"}],
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "get_motivation",
                        "description": "Returns motivational quote",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "category": {"type": "string", "description": "e.g. success, life"}
                            },
                            "required": []
                        }
                    }
                }
            ],
            "tool_choice": "auto",
            "max_tokens": 100,
            "temperature": 0.7,
        }

        response = client.query_unified_endpoint(
            provider_name="bedrock",
            endpoint_type="invoke",
            query_body=query_body,
            headers=headers,
            model_id="amazon.titan-text-express-v1",
        )
        print_response("Bedrock Tool Call", response)
    except Exception as e:
        print(f"Tool call failed: {str(e)}")


async def main():
    await test_function_call()
    await test_tool_call()


if __name__ == "__main__":
    asyncio.run(main())
