from typing import List

import httpx

from javelin_sdk.exceptions import (
    BadRequest,
    InternalServerError,
    RateLimitExceededError,
    SecretAlreadyExistsError,
    SecretNotFoundError,
    UnauthorizedError,
)
from javelin_sdk.models import HttpMethod, Request, Secret, Secrets


class SecretService:
    def __init__(self, client):
        self.client = client

    def _process_secret_response_ok(self, response: httpx.Response) -> str:
        """Process a successful response from the Javelin API."""
        self._handle_secret_response(response)
        return response.text

    def _process_secret_response(self, response: httpx.Response) -> Secret:
        """Process a response from the Javelin API and return a Secret object."""
        self._handle_secret_response(response)
        return Secret(**response.json())

    def _handle_secret_response(self, response: httpx.Response) -> None:
        """Handle the API response by raising appropriate exceptions."""
        if response.status_code == 400:
            raise BadRequest(response=response)
        elif response.status_code == 409:
            raise SecretAlreadyExistsError(response=response)
        elif response.status_code in (401, 403):
            raise UnauthorizedError(response=response)
        elif response.status_code == 404:
            raise SecretNotFoundError(response=response)
        elif response.status_code == 429:
            raise RateLimitExceededError(response=response)
        elif response.status_code != 200:
            raise InternalServerError(response=response)

    def create_secret(self, secret: Secret) -> str:
        response = self.client._send_request_sync(
            Request(method=HttpMethod.POST, secret=secret.name, data=secret.dict())
        )
        return self._process_secret_response_ok(response)

    async def acreate_secret(self, secret: Secret) -> str:
        response = await self.client._send_request_async(
            Request(method=HttpMethod.POST, secret=secret.name, data=secret.dict())
        )
        return self._process_secret_response_ok(response)

    def get_secret(self, secret_name: str) -> Secret:
        response = self.client._send_request_sync(
            Request(method=HttpMethod.GET, secret=secret_name)
        )
        return self._process_secret_response(response)

    async def aget_secret(self, secret_name: str) -> Secret:
        response = await self.client._send_request_async(
            Request(method=HttpMethod.GET, secret=secret_name)
        )
        return self._process_secret_response(response)

    def list_secrets(self) -> List[Secret]:
        response = self.client._send_request_sync(
            Request(method=HttpMethod.GET, secret="###")
        )
        try:
            response_json = response.json()
            if "error" in response_json:
                return Secrets(secrets=[])
            else:
                return Secrets(secrets=response_json)
        except ValueError:
            return Secrets(secrets=[])

    async def alist_secrets(self) -> List[Secret]:
        response = await self.client._send_request_async(
            Request(method=HttpMethod.GET, secret="###")
        )

        try:
            response_json = response.json()
            if "error" in response_json:
                return Secrets(secrets=[])
            else:
                return Secrets(secrets=response_json)
        except ValueError:
            return Secrets(secrets=[])

    def update_secret(self, secret: Secret) -> str:
        response = self.client._send_request_sync(
            Request(method=HttpMethod.PUT, secret=secret.api_key, data=secret.dict())
        )

        ## Reload the secret
        self.reload_secret(secret.api_key)
        return self._process_secret_response_ok(response)

    async def aupdate_secret(self, secret: Secret) -> str:
        response = await self.client._send_request_async(
            Request(method=HttpMethod.PUT, secret=secret.api_key, data=secret.dict())
        )

        ## Reload the secret
        self.areload_secret(secret.api_key)
        return self._process_secret_response_ok(response)

    def delete_secret(self, secret_name: str) -> str:
        response = self.client._send_request_sync(
            Request(method=HttpMethod.DELETE, secret=secret_name)
        )

        ## Reload the secret
        self.reload_secret(secret_name=secret_name)
        return self._process_secret_response_ok(response)

    async def adelete_secret(self, secret_name: str) -> str:
        response = await self.client._send_request_async(
            Request(method=HttpMethod.DELETE, secret=secret_name)
        )

        ## Reload the secret
        self.areload_secret(secret_name=secret_name)
        return self._process_secret_response_ok(response)
    
    def reload_secret(self, secret_name: str) -> str:
        """
        Reload a secret
        """
        response = self.client._send_request_sync(
            Request(method=HttpMethod.POST, secret=f"{secret_name}/reload", data="", is_reload=True)
        )
        return response

    async def areload_secret(self, secret_name: str) -> str:
        """
        Reload a secret in an asynchronous way
        """
        response = await self.client._send_request_async(
            Request(method=HttpMethod.POST, secret=f"{secret_name}/reload", data="", is_reload=True)
        )
        return response
