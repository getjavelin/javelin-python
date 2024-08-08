from enum import Enum, auto
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import httpx

from javelin_sdk.exceptions import (
    GatewayNotFoundError,
    GatewayAlreadyExistsError,
    RouteNotFoundError,
    RouteAlreadyExistsError,
    ProviderNotFoundError,
    ProviderAlreadyExistsError,
    TemplateNotFoundError,
    TemplateAlreadyExistsError,
    SecretNotFoundError,
    SecretAlreadyExistsError,
    NetworkError,
    BadRequest,
    RateLimitExceededError,
    InternalServerError,
    MethodNotAllowedError,
    UnauthorizedError,
    ValidationError,
)
from javelin_sdk.models import QueryResponse
from javelin_sdk.models import Gateway, Gateways
from javelin_sdk.models import Route, Routes
from javelin_sdk.models import Provider, Providers

API_BASEURL = "https://api-dev.javelin.live"
API_BASE_PATH = "/v1"
API_TIMEOUT = 10


def log_request(request):
    print(f"Request URL: {request.url}")
    print(f"Request Method: {request.method}")
    print(f"Request Headers: {request.headers}")
    if request.content:
        print(f"Request Body: {request.content.decode()}")


def log_response(response):
    # Ensure the response content is read for streaming responses
    if hasattr(response, 'is_stream_consumed') and not response.is_stream_consumed:
        response.read()

    print(f"Response Status Code: {response.status_code}")
    print(f"Response Headers: {response.headers}")
    if response.content:
        print(f"Response Body: {response.content.decode()}")

class HttpMethod(Enum):
    GET = auto()
    POST = auto()
    PUT = auto()
    DELETE = auto()


