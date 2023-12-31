from javelin_sdk import (
    JavelinClient,
    Route,
    NetworkError,
    RouteNotFoundError,
    UnauthorizedError,
)

import os
import json

# Retrieve environment variables
javelin_api_key = os.getenv("JAVELIN_API_KEY")
javelin_virtualapikey = os.getenv("JAVELIN_VIRTUALAPIKEY")
llm_api_key = os.getenv("LLM_API_KEY")


def pretty_print(obj):
    """
    Pretty-prints an object that has a JSON representation.
    """
    # If the object has a `dict` method, call it to get its dictionary representation.
    if hasattr(obj, "dict"):
        obj = obj.dict()

    # Use the `json` module to print the dictionary as a string.
    try:
        print(json.dumps(obj, indent=4))
    except TypeError:
        print(obj)


def main():
    print("Javelin Synchronous Example Code")
    """
    Create a JavelinClient object. This object is used to interact
    with the Javelin API. The base_url parameter is the URL of the Javelin API.
    """
    try:
        client = JavelinClient(
            javelin_api_key=javelin_api_key,
            javelin_virtualapikey=javelin_virtualapikey,
            llm_api_key=llm_api_key,
        )
    except NetworkError as e:
        print(e.message, e.response_data)
        return
    except UnauthorizedError as e:
        print(e.message, e.response_data)
        return

    """
    Start the example by cleaning up any pre-existing routes. 
    This is done by deleting the route if it exists.
    """
    print("1. Start clean (by deleting pre-existing routes): ", "test_route_1")
    try:
        client.delete_route("test_route_1")
    except RouteNotFoundError as e:
        print(e.message, e.response_data)

    """
    Create a route. This is done by creating a Route object and passing it to the
    create_route method of the JavelinClient object.
    """
    route_data = {
        "name": "test_route_1",
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
    print("2. Creating route: ", route.name)
    # try:
    #     client.create_route(route)
    # except UnauthorizedError as e:
    #    print("Failed to create route: Unauthorized")
    # except NetworkError as e:
    #    print("Failed to create route: Network Error")

    """
    Query the route. This is done by calling the query_route method of the JavelinClient
    object. The query data is passed as a dictionary. The keys of the dictionary are the
    same as the fields of the QueryRequest object. The values of the dictionary are the
    same as the fields of the Message object.
    """
    query_data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "user",
                "content": "You are a helpful assistant. What is the capital of India",
            },
        ],
        "temperature": 0.8,
    }

    print("3. Querying route: ", "myusers")
    try:
        response = client.query_route("myusers", query_data)
        pretty_print(response)
    except UnauthorizedError as e:
        print("Failed to query route: Unauthorized" + e.message, e.response_data)

    """
    List routes. This is done by calling the list_routes method of the JavelinClient object.
    """
    print("4. Listing routes")
    #    try:
    #        pretty_print(client.list_routes())
    #    except UnauthorizedError as e:
    #        print("Failed to list routes: Unauthorized")
    #    except NetworkError as e:
    #        print("Failed to list routes: Network Error")

    print("5. Get Route: ", route.name)
    try:
        pretty_print(client.get_route(route.name))
    except RouteNotFoundError as e:
        print(e.message, e.response_data)

    """
    Update the route. This is done by calling the update_route method of the JavelinClient
    object. The route object is passed as an argument.
    """
    print("6. Updating Route: ", route.name)
    #    try:
    #        route.config.retries = 5
    #       client.update_route(route)
    #    except UnauthorizedError as e:
    #        print("Failed to update route: Unauthorized")
    #    except NetworkError as e:
    #        print("Failed to update route: Network Error")
    #    except RouteNotFoundError as e:
    #        print("Failed to update route: Route Not Found")

    """
    Get the route. This is done by calling the get_route method of the JavelinClient object.
    """
    print("7. Get Route: ", route.name)
    try:
        pretty_print(client.get_route(route.name))
    except RouteNotFoundError as e:
        print(e.message, e.response_data)

    """
    Delete the route. This is done by calling the delete_route method of the JavelinClient
    object.
    """
    print("8. Deleting Route: ", route.name)
    try:
        client.delete_route(route.name)
    except RouteNotFoundError as e:
        print(e.message, e.response_data)


if __name__ == "__main__":
    main()
