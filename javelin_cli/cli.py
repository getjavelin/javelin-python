import argparse
import importlib.metadata
import os
import webbrowser
from pathlib import Path
import json
import http.server
import socketserver
import threading
import urllib.parse
import random

import requests

from javelin_cli._internal.commands import (
    create_gateway,
    create_provider,
    create_route,
    create_secret,
    create_template,
    delete_gateway,
    delete_provider,
    delete_route,
    delete_secret,
    delete_template,
    get_gateway,
    get_provider,
    get_route,
    get_template,
    list_gateways,
    list_providers,
    list_routes,
    list_secrets,
    list_templates,
    update_gateway,
    update_provider,
    update_route,
    update_secret,
    update_template,
)


def main():
    # Fetch the version dynamically from the package
    package_version = importlib.metadata.version(
        "javelin-sdk"
    )  # Replace with your package name

    parser = argparse.ArgumentParser(
        description="The CLI for Javelin.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="See https://docs.getjavelin.io/docs/javelin-python/cli for more detailed documentation.",
    )
    parser.add_argument(
        "--version", action="version", version=f"Javelin CLI v{package_version}"
    )

    subparsers = parser.add_subparsers(title="commands", metavar="")

    # Auth command
    auth_parser = subparsers.add_parser("auth", help="Authenticate with Javelin.")
    auth_parser.add_argument("--force", action="store_true", help="Force re-authentication, overriding existing credentials")
    auth_parser.set_defaults(func=authenticate)

    # Gateway CRUD
    gateway_parser = subparsers.add_parser(
        "gateway",
        help="Manage gateways: create, list, update, and delete gateways for routing requests.",
    )
    gateway_subparsers = gateway_parser.add_subparsers()

    gateway_create = gateway_subparsers.add_parser("create", help="Create a gateway")
    gateway_create.add_argument(
        "--name", type=str, required=True, help="Name of the gateway"
    )
    gateway_create.add_argument(
        "--type", type=str, required=True, help="Type of the gateway"
    )
    gateway_create.add_argument(
        "--enabled", type=bool, default=True, help="Whether the gateway is enabled"
    )
    gateway_create.add_argument(
        "--config", type=str, required=True, help="JSON string of the GatewayConfig"
    )
    gateway_create.set_defaults(func=create_gateway)

    gateway_list = gateway_subparsers.add_parser("list", help="List gateways")
    gateway_list.set_defaults(func=list_gateways)

    gateway_get = gateway_subparsers.add_parser("get", help="Read a gateway")
    gateway_get.add_argument(
        "--name", type=str, required=True, help="Name of the gateway to get"
    )
    gateway_get.set_defaults(func=get_gateway)

    gateway_update = gateway_subparsers.add_parser("update", help="Update a gateway")
    gateway_update.add_argument(
        "--name", type=str, required=True, help="Name of the gateway to update"
    )
    gateway_update.add_argument(
        "--type", type=str, required=True, help="Type of the gateway"
    )
    gateway_update.add_argument(
        "--enabled", type=bool, default=True, help="Whether the gateway is enabled"
    )
    gateway_update.add_argument(
        "--config", type=str, required=True, help="JSON string of the GatewayConfig"
    )
    gateway_update.set_defaults(func=update_gateway)

    gateway_delete = gateway_subparsers.add_parser("delete", help="Delete a gateway")
    gateway_delete.add_argument(
        "--name", type=str, required=True, help="Name of the gateway to delete"
    )
    gateway_delete.set_defaults(func=delete_gateway)

    # Provider CRUD
    provider_parser = subparsers.add_parser(
        "provider",
        help="Manage model providers: configure and manage large language model providers.",
    )
    provider_subparsers = provider_parser.add_subparsers()

    provider_create = provider_subparsers.add_parser("create", help="Create a provider")
    provider_create.add_argument(
        "--name", type=str, required=True, help="Name of the provider"
    )
    provider_create.add_argument(
        "--type", type=str, required=True, help="Type of the provider"
    )
    provider_create.add_argument(
        "--enabled", type=bool, default=True, help="Whether the provider is enabled"
    )
    provider_create.add_argument(
        "--vault_enabled", type=bool, default=True, help="Whether the vault is enabled"
    )
    provider_create.add_argument(
        "--config", type=str, required=True, help="JSON string of the ProviderConfig"
    )
    provider_create.set_defaults(func=create_provider)

    provider_list = provider_subparsers.add_parser("list", help="List providers")
    provider_list.set_defaults(func=list_providers)

    provider_get = provider_subparsers.add_parser("get", help="Read a provider")
    provider_get.add_argument(
        "--name", type=str, required=True, help="Name of the provider to get"
    )
    provider_get.set_defaults(func=get_provider)

    provider_update = provider_subparsers.add_parser("update", help="Update a provider")
    provider_update.add_argument(
        "--name", type=str, required=True, help="Name of the provider to update"
    )
    provider_update.add_argument(
        "--type", type=str, required=True, help="Type of the provider"
    )
    provider_update.add_argument(
        "--enabled", type=bool, default=True, help="Whether the provider is enabled"
    )
    provider_update.add_argument(
        "--vault_enabled", type=bool, default=True, help="Whether the vault is enabled"
    )
    provider_update.add_argument(
        "--config", type=str, required=True, help="JSON string of the ProviderConfig"
    )
    provider_update.set_defaults(func=update_provider)

    provider_delete = provider_subparsers.add_parser("delete", help="Delete a provider")
    provider_delete.add_argument(
        "--name", type=str, required=True, help="Name of the provider to delete"
    )
    provider_delete.set_defaults(func=delete_provider)

    # Route CRUD
    route_parser = subparsers.add_parser(
        "route",
        help="Manage routing rules: define and control the routing logic for handling requests.",
    )
    route_subparsers = route_parser.add_subparsers()

    route_create = route_subparsers.add_parser("create", help="Create a route")
    route_create.add_argument(
        "--name", type=str, required=True, help="Name of the route"
    )
    route_create.add_argument(
        "--type", type=str, required=True, help="Type of the route"
    )
    route_create.add_argument(
        "--enabled", type=bool, default=True, help="Whether the route is enabled"
    )
    route_create.add_argument(
        "--models", type=str, required=True, help="JSON string of the models"
    )
    route_create.add_argument(
        "--config", type=str, required=True, help="JSON string of the RouteConfig"
    )
    route_create.set_defaults(func=create_route)

    route_list = route_subparsers.add_parser("list", help="List routes")
    route_list.set_defaults(func=list_routes)

    route_get = route_subparsers.add_parser("get", help="Read a route")
    route_get.add_argument(
        "--name", type=str, required=True, help="Name of the route to get"
    )
    route_get.set_defaults(func=get_route)

    route_update = route_subparsers.add_parser("update", help="Update a route")
    route_update.add_argument(
        "--name", type=str, required=True, help="Name of the route to update"
    )
    route_update.add_argument(
        "--type", type=str, required=True, help="Type of the route"
    )
    route_update.add_argument(
        "--enabled", type=bool, default=True, help="Whether the route is enabled"
    )
    route_update.add_argument(
        "--models", type=str, required=True, help="JSON string of the models"
    )
    route_update.add_argument(
        "--config", type=str, required=True, help="JSON string of the RouteConfig"
    )
    route_update.set_defaults(func=update_route)

    route_delete = route_subparsers.add_parser("delete", help="Delete a route")
    route_delete.add_argument(
        "--name", type=str, required=True, help="Name of the route to delete"
    )
    route_delete.set_defaults(func=delete_route)

    # Secret CRUD
    secret_parser = subparsers.add_parser(
        "secret",
        help="Manage API secrets: securely handle and manage API keys and credentials for access control.",
    )
    secret_subparsers = secret_parser.add_subparsers()

    secret_create = secret_subparsers.add_parser("create", help="Create a secret")
    secret_create.add_argument("--api_key", required=True, help="Key of the Secret")
    secret_create.add_argument(
        "--api_key_secret_name", required=True, help="Name of the Secret"
    )
    secret_create.add_argument(
        "--api_key_secret_key", required=True, help="API Key of the Secret"
    )
    secret_create.add_argument(
        "--provider_name", required=True, help="Provider Name of the Secret"
    )
    secret_create.add_argument(
        "--query_param_key", help="Query Param Key of the Secret"
    )
    secret_create.add_argument("--header_key", help="Header Key of the Secret")
    secret_create.add_argument("--group", help="Group of the Secret")
    secret_create.add_argument(
        "--enabled", type=bool, default=True, help="Whether the secret is enabled"
    )
    secret_create.set_defaults(func=create_secret)

    secret_list = secret_subparsers.add_parser("list", help="List secrets")
    secret_list.set_defaults(func=list_secrets)

    secret_update = secret_subparsers.add_parser("update", help="Update a secret")
    secret_update.add_argument("--api_key", required=True, help="Key of the Secret")
    secret_update.add_argument(
        "--api_key_secret_name", required=True, help="Name of the Secret"
    )
    secret_update.add_argument("--api_key_secret_key", help="New API Key of the Secret")
    secret_update.add_argument(
        "--query_param_key", help="New Query Param Key of the Secret"
    )
    secret_update.add_argument("--header_key", help="New Header Key of the Secret")
    secret_update.add_argument("--group", help="New Group of the Secret")
    secret_update.add_argument(
        "--enabled", type=bool, help="Whether the secret is enabled"
    )
    secret_update.set_defaults(func=update_secret)

    secret_delete = secret_subparsers.add_parser("delete", help="Delete a secret")
    secret_delete.add_argument("--api_key", required=True, help="Name of the Secret")
    secret_delete.add_argument(
        "--provider_name", required=True, help="Provider Name of the Secret"
    )
    secret_delete.set_defaults(func=delete_secret)

    # Template CRUD
    template_parser = subparsers.add_parser(
        "template",
        help="Manage templates: configure and manage templates for sensitive data protection.",
    )
    template_subparsers = template_parser.add_subparsers()

    template_create = template_subparsers.add_parser("create", help="Create a template")
    template_create.add_argument(
        "--name", type=str, required=True, help="Name of the template"
    )
    template_create.add_argument(
        "--description", type=str, required=True, help="Description of the template"
    )
    template_create.add_argument(
        "--type", type=str, required=True, help="Type of the template"
    )
    template_create.add_argument(
        "--enabled", type=bool, default=True, help="Whether the template is enabled"
    )
    template_create.add_argument(
        "--models", type=str, required=True, help="JSON string of the models"
    )
    template_create.add_argument(
        "--config", type=str, required=True, help="JSON string of the TemplateConfig"
    )
    template_create.set_defaults(func=create_template)

    template_list = template_subparsers.add_parser("list", help="List templates")
    template_list.set_defaults(func=list_templates)

    template_get = template_subparsers.add_parser("get", help="Read a template")
    template_get.add_argument(
        "--name", type=str, required=True, help="Name of the template to get"
    )
    template_get.set_defaults(func=get_template)

    template_update = template_subparsers.add_parser("update", help="Update a template")
    template_update.add_argument(
        "--name", type=str, required=True, help="Name of the template to update"
    )
    template_update.add_argument(
        "--description", type=str, help="New description of the template"
    )
    template_update.add_argument("--type", type=str, help="New type of the template")
    template_update.add_argument(
        "--enabled", type=bool, help="Whether the template is enabled"
    )
    template_update.add_argument(
        "--models", type=str, help="New JSON string of the models"
    )
    template_update.add_argument(
        "--config", type=str, help="New JSON string of the TemplateConfig"
    )
    template_update.set_defaults(func=update_template)

    template_delete = template_subparsers.add_parser("delete", help="Delete a template")
    template_delete.add_argument(
        "--name", type=str, required=True, help="Name of the template to delete"
    )
    template_delete.set_defaults(func=delete_template)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


