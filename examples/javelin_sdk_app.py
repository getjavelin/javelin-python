import os
import json
from typing import Dict, Any

from javelin_sdk import JavelinConfig, JavelinClient

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


def query_route(
    client: JavelinClient, route_name: str, provider: str, query_data: Dict[str, Any]
):
    response = client.chat.completions.create(
        route=route_name,
        provider=provider,
        messages=query_data["messages"],
        model=query_data.get("model"),
        temperature=query_data.get("temperature", 0.7),
    )
    pretty_print(response)


def main():
    config = JavelinConfig(
        base_url="https://api-dev.javelin.live",
        javelin_api_key=javelin_api_key,
        javelin_virtualapikey=javelin_virtualapikey,
        llm_api_key=llm_api_key,
    )
    client = JavelinClient(config)

    model_providers_routes = [
        {"provider": "OpenAI", "route_name": "myusers"},
        {"provider": "BedrockAmazon", "route_name": "bedrocktitan"},
        {"provider": "BedrockMeta", "route_name": "bedrockllama"},
    ]

    for model in model_providers_routes:
        query_data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello!"},
            ],
            "temperature": 0.7,
        }
        query_route(client, model["route_name"], model["provider"], query_data)


if __name__ == "__main__":
    main()
