import json
import logging
from typing import Any, Dict, List, Optional, Union

from javelin_sdk.model_adapters import ModelAdapterFactory
from javelin_sdk.models import ArrayHandling, ModelSpec, Route, TransformRule, TypeHint

logger = logging.getLogger(__name__)


class BaseCompletions:
    """Base class for handling completions"""

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
        """Create and process a request"""
        try:
            # Get route info and validate
            route_info = self.client.route_service.get_route(route)
            is_completions = isinstance(messages_or_prompt, str)
            route_type = "completions" if is_completions else "chat"

            if route_info.type != route_type:
                raise ValueError(f"Route '{route}' is not a {route_type} route")

            # Validate messages format
            if not is_completions:
                if not isinstance(messages_or_prompt, list):
                    raise ValueError("Messages must be a list of dictionaries")
                for msg in messages_or_prompt:
                    if (
                        not isinstance(msg, dict)
                        or "role" not in msg
                        or "content" not in msg
                    ):
                        raise ValueError(
                            "Each message must have 'role' and 'content' keys"
                        )

            # Get primary model and configuration
            primary_model = route_info.models[0]
            model_spec = self._get_model_spec(
                primary_model.provider, primary_model.name
            )

            # Initialize adapter
            adapter = ModelAdapterFactory.get_adapter(
                primary_model.provider, primary_model.name, model_spec
            )

            # Prepare request data
            request_data = {
                "type": route_type,
                "temperature": temperature,
                **({"max_tokens": max_tokens} if max_tokens is not None else {}),
                **(
                    {"prompt": messages_or_prompt}
                    if is_completions
                    else {"messages": messages_or_prompt}
                ),
                **kwargs,
            }

            # Transform and send request
            prepared_request = adapter.prepare_request(
                provider=primary_model.provider,
                model=primary_model.name,
                **request_data,
            )

            response = self.client.query_route(route, query_body=prepared_request)
            return adapter.parse_response(
                primary_model.provider, primary_model.name, response
            )

        except Exception as e:
            logger.error(f"Error in create request: {str(e)}", exc_info=True)
            raise

    def _get_model_spec(self, provider: str, model_name: str) -> ModelSpec:
        """Get model specification based on provider and model name"""
        try:
            remote_specs = self.client.provider_service.get_model_specs(
                provider, model_name
            )
            if remote_specs:
                return ModelSpec(
                    input_rules=[
                        TransformRule(**rule)
                        for rule in remote_specs.get("input_rules", [])
                    ],
                    output_rules=[
                        TransformRule(**rule)
                        for rule in remote_specs.get("output_rules", [])
                    ],
                )
        except Exception as e:
            logger.warning(f"Failed to get remote model specs: {str(e)}")

        # Fall back to local specs if remote fails
        model_type = self._determine_model_type(model_name)
        provider_specs = {
            "openai": self._get_openai_spec,
            "amazon": self._get_amazon_spec,
            "anthropic": self._get_claude_spec,
            "mistral": self._get_mistral_spec,
        }

        get_spec = provider_specs.get(provider.lower(), self._get_openai_spec)
        return get_spec(model_type)

    def _determine_model_type(self, model_name: str) -> str:
        """Determine model type from model name"""
        model_lower = model_name.lower()

        if "llama" in model_lower:
            return "llama"
        elif "titan" in model_lower:
            return "titan"
        elif "claude" in model_lower:
            return "claude"
        elif "mistral" in model_lower:
            return "mistral"

        return "openai"

    def _get_openai_spec(self, model_type: str) -> ModelSpec:
        """Get OpenAI model specification"""
        return ModelSpec(
            input_rules=[
                TransformRule(
                    source_path="messages",
                    target_path="messages",
                    conditions=["type == 'chat'"],
                ),
                TransformRule(
                    source_path="prompt",
                    target_path="prompt",
                    conditions=["type == 'completions'"],
                ),
                TransformRule(
                    source_path="temperature",
                    target_path="temperature",
                    default_value=0.7,
                    type_hint=TypeHint.FLOAT,
                ),
                TransformRule(
                    source_path="max_tokens",
                    target_path="max_tokens",
                    type_hint=TypeHint.INTEGER,
                ),
            ],
            output_rules=[
                TransformRule(source_path="choices", target_path="choices"),
                TransformRule(source_path="usage", target_path="usage"),
            ],
        )

    def _get_amazon_spec(self, model_type: str) -> ModelSpec:
        """Get Amazon model specification"""
        if model_type == "llama":
            return ModelSpec(
                input_rules=[
                    TransformRule(
                        source_path="messages[*].content",
                        target_path="prompt",
                        array_handling=ArrayHandling.JOIN,
                        conditions=["type == 'chat'"],
                    ),
                    TransformRule(
                        source_path="prompt",
                        target_path="prompt",
                        conditions=["type == 'completions'"],
                    ),
                    TransformRule(
                        source_path="temperature",
                        target_path="temperature",
                        default_value=0.7,
                        type_hint=TypeHint.FLOAT,
                    ),
                    TransformRule(
                        source_path="max_tokens",
                        target_path="max_gen_len",
                        default_value=50,
                        type_hint=TypeHint.INTEGER,
                    ),
                    TransformRule(
                        source_path="top_p",
                        target_path="top_p",
                        default_value=0.9,
                        type_hint=TypeHint.FLOAT,
                    ),
                ],
                output_rules=[
                    TransformRule(
                        source_path="generation",
                        target_path="choices[0].message.content",
                        default_value="",
                    ),
                    TransformRule(
                        source_path="stop_reason",
                        target_path="choices[0].finish_reason",
                        default_value="stop",
                    ),
                    TransformRule(
                        source_path="prompt_token_count",
                        target_path="usage.prompt_tokens",
                        default_value=0,
                        type_hint=TypeHint.INTEGER,
                    ),
                    TransformRule(
                        source_path="generation_token_count",
                        target_path="usage.completion_tokens",
                        default_value=0,
                        type_hint=TypeHint.INTEGER,
                    ),
                ],
            )
        elif model_type == "titan":
            return ModelSpec(
                input_rules=[
                    TransformRule(
                        source_path="messages",
                        target_path="inputText",
                        transform_function="format_messages",
                        conditions=["type == 'chat'"],
                    ),
                    TransformRule(
                        source_path="prompt",
                        target_path="inputText",
                        conditions=["type == 'completions'"],
                    ),
                    TransformRule(
                        source_path="temperature",
                        target_path="textGenerationConfig.temperature",
                        default_value=0.7,
                        type_hint=TypeHint.FLOAT,
                    ),
                    TransformRule(
                        source_path="max_tokens",
                        target_path="textGenerationConfig.maxTokenCount",
                        default_value=50,
                        type_hint=TypeHint.INTEGER,
                    ),
                ],
                output_rules=[
                    TransformRule(
                        source_path="results[*].outputText",
                        target_path="choices[0].message.content",
                        default_value="",
                        array_handling=ArrayHandling.FIRST,
                    ),
                    TransformRule(
                        source_path="inputTextTokenCount",
                        target_path="usage.prompt_tokens",
                        default_value=0,
                        type_hint=TypeHint.INTEGER,
                    ),
                    TransformRule(
                        source_path="results[0].tokenCount",
                        target_path="usage.completion_tokens",
                        default_value=0,
                        type_hint=TypeHint.INTEGER,
                    ),
                ],
            )
        return ModelSpec(input_rules=[], output_rules=[])

    def _get_claude_spec(self, model_type: str) -> ModelSpec:
        """Get Claude model specification"""
        return ModelSpec(
            input_rules=[
                TransformRule(
                    source_path="messages",
                    target_path="messages",
                    conditions=["type == 'chat'"],
                ),
                TransformRule(
                    source_path="prompt",
                    target_path="messages",
                    transform_function="format_claude_completion",
                    conditions=["type == 'completions'"],
                ),
                TransformRule(
                    source_path="temperature",
                    target_path="temperature",
                    default_value=0.7,
                    type_hint=TypeHint.FLOAT,
                ),
                TransformRule(
                    source_path="max_tokens",
                    target_path="max_tokens",
                    type_hint=TypeHint.INTEGER,
                ),
            ],
            output_rules=[
                TransformRule(
                    source_path="completion",
                    target_path="choices[0].message.content",
                    default_value="",
                ),
                TransformRule(
                    source_path="stop_reason",
                    target_path="choices[0].finish_reason",
                    default_value="stop",
                ),
                TransformRule(
                    source_path="usage.input_tokens",
                    target_path="usage.prompt_tokens",
                    default_value=0,
                    type_hint=TypeHint.INTEGER,
                ),
                TransformRule(
                    source_path="usage.output_tokens",
                    target_path="usage.completion_tokens",
                    default_value=0,
                    type_hint=TypeHint.INTEGER,
                ),
            ],
        )

    def _get_mistral_spec(self, model_type: str) -> ModelSpec:
        """Get Mistral model specification"""
        return ModelSpec(
            input_rules=[
                TransformRule(
                    source_path="messages",
                    target_path="messages",
                    conditions=["type == 'chat'"],
                ),
                TransformRule(
                    source_path="prompt",
                    target_path="messages",
                    transform_function="format_mistral_completion",
                    conditions=["type == 'completions'"],
                ),
                TransformRule(
                    source_path="temperature",
                    target_path="temperature",
                    default_value=0.7,
                    type_hint=TypeHint.FLOAT,
                ),
                TransformRule(
                    source_path="max_tokens",
                    target_path="max_length",
                    default_value=500,
                    type_hint=TypeHint.INTEGER,
                ),
            ],
            output_rules=[
                TransformRule(
                    source_path="choices[0].message.content",
                    target_path="choices[0].message.content",
                    default_value="",
                ),
                TransformRule(
                    source_path="choices[0].finish_reason",
                    target_path="choices[0].finish_reason",
                    default_value="stop",
                ),
                TransformRule(source_path="usage", target_path="usage"),
            ],
        )


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


def test_adapter():
    """Test the unified adapter with various models"""

    # Sample client for testing
    class MockClient:
        def query_route(self, route, query_body):
            return {"choices": [{"message": {"content": "Test response"}}]}

        class route_service:
            @staticmethod
            def get_route(route):
                class RouteInfo:
                    type = "chat"
                    models = [
                        type("Model", (), {"provider": "openai", "name": "gpt-4"})
                    ]

                return RouteInfo()

    # Create test instances
    client = MockClient()
    chat = Chat(client)

    # Test chat completion
    chat_response = chat.completions.create(
        route="test-route",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"},
        ],
        temperature=0.7,
    )
    print("Chat completion response:", json.dumps(chat_response, indent=2))

    # Test text completion
    completion = Completions(client)
    completion_response = completion.create(
        route="test-route", prompt="Complete this sentence:", temperature=0.7
    )
    print("Text completion response:", json.dumps(completion_response, indent=2))


if __name__ == "__main__":
    test_adapter()
