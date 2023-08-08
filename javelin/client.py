from __future__ import annotations

from types import TracebackType
from typing import Any, Dict, Optional, Type
from urllib.parse import urljoin

import httpx
from urllib.parse import urljoin

from javelin.models import Route, Routes, QueryBody
from javelin.exceptions import ConnectionError, RouteNotFoundError, RouteAlreadyExistsError, UnauthorizedError, InternalServerError, RateLimitExceededError

API_BASE_PATH = "/api/v1"
API_TIMEOUT = 10

class JavelinClient:

    base_url: str
    aclient: httpx.AsyncClient
    client: httpx.Client

    # __init__
    def __init__(self, base_url: str, api_key: Optional[str] = None) -> None:
        headers: Dict[str, str] = {}
        if api_key is not None:
            headers["Authorization"] = f"Bearer {api_key}"

        self.base_url = urljoin(base_url, API_BASE_PATH)

        self.client: httpx.Client = httpx.Client(
            base_url=self.base_url, timeout=API_TIMEOUT
        )
        
        self.aclient: httpx.AsyncClient = httpx.AsyncClient(
            base_url=self.base_url, headers=headers, timeout=API_TIMEOUT
        )

    # __aenter__
    async def __aenter__(self) -> "JavelinClient":
        """Asynchronous context manager entry point"""
        return self

    # __aexit__
    async def __aexit__(
        self,
        exc_type: Type[Exception],
        exc_val: Exception,
        exc_tb: TracebackType,
    ) -> None:
        """Asynchronous context manager exit point"""
        await self.aclose()

    # aclose
    def __enter__(self) -> "JavelinClient":
        """Sync context manager entry point"""
        return self

    # aclose
    def __exit__(
        self,
        exc_type: Type[Exception],
        exc_val: Exception,
        exc_tb: TracebackType,
    ) -> None:
        """Sync context manager exit point"""
        self.close()

    # handle errors
    def handle_response(self, response: httpx.Response, missing_message: Optional[str] = None) -> None:
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

    # get a route by name
    def get_route(self, route_name: str) -> Dict[str, Any]:
        if (route_name is None or route_name == ""):
            raise ValueError("route name cannot be empty")
        
        url = f"{self.base_url}/{route_name}"
        
        try:
            response = self.client.get(url)
        except httpx.NetworkError as e:
            raise ConnectionError(str(e))

        self.handle_errors(response)
        return response.json()

    # create a route
    def create_route(self, route: Route) -> None:
        if (route is None or route.name is None or route.name == ""):
            raise ValueError("route name cannot be empty")
        
        url = f"{self.base_url}/{route.name}"

        try:    
            response = self.client.post(url, json=route.json())
        except httpx.NetworkError as e:
            raise ConnectionError(str(e))

        self.handle_response(response)
        return response.text

    # update a route
    def update_route(self, route_name: str, route: Route) -> None:
        if (route_name is None or route_name == ""):
            raise ValueError("route name cannot be empty")

        url = f"{self.base_url}/{route_name}"

        try:
            response = self.client.put(url, json=route.json())
        except httpx.NetworkError as e:
            raise ConnectionError(str(e))

        self.handle_response(response)
        return response.text

    # list routes
    def list_routes(self) -> Routes:

        url = f"{self.base_url}/"

        try:
            response = self.client.get(url)
        except httpx.NetworkError as e:
            raise ConnectionError(str(e))
        
        self.handle_response(response)
        return response.json()

    # query an LLM through a route
    def query_route(self, route_name: str, query_body: QueryBody) -> Dict[str, Any]:
        if (route_name is None or route_name == ""):
            raise ValueError("route name cannot be empty")
        
        if (query_body is None):
            raise ValueError("query body cannot be empty")
        
        url = f"{self.base_url}/{route_name}/query"

        try:
            response = self.client.post(url,json=query_body.json())
        except httpx.NetworkError as e:
            raise ConnectionError(str(e))
        
        self.handle_response(response)
        return response.json()

    # delete a route
    def delete_route(self, route_name: str) -> None:
        if (route_name is None or route_name == ""):
            raise ValueError("route name cannot be empty")
        
        url = f"{self.base_url}/{route_name}"

        try:
            response = self.client.delete(url)
        except httpx.NetworkError as e:
            raise ConnectionError(str(e))

        self.handle_response(response)
        return response.text
