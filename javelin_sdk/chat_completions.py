from typing import List, Dict, Any, Optional
from javelin_sdk.model_adapters import ModelAdapterFactory


class ChatCompletions:
    def __init__(self, client):
        self.client = client

    def create(
        self,
        route: str,
        provider: str,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        try:
            adapter = ModelAdapterFactory.get_adapter(provider)
            request_data = adapter.prepare_request(
                model, messages, temperature=temperature
            )

            response = self.client.query_route(route, query_body=request_data)
            return response
        except Exception as e:
            print(f"Error in create method: {str(e)}")
            raise e


class Chat:
    def __init__(self, client):
        self.completions = ChatCompletions(client)
