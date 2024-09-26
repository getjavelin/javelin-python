from typing import List

import httpx

from javelin_sdk.exceptions import (
    BadRequest,
    GatewayAlreadyExistsError,
    GatewayNotFoundError,
    InternalServerError,
    RateLimitExceededError,
    UnauthorizedError,
)
from javelin_sdk.models import Gateway, Gateways, HttpMethod, Request


class GatewayService:
    def __init__(self, client):
        self.client = client

    def _process_gateway_response_ok(self, response: httpx.Response) -> str:
        """Process a successful response from the Javelin API."""
        self._handle_gateway_response(response)
        return response.text

    def _process_gateway_response(self, response: httpx.Response) -> Gateway:
        """Process a response from the Javelin API and return a Gateway object."""
        self._handle_gateway_response(response)
        return Gateway(**response.json())

    @staticmethod
    def _validate_gateway_name(gateway_name: str):
        """
        Validate the gateway name. Raises a ValueError if the gateway name is empty.

        :param gateway_name: Name of the gateway to validate.
        """
        if not gateway_name:
            raise ValueError("Gateway name cannot be empty.")

    def _handle_gateway_response(self, response: httpx.Response) -> None:
        """Handle the API response by raising appropriate exceptions."""
        if response.status_code == 400:
            raise BadRequest(response=response)
        elif response.status_code == 409:
            raise GatewayAlreadyExistsError(response=response)
        elif response.status_code in (401, 403):
            raise UnauthorizedError(response=response)
        elif response.status_code == 404:
            raise GatewayNotFoundError(response=response)
        elif response.status_code == 429:
            raise RateLimitExceededError(response=response)
        elif response.status_code != 200:
            raise InternalServerError(response=response)

    def create_gateway(self, gateway: Gateway) -> str:
        self._validate_gateway_name(gateway.name)
        response = self.client._send_request_sync(
            Request(method=HttpMethod.POST, gateway=gateway.name, data=gateway.dict())
        )
        return self._process_gateway_response_ok(response)

    async def acreate_gateway(self, gateway: Gateway) -> str:
        self._validate_gateway_name(gateway.name)
        response = await self.client._send_request_async(
            Request(method=HttpMethod.POST, gateway=gateway.name, data=gateway.dict())
        )
        return self._process_gateway_response_ok(response)

    def get_gateway(self, gateway_name: str) -> Gateway:
        response = self.client._send_request_sync(
            Request(method=HttpMethod.GET, gateway=gateway_name)
        )
        return self._process_gateway_response(response)

    async def aget_gateway(self, gateway_name: str) -> Gateway:
        response = await self.client._send_request_async(
            Request(method=HttpMethod.GET, gateway=gateway_name)
        )
        return self._process_gateway_response(response)

    def list_gateways(self) -> List[Gateway]:
        response = self.client._send_request_sync(
            Request(method=HttpMethod.GET, gateway="###")
        )

        try:
            response_json = response.json()
            if "error" in response_json:
                return Gateways(gateways=[])
            else:
                return Gateways(gateways=response_json)
        except ValueError:
            return Gateways(gateways=[])

    async def alist_gateways(self) -> List[Gateway]:
        response = await self.client._send_request_async(
            Request(method=HttpMethod.GET, gateway="###")
        )
        try:
            response_json = response.json()
            if "error" in response_json:
                return Gateways(gateways=[])
            else:
                return Gateways(gateways=response_json)
        except ValueError:
            return Gateways(gateways=[])

    def update_gateway(self, gateway: Gateway) -> str:
        response = self.client._send_request_sync(
            Request(method=HttpMethod.PUT, gateway=gateway.name, data=gateway.dict())
        )
        return self._process_gateway_response_ok(response)

    async def aupdate_gateway(self, gateway: Gateway) -> str:
        response = await self.client._send_request_async(
            Request(method=HttpMethod.PUT, gateway=gateway.name, data=gateway.dict())
        )
        return self._process_gateway_response_ok(response)

    def delete_gateway(self, gateway_name: str) -> str:
        self._validate_gateway_name(gateway_name)
        response = self.client._send_request_sync(
            Request(method=HttpMethod.DELETE, gateway=gateway_name)
        )
        return self._process_gateway_response_ok(response)

    async def adelete_gateway(self, gateway_name: str) -> str:
        self._validate_gateway_name(gateway_name)
        response = await self.client._send_request_async(
            Request(method=HttpMethod.DELETE, gateway=gateway_name)
        )
        return self._process_gateway_response_ok(response)
