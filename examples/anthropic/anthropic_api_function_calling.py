import os
from dotenv import load_dotenv
from javelin_sdk import JavelinClient, JavelinConfig

load_dotenv()

# Config setup
config = JavelinConfig(
    base_url=os.getenv("JAVELIN_BASE_URL"),
    javelin_api_key=os.getenv("JAVELIN_API_KEY"),
    llm_api_key=os.getenv("ANTHROPIC_API_KEY"),
    timeout=120,
)
client = JavelinClient(config)

# Headers
headers = {
    "Content-Type": "application/json",
    "x-javelin-route": "anthropic_univ",  # add your universal route
    "x-javelin-model": "claude-3-5-sonnet-20240620",  # add any supported model
    "x-javelin-provider": "https://api.anthropic.com/v1",
    "x-api-key": os.getenv("ANTHROPIC_API_KEY"),
    "anthropic-version": "2023-06-01",
}
client.set_headers(headers)

# Tool definition — using `input_schema` instead of OpenAI's `parameters`
functions = [
    {
        "name": "get_weather",
        "description": "Get the current weather in a city",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name"},
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
            },
            "required": ["location"],
        },
    }
]

# Messages
messages = [
    {
        "role": "user",
        "content": [
            {"type": "text", "text": "What's the weather like in Mumbai in celsius?"}
        ],
    }
]

# Request payload
query_body = {
    "model": "claude-3-5-sonnet-20240620",
    "temperature": 0.7,
    "max_tokens": 300,
    "messages": messages,
    "tools": functions,
    "tool_choice": {"type": "auto"},  # Important: dict, not string
}

# Call
response = client.query_unified_endpoint(
    provider_name="anthropic",
    endpoint_type="messages",
    query_body=query_body,
)

print(response)
