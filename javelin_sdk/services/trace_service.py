from typing import List

import httpx

from javelin_sdk.exceptions import (
    BadRequest,
    InternalServerError,
    RateLimitExceededError,
    TraceNotFoundError,
    UnauthorizedError,
)
from javelin_sdk.models import HttpMethod, Request, Template, Templates


class TraceService:
    def __init__(self, client):
        self.client = client

    def _process_template_response_ok(self, response: httpx.Response) -> str:
        """Process a successful response from the Javelin API."""
        self._handle_template_response(response)
        return response.text

    def _process_template_response(self, response: httpx.Response) -> Template:
        """Process a response from the Javelin API and return a Template object."""
        self._handle_template_response(response)
        return Template(**response.json())

    def _handle_template_response(self, response: httpx.Response) -> None:
        """Handle the API response by raising appropriate exceptions."""
        if response.status_code == 400:
            raise BadRequest(response=response)
        elif response.status_code in (401, 403):
            raise UnauthorizedError(response=response)
        elif response.status_code == 404:
            raise TraceNotFoundError(response=response)
        elif response.status_code == 429:
            raise RateLimitExceededError(response=response)
        elif response.status_code != 200:
            raise InternalServerError(response=response)
        else:
            raise Exception(
                "Unexpected response status code: {}".format(response.status_code)
            )

    def get_traces(self) -> any:
        request = Request(
            method=HttpMethod.GET,
            trace="traces",
        )
        response = self.client._send_request_sync(request)
        return self._process_template_response_ok(response)
