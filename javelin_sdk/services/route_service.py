from typing import Any, Dict, List, Optional

import httpx

from javelin_sdk.exceptions import (
    BadRequest,
    InternalServerError,
    RateLimitExceededError,
    RouteAlreadyExistsError,
    RouteNotFoundError,
    UnauthorizedError,
)
from javelin_sdk.models import HttpMethod, QueryResponse, Request, Route, Routes


class RouteService:
    def __init__(self, client):
        self.client = client

    def _process_route_response_ok(self, response: httpx.Response) -> str:
        """Process a successful response from the Javelin API."""
        self._handle_route_response(response)
        return response.text

    def _process_route_response(self, response: httpx.Response) -> Route:
        """Process a response from the Javelin API and return a Route object."""
        self._handle_route_response(response)
        return Route(**response.json())

    def _handle_route_response(self, response: httpx.Response) -> None:
        """Handle the API response by raising appropriate exceptions."""
        if response.status_code == 400:
            raise BadRequest(response=response)
        elif response.status_code == 409:
            raise RouteAlreadyExistsError(response=response)
        elif response.status_code in (401, 403):
            raise UnauthorizedError(response=response)
        elif response.status_code == 404:
            raise RouteNotFoundError(response=response)
        elif response.status_code == 429:
            raise RateLimitExceededError(response=response)
        elif response.status_code != 200:
            raise InternalServerError(response=response)

    def create_route(self, route: Route) -> str:
        response = self.client._send_request_sync(
            Request(method=HttpMethod.POST, route=route.name, data=route.dict())
        )
        return self._process_route_response_ok(response)

    async def acreate_route(self, route: Route) -> str:
        response = await self.client._send_request_async(
            Request(method=HttpMethod.POST, route=route.name, data=route.dict())
        )
        return self._process_route_response_ok(response)

    def get_route(self, route_name: str) -> Route:
        response = self.client._send_request_sync(
            Request(method=HttpMethod.GET, route=route_name)
        )
        return self._process_route_response(response)

    async def aget_route(self, route_name: str) -> Route:
        response = await self.client._send_request_async(
            Request(method=HttpMethod.GET, route=route_name)
        )
        return self._process_route_response(response)

    def list_routes(self) -> List[Route]:
        response = self.client._send_request_sync(
            Request(method=HttpMethod.GET, route="###")
        )
        try:
            response_json = response.json()
            if "error" in response_json:
                return Routes(routes=[])
            else:
                return Routes(routes=response_json)
        except ValueError:
            return Routes(routes=[])

    async def alist_routes(self) -> List[Route]:
        response = await self.client._send_request_async(
            Request(method=HttpMethod.GET, route="###")
        )
        try:
            response_json = response.json()
            if "error" in response_json:
                return Routes(routes=[])
            else:
                return Routes(routes=response_json)
        except ValueError:
            return Routes(routes=[])

    def update_route(self, route: Route) -> str:
        response = self.client._send_request_sync(
            Request(method=HttpMethod.PUT, route=route.name, data=route.dict())
        )
        return self._process_route_response_ok(response)

    async def aupdate_route(self, route: Route) -> str:
        response = await self.client._send_request_async(
            Request(method=HttpMethod.PUT, route=route.name, data=route.dict())
        )
        return self._process_route_response_ok(response)

    def delete_route(self, route_name: str) -> str:
        response = self.client._send_request_sync(
            Request(method=HttpMethod.DELETE, route=route_name)
        )
        return self._process_route_response_ok(response)

    async def adelete_route(self, route_name: str) -> str:
        response = await self.client._send_request_async(
            Request(method=HttpMethod.DELETE, route=route_name)
        )
        return self._process_route_response_ok(response)

    def query_route(
        self,
        route_name: str,
        query_body: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
    ) -> QueryResponse:
        response = self.client._send_request_sync(
            Request(
                method=HttpMethod.POST,
                route=route_name,
                is_query=True,
                data=query_body,
                headers=headers,
            )
        )
        return QueryResponse(**response.json())

    async def aquery_route(
        self,
        route_name: str,
        query_body: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
    ) -> QueryResponse:
        response = await self.client._send_request_async(
            Request(
                method=HttpMethod.POST,
                route=route_name,
                is_query=True,
                data=query_body,
                headers=headers,
            )
        )
        return QueryResponse(**response.json())
