from typing import List, Optional
from pydantic import BaseModel, Field


class Budget(BaseModel):
    enabled: Optional[bool] = Field(
        default=None, description="Whether the budget feature is enabled"
    )
    annual: Optional[int] = Field(default=None, description="Annual budget limit")
    monthly: Optional[int] = Field(default=None, description="Monthly budget limit")
    weekly: Optional[int] = Field(default=None, description="Weekly budget limit")
    currency: Optional[str] = Field(default=None, description="Currency for the budget")


class Dlp(BaseModel):
    enabled: Optional[bool] = Field(default=None, description="Whether DLP is enabled")
    strategy: Optional[str] = Field(default=None, description="DLP strategy")
    action: Optional[str] = Field(default=None, description="DLP action to take")


class RouteConfig(BaseModel):
    organization: Optional[str] = Field(
        default=None, description="Name of the organization"
    )
    owner: Optional[str] = Field(default=None, description="Owner of the route")
    rate_limit: Optional[int] = Field(
        default=None, description="Rate limit for the route"
    )
    retries: Optional[int] = Field(
        default=None, description="Number of retries for the route"
    )
    archive: Optional[bool] = Field(
        default=None, description="Whether archiving is enabled"
    )
    retention: Optional[int] = Field(default=None, description="Data retention period")
    budget: Optional[Budget] = Field(default=None, description="Budget configuration")
    dlp: Optional[Dlp] = Field(default=None, description="DLP configuration")


class Model(BaseModel):
    name: str = Field(default=None, description="Name of the model")
    provider: str = Field(default=None, description="Provider of the model")
    suffix: str = Field(default=None, description="Suffix of the model")
    weight: Optional[float] = Field(default=None, description="Weight of the model")


class Route(BaseModel):
    name: str = Field(default=None, description="Name of the route")
    type: str = Field(default=None, description="Type of the route")
    enabled: Optional[bool] = Field(
        default=True, description="Whether the route is enabled"
    )
    models: List[Model] = Field(default=[], description="List of models for the route")
    config: RouteConfig = Field(default=None, description="Configuration for the route")


class Routes(BaseModel):
    routes: List[Route] = Field(default=[], description="List of routes")


class Message(BaseModel):
    content: str = Field(..., description="Content of the message")
    role: str = Field(..., description="Role in the message")


class Usage(BaseModel):
    completion_tokens: int = Field(
        ..., description="Number of tokens used in the completion"
    )
    prompt_tokens: int = Field(..., description="Number of tokens used in the prompt")
    total_tokens: int = Field(..., description="Total number of tokens used")


class Choice(BaseModel):
    finish_reason: str = Field(..., description="Reason for the completion finish")
    index: int = Field(..., description="Index of the choice")
    message: Message = Field(..., description="Message details")


class QueryResponse(BaseModel):
    choices: List[Choice] = Field(..., description="List of choices")
    created: int = Field(..., description="Creation timestamp")
    id: str = Field(..., description="Unique identifier of the response")
    model: str = Field(..., description="Model identifier")
    object: str = Field(..., description="Object type")
    system_fingerprint: Optional[str] = Field(
        None, description="System fingerprint if available"
    )
    usage: Usage = Field(..., description="Usage details")
