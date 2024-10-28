import time
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel
import jmespath

from .model_configs import ModelConfigFactory

class TransformRule(BaseModel):
    source_path: str
    target_path: str
    default_value: Any = None
    transform_function: Optional[str] = None

class ModelAdapter(ABC):
    @abstractmethod
    def prepare_request(self, provider: str, model: str, **kwargs) -> Dict[str, Any]:
        pass

    @abstractmethod
    def parse_response(
        self, provider: str, model: str, response: Dict[str, Any]
    ) -> Dict[str, Any]:
        pass

    def transform(self, data: Dict[str, Any], rules: List[TransformRule]) -> Dict[str, Any]:
        """Generic transform method for all adapters"""
        result = {}
        
        for rule in rules:
            # Handle messages specially if present
            if rule.source_path == "messages" and "messages" in data:
                value = data["messages"]
            else:
                value = jmespath.search(rule.source_path, data)

            # Only process if value exists or there's a default
            if value is not None:
                if rule.transform_function and hasattr(self, rule.transform_function):
                    value = getattr(self, rule.transform_function)(value)
            elif rule.default_value is not None:
                value = rule.default_value
            else:
                continue

            # Create nested structure
            current = result
            parts = rule.target_path.split('.')
            
            for i, part in enumerate(parts[:-1]):
                if '[' in part:
                    base_part = part.split('[')[0]
                    if base_part not in current:
                        current[base_part] = []
                    while len(current[base_part]) <= 0:
                        current[base_part].append({})
                    current = current[base_part][0]
                else:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
            
            current[parts[-1]] = value
        
        return result

class OpenAIAdapter(ModelAdapter):
    def prepare_request(self, provider: str, model: str, **kwargs) -> Dict[str, Any]:
        # OpenAI format is our base format, so just pass through
        return kwargs

    def parse_response(
        self, provider: str, model: str, response: Dict[str, Any]
    ) -> Dict[str, Any]:
        # OpenAI format is our base format, so just pass through
        return response

class AzureOpenAIAdapter(OpenAIAdapter):
    pass

class BedrockAmazonAdapter(ModelAdapter):
    def __init__(self):
        self.input_rules = {
            "titan": [
                # For chat completion: Convert messages to inputText
                TransformRule(
                    source_path="messages",
                    target_path="inputText",
                    transform_function="format_messages"
                ),
                # For text completion: Use prompt directly
                TransformRule(
                    source_path="prompt",
                    target_path="inputText"
                ),
                # Config parameters
                TransformRule(
                    source_path="temperature",
                    target_path="textGenerationConfig.temperature",
                    default_value=0.7
                ),
                TransformRule(
                    source_path="max_tokens",
                    target_path="textGenerationConfig.maxTokenCount",
                    default_value=50
                )
            ],
            "llama": [
                # For chat completion: Convert messages to prompt
                TransformRule(
                    source_path="messages",
                    target_path="prompt",
                    transform_function="format_messages"
                ),
                # For text completion: Use prompt directly
                TransformRule(
                    source_path="prompt",
                    target_path="prompt"
                ),
                # Parameters
                TransformRule(
                    source_path="temperature",
                    target_path="temperature",
                    default_value=0.7
                ),
                TransformRule(
                    source_path="max_tokens",
                    target_path="max_gen_len",
                    default_value=50
                ),
                TransformRule(
                    source_path="top_p",
                    target_path="top_p",
                    default_value=0.9
                )
            ]
        }

        self.output_rules = {
            "titan": [
                TransformRule(
                    source_path="results[0].outputText",
                    target_path="choices[0].message.content",
                    default_value=""
                ),
                TransformRule(
                    source_path="inputTextTokenCount",
                    target_path="usage.prompt_tokens",
                    default_value=0
                ),
                TransformRule(
                    source_path="results[0].tokenCount",
                    target_path="usage.completion_tokens",
                    default_value=0
                )
            ],
            "llama": [
                TransformRule(
                    source_path="generation",
                    target_path="choices[0].message.content",
                    default_value=""
                ),
                TransformRule(
                    source_path="prompt_token_count",
                    target_path="usage.prompt_tokens",
                    default_value=0
                ),
                TransformRule(
                    source_path="generation_token_count",
                    target_path="usage.completion_tokens",
                    default_value=0
                )
            ]
        }

    def format_messages(self, messages: List[Dict[str, str]]) -> str:
        """Format OpenAI messages into a single string"""
        if not messages:
            return ""
        return " ".join(msg.get('content', '') for msg in messages)

    def prepare_request(self, provider: str, model: str, **kwargs) -> Dict[str, Any]:
        model_lower = model.lower()
        model_config_type = ModelConfigFactory.get_config(model)
        model_config = model_config_type()
        model_name = model_config.name if hasattr(model_config, "name") else model_lower

        # Transform input based on model type
        rules = self.input_rules.get(model_name, [])
        transformed_input = self.transform(kwargs, rules)

        return transformed_input

    def parse_response(
        self, provider: str, model: str, response: Dict[str, Any]
    ) -> Dict[str, Any]:
        model_config_type = ModelConfigFactory.get_config(model)
        model_config = model_config_type()
        model_name = model_config.name if hasattr(model_config, "name") else model.lower()

        # Transform output based on model type
        rules = self.output_rules.get(model_name, [])
        transformed_output = self.transform(response, rules)

        result = {
            "id": f"chatcmpl-{uuid.uuid4()}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": transformed_output.get("choices", []),
            "usage": transformed_output.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
        }

        # Ensure proper message structure
        if "choices" in result and result["choices"]:
            if "message" not in result["choices"][0]:
                result["choices"][0]["message"] = {
                    "role": "assistant",
                    "content": result["choices"][0].get("content", "")
                }
            else:
                result["choices"][0]["message"]["role"] = "assistant"
            
            if "finish_reason" not in result["choices"][0]:
                result["choices"][0]["finish_reason"] = "stop"
            if "index" not in result["choices"][0]:
                result["choices"][0]["index"] = 0

        # Calculate total tokens
        if "usage" in result:
            result["usage"]["total_tokens"] = (
                result["usage"].get("prompt_tokens", 0) +
                result["usage"].get("completion_tokens", 0)
            )

        return result

class ModelAdapterFactory:
    _adapters = {}

    @classmethod
    def register_adapter(cls, provider: str, model: str, adapter: Type[ModelAdapter]):
        if provider not in cls._adapters:
            cls._adapters[provider] = {}
        cls._adapters[provider][model] = adapter

    @classmethod
    def get_adapter(cls, provider: str, model: str) -> ModelAdapter:
        provider_lower = provider.lower().replace(" ", "")
        model_lower = model.lower()

        if provider_lower not in cls._adapters:
            raise ValueError(f"Unsupported provider: {provider}")

        if model_lower in cls._adapters[provider_lower]:
            return cls._adapters[provider_lower][model_lower]()
        elif "*" in cls._adapters[provider_lower]:
            return cls._adapters[provider_lower]["*"]()
        else:
            raise ValueError(f"Unsupported model for provider {provider}: {model}")

# Register adapters
ModelAdapterFactory.register_adapter("openai", "*", OpenAIAdapter)
ModelAdapterFactory.register_adapter("azureopenai", "*", AzureOpenAIAdapter)
ModelAdapterFactory.register_adapter("amazon", "*", BedrockAmazonAdapter)
