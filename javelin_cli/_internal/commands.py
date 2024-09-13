import os
import toml
from pathlib import Path
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

def get_javelin_client():
    # Path to default.toml file
    home_dir = Path.home()
    toml_file_path = home_dir / ".javelin" / "gateway.toml"
    
    # Load settings from default.toml
    if not toml_file_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {toml_file_path}")

    with open(toml_file_path, 'r') as toml_file:
        config = toml.load(toml_file)

    # Retrieve settings from the TOML config
    try:
        base_url = config.get("settings", {}).get("base_url", "https://api-dev.javelin.live")
        javelin_api_key = config.get("gateway", {}).get(base_url, {}).get("javelin_api_key")
        javelin_virtualapikey = config.get("settings", {}).get("javelin_virtualapikey")
        llm_api_key = config.get("settings", {}).get("llm_api_key")
    except KeyError as e:
        raise KeyError(f"Missing expected key in the configuration file: {e}")

    # Print all the relevant variables for debugging (optional)
    '''
    print(f"Base URL: {base_url}")
    print(f"Javelin API Key: {javelin_api_key}")
    print(f"Javelin Virtual API Key: {javelin_virtualapikey}")
    print(f"LLM API Key: {llm_api_key}")
    '''

    # Ensure the API key is set before initializing
    if not javelin_api_key or javelin_api_key == "":
        raise UnauthorizedError(
            response=None, message=(
                "Please provide a valid Javelin API Key. "
                "When you sign into Javelin, you can find your API Key in the "
                "Account->Developer settings"
            )
        )
    
    # Initialize the JavelinClient when required
    return JavelinClient(
        base_url=base_url,
        javelin_api_key=javelin_api_key,
        javelin_virtualapikey=javelin_virtualapikey,
        llm_api_key=llm_api_key,
    )
    
    # Initialize the JavelinClient when required
    return JavelinClient(
        base_url=base_url,
        javelin_api_key=javelin_api_key,
        javelin_virtualapikey=javelin_virtualapikey,
        llm_api_key=llm_api_key,
    )

def create_gateway(args):
    try:
        client = get_javelin_client()

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

    except UnauthorizedError as e:
        print(f"UnauthorizedError: {e}")
    except (BadRequest, ValidationError, NetworkError) as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def list_gateways(args):
    try:
        client = get_javelin_client()

        # Fetch and print the list of gateways
        gateways = client.list_gateways()
        print("List of gateways:")
        print(json.dumps(gateways, indent=2, default=lambda o: o.__dict__))

    except UnauthorizedError as e:
        print(f"UnauthorizedError: {e}")
    except (BadRequest, ValidationError, NetworkError) as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def get_gateway(args):
    try:
        client = get_javelin_client()

        gateway = client.get_gateway(args.name)
        print(f"Gateway details for '{args.name}':")
        print(json.dumps(gateway, indent=2, default=lambda o: o.__dict__))

    except UnauthorizedError as e:
        print(f"UnauthorizedError: {e}")
    except (BadRequest, ValidationError, NetworkError) as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def update_gateway(args):
    try:
        client = get_javelin_client()

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

    except UnauthorizedError as e:
        print(f"UnauthorizedError: {e}")
    except (BadRequest, ValidationError, NetworkError) as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def delete_gateway(args):
    try:
        client = get_javelin_client()

        client.delete_gateway(args.name)
        print(f"Gateway '{args.name}' deleted successfully.")

    except UnauthorizedError as e:
        print(f"UnauthorizedError: {e}")
    except (BadRequest, ValidationError, NetworkError) as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def create_provider(args):
    try:
        client = get_javelin_client()

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
    except UnauthorizedError as e:
        print(f"UnauthorizedError: {e}")
    except (BadRequest, ValidationError, NetworkError) as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def list_providers(args):
    try:
        client = get_javelin_client()

        providers = client.list_providers()
        print("List of providers:")
        print(json.dumps(providers, indent=2, default=lambda o: o.__dict__))

    except UnauthorizedError as e:
        print(f"UnauthorizedError: {e}")
    except (BadRequest, ValidationError, NetworkError) as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def get_provider(args):
    try:
        client = get_javelin_client()

        provider = client.get_provider(args.name)
        print(f"Provider details for '{args.name}':")
        print(json.dumps(provider, indent=2, default=lambda o: o.__dict__))

    except UnauthorizedError as e:
        print(f"UnauthorizedError: {e}")
    except (BadRequest, ValidationError, NetworkError) as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def update_provider(args):
    try:
        client = get_javelin_client()

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
    except UnauthorizedError as e:
        print(f"UnauthorizedError: {e}")
    except (BadRequest, ValidationError, NetworkError) as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def delete_provider(args):
    try:
        client = get_javelin_client()

        client.delete_provider(args.name)
        print(f"Provider '{args.name}' deleted successfully.")

    except UnauthorizedError as e:
        print(f"UnauthorizedError: {e}")
    except (BadRequest, ValidationError, NetworkError) as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def create_route(args):
    try:
        client = get_javelin_client()

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
    except UnauthorizedError as e:
        print(f"UnauthorizedError: {e}")
    except (BadRequest, ValidationError, NetworkError) as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def list_routes(args):
    try:
        client = get_javelin_client()

        routes = client.list_routes()
        print("List of routes:")
        print(json.dumps(routes, indent=2, default=lambda o: o.__dict__))

    except UnauthorizedError as e:
        print(f"UnauthorizedError: {e}")
    except (BadRequest, ValidationError, NetworkError) as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def get_route(args):
    try:
        client = get_javelin_client()

        route = client.get_route(args.name)
        print(f"Route details for '{args.name}':")
        print(json.dumps(route, indent=2, default=lambda o: o.__dict__))

    except UnauthorizedError as e:
        print(f"UnauthorizedError: {e}")
    except (BadRequest, ValidationError, NetworkError) as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def update_route(args):
    try:
        client = get_javelin_client()

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
    except UnauthorizedError as e:
        print(f"UnauthorizedError: {e}")
    except (BadRequest, ValidationError, NetworkError) as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def delete_route(args):
    try:
        client = get_javelin_client()
        
        client.delete_route(args.name)
        print(f"Route '{args.name}' deleted successfully.")

    except UnauthorizedError as e:
        print(f"UnauthorizedError: {e}")
    except (BadRequest, ValidationError, NetworkError) as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

