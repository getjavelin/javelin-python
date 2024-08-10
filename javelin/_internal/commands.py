import os
import json
from pydantic import ValidationError

from javelin_sdk.client import JavelinClient
from javelin_sdk.models import (
    GatewayConfig,
    Gateway,
    ProviderConfig,
    Provider,
    RouteConfig,
    Route,
    Secret,
    Template,
    Templates,
)
from javelin_sdk.exceptions import (
    NetworkError, 
    UnauthorizedError, 
    GatewayNotFoundError, 
    ProviderNotFoundError, 
    RouteNotFoundError
)

# Retrieve environment variables
javelin_api_key = os.getenv("JAVELIN_API_KEY")
javelin_virtualapikey = os.getenv("JAVELIN_VIRTUALAPIKEY")
llm_api_key = os.getenv("LLM_API_KEY")

# Initialize the global JavelinClient
client = JavelinClient(
    base_url="https://api-dev.javelin.live",
    javelin_api_key=javelin_api_key,
    javelin_virtualapikey=javelin_virtualapikey,
    llm_api_key=llm_api_key,
)

def create_gateway(args):
    try:
        # Parse the JSON input for GatewayConfig
        config_data = json.loads(args.config)
        config = GatewayConfig(**config_data)
        
        gateway = Gateway(
            name=args.name,
            type=args.type,
            enabled=args.enabled,
            config=config
        )
        
        result = client.create_gateway(gateway)
        print(result)

    except ValidationError as e:
        print(f"Validation error: {e}")
    except UnauthorizedError as e:
        print(f"Unauthorized: {e}")
    except NetworkError as e:
        print(f"Network error: {e}")

def list_gateways(args):
    try:
        gateways = client.list_gateways()
        print("List of gateways:")
        print(json.dumps(gateways, indent=2, default=lambda o: o.__dict__))
    except UnauthorizedError as e:
        print(f"Unauthorized: {e}")
    except NetworkError as e:
        print(f"Network error: {e}")

def read_gateway(args):
    try:
        gateway = client.get_gateway(args.name)
        print(f"Gateway details for '{args.name}':")
        print(gateway)
    except GatewayNotFoundError as e:
        print(f"Gateway not found: {e}")
    except UnauthorizedError as e:
        print(f"Unauthorized: {e}")
    except NetworkError as e:
        print(f"Network error: {e}")

def update_gateway(args):
    try:
        config_data = json.loads(args.config)
        config = GatewayConfig(**config_data)

        gateway = Gateway(
            name=args.name,
            type=args.type,
            enabled=args.enabled,
            config=config
        )
        
        client.update_gateway(args.name, gateway_data)
        print(f"Gateway '{args.name}' updated successfully.")

    except GatewayNotFoundError as e:
        print(f"Gateway not found: {e}")
    except UnauthorizedError as e:
        print(f"Unauthorized: {e}")
    except NetworkError as e:
        print(f"Network error: {e}")

def delete_gateway(args):
    try:
        client.delete_gateway(args.name)
        print(f"Gateway '{args.name}' deleted successfully.")
    except GatewayNotFoundError as e:
        print(f"Gateway not found: {e}")
    except UnauthorizedError as e:
        print(f"Unauthorized: {e}")
    except NetworkError as e:
        print(f"Network error: {e}")

def create_provider(args):
    try:
        provider_data = {
            "name": args.name,
            "config": args.config,
        }
        client.create_provider(provider_data)
        print(f"Provider '{args.name}' created successfully.")
    except UnauthorizedError as e:
        print(f"Unauthorized: {e}")
    except NetworkError as e:
        print(f"Network error: {e}")

def list_providers(args):
    try:
        providers = client.list_providers()
        print("List of providers:")
        print(json.dumps(providers, indent=2, default=lambda o: o.__dict__))
    except UnauthorizedError as e:
        print(f"Unauthorized: {e}")
    except NetworkError as e:
        print(f"Network error: {e}")

def read_provider(args):
    try:
        provider = client.get_provider(args.name)
        print(f"Provider details for '{args.name}':")
        print(provider)
    except ProviderNotFoundError as e:
        print(f"Provider not found: {e}")
    except UnauthorizedError as e:
        print(f"Unauthorized: {e}")
    except NetworkError as e:
        print(f"Network error: {e}")

def update_provider(args):
    try:
        provider_data = {
            "name": args.name,
            "config": args.config,
        }
        client.update_provider(args.name, provider_data)
        print(f"Provider '{args.name}' updated successfully.")
    except ProviderNotFoundError as e:
        print(f"Provider not found: {e}")
    except UnauthorizedError as e:
        print(f"Unauthorized: {e}")
    except NetworkError as e:
        print(f"Network error: {e}")

def delete_provider(args):
    try:
        client.delete_provider(args.name)
        print(f"Provider '{args.name}' deleted successfully.")
    except ProviderNotFoundError as e:
        print(f"Provider not found: {e}")
    except UnauthorizedError as e:
        print(f"Unauthorized: {e}")
    except NetworkError as e:
        print(f"Network error: {e}")

def create_route(args):
    try:
        route_data = {
            "name": args.name,
            "config": args.config,
        }
        client.create_route(route_data)
        print(f"Route '{args.name}' created successfully.")
    except UnauthorizedError as e:
        print(f"Unauthorized: {e}")
    except NetworkError as e:
        print(f"Network error: {e}")

def list_routes(args):
    try:
        routes = client.list_routes()
        print("List of routes:")
        print(json.dumps(routes, indent=2, default=lambda o: o.__dict__))
    except UnauthorizedError as e:
        print(f"Unauthorized: {e}")
    except NetworkError as e:
        print(f"Network error: {e}")

def read_route(args):
    try:
        route = client.get_route(args.name)
        print(f"Route details for '{args.name}':")
        print(route)
    except RouteNotFoundError as e:
        print(f"Route not found: {e}")
    except UnauthorizedError as e:
        print(f"Unauthorized: {e}")
    except NetworkError as e:
        print(f"Network error: {e}")

def update_route(args):
    try:
        route_data = {
            "name": args.name,
            "config": args.config,
        }
        client.update_route(args.name, route_data)
        print(f"Route '{args.name}' updated successfully.")
    except RouteNotFoundError as e:
        print(f"Route not found: {e}")
    except UnauthorizedError as e:
        print(f"Unauthorized: {e}")
    except NetworkError as e:
        print(f"Network error: {e}")

def delete_route(args):
    try:
        client.delete_route(args.name)
        print(f"Route '{args.name}' deleted successfully.")
    except RouteNotFoundError as e:
        print(f"Route not found: {e}")
    except UnauthorizedError as e:
        print(f"Unauthorized: {e}")
    except NetworkError as e:
        print(f"Network error: {e}")