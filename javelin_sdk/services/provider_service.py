from typing import Any, Dict, List

import httpx

from javelin_sdk.exceptions import (
    BadRequest,
    InternalServerError,
    ProviderAlreadyExistsError,
    ProviderNotFoundError,
    RateLimitExceededError,
    UnauthorizedError,
)
from javelin_sdk.models import HttpMethod, Provider, Providers, Request, Secrets, EndpointType


class ProviderService:
    def __init__(self, client):
        self.client = client

    @staticmethod
    def _validate_provider_name(provider_name: str):
        """
        Validate the provider name. Raises a ValueError if the provider name is empty.

        :param provider_name: Name of the provider to validate.
        """
        if not provider_name:
            raise ValueError("Provider name cannot be empty.")

    def _process_provider_response_ok(self, response: httpx.Response) -> str:
        """Process a successful response from the Javelin API."""
        self._handle_provider_response(response)
        return response.text

    def _process_provider_response(self, response: httpx.Response) -> Provider:
        """Process a response from the Javelin API and return a Provider object."""
        self._handle_provider_response(response)
        return Provider(**response.json())

    def _handle_provider_response(self, response: httpx.Response) -> None:
        """Handle the API response by raising appropriate exceptions."""
        if response.status_code == 400:
            raise BadRequest(response=response)
        elif response.status_code == 409:
            raise ProviderAlreadyExistsError(response=response)
        elif response.status_code in (401, 403):
            raise UnauthorizedError(response=response)
        elif response.status_code == 404:
            raise ProviderNotFoundError(response=response)
        elif response.status_code == 429:
            raise RateLimitExceededError(response=response)
        elif response.status_code != 200:
            raise InternalServerError(response=response)

    def create_provider(self, provider: Provider) -> str:
        self._validate_provider_name(provider.name)
        response = self.client._send_request_sync(
            Request(
                method=HttpMethod.POST, provider=provider.name, data=provider.dict()
            )
        )
        return self._process_provider_response_ok(response)

    async def acreate_provider(self, provider: Provider) -> str:
        self._validate_provider_name(provider.name)
        response = await self.client._send_request_async(
            Request(
                method=HttpMethod.POST, provider=provider.name, data=provider.dict()
            )
        )
        return self._process_provider_response_ok(response)

    def get_provider(self, provider_name: str) -> Provider:
        response = self.client._send_request_sync(
            Request(method=HttpMethod.GET, provider=provider_name)
        )
        return self._process_provider_response(response)

    async def aget_provider(self, provider_name: str) -> Provider:
        response = await self.client._send_request_async(
            Request(method=HttpMethod.GET, provider=provider_name)
        )
        return self._process_provider_response(response)

    def list_providers(self) -> List[Provider]:
        response = self.client._send_request_sync(
            Request(method=HttpMethod.GET, provider="###")
        )
        try:
            response_json = response.json()
            if "error" in response_json:
                return Providers(providers=[])
            else:
                return Providers(providers=response_json)
        except ValueError:
            return Providers(providers=[])

    async def alist_providers(self) -> List[Provider]:
        response = await self.client._send_request_async(
            Request(method=HttpMethod.GET, provider="###")
        )

        try:
            response_json = response.json()
            if "error" in response_json:
                return Providers(providers=[])
            else:
                return Providers(providers=response_json)
        except ValueError:
            return Providers(providers=[])

    def update_provider(self, provider: Provider) -> str:
        response = self.client._send_request_sync(
            Request(method=HttpMethod.PUT, provider=provider.name, data=provider.dict())
        )

        ## reload the provider
        self.reload_provider(provider.name)
        return self._process_provider_response_ok(response)

    async def aupdate_provider(self, provider: Provider) -> str:
        response = await self.client._send_request_async(
            Request(method=HttpMethod.PUT, provider=provider.name, data=provider.dict())
        )

        ## reload the provider
        self.areload_provider(provider.name)
        return self._process_provider_response_ok(response)

    def delete_provider(self, provider_name: str) -> str:
        self._validate_provider_name(provider_name)
        response = self.client._send_request_sync(
            Request(method=HttpMethod.DELETE, provider=provider_name)
        )

        ## reload the provider
        self.reload_provider(provider_name=provider_name)
        return self._process_provider_response_ok(response)

    async def adelete_provider(self, provider_name: str) -> str:
        self._validate_provider_name(provider_name)
        response = await self.client._send_request_async(
            Request(method=HttpMethod.DELETE, provider=provider_name)
        )

        ## reload the provider
        self.areload_provider(provider_name=provider_name)
        return self._process_provider_response_ok(response)

    async def alist_provider_secrets(self, provider_name: str) -> Secrets:
        response = await self._send_request_async(
            Request(
                method=HttpMethod.GET,
                gateway="",
                provider=provider_name,
                route="",
                secret="###",
            )
        )

        try:
            response_json = response.json()
            if "error" in response_json:
                return Secrets(secrets=[])
            else:
                return Secrets(secrets=response_json)
        except ValueError:
            return Secrets(secrets=[])

    def get_transformation_rules(
        self, provider_name: str, model_name: str, endpoint: EndpointType = EndpointType.UNKNOWN
    ) -> Dict[str, Any]:
        """Get transformation rules from the provider configuration"""
        try:
            response = self.client._send_request_sync(
                Request(
                    method=HttpMethod.GET,
                    provider=provider_name,
                    query_params={
                        "model_name": model_name,
                        "endpoint": endpoint.value
                    },
                    is_transformation_rules=True,
                )
            )

            if response.status_code == 200:
                return response.json()
            return None

        except Exception as e:
            print(f"Failed to fetch transformation rules: {str(e)}")
            return None

    async def aget_transformation_rules(
        self, provider_name: str, model_name: str, endpoint: EndpointType = EndpointType.UNKNOWN
    ) -> Dict[str, Any]:
        """Get transformation rules from the provider configuration asynchronously"""
        try:
            response = await self.client._send_request_async(
                Request(
                    method=HttpMethod.GET,
                    provider=provider_name,
                    route="transformation-rules",
                    query_params={
                        "model_name": model_name,
                        "endpoint": endpoint.value
                    }
                )
            )

            if response.status_code == 200:
                return response.json()
            return None

        except Exception as e:
            print(f"Failed to fetch transformation rules: {str(e)}")
            return None

    def reload_provider(self, provider_name: str) -> str:
        """
        Reload a provider
        """
        response = self.client._send_request_sync(
            Request(method=HttpMethod.POST, provider=f"{provider_name}/reload", data="", is_reload=True)
        )
        return response

    async def areload_provider(self, provider_name: str) -> str:
        """
        Reload a provider in an asynchronous way
        """
        response = await self.client._send_request_async(
            Request(method=HttpMethod.POST, provider=f"{provider_name}/reload", data="", is_reload=True)
        )
        return response