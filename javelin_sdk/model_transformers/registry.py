from typing import Any, Dict, Type

from .schemas import (
    BedrockLlamaInputSchema,
    BedrockLlamaOutputSchema,
    BedrockTitanInputSchema,
    BedrockTitanOutputSchema,
    InputSchema,
    OpenAIInputSchema,
    OpenAIOutputSchema,
    OutputSchema,
)


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


# Register OpenAI schemas
SchemaRegistry.register_schemas("openai", "*", OpenAIInputSchema, OpenAIOutputSchema)
SchemaRegistry.register_schemas(
    "azureopenai", "*", OpenAIInputSchema, OpenAIOutputSchema
)

# Register Bedrock schemas
SchemaRegistry.register_schemas(
    "amazon", "llama", BedrockLlamaInputSchema, BedrockLlamaOutputSchema
)
SchemaRegistry.register_schemas(
    "amazon", "titan", BedrockTitanInputSchema, BedrockTitanOutputSchema
)
