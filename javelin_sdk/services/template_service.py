from typing import List

import httpx

from javelin_sdk.exceptions import (
    BadRequest,
    InternalServerError,
    RateLimitExceededError,
    TemplateAlreadyExistsError,
    TemplateNotFoundError,
    UnauthorizedError,
)
from javelin_sdk.models import HttpMethod, Request, Template, Templates


class TemplateService:
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
        elif response.status_code == 409:
            raise TemplateAlreadyExistsError(response=response)
        elif response.status_code in (401, 403):
            raise UnauthorizedError(response=response)
        elif response.status_code == 404:
            raise TemplateNotFoundError(response=response)
        elif response.status_code == 429:
            raise RateLimitExceededError(response=response)
        elif response.status_code != 200:
            raise InternalServerError(response=response)

    def create_template(self, template: Template) -> str:
        response = self.client._send_request_sync(
            Request(
                method=HttpMethod.POST, template=template.name, data=template.dict()
            )
        )
        self.reload_data_protection(template.name)
        return self._process_template_response_ok(response)

    async def acreate_template(self, template: Template) -> str:
        response = await self.client._send_request_async(
            Request(
                method=HttpMethod.POST, template=template.name, data=template.dict()
            )
        )
        await self.areload_data_protection(template.name)
        return self._process_template_response_ok(response)

    def get_template(self, template_name: str) -> Template:
        response = self.client._send_request_sync(
            Request(method=HttpMethod.GET, template=template_name)
        )
        return self._process_template_response(response)

    async def aget_template(self, template_name: str) -> Template:
        response = await self.client._send_request_async(
            Request(method=HttpMethod.GET, template=template_name)
        )
        return self._process_template_response(response)

    def list_templates(self) -> List[Template]:
        response = self.client._send_request_sync(
            Request(method=HttpMethod.GET, template="###")
        )
        try:
            response_json = response.json()
            if "error" in response_json:
                return Templates(templates=[])
            else:
                return Templates(templates=response_json)
        except ValueError:
            return Templates(templates=[])

    async def alist_templates(self) -> List[Template]:
        response = await self.client._send_request_async(
            Request(method=HttpMethod.GET, template="###")
        )
        try:
            response_json = response.json()
            if "error" in response_json:
                return Templates(templates=[])
            else:
                return Templates(templates=response_json)
        except ValueError:
            return Templates(templates=[])

    def update_template(self, template: Template) -> str:
        response = self.client._send_request_sync(
            Request(method=HttpMethod.PUT, template=template.name, data=template.dict())
        )
        self.reload_data_protection(template.name)
        return self._process_template_response_ok(response)

    async def aupdate_template(self, template: Template) -> str:
        response = await self.client._send_request_async(
            Request(method=HttpMethod.PUT, template=template.name, data=template.dict())
        )
        await self.areload_data_protection(template.name)
        return self._process_template_response_ok(response)

    def delete_template(self, template_name: str) -> str:
        response = self.client._send_request_sync(
            Request(method=HttpMethod.DELETE, template=template_name)
        )

        self.reload_data_protection(template_name)
        return self._process_template_response_ok(response)

    async def adelete_template(self, template_name: str) -> str:
        response = await self.client._send_request_async(
            Request(method=HttpMethod.DELETE, template=template_name)
        )

        await self.areload_data_protection(template_name)
        return self._process_template_response_ok(response)

    def reload_data_protection(self, strategy_name: str) -> str:
        response = self.client._send_request_sync(
            Request(method=HttpMethod.POST, template=f"{strategy_name}/reload", data="", is_reload=True)
        )
        return response

    async def areload_data_protection(self, strategy_name: str) -> str:
        response = await self.client._send_request_async(
            Request(method=HttpMethod.POST, template=f"{strategy_name}/reload", data="", is_reload=True)
        )
        return response
