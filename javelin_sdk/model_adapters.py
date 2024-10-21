import time
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, Union

from pydantic import BaseModel, Field, ValidationError

from javelin_sdk.models import Choice, Message, QueryResponse, Usage

from .model_configs import BedrockTitanConfig, ModelConfig, ModelConfigFactory
from .model_transformers import SchemaRegistry


# Define common fields here.
class InputSchema(BaseModel):
    pass


class OutputSchema(BaseModel):
    pass


class ModelAdapter(ABC):
    @abstractmethod
    def prepare_request(self, provider: str, model: str, **kwargs) -> Dict[str, Any]:
        pass

    @abstractmethod
    def parse_response(
        self, provider: str, model: str, response: Dict[str, Any]
    ) -> Dict[str, Any]:
        pass


class OpenAIAdapter(ModelAdapter):
    def prepare_request(self, provider: str, model: str, **kwargs) -> Dict[str, Any]:
        input_schema = SchemaRegistry.get_input_schema(provider, model)
        validated_input = input_schema(model=model, **kwargs)
        return validated_input.model_dump(exclude_none=True)

    def parse_response(
        self, provider: str, model: str, response: Dict[str, Any]
    ) -> Dict[str, Any]:
        output_schema = SchemaRegistry.get_output_schema(provider, model)
        try:
            validated_output = output_schema(**response)
            return validated_output.model_dump()
        except ValidationError as e:
            print(f"Validation error: {e}")


class AzureOpenAIAdapter(OpenAIAdapter):
    pass


class BedrockAmazonAdapter(ModelAdapter):
    def prepare_request(self, provider: str, model: str, **kwargs) -> Dict[str, Any]:
        model_lower = model.lower()
        model_config_type = ModelConfigFactory.get_config(model)
        model_config = model_config_type()

        # Use the model name from the config
        model_name = model_config.name if hasattr(model_config, "name") else model_lower

        input_schema = SchemaRegistry.get_input_schema(provider, model_name)

        # Handle both messages and prompt inputs
        if "messages" in kwargs:
            prompt = self._convert_messages_to_prompt(kwargs["messages"])
            kwargs["prompt"] = prompt
            del kwargs["messages"]
        elif "prompt" not in kwargs:
            raise ValueError("Either 'messages' or 'prompt' must be provided")

        model_input = self._map_to_model_input(kwargs, model_config)

        try:
            validated_input = input_schema(**model_input)
            return validated_input.model_dump(exclude_none=True)
        except ValidationError as e:
            print(f"Validation error: {e}")
            raise ValueError(f"Invalid input for model {model}: {e}")

    def _convert_messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        return "\n".join(f"{msg['role']}: {msg['content']}" for msg in messages)

    def _map_to_model_input(
        self, kwargs: Dict[str, Any], model_config: ModelConfig
    ) -> Dict[str, Any]:
        input_mapping = model_config.get_input_mapping()
        model_input = {
            model_param: kwargs.pop(generic_param)
            for generic_param, model_param in input_mapping.items()
            if generic_param in kwargs
        }

        if isinstance(model_config, BedrockTitanConfig):
            return {
                "inputText": kwargs.pop("prompt", ""),
                "textGenerationConfig": model_input,
            }

        model_input["prompt"] = kwargs.pop("prompt", "")
        model_input.update(kwargs)
        return model_input

    def parse_response(
        self, provider: str, model: str, response: Dict[str, Any]
    ) -> Dict[str, Any]:
        model_config_type = ModelConfigFactory.get_config(model)
        model_config = model_config_type()
        model_name = (
            model_config.name if hasattr(model_config, "name") else model.lower()
        )

        output_schema = SchemaRegistry.get_output_schema(provider, model_name)

        try:
            validated_output = output_schema(**response)
            parsed_response = validated_output.model_dump()

            content = (
                parsed_response.get("generation", "")
                if model_name == "llama"
                else (
                    parsed_response.get("results", [{}])[0].get("outputText", "")
                    if model_name == "titan"
                    else parsed_response.get("completion", "")
                )
            )

            choices = [
                Choice(
                    index=0,
                    message={"role": "assistant", "content": content},
                    finish_reason="stop",
                )
            ]

            usage = {
                "prompt_tokens": parsed_response.get("prompt_token_count", 0),
                "completion_tokens": parsed_response.get(
                    "generation_token_count", len(content.split())
                ),
                "total_tokens": parsed_response.get("prompt_token_count", 0)
                + parsed_response.get("generation_token_count", len(content.split())),
            }

            return QueryResponse(
                id=f"chatcmpl-{uuid.uuid4()}",
                object="chat.completion",
                created=int(time.time()),
                model=model,
                choices=choices,
                usage=usage,
            ).model_dump()

        except ValidationError as e:
            print(f"Validation error: {e}")
            # If validation fails, return a minimal valid response
            return QueryResponse(
                id=f"chatcmpl-{uuid.uuid4()}",
                object="chat.completion",
                created=int(time.time()),
                model=model,
                choices=[
                    Choice(
                        index=0,
                        message={
                            "role": "assistant",
                            "content": "Error in response validation",
                        },
                        finish_reason="stop",
                    )
                ],
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            ).model_dump()


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


ModelAdapterFactory.register_adapter("openai", "*", OpenAIAdapter)
ModelAdapterFactory.register_adapter("azureopenai", "*", AzureOpenAIAdapter)
ModelAdapterFactory.register_adapter("amazon", "*", BedrockAmazonAdapter)
