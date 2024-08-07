import argparse
from javelin._internal.commands import (
    create_gateway, list_gateways, read_gateway, update_gateway, delete_gateway,
    create_provider, list_providers, read_provider, update_provider, delete_provider,
    create_route, list_routes, read_route, update_route, delete_route
)

def main():
    parser = argparse.ArgumentParser(description="Javelin CLI for interacting with the SDK")
    subparsers = parser.add_subparsers()

    # Gateway CRUD
    gateway_parser = subparsers.add_parser('gateway', help='Handle gateways')
    gateway_subparsers = gateway_parser.add_subparsers()

    gateway_create = gateway_subparsers.add_parser('create', help='Create a gateway')
    gateway_create.set_defaults(func=create_gateway)

    gateway_list = gateway_subparsers.add_parser('list', help='List gateways')
    gateway_list.set_defaults(func=list_gateways)

    gateway_read = gateway_subparsers.add_parser('read', help='Read a gateway')
    gateway_read.set_defaults(func=read_gateway)

    gateway_update = gateway_subparsers.add_parser('update', help='Update a gateway')
    gateway_update.set_defaults(func=update_gateway)

    gateway_delete = gateway_subparsers.add_parser('delete', help='Delete a gateway')
    gateway_delete.set_defaults(func=delete_gateway)

    # Provider CRUD
    provider_parser = subparsers.add_parser('provider', help='Handle providers')
    provider_subparsers = provider_parser.add_subparsers()

    provider_create = provider_subparsers.add_parser('create', help='Create a provider')
    provider_create.set_defaults(func=create_provider)

    provider_list = provider_subparsers.add_parser('list', help='List providers')
    provider_list.set_defaults(func=list_providers)

    provider_read = provider_subparsers.add_parser('read', help='Read a provider')
    provider_read.set_defaults(func=read_provider)

    provider_update = provider_subparsers.add_parser('update', help='Update a provider')
    provider_update.set_defaults(func=update_provider)

    provider_delete = provider_subparsers.add_parser('delete', help='Delete a provider')
    provider_delete.set_defaults(func=delete_provider)

    # Route CRUD
    route_parser = subparsers.add_parser('route', help='Handle routes')
    route_subparsers = route_parser.add_subparsers()

    route_create = route_subparsers.add_parser('create', help='Create a route')
    route_create.set_defaults(func=create_route)

    route_list = route_subparsers.add_parser('list', help='List routes')
    route_list.set_defaults(func=list_routes)

    route_read = route_subparsers.add_parser('read', help='Read a route')
    route_read.set_defaults(func=read_route)

    route_update = route_subparsers.add_parser('update', help='Update a route')
    route_update.set_defaults(func=update_route)

    route_delete = route_subparsers.add_parser('delete', help='Delete a route')
    route_delete.set_defaults(func=delete_route)

    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()