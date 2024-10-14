from abc import ABC, abstractmethod
from typing import Dict, Any, List
from javelin_sdk.models import QueryResponse, Choice, Message, Usage
import time
import uuid


class ModelAdapter(ABC):
    @abstractmethod
    def prepare_request(
        self, model: str, messages: List[Dict[str, str]], **kwargs
    ) -> Dict[str, Any]:
        pass


class OpenAIAdapter(ModelAdapter):
    def prepare_request(
        self, model: str, messages: List[Dict[str, str]], **kwargs
    ) -> Dict[str, Any]:
        return {"model": model, "messages": messages, **kwargs}


class AzureOpenAIAdapter(OpenAIAdapter):
    # Azure OpenAI uses the same format as OpenAI, so we can inherit from OpenAIAdapter
    pass


class BedrockAmazonAdapter(ModelAdapter):
    def prepare_request(
        self, model: str, messages: List[Dict[str, str]], **kwargs
    ) -> Dict[str, Any]:
        prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
        return {
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": kwargs.get("max_tokens", 512),
                "temperature": kwargs.get("temperature", 0.7),
                "topP": kwargs.get("top_p", 0.9),
            },
        }


class BedrockMetaAdapter(ModelAdapter):
    def prepare_request(
        self, model: str, messages: List[Dict[str, str]], **kwargs
    ) -> Dict[str, Any]:
        prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
        return {
            "prompt": prompt,
            "temperature": kwargs.get("temperature", 0.7),
            "top_p": kwargs.get("top_p", 0.9),
            "max_gen_len": kwargs.get("max_tokens", 512),
        }


class ModelAdapterFactory:
    @staticmethod
    def get_adapter(provider: str) -> ModelAdapter:
        if provider.lower().replace(" ", "") == "openai":
            return OpenAIAdapter()
        elif provider.lower().replace(" ", "") == "azureopenai":
            return AzureOpenAIAdapter()
        elif provider.lower().replace(" ", "") == "bedrockamazon":
            return BedrockAmazonAdapter()
        elif provider.lower().replace(" ", "") == "bedrockmeta":
            return BedrockMetaAdapter()
        else:
            raise ValueError(f"Unsupported provider: {provider}")
