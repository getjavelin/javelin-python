import os
import json
from typing import Dict, Any

from javelin_sdk import (
    JavelinConfig,
    JavelinClient,
    Route,
    RouteNotFoundError,
    NetworkError,
    UnauthorizedError,
)

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

def query_route(client: JavelinClient, route_name: str, query_data: Dict[str, Any]):
    try:
        response = client.chat.create(
            model=query_data.get("model", "gpt-3.5-turbo"),
            messages=query_data.get("messages", []),
            route=route_name
        )
        pretty_print(response)
    except UnauthorizedError:
        print("Failed to query route: Unauthorized")
    except NetworkError:
        print("Failed to query route: Network Error")
    except RouteNotFoundError:
        print("Failed to query route: Route Not Found")
    except Exception as e:
        print(f"Failed to query route: {str(e)}")

def main():
    try:
        config = JavelinConfig(
            base_url="https://api-dev.javelin.live",
            javelin_api_key=javelin_api_key,
            javelin_virtualapikey=javelin_virtualapikey,
            llm_api_key=llm_api_key,
        )
        client = JavelinClient(config)
    except NetworkError as e:
        print("Failed to create client: Network Error")
        return

    # For Debugging purposes - Get the route
    route_name = "azureopenai"
    print("Get Route: ", route_name)
    try:
        pretty_print(client.get_route(route_name))
    except UnauthorizedError:
        print("Failed to get route: Unauthorized")
    except NetworkError:
        print("Failed to get route: Network Error")
    except RouteNotFoundError:
        print("Failed to get route: Route Not Found")

    model_providers_routes = [
        {"provider": "OpenAI", "route_name": "myusers"},
        {"provider": "Azure OpenAI", "route_name": "azureopenai"},
        {"provider": "Bedrock Amazon", "route_name": "bedrocktitan"},
        {"provider": "Bedrock Meta", "route_name": "bedrockllama"},
    ]

    for model in model_providers_routes:
        print(f"Querying provider: {model['provider']} with route name: {model['route_name']}")
        query_data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello!"}
            ]
        }
        query_route(client, model['route_name'], query_data)

if __name__ == "__main__":
    main()
