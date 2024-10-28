from typing import Any, Dict, List, Optional, Union
import logging

from javelin_sdk.model_adapters import ModelAdapterFactory
from javelin_sdk.models import (
    Route, ModelSpec, TransformRule, 
    ArrayHandling, TypeHint
)

logger = logging.getLogger(__name__)

class BaseCompletions:
    def __init__(self, client):
        self.client = client

    def _create_request(
        self,
        route: str,
        messages_or_prompt: Union[List[Dict[str, str]], str],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create and process a request for either chat or text completion"""
        try:
            logger.debug(f"Creating request for route: {route}")
            
            # Get route info and validate
            route_info = self.client.route_service.get_route(route)
            is_completions = isinstance(messages_or_prompt, str)
            route_type = "completions" if is_completions else "chat"
            
            if route_info.type != route_type:
                error_msg = f"Route '{route}' is not a {route_type} route. Got {route_info.type}"
                logger.error(error_msg)
                raise ValueError(error_msg)

            # Validate messages format for chat
            if not is_completions:
                if not isinstance(messages_or_prompt, list):
                    raise ValueError("Messages must be a list of dictionaries")
                for msg in messages_or_prompt:
                    if not isinstance(msg, dict) or 'role' not in msg or 'content' not in msg:
                        raise ValueError("Each message must be a dictionary with 'role' and 'content' keys")

            # Get primary model
            try:
                primary_model = route_info.models[0]
            except (IndexError, AttributeError):
                error_msg = f"No models configured for route '{route}'"
                logger.error(error_msg)
                raise ValueError(error_msg)

            # Get model configuration
            model_type = self._determine_model_type(route, primary_model.name)
            model_spec = self._get_model_spec(primary_model.provider, model_type)
            
            logger.debug(f"Using model type: {model_type} for provider: {primary_model.provider}")

            # Initialize adapter
            adapter = ModelAdapterFactory.get_adapter(
                primary_model.provider,
                primary_model.name,
                model_spec
            )

            # Prepare request data
            request_data = {
                "type": route_type,
                "temperature": temperature,
                **({'max_tokens': max_tokens} if max_tokens is not None else {}),
                **({"prompt": messages_or_prompt} if is_completions else {"messages": messages_or_prompt}),
                **kwargs
            }
            
            logger.debug(f"Request data before transformation: {request_data}")
            
            # Prepare and send request
            prepared_request = adapter.prepare_request(
                provider=primary_model.provider,
                model=primary_model.name,
                **request_data
            )
            
            logger.debug(f"Transformed request data: {prepared_request}")
            
            # Send request and parse response
            response = self.client.query_route(route, query_body=prepared_request)
            return adapter.parse_response(
                primary_model.provider, primary_model.name, response
            )

        except Exception as e:
            logger.error(f"Error in create method: {str(e)}", exc_info=True)
            raise

    def _determine_model_type(self, route: str, model_name: str) -> str:
        """Determine the model type from route or model name"""
        route_lower = route.lower()
        model_lower = model_name.lower()
        
        if any(name in route_lower or name in model_lower for name in ["llama"]):
            return "llama"
        elif any(name in route_lower or name in model_lower for name in ["titan"]):
            return "titan"
        return "openai"

    def _get_model_spec(self, provider: str, model_type: str) -> ModelSpec:
        """Get model specification for the given provider and model type"""
        provider_lower = provider.lower()
        
        if provider_lower == "openai":
            return ModelSpec(
                input_rules=[
                    TransformRule(
                        source_path="messages",
                        target_path="messages",
                        conditions=["type == 'chat'"]
                    ),
                    TransformRule(
                        source_path="prompt",
                        target_path="prompt",
                        conditions=["type == 'completion'"]
                    ),
                    TransformRule(
                        source_path="temperature",
                        target_path="temperature",
                        default_value=0.7,
                        type_hint=TypeHint.FLOAT
                    ),
                    TransformRule(
                        source_path="max_tokens",
                        target_path="max_tokens",
                        type_hint=TypeHint.INTEGER
                    )
                ],
                output_rules=[
                    TransformRule(
                        source_path="choices[0].message.content",
                        target_path="choices[0].message.content",
                        default_value=""
                    ),
                    TransformRule(
                        source_path="usage.prompt_tokens",
                        target_path="usage.prompt_tokens",
                        default_value=0,
                        type_hint=TypeHint.INTEGER
                    ),
                    TransformRule(
                        source_path="usage.completion_tokens",
                        target_path="usage.completion_tokens",
                        default_value=0,
                        type_hint=TypeHint.INTEGER
                    )
                ]
            )
        
        # For other providers, return their specific transformations
        if provider_lower == "amazon":
            if model_type == "llama":
                return ModelSpec(
                    input_rules=[
                        # For chat completion: Convert messages to prompt
                        TransformRule(
                            source_path="messages[*].content",
                            target_path="prompt",
                            array_handling=ArrayHandling.JOIN,
                            conditions=["type == 'chat'"]
                        ),
                        # For text completion: Use prompt directly
                        TransformRule(
                            source_path="prompt",
                            target_path="prompt",
                            conditions=["type == 'completions'"]
                        ),
                        # Parameters
                        TransformRule(
                            source_path="temperature",
                            target_path="temperature",
                            default_value=0.7,
                            type_hint=TypeHint.FLOAT
                        ),
                        TransformRule(
                            source_path="max_tokens",
                            target_path="max_gen_len",
                            default_value=50,
                            type_hint=TypeHint.INTEGER
                        ),
                        TransformRule(
                            source_path="top_p",
                            target_path="top_p",
                            default_value=0.9,
                            type_hint=TypeHint.FLOAT
                        )
                    ],
                    output_rules=[
                        TransformRule(
                            source_path="generation",
                            target_path="choices[0].message.content",
                            default_value=""
                        ),
                        TransformRule(
                            source_path="prompt_token_count",
                            target_path="usage.prompt_tokens",
                            default_value=0,
                            type_hint=TypeHint.INTEGER
                        ),
                        TransformRule(
                            source_path="generation_token_count",
                            target_path="usage.completion_tokens",
                            default_value=0,
                            type_hint=TypeHint.INTEGER
                        )
                    ]
                )
            elif "titan" in model_type.lower():
                return ModelSpec(
                    input_rules=[
                        # For chat completion: Convert messages to inputText
                        TransformRule(
                            source_path="messages",
                            target_path="inputText",
                            transform_function="format_messages",
                            conditions=["type == 'chat'"]
                        ),
                        # For text completion: Convert prompt to inputText
                        TransformRule(
                            source_path="prompt",
                            target_path="inputText",
                            conditions=["type == 'completions'"]
                        ),
                        # Config parameters
                        TransformRule(
                            source_path="temperature",
                            target_path="textGenerationConfig.temperature",
                            default_value=0.7,
                            type_hint=TypeHint.FLOAT
                        ),
                        TransformRule(
                            source_path="max_tokens",
                            target_path="textGenerationConfig.maxTokenCount",
                            default_value=50,
                            type_hint=TypeHint.INTEGER
                        )
                    ],
                    output_rules=[
                        TransformRule(
                            source_path="results[*].outputText",
                            target_path="choices[0].message.content",
                            default_value="",
                            array_handling=ArrayHandling.FIRST
                        ),
                        TransformRule(
                            source_path="inputTextTokenCount",
                            target_path="usage.prompt_tokens",
                            default_value=0,
                            type_hint=TypeHint.INTEGER
                        ),
                        TransformRule(
                            source_path="results[0].tokenCount",
                            target_path="usage.completion_tokens",
                            default_value=0,
                            type_hint=TypeHint.INTEGER
                        )
                    ]
                )
        
        return ModelSpec(input_rules=[], output_rules=[])

class ChatCompletions(BaseCompletions):
    def create(
        self,
        route: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        return self._create_request(
            route, messages, temperature=temperature, max_tokens=max_tokens, **kwargs
        )


class Completions(BaseCompletions):
    def create(
        self,
        route: str,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        return self._create_request(
            route, prompt, temperature=temperature, max_tokens=max_tokens, **kwargs
        )


class Chat:
    def __init__(self, client):
        self.completions = ChatCompletions(client)

