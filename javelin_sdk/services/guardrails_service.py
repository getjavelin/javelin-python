import httpx
from typing import Any, Dict, Optional
from javelin_sdk.exceptions import (
    BadRequest,
    RateLimitExceededError,
    UnauthorizedError,
)
from javelin_sdk.models import HttpMethod, Request


class GuardrailsService:
    def __init__(self, client):
        self.client = client

    def _handle_guardrails_response(self, response: httpx.Response) -> None:
        if response.status_code == 400:
            raise BadRequest(response=response)
        elif response.status_code in (401, 403):
            raise UnauthorizedError(response=response)
        elif response.status_code == 429:
            raise RateLimitExceededError(response=response)
        elif 400 <= response.status_code < 500:
            raise BadRequest(
                response=response, message=f"Client Error: {response.status_code}"
            )

    def apply_trustsafety(
        self, text: str, config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        data: Dict[str, Any] = {"input": {"text": text}}
        if config:
            data["config"] = config
        response = self.client._send_request_sync(
            Request(
                method=HttpMethod.POST,
                guardrail="trustsafety",
                data=data,
            )
        )
        self._handle_guardrails_response(response)
        return response.json()

    def apply_promptinjectiondetection(
        self, text: str, config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        data: Dict[str, Any] = {"input": {"text": text}}
        if config:
            data["config"] = config
        response = self.client._send_request_sync(
            Request(
                method=HttpMethod.POST,
                guardrail="promptinjectiondetection",
                data=data,
            )
        )
        self._handle_guardrails_response(response)
        return response.json()

    def apply_guardrails(
        self, text: str, guardrails: list, config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        data: Dict[str, Any] = {"input": {"text": text}, "guardrails": guardrails}
        if config:
            data["config"] = config
        response = self.client._send_request_sync(
            Request(
                method=HttpMethod.POST,
                guardrail="all",
                data=data,
            )
        )
        self._handle_guardrails_response(response)
        return response.json()

    def list_guardrails(self) -> Dict[str, Any]:
        response = self.client._send_request_sync(
            Request(
                method=HttpMethod.GET,
                list_guardrails=True,
            )
        )
        self._handle_guardrails_response(response)
        return response.json()
