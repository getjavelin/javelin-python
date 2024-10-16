from abc import ABC, abstractmethod
from typing import Dict, Any, List, Union, Optional
from javelin_sdk.models import QueryResponse, Choice, Message, Usage
import time
import uuid


class ModelAdapter(ABC):
    @abstractmethod
    def prepare_request(
        self, messages: List[Dict[str, str]], model: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def prepare_completion_request(
        self, prompt: str, model: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        pass


class OpenAIAdapter(ModelAdapter):
    def prepare_request(
        self, messages: List[Dict[str, str]], model: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        request = {"messages": messages}
        if model:
            request["model"] = model
        request.update(kwargs)
        return request

    def prepare_completion_request(
        self, prompt: str, model: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        request = {"prompt": prompt}
        if model:
            request["model"] = model
        request.update(kwargs)
        return request

    def parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        choices = [
            Choice(
                index=choice.get("index"),
                message={
                    "role": choice.get("message", {}).get("role"),
                    "content": choice.get("message", {}).get("content"),
                },
                finish_reason=choice.get("finish_reason"),
            )
            for choice in response.get("choices", [])
        ]

        usage = Usage(
            prompt_tokens=response.get("usage", {}).get("prompt_tokens"),
            completion_tokens=response.get("usage", {}).get("completion_tokens"),
            total_tokens=response.get("usage", {}).get("total_tokens"),
        )

        return QueryResponse(
            id=response.get("id", str(uuid.uuid4())),
            object=response.get("object", "chat.completion"),
            created=response.get("created", int(time.time())),
            model=response.get("model", ""),
            choices=choices,
            usage=usage,
        ).dict()


class AzureOpenAIAdapter(OpenAIAdapter):
    # Azure OpenAI uses the same format as OpenAI, so we can inherit from OpenAIAdapter
    pass


class BedrockAmazonAdapter(ModelAdapter):
    def prepare_request(
        self, messages: List[Dict[str, str]], model: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
        return self.prepare_completion_request(prompt, model, **kwargs)

    def prepare_completion_request(
        self, prompt: str, model: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        request = {
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": kwargs.get("max_tokens", 512),
                "temperature": kwargs.get("temperature", 0.7),
                "topP": kwargs.get("top_p", 0.9),
            },
        }
        return request

    def parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        choices = [
            Choice(
                index=0,
                message={
                    "role": "assistant",
                    "content": response.get("results", [{}])[0].get("outputText", ""),
                },
                finish_reason=response.get("results", [{}])[0]
                .get("completionReason", "")
                .lower(),
            )
        ]

        usage = Usage(
            prompt_tokens=response.get("inputTextTokenCount", 0),
            completion_tokens=response.get("results", [{}])[0].get("tokenCount", 0),
            total_tokens=response.get("inputTextTokenCount", 0)
            + response.get("results", [{}])[0].get("tokenCount", 0),
        )

        return QueryResponse(
            id=f"chatcmpl-{uuid.uuid4()}",
            object="chat.completion",
            created=int(time.time()),
            model=response.get("javelin", {}).get("model_name", ""),
            choices=choices,
            usage=usage,
        ).dict()


class BedrockMetaAdapter(ModelAdapter):
    def prepare_request(
        self, messages: List[Dict[str, str]], model: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
        return self.prepare_completion_request(prompt, model, **kwargs)

    def prepare_completion_request(
        self, prompt: str, model: Optional[str] = None, **kwargs
    ) -> QueryResponse:
        request = {
            "prompt": prompt,
            "temperature": kwargs.get("temperature", 0.7),
            "top_p": kwargs.get("top_p", 0.9),
            "max_gen_len": kwargs.get("max_tokens", 512),
        }
        return request

    def parse_response(self, response: Dict[str, Any]) -> QueryResponse:
        choices = [
            Choice(
                index=0,
                message={
                    "role": "assistant",
                    "content": response.get("generation", ""),
                },
                finish_reason=response.get("stop_reason", "").lower(),
            )
        ]

        usage = Usage(
            prompt_tokens=response.get("prompt_token_count", 0),
            completion_tokens=response.get("generation_token_count", 0),
            total_tokens=response.get("prompt_token_count", 0)
            + response.get("generation_token_count", 0),
        )

        return QueryResponse(
            id=f"chatcmpl-{uuid.uuid4()}",
            object="chat.completion",
            created=int(time.time()),
            model=response.get("javelin", {}).get("model_name", ""),
            choices=choices,
            usage=usage,
        ).dict()


class ModelAdapterFactory:
    @staticmethod
    def get_adapter(provider: str, model: str) -> ModelAdapter:
        provider_lower = provider.lower().replace(" ", "")
        if provider_lower == "openai":
            return OpenAIAdapter()
        elif provider_lower == "azureopenai":
            return AzureOpenAIAdapter()
        elif provider_lower == "amazon":
            return (
                BedrockMetaAdapter()
                if "llama" in model.lower()
                else BedrockAmazonAdapter()
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")
