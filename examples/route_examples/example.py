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
llm_api_key = os.getenv("LLM_API_KEY")


def pretty_print(obj):
    """
    Pretty-prints an object that has a JSON representation.
    """
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
            "temperature": 0.8,
        }
        response = client.query_route(route_name, query_data)
        pretty_print(response)
    except UnauthorizedError:
        print("Failed to query route: Unauthorized")
    except NetworkError:
        print("Failed to query route: Network Error")
    except RouteNotFoundError:
        print("Failed to query route: Route Not Found")


def list_routes(client):
    print("4. Listing routes")
    try:
        pretty_print(client.list_routes())
    except UnauthorizedError:
        print("Failed to list routes: Unauthorized")
    except NetworkError:
        print("Failed to list routes: Network Error")


def get_route(client, route_name):
    print("5. Get Route: ", route_name)
    try:
        pretty_print(client.get_route(route_name))
    except UnauthorizedError:
        print("Failed to get route: Unauthorized")
    except NetworkError:
        print("Failed to get route: Network Error")
    except RouteNotFoundError:
        print("Failed to get route: Route Not Found")


def update_route(client, route):
    print("6. Updating Route: ", route.name)
    try:
        route.config.retries = 5
        client.update_route(route)
    except UnauthorizedError:
        print("Failed to update route: Unauthorized")
    except NetworkError:
        print("Failed to update route: Network Error")
    except RouteNotFoundError:
        print("Failed to update route: Route Not Found")


def delete_route(client, route_name):
    print("8. Deleting Route: ", route_name)
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
                "provider": "openai",
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
    list_routes(client)
    get_route(client, route_name)
    update_route(client, route)
    get_route(client, route_name)
    delete_route(client, route_name)


def main():
    print("Javelin Synchronous Example Code")
    """
    Create a JavelinClient object. This object is used to interact
    with the Javelin API. The base_url parameter is the URL of the Javelin API.
    """

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
