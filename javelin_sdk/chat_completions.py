import logging
from typing import Any, Dict, List, Optional, Union

from javelin_sdk.model_adapters import ModelTransformer, TransformationRuleManager
from javelin_sdk.models import EndpointType
logger = logging.getLogger(__name__)

def get_endpoint_type_from_suffix(url: str) -> EndpointType:
    if not url:
        return EndpointType.UNKNOWN
    
    lower_url = url.lower()

    if '/chat/completions' in lower_url:
        return EndpointType.CHAT

    if 'embeddings' in lower_url:
        return EndpointType.EMBED

    if '/invoke' in lower_url:
        if 'stream' in lower_url:
            return EndpointType.INVOKE_STREAM
        return EndpointType.INVOKE

    if '/converse' in lower_url:
        if 'stream' in lower_url:
            return EndpointType.CONVERSE_STREAM
        return EndpointType.CONVERSE

    return EndpointType.UNKNOWN


class BaseCompletions:
    """Base class for handling completions"""

    def __init__(self, client):
        self.client = client
        self.rule_manager = TransformationRuleManager(client)
        self.transformer = ModelTransformer()

    def _create_request(
        self,
        route: str,
        messages_or_prompt: Union[List[Dict[str, str]], str],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create and process a request"""
        try:
            route_info = self.client.route_service.get_route(route)
            request_data = self._build_request_data(
                route_info.type,
                messages_or_prompt,
                temperature,
                max_tokens,
                kwargs
            )
            
            primary_model = route_info.models[0]
            endpoint = get_endpoint_type_from_suffix(route_info.models[0].suffix)
            model_rules = self.rule_manager.get_rules(primary_model.provider, primary_model.name, endpoint)
            
            transformed_request = self.transformer.transform(request_data, model_rules.input_rules)
            
            model_response = self.client.query_route(route, query_body=transformed_request)
            
            return self.transformer.transform(model_response, model_rules.output_rules)

        except Exception as e:
            logger.error(f"Error in create request: {str(e)}", exc_info=True)
            raise

    def _build_request_data(
        self,
        route_type: str,
        messages_or_prompt: Union[List[Dict[str, str]], str],
        temperature: float,
        max_tokens: Optional[int],
        additional_kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        is_completions = route_type == "completions"
        request_data = {
            "type": route_type,
            "temperature": temperature,
            **({"max_tokens": max_tokens} if max_tokens is not None else {}),
            **(
                {"prompt": messages_or_prompt}
                if is_completions
                else {"messages": messages_or_prompt}
            ),
            **additional_kwargs,
        }
        return request_data


class ChatCompletions(BaseCompletions):
    """Handler for chat completions"""

    def create(
        self,
        route: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create a chat completion request"""
        return self._create_request(
            route, messages, temperature=temperature, max_tokens=max_tokens, **kwargs
        )


class Completions(BaseCompletions):
    """Handler for text completions"""

    def create(
        self,
        route: str,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create a text completion request"""
        return self._create_request(
            route, prompt, temperature=temperature, max_tokens=max_tokens, **kwargs
        )


class Chat:
    """Main chat interface"""

    def __init__(self, client):
        self.completions = ChatCompletions(client)