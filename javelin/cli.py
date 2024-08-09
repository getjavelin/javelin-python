import argparse
from ._internal.commands import handle_route, handle_provider, handle_gateway

def main():
    parser = argparse.ArgumentParser(description="Javelin CLI for interacting with the SDK")
    subparsers = parser.add_subparsers()

    # Example command for handling gateways
    parser_gateway = subparsers.add_parser('gateway', help='Handle gateways')
    parser_gateway.set_defaults(func=handle_gateway)


    # Example command for handling providers
    parser_provider = subparsers.add_parser('provider', help='Handle providers')
    parser_provider.set_defaults(func=handle_provider)

    # Example command for handling routes
    parser_route = subparsers.add_parser('route', help='Handle routes')
    parser_route.set_defaults(func=handle_route)

    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()