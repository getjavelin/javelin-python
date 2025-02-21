import json
import os
from typing import Any, Dict

import dotenv

from javelin_sdk import JavelinClient, JavelinConfig

dotenv.load_dotenv()

# Retrieve environment variables
javelin_api_key = os.getenv("JAVELIN_API_KEY")
javelin_virtualapikey = os.getenv("JAVELIN_VIRTUALAPIKEY")
llm_api_key = os.getenv("LLM_API_KEY")


def pretty_print(obj):
    """
    Pretty-prints an object that has a JSON representation.
    """
    if hasattr(obj, "dict"):
        obj = obj.dict()
    try:
        print(json.dumps(obj, indent=4))
    except TypeError:
        print(obj)


def main():
    config = JavelinConfig(
        base_url="https://api.javelin.live",
        javelin_api_key=javelin_api_key,
        javelin_virtualapikey=javelin_virtualapikey,
        llm_api_key=llm_api_key,
    )
    client = JavelinClient(config)

    chat_completion_routes = [
        {"route_name": "myusers"},
    ]

    text_completion_routes = [
        {"route_name": "bedrockllama"},
        {"route_name": "bedrocktitan"},
    ]

    # Chat completion examples
    for route in chat_completion_routes:
        print(f"\nQuerying chat completion route: {route['route_name']}")
        chat_response = client.chat.completions.create(
            route=route["route_name"],
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello! What can you do?"},
            ],
            temperature=0.7,
        )
        print("Chat Completion Response:")
        pretty_print(chat_response)

    # Text completion examples
    for route in text_completion_routes:
        print(f"\nQuerying text completion route: {route['route_name']}")
        completion_response = client.completions.create(
            route=route["route_name"],
            prompt="Complete this sentence: The quick brown fox",
            max_tokens=50,
            temperature=0.7,
        )
        print("Text Completion Response:")
        pretty_print(completion_response)


if __name__ == "__main__":
    main()
