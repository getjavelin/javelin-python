from typing import Dict, Optional, Any
import httpx
from urllib.parse import urljoin

from javelin.models import Route, Routes, QueryBody, Response
from javelin.exceptions import (NetworkError, RouteNotFoundError, RouteAlreadyExistsError, UnauthorizedError,
                                InternalServerError, RateLimitExceededError, ValidationError)

API_BASE_PATH = "/api/v1"
API_TIMEOUT = 10

class JavelinClient:

    def __init__(self, base_url: str, api_key: Optional[str] = None) -> None:
        """
        Initialize the JavelinClient.

        :param base_url: Base URL for the Javelin API.
        :param api_key: API key for authorization (if required).
        """
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        self.base_url = urljoin(base_url, API_BASE_PATH)
        self._headers = headers
        self._client = None
        self._aclient = None

    @property
    def client(self):
        if self._client is None:
            self._client = httpx.Client(base_url=self.base_url, headers=self._headers, timeout=API_TIMEOUT)
        return self._client

    @property
    def aclient(self):
        if self._aclient is None:
            self._aclient = httpx.AsyncClient(base_url=self.base_url, headers=self._headers, timeout=API_TIMEOUT)
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

    def _handle_response(self, response: httpx.Response) -> None:
        """
        Handle the API response by raising appropriate exceptions based on the response status code.

        :param response: The API response to handle.
        """
        if response.status_code == 400:
            raise RouteAlreadyExistsError(response)
        elif response.status_code == 401:
            raise UnauthorizedError(response)
        elif response.status_code == 404:
            raise RouteNotFoundError(response)
        elif response.status_code == 429:
            raise RateLimitExceededError(response)
        elif response.status_code != 200:
            raise InternalServerError(response)
    
    def _construct_url(self, route_name: Optional[str] = "", query: bool = False) -> str:
        """
        Construct the complete URL for a given route name and action.

        :param route_name: Name of the route.
        :param query: If True, add "query" to the end of the URL.
        :return: Constructed URL.
        """
        url_parts = [self.base_url]
        if route_name:
            url_parts.append(route_name)
        if query:
            url_parts.append("query")
        return "/".join(url_parts)


    def get_route(self, route_name: str) -> Response:
        """
        Retrieve details of a specific route.

        :param route_name: Name of the route to retrieve.
        :return: Response object containing route details.
        """
        self._validate_route_name(route_name)
        url = self._construct_url(route_name)

        try:
            response = self.client.get(url)
            self._handle_response(response)
            return Response(**response.json())
        except httpx.NetworkError as e:
            raise NetworkError(str(e))

    async def aget_route(self, route_name: str) -> Response:
        """
        Asynchronously retrieve details of a specific route.

        :param route_name: Name of the route to retrieve.
        :return: Response object containing route details.
        """
        self._validate_route_name(route_name)
        url = self._construct_url(route_name)

        try:
            response = await self.aclient.get(url)
            self._handle_response(response)
            return Response(**response.json())
        except httpx.NetworkError as e:
            raise NetworkError(str(e))
        
    # create a route
    def create_route(self, route: Route) -> str:
        """
        Create a new route.

        :param route: Route object containing route details.
        :return: Response text indicating the success status (e.g., "OK").
        """
        self._validate_route_name(route.name)
        url = self._construct_url(route.name)

        try:    
            response = self.client.post(url, json=route.json())
        except httpx.NetworkError as e:
            raise NetworkError(str(e))

        self._handle_response(response)
        return response.text
    
    # async create a route
    async def acreate_route(self, route: Route) -> str:
        """
        Asynchronously create a new route.

        :param route: Route object containing route details.
        :return: Response text indicating the success status (e.g., "OK").
        """
        self._validate_route_name(route.name)
        url = self._construct_url(route.name)

        try:    
            response = await self.aclient.post(url, json=route.json())
        except httpx.NetworkError as e:
            raise NetworkError(str(e))

        self._handle_response(response)
        return response.text

    # update a route
    def update_route(self, route_name: str, route: Route) -> str:
        """
        Update an existing route.

        :param route_name: Name of the route to update.
        :param route: Route object containing updated route details.
        :return: Response text indicating the success status (e.g., "OK").
        """    
        self._validate_route_name(route_name)
        url = self._construct_url(route_name)

        try:
            response = self.client.put(url, json=route.json())
        except httpx.NetworkError as e:
            raise NetworkError(str(e))

        self._handle_response(response)
        return response.text
    
    # async update a route
    async def aupdate_route(self, route_name: str, route: Route) -> str:
        """
        Asynchronously update an existing route.

        :param route_name: Name of the route to update.
        :param route: Route object containing updated route details.
        :return: Response text indicating the success status (e.g., "OK").
        """
        self._validate_route_name(route_name)
        url = self._construct_url(route_name)

        try:
            response = await self.aclient.put(url, json=route.json())
        except httpx.NetworkError as e:
            raise NetworkError(str(e))

        self._handle_response(response)
        return response.text

    # list routes
    def list_routes(self) -> Routes:
        """
        Retrieve a list of all routes.

        :return: Routes object containing a list of all routes.
        """
        url = f"{self.base_url}/"

        try:
            response = self.client.get(url)
        except httpx.NetworkError as e:
            raise NetworkError(str(e))
        
        self._handle_response(response)
        try:
                return Routes(**response.json())
        except ValidationError as e:
            raise ValueError(f"Unable to parse response into Routes object: {str(e)}")
    
    # async list routes
    async def alist_routes(self) -> Routes:
        """
        Asynchronously retrieve a list of all routes.

        :return: Routes object containing a list of all routes.
        """
        url = f"{self.base_url}/"

        try:
            response = await self.aclient.get(url)
        except httpx.NetworkError as e:
            raise NetworkError(str(e))
        
        self._handle_response(response)

        try:
                return Routes(**response.json())
        except ValidationError as e:
            raise ValueError(f"Unable to parse response into Routes object: {str(e)}")

    # query an LLM through a route
    def query_route(self, route_name: str, query_body: QueryBody) -> Response:
        """
        Query an LLM through a specific route.

        :param route_name: Name of the route to query.
        :param query_body: QueryBody object containing the query details.
        :return: Response object containing query results.
        """
        self._validate_route_name(route_name)
        url = self._construct_url(route_name, query=True)

        try:
            response = self.client.post(url, json=query_body.json())
        except httpx.NetworkError as e:
            raise NetworkError(str(e))

        self._handle_response(response)
        response_data = response.json()
        return Response(**response_data)

    
    # async query an LLM through a route
    async def aquery_route(self, route_name: str, query_body: QueryBody) -> Response:
        """
        Asynchronously query an LLM through a specific route.

        :param route_name: Name of the route to query.
        :param query_body: QueryBody object containing the query details.
        :return: Response object containing query results.
        """
        self._validate_route_name(route_name)
        url = self._construct_url(route_name, query=True)
        
        try:
            response = await self.aclient.post(url,json=query_body.json())
        except httpx.NetworkError as e:
            raise NetworkError(str(e))
        
        self._handle_response(response)
        response_data = response.json()
        return Response(**response_data)

    # delete a route
    def delete_route(self, route_name: str) -> str:
        """
        Delete a specific route.

        :param route_name: Name of the route to delete.
        :return: Response text indicating the success status (e.g., "OK").
        """
        self._validate_route_name(route_name)
        url = self._construct_url(route_name)

        try:
            response = self.client.delete(url)
        except httpx.NetworkError as e:
            raise NetworkError(str(e))

        self._handle_response(response)
        return response.text
    
    # async delete a route
    async def adelete_route(self, route_name: str) -> str:
        """
        Asynchronously delete a specific route.

        :param route_name: Name of the route to delete.
        :return: Response text indicating the success status (e.g., "OK").
        """
        self._validate_route_name(route_name)
        url = self._construct_url(route_name)

        try:
            response = await self.aclient.delete(url)
        except httpx.NetworkError as e:
            raise NetworkError(str(e))

        self._handle_response(response)
        return response.text


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