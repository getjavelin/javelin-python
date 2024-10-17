from abc import ABC, abstractmethod
from typing import Dict, Any, List, Union, Optional, Type
from javelin_sdk.models import QueryResponse, Choice, Message, Usage
import time
import uuid
from pydantic import BaseModel, Field, ValidationError


# Define common fields here.
class InputSchema(BaseModel):
    pass


class OutputSchema(BaseModel):
    pass


class SchemaRegistry:
    _input_schemas: Dict[str, Dict[str, Type[InputSchema]]] = {}
    _output_schemas: Dict[str, Dict[str, Type[OutputSchema]]] = {}

    @classmethod
    def register_schemas(
        cls,
        provider: str,
        model: str,
        input_schema: Type[InputSchema],
        output_schema: Type[OutputSchema],
    ):
        if provider not in cls._input_schemas:
            cls._input_schemas[provider] = {}
            cls._output_schemas[provider] = {}
        cls._input_schemas[provider][model] = input_schema
        cls._output_schemas[provider][model] = output_schema

    @classmethod
    def get_input_schema(cls, provider: str, model: str) -> Type[InputSchema]:
        return cls._get_schema(cls._input_schemas, provider, model)

    @classmethod
    def get_output_schema(cls, provider: str, model: str) -> Type[OutputSchema]:
        return cls._get_schema(cls._output_schemas, provider, model)

    @classmethod
    def _get_schema(
        cls, schema_dict: Dict[str, Dict[str, Any]], provider: str, model: str
    ) -> Any:
        provider_lower = provider.lower().replace(" ", "")
        model_lower = model.lower()

        if provider_lower not in schema_dict:
            raise ValueError(f"Unsupported provider: {provider}")

        if model_lower in schema_dict[provider_lower]:
            return schema_dict[provider_lower][model_lower]
        elif "*" in schema_dict[provider_lower]:
            return schema_dict[provider_lower]["*"]
        else:
            raise ValueError(f"Unsupported model for provider {provider}: {model}")


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
        # Remove 'model' from kwargs if it exists
        kwargs.pop("model", None)
        validated_input = input_schema(model=model, **kwargs)
        return self._prepare_request_impl(validated_input.dict())

    def _prepare_request_impl(self, validated_input: Dict[str, Any]) -> Dict[str, Any]:
        # OpenAI-specific request preparation
        prepared_request = {
            "model": validated_input["model"],
            "messages": validated_input["messages"],
            "temperature": validated_input.get("temperature", 0.7),
            "max_tokens": validated_input.get("max_tokens"),
        }
        # Remove None values
        return {k: v for k, v in prepared_request.items() if v is not None}

    def parse_response(
        self, provider: str, model: str, response: Dict[str, Any]
    ) -> Dict[str, Any]:
        parsed_response = self._parse_response_impl(response)
        output_schema = SchemaRegistry.get_output_schema(provider, model)
        try:
            validated_output = output_schema(**parsed_response)
            return validated_output.model_dump()
        except ValidationError as e:
            print(f"Validation error: {e}")
            # If validation fails, return the original parsed response
            return parsed_response

    def _parse_response_impl(self, response: Dict[str, Any]) -> Dict[str, Any]:
        # OpenAI-specific response parsing
        parsed_response = {
            "choices": response.get("choices", []),
            "usage": {
                "prompt_tokens": response.get("usage", {}).get("prompt_tokens", 0),
                "completion_tokens": response.get("usage", {}).get(
                    "completion_tokens", 0
                ),
                "total_tokens": response.get("usage", {}).get("total_tokens", 0),
                "completion_tokens_details": response.get("usage", {}).get(
                    "completion_tokens_details", {}
                ),
                "prompt_tokens_details": response.get("usage", {}).get(
                    "prompt_tokens_details", {}
                ),
            },
        }
        return parsed_response


class AzureOpenAIAdapter(OpenAIAdapter):
    pass


class BedrockAmazonAdapter(ModelAdapter):
    def prepare_request(self, provider: str, model: str, **kwargs) -> Dict[str, Any]:
        if "messages" in kwargs:
            return self.prepare_chat_request(provider, model, **kwargs)
        else:
            return self.prepare_completion_request(provider, model, **kwargs)

    def prepare_chat_request(
        self, provider: str, model: str, **kwargs
    ) -> Dict[str, Any]:
        prompt = "\n".join(
            [f"{msg['role']}: {msg['content']}" for msg in kwargs.get("messages", [])]
        )
        return self.prepare_completion_request(provider, model, prompt=prompt, **kwargs)

    def prepare_completion_request(
        self, provider: str, model: str, **kwargs
    ) -> Dict[str, Any]:
        if "llama" in model.lower():
            request = {
                "prompt": kwargs.get("prompt", ""),
                "max_gen_len": kwargs.get("max_tokens", 512),
                "temperature": kwargs.get("temperature", 0.7),
                "top_p": kwargs.get("top_p", 0.9),
            }
        elif "claude" in model.lower():
            request = {
                "prompt": kwargs.get("prompt", ""),
                "max_tokens_to_sample": kwargs.get("max_tokens", 512),
                "temperature": kwargs.get("temperature", 0.7),
                "top_p": kwargs.get("top_p", 0.9),
            }
        else:
            request = {
                "inputText": kwargs.get("prompt", ""),
                "textGenerationConfig": {
                    "maxTokenCount": kwargs.get("max_tokens", 512),
                    "temperature": kwargs.get("temperature", 0.7),
                    "topP": kwargs.get("top_p", 0.9),
                },
            }
        return request

    def parse_response(
        self, provider: str, model: str, response: Dict[str, Any]
    ) -> Dict[str, Any]:
        if "llama" in model.lower():
            content = response.get("generation", "")
        elif "claude" in model.lower():
            content = response.get("completion", "")
        else:  # Default for other Amazon models like Titan
            content = response.get("results", [{}])[0].get("outputText", "")

        choices = [
            Choice(
                index=0,
                message={
                    "role": "assistant",
                    "content": content,
                },
                finish_reason="stop",  # Bedrock doesn't provide this, so we default to "stop"
            )
        ]

        # Use the token counts provided in the response, or estimate if not available
        usage = {
            "prompt_tokens": response.get("prompt_token_count", 0),
            "completion_tokens": response.get(
                "generation_token_count", len(content.split())
            ),
            "total_tokens": response.get("prompt_token_count", 0)
            + response.get("generation_token_count", len(content.split())),
        }

        return QueryResponse(
            id=f"chatcmpl-{uuid.uuid4()}",
            object="chat.completion",
            created=int(time.time()),
            model=model,
            choices=choices,
            usage=usage,
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


class OpenAIInputSchema(BaseModel):
    messages: List[Dict[str, str]]
    model: str
    temperature: float = Field(default=0.7)
    max_tokens: Optional[int] = None


class OpenAIOutputSchema(BaseModel):
    choices: List[Dict[str, Any]]
    usage: Usage


SchemaRegistry.register_schemas("openai", "*", OpenAIInputSchema, OpenAIOutputSchema)
SchemaRegistry.register_schemas(
    "azureopenai", "*", OpenAIInputSchema, OpenAIOutputSchema
)


class TokenDetails(BaseModel):
    reasoning_tokens: Optional[int] = None
    cached_tokens: Optional[int] = None


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    completion_tokens_details: Optional[TokenDetails] = None
    prompt_tokens_details: Optional[TokenDetails] = None
