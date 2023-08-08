from typing import Optional, List
from pydantic import BaseModel, Field

class RouteConfig(BaseModel):
    rate_limit: Optional[int] = Field(optional=True, default=None)
    owner: Optional[str] = Field(optional=True, default=None)
    organization: Optional[str] = Field(optional=True, default=None)
    archive: Optional[bool] = Field(optional=True, default=None)
    retries: Optional[int] = Field(optional=True, default=0)

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
    model: Optional[str]
    prompt: Optional[str]
    messages: Optional[List[Message]]
    text: Optional[List[str]]

class RouteResponse(BaseModel):
    route: Route