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
    Model,
    Route,
    Secret,
    Template,
    Templates,
)
from javelin_sdk.exceptions import (
    BadRequest,
    NetworkError, 
    UnauthorizedError, 
    GatewayNotFoundError, 
    ProviderNotFoundError, 
    RouteNotFoundError,
    SecretNotFoundError,
    TemplateNotFoundError
)

# Retrieve environment variables
base_url = os.getenv("JAVELIN_BASE_URL", "https://api-dev.javelin.live")
javelin_api_key = os.getenv("JAVELIN_API_KEY")
javelin_virtualapikey = os.getenv("JAVELIN_VIRTUALAPIKEY")
llm_api_key = os.getenv("LLM_API_KEY")

# Initialize the global JavelinClient
client = JavelinClient(
    base_url=base_url,
    javelin_api_key=javelin_api_key,
    javelin_virtualapikey=javelin_virtualapikey,
    llm_api_key=llm_api_key,
)

'''
# Print all the relevant variables
print(f"Base URL: {base_url}")
print(f"Javelin API Key: {javelin_api_key}")
print(f"Javelin Virtual API Key: {javelin_virtualapikey}")
print(f"LLM API Key: {llm_api_key}")
'''

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

    except (BadRequest, ValidationError, UnauthorizedError, NetworkError) as e:
        print(f"{e}")
    except Exception as e:
        print(f"{e}")

def list_gateways(args):
    try:
        gateways = client.list_gateways()
        print("List of gateways:")
        print(json.dumps(gateways, indent=2, default=lambda o: o.__dict__))

    except (BadRequest, ValidationError, UnauthorizedError, NetworkError) as e:
        print(f"{e}")
    except Exception as e:
        print(f"{e}")

def get_gateway(args):
    try:
        gateway = client.get_gateway(args.name)
        print(f"Gateway details for '{args.name}':")
        print(json.dumps(gateway, indent=2, default=lambda o: o.__dict__))

    except (BadRequest, ValidationError, UnauthorizedError, NetworkError) as e:
        print(f"{e}")
    except Exception as e:
        print(f"{e}")

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

    except (BadRequest, ValidationError, UnauthorizedError, NetworkError) as e:
        print(f"{e}")
    except Exception as e:
        print(f"{e}")

def delete_gateway(args):
    try:
        client.delete_gateway(args.name)
        print(f"Gateway '{args.name}' deleted successfully.")

    except (BadRequest, ValidationError, UnauthorizedError, NetworkError) as e:
        print(f"{e}")
    except Exception as e:
        print(f"{e}")

def create_provider(args):
    try:
        # Parse the JSON string from args.config to a dictionary
        config_data = json.loads(args.config)
        # Create an instance of ProviderConfig using the parsed config_data
        config = ProviderConfig(**config_data)

        # Create an instance of the Provider class
        provider = Provider(
            name=args.name,
            type=args.type,
            enabled=args.enabled if args.enabled is not None else True,  # Default to True if not provided
            vault_enabled=args.vault_enabled if args.vault_enabled is not None else True,  # Default to True if not provided
            config=config
        )

        # Assuming client.create_provider accepts a Pydantic model and handles it internally
        client.create_provider(provider)
        print(f"Provider '{args.name}' created successfully.")

    except json.JSONDecodeError as e:
        print(f"Error parsing configuration JSON: {e}")
    except (BadRequest, ValidationError, UnauthorizedError, NetworkError) as e:
        print(f"{e}")
    except Exception as e:
        print(f"{e}")

def list_providers(args):
    try:
        providers = client.list_providers()
        print("List of providers:")
        print(json.dumps(providers, indent=2, default=lambda o: o.__dict__))

    except (BadRequest, ValidationError, UnauthorizedError, NetworkError) as e:
        print(f"{e}")
    except Exception as e:
        print(f"{e}")

def get_provider(args):
    try:
        provider = client.get_provider(args.name)
        print(f"Provider details for '{args.name}':")
        print(json.dumps(provider, indent=2, default=lambda o: o.__dict__))

    except (BadRequest, ValidationError, UnauthorizedError, NetworkError) as e:
        print(f"{e}")
    except Exception as e:
        print(f"{e}")