class JavelinClient:
    def __init__(
        self,
        javelin_api_key: str,
        base_url: str = API_BASEURL,
        javelin_virtualapikey: Optional[str] = None,
        llm_api_key: Optional[str] = None,
    ) -> None:
        """
        Initialize the JavelinClient.

        :param base_url: Base URL for the Javelin API.
        :param api_key: API key for authorization (if required).
        """
        headers = {}
        if not javelin_api_key or javelin_api_key == "":
            raise UnauthorizedError(
                response=None, message=
                "Please provide a valid Javelin API Key. "
                + "When you sign into Javelin, you can find your API Key in the "
                + "Account->Developer settings"
            )

        headers["x-api-key"] = javelin_api_key

        if javelin_virtualapikey:
            headers["x-javelin-virtualapikey"] = javelin_virtualapikey

        if llm_api_key:
            headers["Authorization"] = f"Bearer {llm_api_key}"

        self.base_url = urljoin(base_url, API_BASE_PATH)
        self._headers = headers
        self._client = None
        self._aclient = None

    @property
    def client(self):
        if self._client is None:
            self._client = httpx.Client(
                # base_url=self.base_url, headers=self._headers, timeout=API_TIMEOUT,
                # event_hooks={"request": [log_request], "response": [log_response]},
                base_url=self.base_url,
                headers=self._headers,
                timeout=API_TIMEOUT,
            )
        return self._client

    @property
    def aclient(self):
        if self._aclient is None:
            self._aclient = httpx.AsyncClient(
                base_url=self.base_url, headers=self._headers, timeout=API_TIMEOUT
            )
        return self._aclient

    async def __aenter__(self) -> "JavelinClient":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.aclose()

    def __enter__(self) -> "JavelinClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    async def aclose(self):
        if self._aclient:
            await self._aclient.aclose()

    def close(self):
        if self._client:
            self._client.close()

    def _send_request_sync(
        self,
        method: HttpMethod,
        gateway: Optional[str] = "",
        provider: Optional[str] = "",
        route: Optional[str] = "",
        is_query: bool = False,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """
        Send a request to the Javelin API.

        :param method: HTTP method to use.
        :param gateway: Name of the gateway to send the request to.
        :param provider: Name of the provider to send the request to.
        :param route: Name of the route to send the request to.
        :param is_query: Whether the route is a query route.
        :param data: Data to send with the request.
        :param headers: Additional headers to send with the request.
        :return: Response from the Javelin API.

        :raises ValueError: If an unsupported HTTP method is used.
        :raises NetworkError: If a network error occurs.

        :raises InternalServerError: If the Javelin API returns a 500 error.
        :raises RateLimitExceededError: If the Javelin API returns a 429 error.
        :raises GatewayAlreadyExistsError: If the Javelin API returns a 409 error.
        :raises GatewayNotFoundError: If the Javelin API returns a 404 error.
        :raises ProviderAlreadyExistsError: If the Javelin API returns a 409 error.
        :raises ProviderNotFoundError: If the Javelin API returns a 404 error.
        :raises RouteAlreadyExistsError: If the Javelin API returns a 409 error.
        :raises RouteNotFoundError: If the Javelin API returns a 404 error.
        :raises UnauthorizedError: If the Javelin API returns a 401 error.

        """
        url = self._construct_url(gateway_name=gateway, 
                                  provider_name=provider,
                                  route_name=route, 
                                  query=is_query)
        client = self.client

        # Merging additional headers with default headers
        request_headers = {**self._headers, **(headers or {})}
        if is_query and route:
            request_headers["x-javelin-route"] = route

        try:
            if method == HttpMethod.GET:
                response = client.get(url, headers=request_headers)
            elif method == HttpMethod.POST:
                response = client.post(url, json=data, headers=request_headers)
            elif method == HttpMethod.PUT:
                response = client.put(url, json=data, headers=request_headers)
            elif method == HttpMethod.DELETE:
                response = client.delete(url, headers=request_headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            return response
        except httpx.NetworkError as e:
            raise NetworkError(message=str(e))

    async def _send_request_async(
        self,
        method: HttpMethod,
        gateway: Optional[str] = "",
        provider: Optional[str] = "",
        route: Optional[str] = "",
        is_query: bool = False,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """
        Send a request asynchronously to the Javelin API.

        :param method: HTTP method to use.
        
        :param gateway: Name of the gateway to send the request to.
        :param provider: Name of the provider to send the request to.
        :param route: Name of the route to send the request to.
        :param is_query: Whether the route is a query route.
        :param data: Data to send with the request.
        :param headers: Additional headers to send with the request.
        :return: Response from the Javelin API.

        :raises ValueError: If an unsupported HTTP method is used.
        :raises NetworkError: If a network error occurs.

        :raises InternalServerError: If the Javelin API returns a 500 error.
        :raises RateLimitExceededError: If the Javelin API returns a 429 error.
        :raises RouteAlreadyExistsError: If the Javelin API returns a 409 error.
        :raises GatewayAlreadyExistsError: If the Javelin API returns a 409 error.
        :raises GatewayNotFoundError: If the Javelin API returns a 404 error.
        :raises ProviderAlreadyExistsError: If the Javelin API returns a 409 error.
        :raises ProviderNotFoundError: If the Javelin API returns a 404 error.
        :raises RouteNotFoundError: If the Javelin API returns a 404 error.
        :raises UnauthorizedError: If the Javelin API returns a 401 error.

        """
        url = self._construct_url(gateway_name=gateway,
                                  provider_name=provider,
                                  route_name=route, 
                                  query=is_query)
        aclient = self.aclient

        # Merging additional headers with default headers
        request_headers = {**self._headers, **(headers or {})}
        if is_query and route:
            request_headers["x-javelin-route"] = route

        try:
            if method == HttpMethod.GET:
                response = await aclient.get(url, headers=request_headers)
            elif method == HttpMethod.POST:
                response = await aclient.post(url, json=data, headers=request_headers)
            elif method == HttpMethod.PUT:
                response = await aclient.put(url, json=data, headers=request_headers)
            elif method == HttpMethod.DELETE:
                response = await aclient.delete(url, headers=request_headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            return response
        except httpx.NetworkError as e:
            raise NetworkError(message=str(e))

    def _process_gateway_response_ok(self, response: httpx.Response) -> str:
        """
        Process a successful response from the Javelin API.
        """
        self._handle_gateway_response(response)
        return response.text

    def _process_provider_response_ok(self, response: httpx.Response) -> str:
        """
        Process a successful response from the Javelin API.
        """
        self._handle_provider_response(response)
        return response.text

    def _process_route_response_ok(self, response: httpx.Response) -> str:
        """
        Process a successful response from the Javelin API.
        """
        self._handle_route_response(response)
        return response.text

    def _process_gateway_response_json(self, response: httpx.Response) -> QueryResponse:
        """
        Process a successful response from the Javelin API.
        Parse body into a QueryResponse object and return it.
        This is for Query() requests.
        """
        self._handle_gateway_response(response)
        return QueryResponse(**response.json())

    def _process_provider_response_json(self, response: httpx.Response) -> QueryResponse:
        """
        Process a successful response from the Javelin API.
        Parse body into a QueryResponse object and return it.
        This is for Query() requests.
        """
        self._handle_provider_response(response)
        return QueryResponse(**response.json())

    def _process_route_response_json(self, response: httpx.Response) -> QueryResponse:
        """
        Process a successful response from the Javelin API.
        Parse body into a QueryResponse object and return it.
        This is for Query() requests.
        """
        self._handle_route_response(response)
        return QueryResponse(**response.json())

    def _handle_gateway_response(self, response: httpx.Response) -> None:
        """
        Handle the API response by raising appropriate exceptions based on the
        response status code.

        :param response: The API response to handle.
        """
        if response.status_code == 400:
            raise BadRequest(response=response)
        elif response.status_code == 409:
            raise GatewayAlreadyExistsError(response=response)
        elif response.status_code == 401:
            raise UnauthorizedError(response=response)
        elif response.status_code == 403:
            raise UnauthorizedError(response=response)
        elif response.status_code == 404:
            raise GatewayNotFoundError(response=response)
        elif response.status_code == 409:
            raise GatewayAlreadyExistsError(response=response)
        elif response.status_code == 429:
            raise RateLimitExceededError(response=response)
        elif response.status_code != 200:
            raise InternalServerError(response=response)

    def _handle_provider_response(self, response: httpx.Response) -> None:
        """
        Handle the API response by raising appropriate exceptions based on the
        response status code.

        :param response: The API response to handle.
        """
        if response.status_code == 400:
            raise BadRequest(response=response)
        elif response.status_code == 409:
            raise ProviderAlreadyExistsError(response=response)
        elif response.status_code == 401:
            raise UnauthorizedError(response=response)
        elif response.status_code == 403:
            raise UnauthorizedError(response=response)
        elif response.status_code == 404:
            raise ProviderNotFoundError(response=response)
        elif response.status_code == 409:
            raise ProviderAlreadyExistsError(response=response)
        elif response.status_code == 429:
            raise RateLimitExceededError(response=response)
        elif response.status_code != 200:
            raise InternalServerError(response=response)

    def _handle_route_response(self, response: httpx.Response) -> None:
        """
        Handle the API response by raising appropriate exceptions based on the
        response status code.

        :param response: The API response to handle.
        """
        if response.status_code == 400:
            raise BadRequest(response=response)
        elif response.status_code == 409:
            raise RouteAlreadyExistsError(response=response)
        elif response.status_code == 401:
            raise UnauthorizedError(response=response)
        elif response.status_code == 403:
            raise UnauthorizedError(response=response)
        elif response.status_code == 404:
            raise RouteNotFoundError(response=response)
        elif response.status_code == 409:
            raise RouteAlreadyExistsError(response=response)
        elif response.status_code == 429:
            raise RateLimitExceededError(response=response)
        elif response.status_code != 200:
            raise InternalServerError(response=response)

    def _construct_url(
        self, 
        gateway_name: Optional[str] = "", 
        provider_name: Optional[str] = "", 
        route_name: Optional[str] = "", 
        query: bool = False
    ) -> str:
        """
        Construct the complete URL for a given route name and action.

        :param route_name: Name of the route.
        :param query: If True, add "query" to the end of the URL.
        :return: Constructed URL.
        """
        url_parts = [self.base_url]
        if query:
            url_parts.append("query")
            if route_name is not None:  # Check if route_name is not None
                url_parts.append(route_name)
        elif gateway_name:
            url_parts.append("admin")
            url_parts.append("gateways")
            if gateway_name != "###":
                url_parts.append(gateway_name)
        elif provider_name:
            url_parts.append("admin")
            url_parts.append("providers")
            if provider_name != "###":
                url_parts.append(provider_name)
        elif route_name:
            url_parts.append("admin")
            url_parts.append("routes")
            if route_name != "###":
                url_parts.append(route_name)
        else:
            url_parts.append("admin")
            url_parts.append("routes")
        return "/".join(url_parts)

    def get_route(self, route_name: str) -> Route:
        """
        Retrieve details of a specific route.

        :param route_name: Name of the route to retrieve.
        :return: Response object containing route details.
        """
        self._validate_route_name(route_name)
        response = self._send_request_sync(HttpMethod.GET, route=route_name)
        return self._process_response_route(response)

    async def aget_route(self, route_name: str) -> Route:
        """
        Asynchronously retrieve details of a specific route.

        :param route_name: Name of the route to retrieve.
        :return: Response object containing route details.
        """
        self._validate_route_name(route_name)
        response = await self._send_request_async(HttpMethod.GET, route=route_name)
        return self._process_response_route(response)

    def _process_response_route(self, response: httpx.Response) -> Route:
        """
        Process a successful response from the Javelin API.
        Parse body into a Route object and return it.
        This is for Get() requests.
        """
        self._handle_route_response(response)
        return Route(**response.json())

    # create a route
    def create_route(self, route: Route) -> str:
        """
        Create a new route.

        :param route: Route object containing route details.
        :return: Response text indicating the success status (e.g., "OK").
        """
        self._validate_route_name(route.name)
        response = self._send_request_sync(
            HttpMethod.POST, route=route.name, data=route.dict()
        )
        return self._process_route_response_ok(response)

    # async create a route
    async def acreate_route(self, route: Route) -> str:
        """
        Asynchronously create a new route.

        :param route: Route object containing route details.
        :return: Response text indicating the success status (e.g., "OK").
        """
        self._validate_route_name(route.name)
        response = await self._send_request_async(
            HttpMethod.POST, route=route.name, data=route.dict()
        )
        return self._process_route_response_ok(response)

    # update a route
    def update_route(self, route: Route) -> str:
        """
        Update an existing route.

        :param route_name: Name of the route to update.
        :param route: Route object containing updated route details.
        :return: Response text indicating the success status (e.g., "OK").
        """
        self._validate_route_name(route.name)
        response = self._send_request_sync(
            HttpMethod.PUT, route=route.name, data=route.dict()
        )
        return self._process_route_response_ok(response)

    # async update a route
    async def aupdate_route(self, route: Route) -> str:
        """
        Asynchronously update an existing route.

        :param route_name: Name of the route to update.
        :param route: Route object containing updated route details.
        :return: Response text indicating the success status (e.g., "OK").
        """
        self._validate_route_name(route.name)
        response = await self._send_request_async(
            HttpMethod.PUT, route=route.name, data=route.dict()
        )
        return self._process_route_response_ok(response)

    # list routes
    def list_routes(self) -> Routes:
        """
        Retrieve a list of all routes.

        :return: Routes object containing a list of all routes.
        """
        response = self._send_request_sync(HttpMethod.GET, gateway="", provider="", route="###")
        return Routes(routes=response.json())

    # async list routes
    async def alist_routes(self) -> Routes:
        """
        Asynchronously retrieve a list of all routes.

        :return: Routes object containing a list of all routes.
        """
        response = await self._send_request_async(HttpMethod.GET, gateway="", provider="", route="###")
        return Routes(routes=response.json())

    # query an LLM through a route
    def query_route(
        self,
        route_name: str,
        query_body: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
    ) -> QueryResponse:
        """
        Query an LLM through a specific route.

        :param route_name: Name of the route to query.
        :param query_body: QueryBody object containing the query details.
        :param headers: Additional headers to send with the request.
        :return: Response object containing query results.
        """
        self._validate_route_name(route_name)
        response = self._send_request_sync(
            HttpMethod.POST, route=route_name, is_query=True, data=query_body, headers=headers
        )
        return self._process_route_response_json(response)

    # async query an LLM through a route
    async def aquery_route(
        self,
        route_name: str,
        query_body: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
    ) -> QueryResponse:
        """
        Asynchronously query an LLM through a specific route.

        :param route_name: Name of the route to query.
        :param query_body: QueryBody object containing the query details.
        :param headers: Additional headers to send with the request.
        :return: Response object containing query results.
        """
        self._validate_route_name(route_name)
        response = await self._send_request_async(
            HttpMethod.POST, route=route_name, is_query=True, data=query_body, headers=headers
        )
        return self._process_route_response_json(response)

    # delete a route
    def delete_route(self, route_name: str) -> str:
        """
        Delete a specific route.

        :param route_name: Name of the route to delete.
        :return: Response text indicating the success status (e.g., "OK").
        """
        self._validate_route_name(route_name)
        response = self._send_request_sync(HttpMethod.DELETE, route=route_name)
        return self._process_route_response_ok(response)

    # async delete a route
    async def adelete_route(self, route_name: str) -> str:
        """
        Asynchronously delete a specific route.

        :param route_name: Name of the route to delete.
        :return: Response text indicating the success status (e.g., "OK").
        """
        self._validate_route_name(route_name)
        response = await self._send_request_async(HttpMethod.DELETE, route=route_name)
        return self._process_route_response_ok(response)

    @staticmethod
    def _validate_route_name(route_name: str):
        """
        Validate the route name. Raises a ValueError if the route name is empty.

        :param route_name: Name of the route to validate.
        """
        if not route_name:
            raise ValueError("Route name cannot be empty.")

    @staticmethod
    def _validate_body(body: Optional[Dict[str, Any]]):
        """
        Validate the request body. Raises a ValueError if the body is empty.

        :param body: Request body to validate.
        """
        if not body:
            raise ValueError("Body cannot be empty.")

    def get_gateway(self, gateway_name: str) -> Gateway:
        """
        Retrieve details of a specific gateway.

        :param gateway_name: Name of the gateway to retrieve.
        :return: Response object containing gateway details.
        """
        self._validate_gateway_name(gateway_name)
        response = self._send_request_sync(HttpMethod.GET, gateway=gateway_name)
        return self._process_gateway_response_gateway(response)

    async def aget_gateway(self, gateway_name: str) -> Gateway:
        """
        Asynchronously retrieve details of a specific gateway.

        :param gateway_name: Name of the gateway to retrieve.
        :return: Response object containing gateway details.
        """
        self._validate_gateway_name(gateway_name)
        response = await self._send_request_async(HttpMethod.GET, gateway=gateway_name)
        return self._process_gateway_response_gateway(response)

    def _process_response_gateway(self, response: httpx.Response) -> Gateway:
        """
        Process a successful response from the Javelin API.
        Parse body into a Gateway object and return it.
        This is for Get() requests.
        """
        self._handle_gateway_response(response)
        return Gateway(**response.json())

    # create a gateway
    def create_gateway(self, gateway: Gateway) -> str:
        """
        Create a new gateway.

        :param gateway: Gateway object containing gateway details.
        :return: Response text indicating the success status (e.g., "OK").
        """
        self._validate_gateway_name(gateway.name)
        response = self._send_request_sync(
            HttpMethod.POST, gateway=gateway.name, data=gateway.dict()
        )
        return self._process_gateway_response_ok(response)

    # async create a gateway
    async def acreate_gateway(self, gateway: Gateway) -> str:
        """
        Asynchronously create a new gateway.

        :param gateway: Gateway object containing gateway details.
        :return: Response text indicating the success status (e.g., "OK").
        """
        self._validate_gateway_name(gateway.name)
        response = await self._send_request_async(
            HttpMethod.POST, gateway=gateway.name, data=gateway.dict()
        )
        return self._process_gateway_response_ok(response)

    # update a gateway
    def update_gateway(self, gateway: Gateway) -> str:
        """
        Update an existing gateway.

        :param gateway_name: Name of the gateway to update.
        :param gateway: Gateway object containing updated gateway details.
        :return: Response text indicating the success status (e.g., "OK").
        """
        self._validate_gateway_name(gateway.name)
        response = self._send_request_sync(
            HttpMethod.PUT, gateway=gateway.name, data=gateway.dict()
        )
        return self._process_gateway_response_ok(response)

    # async update a gateway
    async def update_gateway(self, gateway: Gateway) -> str:
        """
        Asynchronously update an existing gateway.

        :param gateway_name: Name of the gateway to update.
        :param gateway: Gateway object containing updated gateway details.
        :return: Response text indicating the success status (e.g., "OK").
        """
        self._validate_gateway_name(gateway.name)
        response = await self._send_request_async(
            HttpMethod.PUT, gateway=gateway.name, data=gateway.dict()
        )
        return self._process_gateway_response_ok(response)

    # list gateways
    def list_gateways(self) -> Gateways:
        """
        Retrieve a list of all gateways.

        :return: Gateways object containing a list of all gateways.
        """
        response = self._send_request_sync(HttpMethod.GET, gateway="###", provider="", route="")
        return Gateways(gateways=response.json())

    # async list gateways
    async def alist_gateways(self) -> Gateways:
        """
        Asynchronously retrieve a list of all gateways.

        :return: Gateways object containing a list of all gateways.
        """
        response = await self._send_request_async(HttpMethod.GET, gateway="###", provider="", route="")
        return Gateways(gateways=response.json())

    # delete a gateway
    def delete_gateway(self, gateway_name: str) -> str:
        """
        Delete a specific gateway.

        :param gateway_name: Name of the gateway to delete.
        :return: Response text indicating the success status (e.g., "OK").
        """
        self._validate_gateway_name(gateway_name)
        response = self._send_request_sync(HttpMethod.DELETE, gateway=gateway_name)
        return self._process_gateway_response_ok(response)

    # async delete a gateway
    async def adelete_gateway(self, gateway_name: str) -> str:
        """
        Asynchronously delete a specific gateway.

        :param gateway_name: Name of the provider to delete.
        :return: Response text indicating the success status (e.g., "OK").
        """
        self._validate_gateway_name(gateway_name)
        response = await self._send_request_async(HttpMethod.DELETE, gateway=gateway_name)
        return self._process_gateway_response_ok(response)

    @staticmethod
    def _validate_gateway_name(gateway_name: str):
        """
        Validate the gateway name. Raises a ValueError if the gateway name is empty.

        :param gateway_name: Name of the gateway to validate.
        """
        if not gateway_name:
            raise ValueError("Gateway name cannot be empty.")
        
    def get_provider(self, provider_name: str) -> Provider:
        """
        Retrieve details of a specific provider.

        :param provider_name: Name of the provider to retrieve.
        :return: Response object containing provider details.
        """
        self._validate_provider_name(provider_name)
        response = self._send_request_sync(HttpMethod.GET, provider=provider_name)
        return self._process_provider_response_provider(response)

    async def aget_provider(self, provider_name: str) -> Provider:
        """
        Asynchronously retrieve details of a specific provider.

        :param provider_name: Name of the provider to retrieve.
        :return: Response object containing provider details.
        """
        self._validate_provider_name(provider_name)
        response = await self._send_request_async(HttpMethod.GET, provider=provider_name)
        return self._process_response_provider(response)

    def _process_response_provider(self, response: httpx.Response) -> Provider:
        """
        Process a successful response from the Javelin API.
        Parse body into a Provider object and return it.
        This is for Get() requests.
        """
        self._handle_provider_response(response)
        return Provider(**response.json())

    # create a provider
    def create_provider(self, provider: Provider) -> str:
        """
        Create a new provider.

        :param provider: Provider object containing provider details.
        :return: Response text indicating the success status (e.g., "OK").
        """
        self._validate_provider_name(provider.name)
        response = self._send_request_sync(
            HttpMethod.POST, provider=provider.name, data=provider.dict()
        )
        return self._process_provider_response_ok(response)

    # async create a provider
    async def acreate_provider(self, provider: Provider) -> str:
        """
        Asynchronously create a new provider.

        :param provider: Provider object containing provider details.
        :return: Response text indicating the success status (e.g., "OK").
        """
        self._validate_provider_name(provider.name)
        response = await self._send_request_async(
            HttpMethod.POST, provider=provider.name, data=provider.dict()
        )
        return self._process_provider_response_ok(response)

    # update a provider
    def update_provider(self, provider: Provider) -> str:
        """
        Update an existing provider.

        :param provider_name: Name of the provider to update.
        :param provider: Provider object containing updated provider details.
        :return: Response text indicating the success status (e.g., "OK").
        """
        self._validate_provider_name(provider.name)
        response = self._send_request_sync(
            HttpMethod.PUT, provider=provider.name, data=provider.dict()
        )
        return self._process_provider_response_ok(response)

    # async update a provider
    async def update_provider(self, provider: Provider) -> str:
        """
        Asynchronously update an existing provider.

        :param provider_name: Name of the provider to update.
        :param provider: Provider object containing updated provider details.
        :return: Response text indicating the success status (e.g., "OK").
        """
        self._validate_provider_name(provider.name)
        response = await self._send_request_async(
            HttpMethod.PUT, provider=provider.name, data=provider.dict()
        )
        return self._process_provider_response_ok(response)

    # list providers
    def list_providers(self) -> Providers:
        """
        Retrieve a list of all providers.

        :return: Providers object containing a list of all providers.
        """
        response = self._send_request_sync(HttpMethod.GET, gateway="", provider="###", route="")
        return Providers(providers=response.json())

    # async list providers
    async def alist_providers(self) -> Providers:
        """
        Asynchronously retrieve a list of all providers.

        :return: Providers object containing a list of all providers.
        """
        response = await self._send_request_async(HttpMethod.GET, gateway="", provider="###", route="")
        return Providers(providers=response.json())

    # delete a provider
    def delete_provider(self, provider_name: str) -> str:
        """
        Delete a specific provider.

        :param provider_name: Name of the provider to delete.
        :return: Response text indicating the success status (e.g., "OK").
        """
        self._validate_provider_name(provider_name)
        response = self._send_request_sync(HttpMethod.DELETE, provider=provider_name)
        return self._process_provider_response_ok(response)

    # async delete a provider
    async def adelete_provider(self, provider_name: str) -> str:
        """
        Asynchronously delete a specific provider.

        :param provider_name: Name of the provider to delete.
        :return: Response text indicating the success status (e.g., "OK").
        """
        self._validate_provider_name(provider_name)
        response = await self._send_request_async(HttpMethod.DELETE, provider=provider_name)
        return self._process_provider_response_ok(response)

    @staticmethod
    def _validate_provider_name(provider_name: str):
        """
        Validate the provider name. Raises a ValueError if the provider name is empty.

        :param provider_name: Name of the provider to validate.
        """
        if not provider_name:
            raise ValueError("Provider name cannot be empty.")
        

