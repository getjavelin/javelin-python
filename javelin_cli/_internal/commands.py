import json
import os
from pathlib import Path

from pydantic import ValidationError

from javelin_sdk.client import JavelinClient
from javelin_sdk.exceptions import (
    BadRequest,
    GatewayNotFoundError,
    NetworkError,
    ProviderNotFoundError,
    RouteNotFoundError,
    SecretNotFoundError,
    TemplateNotFoundError,
    UnauthorizedError,
)
from javelin_sdk.models import (
    Gateway,
    GatewayConfig,
    JavelinConfig,
    Model,
    Provider,
    ProviderConfig,
    Route,
    RouteConfig,
    Secret,
    Secrets,
    Template,
    Templates,
)


def get_javelin_client():
    # Path to cache.json file
    home_dir = Path.home()
    json_file_path = home_dir / ".javelin" / "cache.json"

    # Load cache.json
    if not json_file_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {json_file_path}")

    with open(json_file_path, "r") as json_file:
        cache_data = json.load(json_file)

    # Retrieve the list of gateways
    gateways = cache_data.get("memberships", {}).get("data", [{}])[0].get("organization", {}).get("public_metadata", {}).get("Gateways", [])
    if not gateways:
        raise ValueError("No gateways found in the configuration.")

    # List available gateways
    print("Available Gateways:")
    for i, gateway in enumerate(gateways):
        print(f"{i + 1}. {gateway['namespace']} - {gateway['base_url']}")

    # Allow the user to select a gateway
    choice = int(input("Select a gateway (enter the number): ")) - 1

    if choice < 0 or choice >= len(gateways):
        raise ValueError("Invalid selection. Please choose a valid gateway.")

    selected_gateway = gateways[choice]
    base_url = selected_gateway["base_url"]
    javelin_api_key = selected_gateway["api_key_value"]

    # Print all the relevant variables for debugging (optional)
    # print(f"Base URL: {base_url}")
    # print(f"Javelin API Key: {javelin_api_key}")

    # Ensure the API key is set before initializing
    if not javelin_api_key or javelin_api_key == "":
        raise UnauthorizedError(
            response=None,
            message=(
                "Please provide a valid Javelin API Key. "
                "When you sign into Javelin, you can find your API Key in the "
                "Account->Developer settings"
            ),
        )

    # Initialize the JavelinClient when required
    config = JavelinConfig(
        base_url=base_url,
        javelin_api_key=javelin_api_key,
    )

    return JavelinClient(config)


def create_gateway(args):
    try:
        client = get_javelin_client()

        # Parse the JSON input for GatewayConfig
        config_data = json.loads(args.config)
        config = GatewayConfig(**config_data)
        gateway = Gateway(
            name=args.name, type=args.type, enabled=args.enabled, config=config
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
    """
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
    """
    # Path to cache.json file
    home_dir = Path.home()
    json_file_path = home_dir / ".javelin" / "cache.json"

    # Load cache.json
    if not json_file_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {json_file_path}")

    with open(json_file_path, "r") as json_file:
        cache_data = json.load(json_file)

    # Retrieve the list of gateways
    gateways = cache_data.get("memberships", {}).get("data", [{}])[0].get("organization", {}).get("public_metadata", {}).get("Gateways", [])
    if not gateways:
        print("No gateways found in the configuration.")
        return

    if not gateways:
        raise ValueError("No gateways found in the configuration.")

    # List available gateways
    print("Available Gateways:")
    for i, gateway in enumerate(gateways):
        print(f"\nGateway {i + 1}:")
        for key, value in gateway.items():
            print(f"  {key}: {value}")


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
            name=args.name, type=args.type, enabled=args.enabled, config=config
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
            enabled=(
                args.enabled if args.enabled is not None else True
            ),  # Default to True if not provided
            vault_enabled=(
                args.vault_enabled if args.vault_enabled is not None else True
            ),  # Default to True if not provided
            config=config,
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
            vault_enabled=(
                args.vault_enabled if args.vault_enabled is not None else None
            ),
            config=config,
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
            enabled=(
                args.enabled if args.enabled is not None else True
            ),  # Default to True if not provided
            models=models,
            config=config,
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
            config=config,
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
            enabled=(
                args.enabled if args.enabled is not None else True
            ),  # Default to True if not provided
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

        # Fetch the list of secrets from the client
        secrets_response = client.list_secrets()
        # print(secrets_response.json(indent=2))

        # Check if the response is an instance of Secrets
        if isinstance(secrets_response, Secrets):
            secrets_list = secrets_response.secrets

            # Check if there are no secrets
            if not secrets_list:
                print("No secrets available.")
                return

            # Iterate over the secrets and mask sensitive data
            masked_secrets = [secret.masked() for secret in secrets_list]

            # Print the masked secrets
            print(json.dumps({"secrets": masked_secrets}, indent=2))

        else:
            print(f"Unexpected secret format: {secrets_response}")

    except UnauthorizedError as e:
        print(f"UnauthorizedError: {e}")
    except (BadRequest, ValidationError, NetworkError) as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def get_secret(args):
    try:
        client = get_javelin_client()

        # Fetch the secret and mask sensitive data
        secret = client.get_secret(args.api_key)
        masked_secret = secret.masked()  # Ensure the sensitive fields are masked

        print(f"Secret details for '{args.api_key}':")
        print(json.dumps(masked_secret, indent=2))

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
            api_key_secret_name=(
                args.api_key_secret_name if args.api_key_secret_name else None
            ),
            api_key_secret_key=(
                args.api_key_secret_key if args.api_key_secret_key else None
            ),
            query_param_key=args.query_param_key if args.query_param_key else None,
            header_key=args.header_key if args.header_key else None,
            group=args.group if args.group else None,
            enabled=args.enabled if args.enabled is not None else None,
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
            enabled=(
                args.enabled if args.enabled is not None else True
            ),  # Default to True if not provided
            models=models,
            config=config,
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
            config=config,
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
