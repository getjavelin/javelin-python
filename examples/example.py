import httpx
from javelin import (
    JavelinClient,
    Route,
    NetworkError,
    RouteNotFoundError,
    UnauthorizedError,
    QueryResponse,
)


def main():
    print("Javelin Example Code")
    print("Starting the script...")
    try:
        client = JavelinClient(base_url="http://localhost:8000")
    except NetworkError as e:
        print("Failed to create client: Network Error")
        return

    print("Start clean (by deleting pre-existing routes): ", "test_route_1")
    try:
        client.delete_route("test_route_1")
    except UnauthorizedError as e:
        print("Failed to delete route: Unauthorized")
    except NetworkError as e:
        print("Failed to delete route: Network Error")
    except RouteNotFoundError as e:
        print("Failed to delete route: Route Not Found")

    route_data = {
        "name": "test_route_1",
        "type": "chat",
        "model": {
            "name": "gpt-3.5-turbo",
            "provider": "openai",
            "suffix": "/chat/completions",
        },
        "config": {
            "archive": True,
            "organization": "myusers",
            "retries": 3,
            "rate_limit": 7,
        },
    }
    route = Route.parse_obj(route_data)
    print("Creating route: ", route.name)
    try:
        client.create_route(route)
    except UnauthorizedError as e:
        print("Failed to create route: Unauthorized")
    except NetworkError as e:
        print("Failed to create route: Network Error")

    query_data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"},
        ],
        "temperature": 0.8,
    }

    print("Querying route: ", route.name)
    try:
        response = client.query_route("test_route_1", query_data)
        print(response)
    except UnauthorizedError as e:
        print("Failed to query route: Unauthorized")
    except NetworkError as e:
        print("Failed to query route: Network Error")
    except RouteNotFoundError as e:
        print("Failed to query route: Route Not Found")

    print("Listing routes")
    try:
        print(client.list_routes())
    except UnauthorizedError as e:
        print("Failed to list routes: Unauthorized")
    except NetworkError as e:
        print("Failed to list routes: Network Error")

    print("Get Route: ", route.name)
    try:
        print(client.get_route(route.name))
    except UnauthorizedError as e:
        print("Failed to get route: Unauthorized")
    except NetworkError as e:
        print("Failed to get route: Network Error")
    except RouteNotFoundError as e:
        print("Failed to get route: Route Not Found")

    print("Updating Route: ", route.name)
    try:
        route.config.retries = 5
        client.update_route(route)
    except UnauthorizedError as e:
        print("Failed to update route: Unauthorized")
    except NetworkError as e:
        print("Failed to update route: Network Error")
    except RouteNotFoundError as e:
        print("Failed to update route: Route Not Found")

    print("Get Route: ", route.name)
    try:
        print(client.get_route(route.name))
    except UnauthorizedError as e:
        print("Failed to get route: Unauthorized")
    except NetworkError as e:
        print("Failed to get route: Network Error")
    except RouteNotFoundError as e:
        print("Failed to get route: Route Not Found")

    print("Deleting Route: ", route.name)
    try:
        client.delete_route(route.name)
    except UnauthorizedError as e:
        print("Failed to delete route: Unauthorized")
    except NetworkError as e:
        print("Failed to delete route: Network Error")
    except RouteNotFoundError as e:
        print("Failed to delete route: Route Not Found")


if __name__ == "__main__":
    main()
