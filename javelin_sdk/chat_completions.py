from typing import List, Dict, Any, Optional, Union
from javelin_sdk.model_adapters import ModelAdapterFactory
from javelin_sdk.models import Route


class BaseCompletions:
    def __init__(self, client):
        self.client = client

    def _create_request(
        self,
        route: str,
        messages_or_prompt: Union[List[Dict[str, str]], str],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        try:
            route_info = self.client.route_service.get_route(route)
            is_completions = isinstance(messages_or_prompt, str)
            route_type = "completions" if is_completions else "chat"
            if route_info.type != route_type:
                raise ValueError(
                    f"Route '{route}' is not a {route_type} route. {route_info.type} != {route_type}"
                )

            primary_model = route_info.models[0]
            if not primary_model:
                raise ValueError(f"No primary model found for route '{route}'")

            adapter = ModelAdapterFactory.get_adapter(
                primary_model.provider, primary_model.name
            )

            request_data = {
                "model": model or primary_model.name,
                "temperature": temperature,
                "max_tokens": max_tokens,
                **kwargs,
            }

            if is_completions:
                request_data["prompt"] = messages_or_prompt
            else:
                request_data["messages"] = messages_or_prompt

            prepared_request = (
                adapter.prepare_completion_request(**request_data)
                if is_completions
                else adapter.prepare_request(**request_data)
            )

            response = self.client.query_route(route, query_body=prepared_request)
            return adapter.parse_response(response)
        except Exception as e:
            print(f"Error in create method: {str(e)}")
            raise e


class ChatCompletions(BaseCompletions):
    def create(
        self,
        route: str,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        return self._create_request(
            route, messages, model, temperature, max_tokens, **kwargs
        )


class Completions(BaseCompletions):
    def create(
        self,
        route: str,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        return self._create_request(
            route, prompt, model, temperature, max_tokens, **kwargs
        )


class Chat:
    def __init__(self, client):
        self.completions = ChatCompletions(client)