def update_provider(args):
    try:
        # Parse the JSON string for config
        config_data = json.loads(args.config)
        # Create an instance of ProviderConfig using the parsed config_data
        config = ProviderConfig(**config_data)

        # Create an instance of the Provider class
        provider = Provider(
            name=args.name,
            type=args.type,
            enabled=args.enabled if args.enabled is not None else None,
            vault_enabled=args.vault_enabled if args.vault_enabled is not None else None,
            config=config
        )

        result = client.update_provider(provider)
        print(f"Provider '{args.name}' updated successfully.")

    except json.JSONDecodeError as e:
        print(f"Error parsing configuration JSON: {e}")
    except (BadRequest, ValidationError, UnauthorizedError, NetworkError) as e:
        print(f"{e}")
    except Exception as e:
        print(f"{e}")

def delete_provider(args):
    try:
        client.delete_provider(args.name)
        print(f"Provider '{args.name}' deleted successfully.")

    except (BadRequest, ValidationError, UnauthorizedError, NetworkError) as e:
        print(f"{e}")
    except Exception as e:
        print(f"{e}")

def create_route(args):
    try:
        # Parse the JSON string for config and models
        config_data = json.loads(args.config)
        models_data = json.loads(args.models)

        # Create instances of RouteConfig and Model using the parsed data
        config = RouteConfig(**config_data)
        models = [Model(**model) for model in models_data]

        # Create an instance of the Route class
        route = Route(
            name=args.name,
            type=args.type,
            enabled=args.enabled if args.enabled is not None else True,  # Default to True if not provided
            models=models,
            config=config
        )

        # Assuming client.create_route accepts a Pydantic model and handles it internally
        client.create_route(route)
        print(f"Route '{args.name}' created successfully.")

    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
    except (BadRequest, ValidationError, UnauthorizedError, NetworkError) as e:
        print(f"{e}")
    except Exception as e:
        print(f"{e}")

def list_routes(args):
    try:
        routes = client.list_routes()
        print("List of routes:")
        print(json.dumps(routes, indent=2, default=lambda o: o.__dict__))

    except UnauthorizedError as e:
        print(f"{e}")
    except NetworkError as e:
        
        print(f"{e}")

def get_route(args):
    try:
        route = client.get_route(args.name)
        print(f"Route details for '{args.name}':")
        print(json.dumps(route, indent=2, default=lambda o: o.__dict__))

    except (BadRequest, ValidationError, UnauthorizedError, NetworkError) as e:
        print(f"{e}")
    except Exception as e:
        print(f"{e}")

def update_route(args):
    try:
        # Parse the JSON string for config and models
        config_data = json.loads(args.config)
        models_data = json.loads(args.models)

        # Create instances of RouteConfig and Model using the parsed data
        config = RouteConfig(**config_data)
        models = [Model(**model) for model in models_data]

        # Create an instance of the Route class
        route = Route(
            name=args.name,
            type=args.type,
            enabled=args.enabled if args.enabled is not None else None,
            models=models,
            config=config
        )

        result = client.update_route(route)
        print(f"Route '{args.name}' updated successfully.")

    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
    except (BadRequest, ValidationError, UnauthorizedError, NetworkError) as e:
        print(f"{e}")
    except Exception as e:
        print(f"{e}")

def delete_route(args):
    try:
        client.delete_route(args.name)
        print(f"Route '{args.name}' deleted successfully.")

    except (BadRequest, ValidationError, UnauthorizedError, NetworkError) as e:
        print(f"{e}")
    except Exception as e:
        print(f"{e}")

from collections import namedtuple

def create_secret(args):
    try:
        # Create an instance of the Secret class using the provided arguments
        secret = Secret(
            api_key=args.api_key,
            api_key_secret_name=args.api_key_secret_name,
            api_key_secret_key=args.api_key_secret_key,
            provider_name=args.provider_name,
            enabled=args.enabled if args.enabled is not None else True  # Default to True if not provided
        )

        # Include optional arguments only if they are provided
        if args.query_param_key is not None:
            secret.query_param_key = args.query_param_key
        if args.header_key is not None:
            secret.header_key = args.header_key
        if args.group is not None:
            secret.group = args.group

        # Use the client to create the secret
        result = client.create_secret(secret)
        print(result)

    except (BadRequest, ValidationError, UnauthorizedError, NetworkError) as e:
        print(f"{e}")
    except Exception as e:
        print(f"{e}")