def authenticate(args):
    home_dir = Path.home()
    javelin_dir = home_dir / ".javelin"
    cache_file = javelin_dir / "cache.json"
    print(cache_file)
    if cache_file.exists() and not args.force:
        print("✅ User is already authenticated!")
        print("Use --force to re-authenticate and override existing cache.")
        return
    
    default_url = "https://dev.javelin.live/"
    
    print("   O")
    print("  /|\\")
    print("  / \\    ========> Welcome to Javelin! 🚀")
    print("\nBefore you can use Javelin, you need to authenticate.")
    print("Press Enter to open the default login URL in your browser...")
    print(f"Default URL: {default_url}")
    print("Or enter a new URL (leave blank to use the default): ", end="")
    
    new_url = input().strip()
    url_to_open = new_url if new_url else default_url

    server_thread, port = start_local_server()

    redirect_uri = f"http://localhost:{port}"
    encoded_redirect = urllib.parse.quote(redirect_uri)
    
    url_to_open = f"{url_to_open}sign-in?localhost_url={encoded_redirect}&cli=1"

    print(f"\n🚀 Opening {url_to_open} in your browser...")
    webbrowser.open(url_to_open)

    print("\n⚡ Waiting for authentication... (Server is running)")
    
    server_thread.join()

    if cache_file.exists():
        print("✅ Successfully authenticated!")
    else:
        print("⚠️ Failed to retrieve Javelin cache.")


