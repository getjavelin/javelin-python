import os
import json
from javelin_sdk import JavelinClient, JavelinConfig, OpenAIModel, Route, RouteNotFoundError, UnauthorizedError, NetworkError

# Retrieve environment variables
javelin_api_key = os.getenv("JAVELIN_API_KEY")
javelin_virtualapikey = os.getenv("JAVELIN_VIRTUALAPIKEY")
llm_api_key = os.getenv("LLM_API_KEY")

def pretty_print(obj):
    if hasattr(obj, "dict"):
        obj = obj.dict()
    print(json.dumps(obj, indent=4))

# Create JavelinConfig
config = JavelinConfig(
    javelin_api_key=javelin_api_key,
    javelin_virtualapikey=javelin_virtualapikey,
    llm_api_key=llm_api_key,
    models=[OpenAIModel(name="gpt-3.5-turbo")]
)

# Create JavelinClient
client = JavelinClient(config)

# Create a route
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
print("Creating route: ", route.name)
try:
    client.create_route(route)
except UnauthorizedError as e:
    print("Failed to create route: Unauthorized")
except NetworkError as e:
    print("Failed to create route: Network Error")

# Query the route
print("Querying route: ", route.name)
try:
    response = client.chat.create(
        model="gpt-3.5-turbo",
        route="test_route_1",  # Use the route name we just created
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is the capital of France?"}
        ]
    )
    pretty_print(response)
except UnauthorizedError as e:
    print("Failed to query route: Unauthorized")
except NetworkError as e:
    print("Failed to query route: Network Error")
except RouteNotFoundError as e:
    print("Failed to query route: Route Not Found")

# Clean up: Delete the route
print("Deleting Route: ", route.name)
try:
    client.delete_route(route.name)
except UnauthorizedError as e:
    print("Failed to delete route: Unauthorized")
except NetworkError as e:
    print("Failed to delete route: Network Error")
except RouteNotFoundError as e:
    print("Failed to delete route: Route Not Found")