def list_secrets(args):
    try:
        secrets = client.list_secrets()
        print("List of secrets:")
        print(json.dumps(secrets, indent=2, default=lambda o: o.__dict__))

    except (BadRequest, ValidationError, UnauthorizedError, NetworkError) as e:
        print(f"{e}")
    except Exception as e:
        print(f"{e}")

def get_secret(args):
    try:
        secret = client.get_secret(args.api_key)
        print(f"Secret details for '{args.api_key}':")
        print(json.dumps(secret, indent=2, default=lambda o: o.__dict__))

    except (BadRequest, ValidationError, UnauthorizedError, NetworkError) as e:
        print(f"{e}")
    except Exception as e:
        print(f"{e}")

def update_secret(args):
    try:
        # Create an instance of the Secret class
        secret = Secret(
            api_key=args.api_key,
            api_key_secret_name=args.api_key_secret_name if args.api_key_secret_name else None,
            api_key_secret_key=args.api_key_secret_key if args.api_key_secret_key else None,
            query_param_key=args.query_param_key if args.query_param_key else None,
            header_key=args.header_key if args.header_key else None,
            group=args.group if args.group else None,
            enabled=args.enabled if args.enabled is not None else None
        )

        result = client.update_secret(secret)
        print(f"Secret '{args.api_key}' updated successfully.")

    except (BadRequest, ValidationError, UnauthorizedError, NetworkError) as e:
        print(f"{e}")
    except Exception as e:
        print(f"{e}")

def delete_secret(args):
    try:
        client.delete_secret(args.provider_name, args.api_key)
        print(f"Secret '{args.api_key}' deleted successfully.")

    except (BadRequest, ValidationError, UnauthorizedError, NetworkError) as e:
        print(f"{e}")
    except Exception as e:
        print(f"{e}")

def create_template(args):
    try:
        # Parse the JSON string for config and models
        config_data = json.loads(args.config)
        models_data = json.loads(args.models)

        # Create instances of TemplateConfig and Model using the parsed data
        config = TemplateConfig(**config_data)
        models = [Model(**model) for model in models_data]

        # Create an instance of the Template class
        template = Template(
            name=args.name,
            description=args.description,
            type=args.type,
            enabled=args.enabled if args.enabled is not None else True,  # Default to True if not provided
            models=models,
            config=config
        )

        result = client.create_template(template)
        print(f"Template '{args.name}' created successfully.")

    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
    except (BadRequest, ValidationError, UnauthorizedError, NetworkError) as e:
        print(f"{e}")
    except Exception as e:
        print(f"{e}")

def list_templates(args):
    try:
        templates = client.list_templates()
        print("List of templates:")
        print(json.dumps(templates, indent=2, default=lambda o: o.__dict__))

    except (BadRequest, ValidationError, UnauthorizedError, NetworkError) as e:
        print(f"{e}")
    except Exception as e:
        print(f"{e}")

def get_template(args):
    try:
        template = client.get_template(args.name)
        print(f"Template details for '{args.name}':")
        print(json.dumps(template, indent=2, default=lambda o: o.__dict__))

    except (BadRequest, ValidationError, UnauthorizedError, NetworkError) as e:
        print(f"{e}")
    except Exception as e:
        print(f"{e}")

def update_template(args):
    try:
        # Parse the JSON string for config and models
        config_data = json.loads(args.config)
        models_data = json.loads(args.models)

        # Create instances of TemplateConfig and Model using the parsed data
        config = TemplateConfig(**config_data)
        models = [Model(**model) for model in models_data]

        # Create an instance of the Template class
        template = Template(
            name=args.name,
            description=args.description if args.description else None,
            type=args.type if args.type else None,
            enabled=args.enabled if args.enabled is not None else None,
            models=models,
            config=config
        )

        result = client.update_template(template)
        print(f"Template '{args.name}' updated successfully.")

    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
    except (BadRequest, ValidationError, UnauthorizedError, NetworkError) as e:
        print(f"{e}")
    except Exception as e:
        print(f"{e}")

def delete_template(args):
    try:
        client.delete_template(args.name)
        print(f"Template '{args.name}' deleted successfully.")
    
    except (BadRequest, ValidationError, UnauthorizedError, NetworkError) as e:
        print(f"{e}")
    except Exception as e:
        print(f"{e}")