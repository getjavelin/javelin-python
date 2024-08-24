import argparse
from javelin_cli._internal.commands import (
    create_gateway, list_gateways, get_gateway, update_gateway, delete_gateway,
    create_provider, list_providers, get_provider, update_provider, delete_provider,
    create_route, list_routes, get_route, update_route, delete_route,
    create_secret, list_secrets, update_secret, delete_secret,
)

def main():
    parser = argparse.ArgumentParser(description="Javelin CLI for interacting with the SDK")
    subparsers = parser.add_subparsers()

    # Gateway CRUD
    gateway_parser = subparsers.add_parser('gateway', help='Handle gateways')
    gateway_subparsers = gateway_parser.add_subparsers()

    gateway_create = gateway_subparsers.add_parser('create', help='Create a gateway')
    gateway_create.add_argument('--name', type=str, required=True, help='Name of the gateway')
    gateway_create.add_argument('--type', type=str, required=True, help='Type of the gateway')
    gateway_create.add_argument('--enabled', type=bool, default=True, help='Whether the gateway is enabled')
    gateway_create.add_argument('--config', type=str, required=True, help='JSON string of the GatewayConfig')
    gateway_create.set_defaults(func=create_gateway)

    gateway_list = gateway_subparsers.add_parser('list', help='List gateways')
    gateway_list.set_defaults(func=list_gateways)

    gateway_get = gateway_subparsers.add_parser('get', help='Read a gateway')
    gateway_get.add_argument('--name', type=str, required=True, help='Name of the gateway to get')
    gateway_get.set_defaults(func=get_gateway)

    gateway_update = gateway_subparsers.add_parser('update', help='Update a gateway')
    gateway_update.add_argument('--name', type=str, required=True, help='Name of the gateway to update')
    gateway_update.add_argument('--type', type=str, required=True, help='Type of the gateway')
    gateway_update.add_argument('--enabled', type=bool, default=True, help='Whether the gateway is enabled')
    gateway_update.add_argument('--config', type=str, required=True, help='JSON string of the GatewayConfig')
    gateway_update.set_defaults(func=update_gateway)

    gateway_delete = gateway_subparsers.add_parser('delete', help='Delete a gateway')
    gateway_delete.add_argument('--name', type=str, required=True, help='Name of the gateway to delete')
    gateway_delete.set_defaults(func=delete_gateway)

    # Provider CRUD
    provider_parser = subparsers.add_parser('provider', help='Handle providers')
    provider_subparsers = provider_parser.add_subparsers()

    provider_create = provider_subparsers.add_parser('create', help='Create a provider')
    provider_create.add_argument('--name', type=str, required=True, help='Name of the provider')
    provider_create.add_argument('--type', type=str, required=True, help='Type of the provider')
    provider_create.add_argument('--enabled', type=bool, default=True, help='Whether the provider is enabled')
    provider_create.add_argument('--vault_enabled', type=bool, default=True, help='Whether the vault is enabled')
    provider_create.add_argument('--config', type=str, required=True, help='JSON string of the ProviderConfig')
    provider_create.set_defaults(func=create_provider)

    provider_list = provider_subparsers.add_parser('list', help='List providers')
    provider_list.set_defaults(func=list_providers)

    provider_get = provider_subparsers.add_parser('get', help='Read a provider')
    provider_get.add_argument('--name', type=str, required=True, help='Name of the provider to get')
    provider_get.set_defaults(func=get_provider)

    provider_update = provider_subparsers.add_parser('update', help='Update a provider')
    provider_update.add_argument('--name', type=str, required=True, help='Name of the provider to update')
    provider_update.add_argument('--type', type=str, required=True, help='Type of the provider')
    provider_update.add_argument('--enabled', type=bool, default=True, help='Whether the provider is enabled')
    provider_update.add_argument('--vault_enabled', type=bool, default=True, help='Whether the vault is enabled')
    provider_update.add_argument('--config', type=str, required=True, help='JSON string of the ProviderConfig')
    provider_update.set_defaults(func=update_provider)

    provider_delete = provider_subparsers.add_parser('delete', help='Delete a provider')
    provider_delete.add_argument('--name', type=str, required=True, help='Name of the provider to delete')
    provider_delete.set_defaults(func=delete_provider)

    # Route CRUD
    route_parser = subparsers.add_parser('route', help='Handle routes')
    route_subparsers = route_parser.add_subparsers()

    route_create = route_subparsers.add_parser('create', help='Create a route')
    route_create.add_argument('--name', type=str, required=True, help='Name of the route')
    route_create.add_argument('--type', type=str, required=True, help='Type of the route')
    route_create.add_argument('--enabled', type=bool, default=True, help='Whether the route is enabled')
    route_create.add_argument('--models', type=str, required=True, help='JSON string of the models')
    route_create.add_argument('--config', type=str, required=True, help='JSON string of the RouteConfig')
    route_create.set_defaults(func=create_route)

    route_list = route_subparsers.add_parser('list', help='List routes')
    route_list.set_defaults(func=list_routes)

    route_get = route_subparsers.add_parser('get', help='Read a route')
    route_get.add_argument('--name', type=str, required=True, help='Name of the route to get')
    route_get.set_defaults(func=get_route)

    route_update = route_subparsers.add_parser('update', help='Update a route')
    route_update.add_argument('--name', type=str, required=True, help='Name of the route to update')
    route_update.add_argument('--type', type=str, required=True, help='Type of the route')
    route_update.add_argument('--enabled', type=bool, default=True, help='Whether the route is enabled')
    route_update.add_argument('--models', type=str, required=True, help='JSON string of the models')
    route_update.add_argument('--config', type=str, required=True, help='JSON string of the RouteConfig')
    route_update.set_defaults(func=update_route)

    route_delete = route_subparsers.add_parser('delete', help='Delete a route')
    route_delete.add_argument('--name', type=str, required=True, help='Name of the route to delete')
    route_delete.set_defaults(func=delete_route)

    # Secret CRUD
    secret_parser = subparsers.add_parser('secret', help='Handle secrets')
    secret_subparsers = secret_parser.add_subparsers()

    secret_create = secret_subparsers.add_parser('create', help='Create a secret')
    secret_create.add_argument('--api_key', required=True, help='Key of the Secret')
    secret_create.add_argument('--api_key_secret_name', required=True, help='Name of the Secret')
    secret_create.add_argument('--api_key_secret_key', required=True, help='API Key of the Secret')
    secret_create.add_argument('--provider_name', required=True, help='Provider Name of the Secret')
    secret_create.add_argument('--query_param_key', help='Query Param Key of the Secret')
    secret_create.add_argument('--header_key', help='Header Key of the Secret')
    secret_create.add_argument('--group', help='Group of the Secret')
    secret_create.add_argument('--enabled', type=bool, default=True, help='Whether the secret is enabled')
    secret_create.set_defaults(func=create_secret)

    secret_list = secret_subparsers.add_parser('list', help='List secrets')
    secret_list.set_defaults(func=list_secrets)

    secret_update = secret_subparsers.add_parser('update', help='Update a secret')
    secret_update.add_argument('--api_key', required=True, help='Key of the Secret')
    secret_update.add_argument('--api_key_secret_name', required=True, help='Name of the Secret')
    secret_update.add_argument('--api_key_secret_key', help='New API Key of the Secret')
    secret_update.add_argument('--query_param_key', help='New Query Param Key of the Secret')
    secret_update.add_argument('--header_key', help='New Header Key of the Secret')
    secret_update.add_argument('--group', help='New Group of the Secret')
    secret_update.add_argument('--enabled', type=bool, help='Whether the secret is enabled')
    secret_update.set_defaults(func=update_secret)

    secret_delete = secret_subparsers.add_parser('delete', help='Delete a secret')
    secret_delete.add_argument('--api_key', required=True, help='Name of the Secret')
    secret_delete.add_argument('--provider_name', required=True, help='Provider Name of the Secret')
    secret_delete.set_defaults(func=delete_secret)

    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()