from collections import namedtuple

def create_secret(args):
    try:
        client = get_javelin_client()

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

    except UnauthorizedError as e:
        print(f"UnauthorizedError: {e}")
    except (BadRequest, ValidationError, NetworkError) as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def list_secrets(args):
    try:
        client = get_javelin_client()

        secrets = client.list_secrets()
        print("List of secrets:")
        print(json.dumps(secrets, indent=2, default=lambda o: o.__dict__))

    except UnauthorizedError as e:
        print(f"UnauthorizedError: {e}")
    except (BadRequest, ValidationError, NetworkError) as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def get_secret(args):
    try:
        client = get_javelin_client()

        secret = client.get_secret(args.api_key)
        print(f"Secret details for '{args.api_key}':")
        print(json.dumps(secret, indent=2, default=lambda o: o.__dict__))

    except UnauthorizedError as e:
        print(f"UnauthorizedError: {e}")
    except (BadRequest, ValidationError, NetworkError) as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def update_secret(args):
    try:
        client = get_javelin_client()

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

    except UnauthorizedError as e:
        print(f"UnauthorizedError: {e}")
    except (BadRequest, ValidationError, NetworkError) as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def delete_secret(args):
    try:
        client = get_javelin_client()

        client.delete_secret(args.provider_name, args.api_key)
        print(f"Secret '{args.api_key}' deleted successfully.")

    except UnauthorizedError as e:
        print(f"UnauthorizedError: {e}")
    except (BadRequest, ValidationError, NetworkError) as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def create_template(args):
    try:
        client = get_javelin_client()

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
    except UnauthorizedError as e:
        print(f"UnauthorizedError: {e}")
    except (BadRequest, ValidationError, NetworkError) as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def list_templates(args):
    try:
        client = get_javelin_client()

        templates = client.list_templates()
        print("List of templates:")
        print(json.dumps(templates, indent=2, default=lambda o: o.__dict__))

    except UnauthorizedError as e:
        print(f"UnauthorizedError: {e}")
    except (BadRequest, ValidationError, NetworkError) as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def get_template(args):
    try:
        client = get_javelin_client()

        template = client.get_template(args.name)
        print(f"Template details for '{args.name}':")
        print(json.dumps(template, indent=2, default=lambda o: o.__dict__))

    except UnauthorizedError as e:
        print(f"UnauthorizedError: {e}")
    except (BadRequest, ValidationError, NetworkError) as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def update_template(args):
    try:
        client = get_javelin_client()

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
    except UnauthorizedError as e:
        print(f"UnauthorizedError: {e}")
    except (BadRequest, ValidationError, NetworkError) as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def delete_template(args):
    try:
        client = get_javelin_client()

        client.delete_template(args.name)
        print(f"Template '{args.name}' deleted successfully.")
    
    except UnauthorizedError as e:
        print(f"UnauthorizedError: {e}")
    except (BadRequest, ValidationError, NetworkError) as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")