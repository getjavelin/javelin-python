import os, sys
import json

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
    # If the object has a `dict` method, call it to get its dictionary representation.
    if hasattr(obj, "dict"):
        obj = obj.dict()

    # Use the `json` module to print the dictionary as a string.
    try:
        print(json.dumps(obj, indent=4))
    except TypeError:
        print(obj)

def route_openai(client, route_name):
    query_data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"}
        ]
    }
    query_route(client, route_name, query_data)
    
def route_azureopenai(client, route_name):
    query_data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"}
        ]
    }
    query_route(client, route_name, query_data)

def route_bedrockmeta(client, route_name):
    query_data = {
        "prompt": "Hello!"
    }
    query_route(client, route_name, query_data)

def route_bedrockamazon(client, route_name):
    query_data = {
        "inputText": "Hello!"
    }
    query_route(client, route_name, query_data)

# Reusable query_route function
def query_route(client, route_name, query_data):
    print("Querying route: ", route_name)
    try:
        response = client.query_route(route_name, query_data)
        pretty_print(response)
    except UnauthorizedError:
        print("Failed to query route: Unauthorized")
    except NetworkError:
        print("Failed to query route: Network Error")
    except RouteNotFoundError:
        print("Failed to query route: Route Not Found")

# Function to iterate over the model providers and query routes
def query_routes(client):
    for model_provider_route in model_providers_routes:
        provider = model_provider_route["provider"]
        route_name = model_provider_route["route_name"]
        route_function = model_provider_route["route_function"]
        
        print(f"Querying route for provider: {provider}")
        route_function(client, route_name)

# Array of model providers & corresponding route names (Please Note: Routes created using Javelin App https://dev.javelin.live/)
model_providers_routes = [
    {"provider": "OpenAI", "route_name": "myusers", "route_function": route_openai},
    {"provider": "Azure OpenAI", "route_name": "azureopenai", "route_function": route_azureopenai},
#   {"provider": "Bedrock AI21 Labs", "route_name": "bedrockai21labs", "route_function": route_bedrockai21labs},
    {"provider": "Bedrock Amazon", "route_name": "bedrocktitan", "route_function": route_bedrockamazon},
#   {"provider": "Bedrock Anthropic", "route_name": "bedrockanthropic", "route_function": route_bedrockanthropic},
#   {"provider": "Bedrock Cohere", "route_name": "bedrockcohere", "route_function": route_bedrockcohere},
    {"provider": "Bedrock Meta", "route_name": "bedrockllama", "route_function": route_bedrockmeta},
#   {"provider": "Bedrock Mistral AI", "route_name": "bedrockmistral", "route_function": route_bedrockmistral}
]

def main():
    """
    Create a JavelinClient object. This object is used to interact
    with the Javelin API. The base_url parameter is the URL of the Javelin API.
    """

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
    except UnauthorizedError as e:
        print("Failed to get route: Unauthorized")
    except NetworkError as e:
        print("Failed to get route: Network Error")
    except RouteNotFoundError as e:
        print("Failed to get route: Route Not Found")       

    # Loop through the model providers and query each route
    for model in model_providers_routes:
        print(f"Querying provider: {model['provider']} with route name: {model['route_name']}")
        try:
            # Call the route function with the client and route name
            model['route_function'](client, model['route_name'])
        except Exception as e:
            print(f"Failed to query route for {model['provider']}: {str(e)}")

if __name__ == "__main__":
    main()