#!/usr/bin/env python
import os
import json
import asyncio
from javelin_sdk import JavelinClient, JavelinConfig

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Javelin Setup
config = JavelinConfig(
    base_url=os.getenv("JAVELIN_BASE_URL"),
    javelin_api_key=os.getenv("JAVELIN_API_KEY"),
)
client = JavelinClient(config)

# Anthropic Headers
headers = {
    "Content-Type": "application/json",
    "x-javelin-route": "amazon_univ",
    "x-javelin-model": "claude-3-5-sonnet-20240620",
    "x-api-key": os.getenv("ANTHROPIC_API_KEY"),
}

# Messages and dummy tool call (check if tool support throws any error)
messages = [
    {"role": "user", "content": "Please call the tool to fetch today's weather in Paris."}
]

tools = [
    {
        "name": "get_weather",
        "description": "Get weather info by city",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "Name of the city"},
            },
            "required": ["city"]
        }
    }
]

async def run_anthropic_test():
    print("\n==== Testing Anthropic Function Calling Support via Javelin ====")
    try:
        body = {
            "messages": messages,
            "tools": tools,  # test tool support
            "tool_choice": "auto",
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 256,
            "temperature": 0.7,
        }
        result = client.query_unified_endpoint(
            provider_name="anthropic",
            endpoint_type="messages",
            query_body=body,
            headers=headers,
        )
        print("Raw Response:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Function/tool call failed for Anthropic: {str(e)}")

if __name__ == "__main__":
    asyncio.run(run_anthropic_test())
