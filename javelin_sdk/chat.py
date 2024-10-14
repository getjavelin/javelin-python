from typing import List, Dict, Any
from javelin_sdk.model_adapters import ModelAdapterFactory
from javelin_sdk.exceptions import BadRequest, UnauthorizedError

class ChatCompletions:
    def __init__(self, client):
        self.client = client

    def create(self, model: str, messages: List[Dict[str, str]], route: str, **kwargs) -> Dict[str, Any]:
        route_info = self.client.get_route(route)
        provider = route_info.models[0].provider  # Assuming the first model is the one we're using

        adapter = ModelAdapterFactory.get_adapter(provider)
        request_data = adapter.prepare_request(model, messages, **kwargs)

        response = self.client.route_service.query_route(route, request_data)
        return adapter.parse_response(response)
