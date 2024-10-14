from abc import ABC, abstractmethod
from typing import Dict, Any, List
from javelin_sdk.models import QueryResponse, Choice, Message, Usage
import time
import uuid

class ModelAdapter(ABC):
    @abstractmethod
    def prepare_request(self, model: str, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        pass

    @abstractmethod
    def parse_response(self, response: Dict[str, Any]) -> QueryResponse:
        pass

class OpenAIAdapter(ModelAdapter):
    def prepare_request(self, model: str, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        return {
            "model": model,
            "messages": messages,
            **kwargs
        }

    def parse_response(self, response: Dict[str, Any]) -> QueryResponse:
        return QueryResponse(**response)

class AzureOpenAIAdapter(OpenAIAdapter):
    # Azure OpenAI uses the same format as OpenAI, so we can inherit from OpenAIAdapter
    pass

class BedrockAmazonAdapter(ModelAdapter):
    def prepare_request(self, model: str, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
        return {
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": kwargs.get("max_tokens", 100),
                "stopSequences": kwargs.get("stop", []),
                "temperature": kwargs.get("temperature", 0.7),
                "topP": kwargs.get("top_p", 1.0)
            }
        }

    def parse_response(self, response: Dict[str, Any]) -> QueryResponse:
        output_text = response.get("results", [{}])[0].get("outputText", "")
        return QueryResponse(
            choices=[Choice(
                finish_reason="stop",
                index=0,
                message=Message(
                    content=output_text,
                    role="assistant"
                )
            )],
            created=int(time.time()),
            id=str(uuid.uuid4()),
            model="bedrock-amazon",
            object="chat.completion",
            usage=Usage(
                completion_tokens=len(output_text.split()),
                prompt_tokens=response.get("inputTextTokenCount", 0),
                total_tokens=len(output_text.split()) + response.get("inputTextTokenCount", 0)
            )
        )

class BedrockMetaAdapter(ModelAdapter):
    def prepare_request(self, model: str, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
        return {
            "prompt": prompt,
            "max_gen_len": kwargs.get("max_tokens", 100),
            "temperature": kwargs.get("temperature", 0.7),
            "top_p": kwargs.get("top_p", 0.9)
        }

    def parse_response(self, response: Dict[str, Any]) -> QueryResponse:
        generation = response.get("generation", "")
        return QueryResponse(
            choices=[Choice(
                finish_reason=response.get("stop_reason", "stop"),
                index=0,
                message=Message(
                    content=generation,
                    role="assistant"
                )
            )],
            created=int(time.time()),
            id=str(uuid.uuid4()),
            model="bedrock-meta",
            object="chat.completion",
            usage=Usage(
                completion_tokens=len(generation.split()),
                prompt_tokens=0,  # We don't have this information
                total_tokens=len(generation.split())
            )
        )

class ModelAdapterFactory:
    @staticmethod
    def get_adapter(provider: str) -> ModelAdapter:
        if provider.lower() == "openai":
            return OpenAIAdapter()
        elif provider.lower() == "azureopenai":
            return AzureOpenAIAdapter()
        elif provider.lower() == "bedrockamazon":
            return BedrockAmazonAdapter()
        elif provider.lower() == "bedrockmeta":
            return BedrockMetaAdapter()
        else:
            raise ValueError(f"Unsupported provider: {provider}")
