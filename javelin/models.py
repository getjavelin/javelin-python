from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class RouteConfig(BaseModel):
    rate_limit: Optional[int] = Field(optional=True, default=None)
    owner: Optional[str] = Field(optional=True, default=None)
    organization: Optional[str] = Field(optional=True, default=None)
    archive: Optional[bool] = Field(optional=True, default=None)
    retries: Optional[int] = Field(optional=True, default=0)
    budget: Optional[int] = Field(optional=True, default=0)

class Model(BaseModel):
    name: str = Field(optional=False, default=None)
    provider: str = Field(optional=False, default=None)
    suffix: str = Field(optional=False, default=None)

class Route(BaseModel):
    name: str= Field(optional=False, default=None)
    model: Model= Field(optional=False, default=None)
    config: RouteConfig= Field(optional=False, default=None)

class Routes(BaseModel):
    routes: List[Route]

class Message(BaseModel):
    role: str = Field(optional=False, default=None)
    content: str = Field(optional=False, default=None)

class QueryBody(BaseModel):
    data: Dict[str, Any]

class ResponseMetaData(BaseModel):
    route_name: str = Field(None, description="Name of the route")
    model: str = Field(None, description="Model identifier")
    archive_enabled: bool = Field(None, description="Flag for archive enabled")
    input_tokens: Optional[int] = Field(None, description="Number of input tokens")
    output_tokens: Optional[int] = Field(None, description="Number of output tokens")
    total_tokens: Optional[int] = Field(None, description="Total number of tokens")
    usage: Optional[float] = Field(None, description="Usage metric")
    retries: Optional[int] = Field(None, description="Number of retries")
    throttled: Optional[bool] = Field(None, description="Request was throttled by gateway")

class LLMResponse(BaseModel):
    llm_response: Dict[str, Any]
    metadata: ResponseMetaData

class Response(BaseModel):
    llm_response: List[LLMResponse]
    metadata: ResponseMetaData
