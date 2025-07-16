import json
from typing import Any, AsyncGenerator, Dict, Generator, List, Optional, Union

import httpx
from javelin_sdk.exceptions import (
    BadRequest,
    InternalServerError,
    RateLimitExceededError,
    RouteAlreadyExistsError,
    RouteNotFoundError,
    UnauthorizedError,
)
from javelin_sdk.models import HttpMethod, Request, Route, Routes, UnivModelConfig
from jsonpath_ng import parse


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

    def _validate_route_name(self, route_name: str):
        """
        Validate the route name. Raises a ValueError if the route name is empty.

        :param route_name: Name of the route to validate.
        """
        if not route_name:
            raise ValueError("Route name cannot be empty.")

    def _process_route_response_json(self, response: httpx.Response) -> Dict[str, Any]:
        """
        Process a successful response from the Javelin API.
        Parse body into a Dict[str, Any] object and return it.
        This is for Query() requests.
        """
        self._handle_route_response(response)
        return response.json()

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

    def create_route(self, route) -> str:
        # Accepts dict or Route instance
        if not isinstance(route, Route):
            route = Route.model_validate(route)
        self._validate_route_name(route.name)
        response = self.client._send_request_sync(
            Request(
                method=HttpMethod.POST,
                route=route.name,
                data=route.dict(exclude_none=True),
            )
        )
        return self._process_route_response_ok(response)

    async def acreate_route(self, route) -> str:
        if not isinstance(route, Route):
            route = Route.model_validate(route)
        self._validate_route_name(route.name)
        response = await self.client._send_request_async(
            Request(
                method=HttpMethod.POST,
                route=route.name,
                data=route.dict(exclude_none=True),
            )
        )
        return self._process_route_response_ok(response)

    def get_route(self, route_name: str) -> Route:
        self._validate_route_name(route_name)
        response = self.client._send_request_sync(
            Request(method=HttpMethod.GET, route=route_name)
        )
        return self._process_route_response(response)

    async def aget_route(self, route_name: str) -> Route:
        self._validate_route_name(route_name)
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

    def update_route(self, route) -> str:
        if not isinstance(route, Route):
            route = Route.model_validate(route)
        self._validate_route_name(route.name)
        response = self.client._send_request_sync(
            Request(method=HttpMethod.PUT, route=route.name, data=route.dict())
        )
        self.reload_route(route.name)
        return self._process_route_response_ok(response)

    async def aupdate_route(self, route) -> str:
        if not isinstance(route, Route):
            route = Route.model_validate(route)
        self._validate_route_name(route.name)
        response = await self.client._send_request_async(
            Request(method=HttpMethod.PUT, route=route.name, data=route.dict())
        )
        self.areload_route(route.name)
        return self._process_route_response_ok(response)

    def delete_route(self, route_name: str) -> str:
        self._validate_route_name(route_name)
        response = self.client._send_request_sync(
            Request(method=HttpMethod.DELETE, route=route_name)
        )

        # Reload the route
        self.reload_route(route_name=route_name)
        return self._process_route_response_ok(response)

    async def adelete_route(self, route_name: str) -> str:
        response = await self.client._send_request_async(
            Request(method=HttpMethod.DELETE, route=route_name)
        )

        # Reload the route
        self.areload_route(route_name=route_name)
        return self._process_route_response_ok(response)

    def _extract_json_from_line(self, line_str: str) -> Optional[Dict[str, Any]]:
        """Extract JSON data from a line string."""
        try:
            json_start = line_str.find("{")
            json_end = line_str.rfind("}") + 1
            if json_start != -1 and json_end != -1:
                json_str = line_str[json_start:json_end]
                return json.loads(json_str)
        except Exception:
            pass
        return None

    def _process_bytes_message(
        self, data: Dict[str, Any], jsonpath_expr
    ) -> Optional[str]:
        """Process a message with bytes data."""
        try:
            if "bytes" in data:
                import base64

                bytes_data = base64.b64decode(data["bytes"])
                decoded_data = json.loads(bytes_data)
                matches = jsonpath_expr.find(decoded_data)
                if matches and matches[0].value:
                    return matches[0].value
        except Exception:
            pass
        return None

    def _process_delta_message(self, data: Dict[str, Any]) -> Optional[str]:
        """Process a message with delta data."""
        try:
            if "delta" in data and "text" in data["delta"]:
                return data["delta"]["text"]
        except Exception:
            pass
        return None

    def _process_sse_data(self, line_str: str, jsonpath_expr) -> Optional[str]:
        """Process Server-Sent Events (SSE) data format."""
        try:
            if line_str.strip() != "data: [DONE]":
                json_str = line_str.replace("data: ", "")
                data = json.loads(json_str)
                matches = jsonpath_expr.find(data)
                if matches and matches[0].value:
                    return matches[0].value
        except Exception:
            pass
        return None

    def _process_stream_line(
        self, line_str: str, jsonpath_expr, is_bedrock: bool = False
    ) -> Optional[str]:
        """Process a single line from the stream response
        and extract text if available."""
        try:
            if "message-type" in line_str:
                data = self._extract_json_from_line(line_str)
                if data:
                    if "bytes" in line_str:
                        return self._process_bytes_message(data, jsonpath_expr)
                    else:
                        return self._process_delta_message(data)

            # Handle SSE data format
            elif line_str.startswith("data: "):
                return self._process_sse_data(line_str, jsonpath_expr)

        except Exception:
            pass
        return None

    def query_route(
        self,
        route_name: str,
        query_body: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
        stream: bool = False,
        stream_response_path: Optional[str] = None,
    ) -> Union[Dict[str, Any], Generator[str, None, None]]:
        """Query a route synchronously."""
        self._validate_route_name(route_name)

        response = self.client._send_request_sync(
            Request(
                method=HttpMethod.POST,
                route=route_name,
                is_query=True,
                data=query_body,
                headers=headers,
            )
        )

        if not stream or response.status_code != 200:
            return self._process_route_response_json(response)

        jsonpath_expr = parse(stream_response_path)

        def generate_stream():
            for line in response.iter_lines():
                if line:
                    line_str = line.decode("utf-8") if isinstance(line, bytes) else line
                    text = self._process_stream_line(line_str, jsonpath_expr)
                    if text:
                        yield text

        return generate_stream()

    async def aquery_route(
        self,
        route_name: str,
        query_body: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
        stream: bool = False,
        stream_response_path: Optional[str] = None,
    ) -> Union[Dict[str, Any], AsyncGenerator[str, None]]:
        """Query a route asynchronously."""
        self._validate_route_name(route_name)

        response = await self.client._send_request_async(
            Request(
                method=HttpMethod.POST,
                route=route_name,
                is_query=True,
                data=query_body,
                headers=headers,
            )
        )

        if not stream or response.status_code != 200:
            return self._process_route_response_json(response)

        jsonpath_expr = parse(stream_response_path)

        async def generate_stream():
            async for line in response.aiter_lines():
                if line:
                    line_str = line.decode("utf-8") if isinstance(line, bytes) else line
                    text = self._process_stream_line(
                        line_str, jsonpath_expr, is_bedrock=True
                    )
                    if text:
                        yield text

        return generate_stream()

    def reload_route(self, route_name: str) -> str:
        """
        Reload a route
        """
        response = self.client._send_request_sync(
            Request(
                method=HttpMethod.POST,
                route=f"{route_name}/reload",
                data="",
                is_reload=True,
            )
        )
        return response

    async def areload_route(self, route_name: str) -> str:
        """
        Reload a route in an asynchronous way
        """
        response = await self.client._send_request_async(
            Request(
                method=HttpMethod.POST,
                route=f"{route_name}/reload",
                data="",
                is_reload=True,
            )
        )
        return response

    def query_unified_endpoint(
        self,
        provider_name: str,
        endpoint_type: str,
        query_body: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, Any]] = None,
        deployment: Optional[str] = None,
        model_id: Optional[str] = None,
        stream_response_path: Optional[str] = None,
    ) -> Union[Dict[str, Any], Generator[str, None, None], httpx.Response]:
        univ_model_config = UnivModelConfig(
            provider_name=provider_name,
            endpoint_type=endpoint_type,
            deployment=deployment,
            model_id=model_id,
        )

        request = Request(
            method=HttpMethod.POST,
            data=query_body,
            univ_model_config=univ_model_config.__dict__,
            headers=headers,
            query_params=query_params,
        )

        response = self.client._send_request_sync(request)

        # Only parse JSON for application/json responses
        content_type = response.headers.get("content-type", "").lower()
        print(f"Content-Type: {content_type}")
        if "application/json" in content_type:
            print(f"Response: {response.json()}")
            return response.json()

        # Handle streaming response if stream_response_path is provided
        jsonpath_expr = parse(stream_response_path)

        def generate_stream():
            for line in response.iter_lines():
                if line:
                    line_str = line.decode("utf-8") if isinstance(line, bytes) else line
                    text = self._process_stream_line(line_str, jsonpath_expr)
                    if text:
                        yield text

        return generate_stream()

    async def aquery_unified_endpoint(
        self,
        provider_name: str,
        endpoint_type: str,
        query_body: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, Any]] = None,
        deployment: Optional[str] = None,
        model_id: Optional[str] = None,
        stream_response_path: Optional[str] = None,
    ) -> Union[Dict[str, Any], AsyncGenerator[str, None], httpx.Response]:
        univ_model_config = UnivModelConfig(
            provider_name=provider_name,
            endpoint_type=endpoint_type,
            deployment=deployment,
            model_id=model_id,
        )

        request = Request(
            method=HttpMethod.POST,
            data=query_body,
            univ_model_config=univ_model_config.__dict__,
            headers=headers,
            query_params=query_params,
        )
        response = await self.client._send_request_async(request)

        # Only parse JSON for application/json responses
        content_type = response.headers.get("content-type", "").lower()
        if "application/json" in content_type:
            return response.json()

        # Handle streaming response if stream_response_path is provided
        jsonpath_expr = parse(stream_response_path)

        async def generate_stream():
            async for line in response.aiter_lines():
                if line:
                    line_str = line.decode("utf-8") if isinstance(line, bytes) else line
                    text = self._process_stream_line(
                        line_str, jsonpath_expr, is_bedrock=True
                    )
                    if text:
                        yield text

        return generate_stream()
