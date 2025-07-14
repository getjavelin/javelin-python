import json
import os

import dotenv

from javelin_sdk import (
    JavelinClient,
    JavelinConfig,
    NetworkError,
    Route,
    RouteNotFoundError,
    UnauthorizedError,
)

dotenv.load_dotenv()

# Retrieve environment variables
javelin_api_key = os.getenv("JAVELIN_API_KEY")
javelin_virtualapikey = os.getenv("JAVELIN_VIRTUALAPIKEY")
llm_api_key = os.getenv("OPENAI_API_KEY")


def pretty_print(obj):
    if hasattr(obj, "dict"):
        obj = obj.dict()
    print(json.dumps(obj, indent=4))


def delete_route_if_exists(client, route_name):
    print("1. Start clean (by deleting pre-existing routes): ", route_name)
    try:
        client.delete_route(route_name)
    except UnauthorizedError:
        print("Failed to delete route: Unauthorized")
    except NetworkError:
        print("Failed to delete route: Network Error")
    except RouteNotFoundError:
        print("Failed to delete route: Route Not Found")


def create_route(client, route):
    print("2. Creating route: ", route.name)
    try:
        client.create_route(route)
    except UnauthorizedError:
        print("Failed to create route: Unauthorized")
    except NetworkError:
        print("Failed to create route: Network Error")


def query_route(client, route_name):
    print("3. Querying route: ", route_name)
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
            route=route_name,
            messages=query_data["messages"],
            temperature=query_data.get("temperature", 0.7),
        )
        pretty_print(response)
    except UnauthorizedError:
        print("Failed to query route: Unauthorized")
    except NetworkError:
        print("Failed to query route: Network Error")
    except RouteNotFoundError:
        print("Failed to query route: Route Not Found")


def delete_route(client, route_name):
    print("4. Deleting Route: ", route_name)
    try:
        client.delete_route(route_name)
    except UnauthorizedError:
        print("Failed to delete route: Unauthorized")
    except NetworkError:
        print("Failed to delete route: Network Error")
    except RouteNotFoundError:
        print("Failed to delete route: Route Not Found")


def route_example(client):
    route_name = "test_route_1"
    delete_route_if_exists(client, route_name)
    route_data = {
        "name": route_name,
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
    create_route(client, route)
    query_route(client, route_name)
    delete_route(client, route_name)


def main():
    print("Javelin Drop-in Replacement Example")

    try:
        config = JavelinConfig(
            base_url=os.getenv("JAVELIN_BASE_URL"),
            javelin_api_key=javelin_api_key,
            javelin_virtualapikey=javelin_virtualapikey,
            llm_api_key=llm_api_key,
        )
        client = JavelinClient(config)
    except NetworkError:
        print("Failed to create client: Network Error")
        return

    route_example(client)


if __name__ == "__main__":
    main()
