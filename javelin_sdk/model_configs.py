from typing import Any, Dict


class ModelConfig:
    @staticmethod
    def get_input_mapping() -> Dict[str, str]:
        return {
            "max_tokens": "max_tokens",
            "temperature": "temperature",
            "top_p": "top_p",
        }


class BedrockConfig(ModelConfig):
    @staticmethod
    def get_input_mapping() -> Dict[str, str]:
        return {**ModelConfig.get_input_mapping(), "max_tokens": "maxTokens"}


class BedrockTitanConfig(BedrockConfig):
    def __init__(self):
        self.name = "titan"

    @staticmethod
    def get_input_mapping() -> Dict[str, str]:
        return {**BedrockConfig.get_input_mapping(), "max_tokens": "maxTokenCount"}


class BedrockLlamaConfig(BedrockConfig):
    def __init__(self):
        self.name = "llama"

    @staticmethod
    def get_input_mapping() -> Dict[str, str]:
        return {**BedrockConfig.get_input_mapping(), "max_tokens": "max_gen_len"}


class ModelConfigFactory:
    TITAN_MODELS = ["amazon.titan-text-express-v1"]
    LLAMA_MODELS = ["meta.llama3-8b-instruct-v1:0"]

    @staticmethod
    def get_config(model: str) -> type[ModelConfig]:
        if model in ModelConfigFactory.TITAN_MODELS:
            return BedrockTitanConfig
        elif model in ModelConfigFactory.LLAMA_MODELS:
            return BedrockLlamaConfig
        else:
            return BedrockConfig
