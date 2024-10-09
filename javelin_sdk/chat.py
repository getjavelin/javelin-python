from typing import List, Dict, Any

class ChatCompletions:
    def __init__(self, client):
        self.client = client

    def create(self, model: str, messages: List[Dict[str, str]], route: str, **kwargs) -> Dict[str, Any]:
        print("model", model)
        print("messages", messages)
        print("route", route)
        print("kwargs", kwargs)
        query_data = {
            "model": model,
            "messages": messages,
            **kwargs
        }
        
        response = self.client.route_service.query_route(route, query_data)
        return response