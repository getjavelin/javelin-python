import json
import os

from javelin_sdk import (
    JavelinClient,
    JavelinConfig,
    NetworkError,
    Route,
    RouteNotFoundError,
    UnauthorizedError,
)


# Retrieve environment variables
javelin_api_key = os.getenv("JAVELIN_API_KEY")
javelin_virtualapikey = os.getenv("JAVELIN_VIRTUALAPIKEY")
llm_api_key = os.getenv("OPENAI_API_KEY")


def pretty_print(obj):
    if hasattr(obj, "dict"):
        obj = obj.dict()
    print(json.dumps(obj, indent=4))


def route_example(client):
    # Clean up pre-existing route
    print("1. Start clean (by deleting pre-existing routes): ", "test_route_1")
    try:
        client.delete_route("test_route_1")
    except UnauthorizedError as e:
        print("Failed to delete route: Unauthorized")
    except NetworkError as e:
        print("Failed to delete route: Network Error")
    except RouteNotFoundError as e:
        print("Failed to delete route: Route Not Found")

    # Create a route
    route_data = {
        "name": "test_route_1",
        "type": "chat",
        "enabled": True,
        "models": [
            {
                "name": "gpt-3.5-turbo",
                "provider": "Azure OpenAI",
                "suffix": "/chat/completions",
            }
        ],
        "config": {
            "organization": "myusers",
            "rate_limit": 7,
            "retries": 3,
            "archive": True,
            "retention": 7,
            "budget": {
                "enabled": True,
                "annual": 100000,
                "currency": "USD",
            },
            "dlp": {"enabled": True, "strategy": "Inspect", "action": "notify"},
        },
    }
    route = Route.parse_obj(route_data)
    print("2. Creating route: ", route.name)
    try:
        client.create_route(route)
    except UnauthorizedError as e:
        print("Failed to create route: Unauthorized")
    except NetworkError as e:
        print("Failed to create route: Network Error")

    # Query the route
    print("3. Querying route: ", route.name)
    try:
        query_data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello!"},
            ],
            "temperature": 0.7,
        }

        response = client.chat.completions.create(
            route="test_route_1",
            provider="Azure OpenAI",
            model=query_data["model"],
            messages=query_data["messages"],
            temperature=query_data.get("temperature", 0.7),
        )
        pretty_print(response)
    except UnauthorizedError as e:
        print("Failed to query route: Unauthorized")
    except NetworkError as e:
        print("Failed to query route: Network Error")
    except RouteNotFoundError as e:
        print("Failed to query route: Route Not Found")

    # Clean up: Delete the route
    print("4. Deleting Route: ", route.name)
    try:
        client.delete_route(route.name)
    except UnauthorizedError as e:
        print("Failed to delete route: Unauthorized")
    except NetworkError as e:
        print("Failed to delete route: Network Error")
    except RouteNotFoundError as e:
        print("Failed to delete route: Route Not Found")


def main():
    print("Javelin Drop-in Replacement Example")

    try:
        config = JavelinConfig(
            javelin_api_key=javelin_api_key,
            javelin_virtualapikey=javelin_virtualapikey,
            llm_api_key=llm_api_key,
        )
        client = JavelinClient(config)
    except NetworkError as e:
        print("Failed to create client: Network Error")
        return

    route_example(client)


if __name__ == "__main__":
    main()
