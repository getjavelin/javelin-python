import logging
from typing import Any, Dict, Generator, List, Optional, Union

from javelin_sdk.model_adapters import ModelTransformer, TransformationRuleManager
from javelin_sdk.models import EndpointType

logger = logging.getLogger(__name__)


class BaseCompletions:
    """Base class for handling completions"""

    def __init__(self, client):
        self.client = client
        self.rule_manager = TransformationRuleManager(client)
        self.transformer = ModelTransformer()

    def _create_request(
        self,
        messages_or_prompt: Union[List[Dict[str, str]], str],
        route: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        api_version: Optional[str] = None,
        stream: bool = False,
        model: Optional[str] = None,
        deployment_name: Optional[str] = None,
        **kwargs,
    ) -> Union[Dict[str, Any], Generator[str, None, None]]:
        """Create and process a request"""
        try:
            custom_headers = self.client._headers
            use_model = custom_headers.get("x-javelin-route") is not None

            if route and not use_model:
                return self._handle_route_flow(
                    route, messages_or_prompt, temperature, max_tokens, stream, kwargs
                )
            elif model or use_model:
                return self._handle_model_flow(
                    model,
                    messages_or_prompt,
                    temperature,
                    max_tokens,
                    api_version,
                    stream,
                    deployment_name,
                    kwargs,
                )
            else:
                raise ValueError("Either route or model must be provided.")
        except Exception as e:
            logger.error(f"Error in create request: {str(e)}", exc_info=True)
            raise

    def _handle_route_flow(
        self,
        route: str,
        messages_or_prompt: Union[List[Dict[str, str]], str],
        temperature: float,
        max_tokens: Optional[int],
        stream: bool,
        kwargs: Dict[str, Any],
    ) -> Union[Dict[str, Any], Generator[str, None, None]]:
        """Handle the flow when a route is provided"""
        route_info = self.client.route_service.get_route(route)
        request_data = self._build_request_data(
            route_info.type, messages_or_prompt, temperature, max_tokens, kwargs
        )

        primary_model = route_info.models[0]
        provider_name = primary_model.provider
        provider_object = self.client.provider_service.get_provider(provider_name)

        model_rules = self.rule_manager.get_rules(
            provider_object.config.api_base.rstrip("/") + primary_model.suffix,
            primary_model.name,
        )
        transformed_request = self.transformer.transform(
            request_data, model_rules.input_rules
        )

        model_response = self.client.query_route(
            route,
            query_body=transformed_request,
            headers={},
            stream=stream,
            stream_response_path=model_rules.stream_response_path,
        )
        if stream:
            return model_response
        return self.transformer.transform(model_response, model_rules.output_rules)

    def _handle_model_flow(
        self,
        model: Optional[str],
        messages_or_prompt: Union[List[Dict[str, str]], str],
        temperature: float,
        max_tokens: Optional[int],
        api_version: Optional[str],
        stream: bool,
        deployment_name: Optional[str],
        kwargs: Dict[str, Any],
    ) -> Union[Dict[str, Any], Generator[str, None, None]]:
        """Handle the flow when a model is provided"""
        self.client.set_headers({"x-javelin-model": model})
        custom_headers = self.client._headers
        provider_api_base = custom_headers.get("x-javelin-provider", "")

        if not provider_api_base:
            route = custom_headers.get("x-javelin-route", "")
            route_info = self.client.route_service.get_route(route)
            primary_model = route_info.models[0]
            provider_name = primary_model.provider
            provider_object = self.client.provider_service.get_provider(provider_name)
            provider_api_base = provider_object.config.api_base
            self.client.set_headers({"x-javelin-provider": provider_api_base})

        provider_name = self._determine_provider_name(provider_api_base)
        endpoint_type = "invoke" if provider_name == "bedrock" else "chat"

        request_data = self._build_request_data(
            "chat", messages_or_prompt, temperature, max_tokens, kwargs
        )

        if provider_name == "bedrock":
            model_rules = self.rule_manager.get_rules(provider_api_base, model)
            transformed_request = self.transformer.transform(
                request_data, model_rules.input_rules
            )
        else:
            transformed_request = request_data

        deployment = deployment_name if deployment_name else model
        if api_version:
            kwargs["query_params"] = {"api-version": api_version}

        model_response = self.client.query_unified_endpoint(
            provider_name=provider_name,
            endpoint_type=endpoint_type,
            query_body=transformed_request,
            headers=custom_headers,
            query_params=kwargs.get("query_params"),
            deployment=deployment,
            model_id=model,
        )
        if stream or provider_name != "bedrock":
            return model_response
        return self.transformer.transform(model_response, model_rules.output_rules)

    def _determine_provider_name(self, provider_api_base: str) -> str:
        """Determine the provider name based on the API base"""
        if "azure" in provider_api_base:
            return "azureopenai"
        elif "openai" in provider_api_base:
            return "openai"
        elif "google" in provider_api_base:
            return "gemini"
        else:
            return "bedrock"

    def _build_request_data(
        self,
        route_type: str,
        messages_or_prompt: Union[List[Dict[str, str]], str],
        temperature: float,
        max_tokens: Optional[int],
        additional_kwargs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build the request data for the API call"""
        is_completions = route_type == "completions"
        is_embeddings = route_type == "embeddings"
        if is_embeddings:
            return {
                "type": route_type,
                "input": messages_or_prompt,
                **additional_kwargs,
            }
        request_data = {
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
        messages: List[Dict[str, str]],
        route: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        api_version: Optional[str] = None,
        stream: bool = False,
        deployment_name: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create a chat completion request"""
        return self._create_request(
            messages,
            route=route,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_version=api_version,
            stream=stream,
            deployment_name=deployment_name,
            **kwargs,
        )


class Completions(BaseCompletions):
    """Handler for text completions"""

    def create(
        self,
        prompt: str,
        route: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        deployment_name: Optional[str] = None,
        api_version: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create a text completion request"""
        return self._create_request(
            prompt,
            route=route,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
            deployment_name=deployment_name,
            api_version=api_version,
            **kwargs,
        )


class Chat:
    """Main chat interface"""

    def __init__(self, client):
        self.completions = ChatCompletions(client)


class Embeddings(BaseCompletions):
    """Main embeddings interface"""

    def create(
        self,
        route: str,
        input: str,
        model: Optional[str] = None,
        encoding_format: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create a chat completion request"""
        return self._create_request(
            route,
            input,
            model=model,
            encoding_format=encoding_format,
            **kwargs,
        )
