from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class InputSchema(BaseModel):
    pass


class OutputSchema(BaseModel):
    pass


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class TokenDetails(BaseModel):
    reasoning_tokens: Optional[int] = None
    cached_tokens: Optional[int] = None


class OpenAIInputSchema(InputSchema):
    messages: List[Dict[str, str]]
    model: str
    temperature: float = Field(default=0.7)
    max_tokens: Optional[int] = None


class OpenAIOutputSchema(OutputSchema):
    choices: List[Dict[str, Any]]
    usage: Usage


class BedrockLlamaInputSchema(InputSchema):
    prompt: str
    max_gen_len: int = Field(default=50)
    temperature: float = Field(default=0.7)
    top_p: float = Field(default=0.9)


class BedrockLlamaOutputSchema(OutputSchema):
    generation: str
    generation_token_count: int
    prompt_token_count: int
    stop_reason: str


class BedrockTitanInputSchema(InputSchema):
    inputText: str
    textGenerationConfig: Dict[str, Any]


class BedrockTitanOutputSchema(OutputSchema):
    inputTextTokenCount: int
    results: List[Dict[str, Any]]