def start_local_server():
    # Find an available port
    port = random.randint(8000, 9000)
    
    class AuthHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            pass
        def end_headers(self):
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            super().end_headers()

        def do_OPTIONS(self):
            self.send_response(200)
            self.end_headers()

        def do_GET(self):
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            
            if 'secrets' in params:
                secrets = params['secrets'][0]
                store_credentials(secrets)
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"Authentication successful. You can close this window.")
                
                # Shutdown the server
                threading.Thread(target=self.server.shutdown).start()
            else:
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"Invalid request. Missing 'secrets' parameter.")

    def run_server():
        with socketserver.TCPServer(("", port), AuthHandler) as httpd:
            print(f"Server started on port {port}")
            httpd.serve_forever()

    server_thread = threading.Thread(target=run_server)
    server_thread.start()
    
    return server_thread, port


def store_credentials(secrets):
    home_dir = Path.home()
    javelin_dir = home_dir / ".javelin"
    javelin_dir.mkdir(exist_ok=True)
    
    cache_file = javelin_dir / "cache.json"
    
    try:
        cache_data = json.loads(secrets)
        with open(cache_file, "w") as f:
            json.dump(cache_data, f, indent=4)
        print("Cache data stored successfully.")
    except json.JSONDecodeError:
        print("Error: Invalid JSON data received.")
    except IOError:
        print("Error: Unable to write cache data to file.")


def get_profile(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes
        return response.json()  # Assuming the response is a JSON object
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch the profile: {e}")
        return None


if __name__ == "__main__":
    main()