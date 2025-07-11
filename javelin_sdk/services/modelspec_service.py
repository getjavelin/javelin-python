from typing import Any, Dict, Optional

import httpx
from javelin_sdk.exceptions import (
    BadRequest,
    InternalServerError,
    RateLimitExceededError,
    UnauthorizedError,
)
from javelin_sdk.models import HttpMethod, Request


class ModelSpecService:
    def __init__(self, client):
        self.client = client

    def _handle_modelspec_response(self, response: httpx.Response) -> None:
        """Handle the API response by raising appropriate exceptions."""
        if response.status_code == 400:
            raise BadRequest(response=response)
        elif response.status_code in (401, 403):
            raise UnauthorizedError(response=response)
        elif response.status_code == 429:
            raise RateLimitExceededError(response=response)
        elif response.status_code != 200:
            raise InternalServerError(response=response)

    def get_model_specs(
        self, provider_url: str, model_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get model specifications from the provider configuration"""
        try:
            response = self.client._send_request_sync(
                Request(
                    method=HttpMethod.GET,
                    query_params={"api_base": provider_url, "model_name": model_name},
                    is_model_specs=True,
                )
            )

            if response.status_code == 200:
                return response.json()
            return None

        except Exception as e:
            print(f"Failed to fetch model specs: {str(e)}")
            return None

    async def aget_model_specs(
        self, provider_url: str, model_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get model specifications from the provider configuration asynchronously"""
        try:
            response = await self.client._send_request_async(
                Request(
                    method=HttpMethod.GET,
                    query_params={
                        "api_base": provider_url,
                        "model_name": model_name,
                    },
                    is_model_specs=True,
                )
            )

            if response.status_code == 200:
                return response.json()
            return None

        except Exception as e:
            print(f"Failed to fetch model specs: {str(e)}")
            return None
