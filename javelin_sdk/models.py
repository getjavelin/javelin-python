from enum import Enum, auto
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from javelin_sdk.exceptions import UnauthorizedError


class GatewayConfig(BaseModel):
    buid: Optional[str] = Field(
        default=None,
        description="Business Unit ID (BUID) uniquely identifies the business unit associated with this gateway configuration",
    )
    base_url: Optional[str] = Field(
        default=None,
        description="The foundational URL where all API requests are directed. It acts as the root from which endpoint paths are extended",
    )
    api_key_value: Optional[str] = Field(
        default=None,
        description="The API key used for authenticating requests to the API endpoints specified by the base_url",
    )
    organization_id: Optional[str] = Field(
        default=None, description="Unique identifier of the organization"
    )
    system_namespace: Optional[str] = Field(
        default=None,
        description="A unique namespace within the system to prevent naming conflicts and to organize resources logically",
    )


class Gateway(BaseModel):
    gateway_id: str = Field(
        default=None, description="Unique identifier for the gateway"
    )
    name: str = Field(default=None, description="Name of the gateway")
    type: str = Field(
        default=None,
        description="The type of this gateway (e.g., development, staging, production)",
    )
    enabled: Optional[bool] = Field(
        default=True, description="Whether the gateway is enabled"
    )
    config: GatewayConfig = Field(
        default=None, description="Configuration for the gateway"
    )


class Gateways(BaseModel):
    gateways: List[Gateway] = Field(default=[], description="List of gateways")


class Budget(BaseModel):
    enabled: Optional[bool] = Field(
        None, description="Whether the budget feature is enabled"
    )
    daily: Optional[float] = Field(None, description="Daily budget limit")
    monthly: Optional[float] = Field(None, description="Monthly budget limit")
    weekly: Optional[float] = Field(None, description="Weekly budget limit")
    annual: Optional[float] = Field(None, description="Annual budget limit")
    currency: Optional[str] = Field(None, description="Currency for the budget")


class ContentTypes(BaseModel):
    operator: Optional[str] = Field(default=None, description="Content type operator")
    restriction: Optional[str] = Field(
        default=None, description="Content type restriction"
    )
    probability_threshold: Optional[float] = Field(
        default=None, description="Content type probability threshold"
    )


class Dlp(BaseModel):
    enabled: Optional[bool] = Field(default=None, description="Whether DLP is enabled")
    strategy: Optional[str] = Field(default=None, description="DLP strategy")
    action: Optional[str] = Field(default=None, description="DLP action to take")
    risk_analysis: Optional[str] = Field(
        default=None, description="Risk analysis configuration"
    )


class PromptSafety(BaseModel):
    enabled: Optional[bool] = Field(
        default=None, description="Whether prompt safety is enabled"
    )
    reject_prompt: Optional[str] = Field(
        default=None, description="Reject prompt for the route"
    )
    content_types: Optional[List[ContentTypes]] = Field(
        default=None, description="List of content types"
    )


class ContentFilter(BaseModel):
    enabled: Optional[bool] = Field(
        default=None, description="Whether content filter is enabled"
    )
    reject_prompt: Optional[str] = Field(
        default=None, description="Reject prompt for the route"
    )
    content_types: Optional[List[ContentTypes]] = Field(
        default=None, description="List of content types"
    )


class RouteConfig(BaseModel):
    rate_limit: Optional[int] = Field(
        default=None, description="Rate limit for the route"
    )
    owner: Optional[str] = Field(default=None, description="Owner of the route")
    organization: Optional[str] = Field(
        default=None, description="Organization associated with the route"
    )
    archive: Optional[bool] = Field(
        default=None, description="Whether archiving is enabled"
    )
    retries: Optional[int] = Field(
        default=None, description="Number of retries for the route"
    )
    llm_cache: bool = Field(False, description="Whether LLM cache is enabled")
    role_to_assume: Optional[str] = Field(
        None, description="Role to assume for the route"
    )
    enable_telemetry: Optional[bool] = Field(
        None, description="Whether telemetry is enabled"
    )
    retention: Optional[int] = Field(default=None, description="Data retention period")
    request_chain: Optional[Dict[str, Any]] = Field(
        None, description="Request chain configuration"
    )
    response_chain: Optional[Dict[str, Any]] = Field(
        None, description="Response chain configuration"
    )
    budget: Optional[Budget] = Field(default=None, description="Budget configuration")
    dlp: Optional[Dlp] = Field(default=None, description="DLP configuration")
    content_filter: Optional[ContentFilter] = Field(
        default=None, description="Content Filter Description"
    )
    prompt_safety: Optional[PromptSafety] = Field(
        default=None, description="Prompt Safety Description"
    )


class Model(BaseModel):
    name: str = Field(default=None, description="Name of the model")
    provider: str = Field(default=None, description="Provider of the model")
    suffix: str = Field(default=None, description="Suffix for the model")
    weight: Optional[int] = Field(default=None, description="Weight of the model")
    virtual_secret_name: Optional[str] = Field(None, description="Virtual secret name")
    fallback_enabled: Optional[bool] = Field(
        None, description="Whether fallback is enabled"
    )
    fallback_codes: Optional[List[int]] = Field(None, description="Fallback codes")


class Route(BaseModel):
    name: str = Field(default=None, description="Name of the route")
    type: str = Field(
        default=None, description="Type of the route chat, completion, etc"
    )
    enabled: Optional[bool] = Field(
        default=True, description="Whether the route is enabled"
    )
    models: List[Model] = Field(default=[], description="List of models for the route")
    config: RouteConfig = Field(default=None, description="Configuration for the route")


class Routes(BaseModel):
    routes: List[Route] = Field(default=[], description="List of routes")


class ArrayHandling(str, Enum):
    JOIN = "join"
    FIRST = "first"
    LAST = "last"
    FLATTEN = "flatten"


class TypeHint(str, Enum):
    STRING = "str"
    INTEGER = "int"
    FLOAT = "float"
    BOOLEAN = "bool"
    ARRAY = "array"
    OBJECT = "object"
    PASSTHROUGH = "passthrough"


class TransformRule(BaseModel):
    source_path: str
    target_path: str
    default_value: Any = None
    transform_function: Optional[str] = None
    conditions: Optional[List[str]] = None
    array_handling: Optional[ArrayHandling] = None
    type_hint: Optional[TypeHint] = None
    additional_data: Optional[Dict[str, Any]] = None


class ModelSpec(BaseModel):
    input_rules: List[TransformRule] = Field(
        default=[], description="Rules for input transformation"
    )
    output_rules: List[TransformRule] = Field(
        default=[], description="Rules for output transformation"
    )
    input_schema: Dict[str, Any] = Field(
        default={}, description="Input schema for validation"
    )
    output_schema: Dict[str, Any] = Field(
        default={}, description="Output schema for validation"
    )
    supported_features: List[str] = Field(
        default=[], description="List of supported features"
    )
    max_tokens: Optional[int] = Field(
        default=None, description="Maximum tokens supported"
    )
    default_parameters: Dict[str, Any] = Field(
        default={}, description="Default parameters"
    )


class ProviderConfig(BaseModel):
    api_base: str = Field(default=None, description="Base URL of the API")
    api_type: Optional[str] = Field(default=None, description="Type of the API")
    api_version: Optional[str] = Field(default=None, description="Version of the API")
    deployment_name: Optional[str] = Field(
        default=None, description="Name of the deployment"
    )
    organization: Optional[str] = Field(
        default=None, description="Name of the organization"
    )
    model_specs: Dict[str, ModelSpec] = Field(
        default={}, description="Model specifications"
    )

    class Config:
        protected_namespaces = ()


class Provider(BaseModel):
    name: str = Field(default=None, description="Name of the Provider")
    type: str = Field(default=None, description="Type of the Provider")
    enabled: Optional[bool] = Field(
        default=True, description="Whether the provider is enabled"
    )
    vault_enabled: Optional[bool] = Field(
        default=True, description="Whether the secrets vault is enabled"
    )
    config: ProviderConfig = Field(
        default=None, description="Configuration for the provider"
    )


class Providers(BaseModel):
    providers: List[Provider] = Field(default=[], description="List of providers")


class InfoType(BaseModel):
    name: str = Field(default=None, description="Name of the infoType")
    description: Optional[str] = Field(
        default=None, description="Description of the InfoType"
    )
    regex: Optional[str] = Field(default=None, description="Regex of the infoType")
    wordlist: Optional[List[str]] = Field(
        default=None,
        description="Optional word list field, corresponding to 'wordlist' in JSON",
    )


class Transformation(BaseModel):
    method: str = Field(
        default=None,
        description="Method of the transformation Mask, Redact, Replace, etc",
    )


class TemplateConfig(BaseModel):
    infoTypes: Optional[List[InfoType]] = Field(
        default=[], description="List of InfoTypes"
    )
    transformation: Optional[Transformation] = Field(
        default=None, description="Transformation to be used"
    )
    notify: Optional[bool] = Field(default=False, description="Whether to notify")
    reject: Optional[bool] = Field(default=False, description="Whether to reject")
    likelihood: Optional[str] = Field(
        default="Likely",
        description="indicate how likely it is that a piece of data matches infoTypes",
    )
    rejectPrompt: Optional[str] = Field(
        default=None, description="Prompt to be used for the route"
    )
    risk_analysis: Optional[str] = Field(
        default=None, description="Risk analysis configuration"
    )


class TemplateModel(BaseModel):
    name: str = Field(default=None, description="Name of the model")
    provider: str = Field(default=None, description="Provider of the model")
    suffix: str = Field(default=None, description="Suffix for the model")


class Template(BaseModel):
    name: str = Field(default=None, description="Name of the Template")
    description: str = Field(default=None, description="Description of the Template")
    type: str = Field(default=None, description="Type of the Template")
    enabled: Optional[bool] = Field(
        default=True, description="Whether the template is enabled"
    )
    models: List[TemplateModel] = Field(
        default=[], description="List of models for the template"
    )
    config: TemplateConfig = Field(
        default=None, description="Configuration for the template"
    )


class Templates(BaseModel):
    templates: List[Template] = Field(default=[], description="List of templates")


class Secret(BaseModel):
    api_key: str = Field(default=None, description="Key of the Secret")
    api_key_secret_name: str = Field(default=None, description="Name of the Secret")
    api_key_secret_key: str = Field(default=None, description="API Key of the Secret")
    api_key_secret_key_javelin: str = Field(
        default=None, description="Virtual API Key of the Secret"
    )
    provider_name: str = Field(default=None, description="Provider Name of the Secret")
    query_param_key: str = Field(
        default=None, description="Query Param Key of the Secret"
    )
    header_key: str = Field(default=None, description="Header Key of the Secret")
    group: str = Field(default=None, description="Group of the Secret")
    enabled: Optional[bool] = Field(
        default=True, description="Whether the secret is enabled"
    )

    def masked(self):
        """
        Return a version of the model where sensitive fields are masked.
        """
        return {
            "api_key": self.api_key,
            "api_key_secret_name": self.api_key_secret_name,
            "api_key_secret_key": "***MASKED***" if self.api_key_secret_key else None,
            "api_key_secret_key_javelin": (
                "***MASKED***" if self.api_key_secret_key_javelin else None
            ),
            "provider_name": self.provider_name,
            "query_param_key": self.query_param_key,
            "header_key": self.header_key,
            "group": self.group,
            "enabled": self.enabled,
        }


class Secrets(BaseModel):
    secrets: List[Secret] = Field(default=[], description="List of secrets")


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
    message: Dict[str, str] = Field(..., description="Message details")


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


class JavelinConfig(BaseModel):
    javelin_api_key: str = Field(..., description="Javelin API key")
    base_url: str = Field(
        default="https://api-dev.javelin.live",
        description="Base URL for the Javelin API",
    )
    javelin_virtualapikey: Optional[str] = Field(
        default=None, description="Virtual API key for Javelin"
    )
    llm_api_key: Optional[str] = Field(
        default=None, description="API key for the LLM provider"
    )
    api_version: Optional[str] = Field(default=None, description="API version")

    @field_validator("javelin_api_key")
    @classmethod
    def validate_api_key(cls, value: str) -> str:
        if not value:
            raise UnauthorizedError(
                response=None,
                message=(
                    "Please provide a valid Javelin API Key. "
                    "When you sign into Javelin, you can find your API Key in the "
                    "Account->Developer settings"
                ),
            )
        return value


class HttpMethod(Enum):
    GET = auto()
    POST = auto()
    PUT = auto()
    DELETE = auto()


class Request:
    def __init__(
        self,
        method: HttpMethod,
        gateway: Optional[str] = "",
        provider: Optional[str] = "",
        route: Optional[str] = "",
        secret: Optional[str] = "",
        template: Optional[str] = "",
        is_query: bool = False,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        archive: Optional[str] = "",
        query_params: Optional[Dict[str, Any]] = None,
        is_transformation_rules: bool = False,
        is_reload: bool = False,
    ):
        self.method = method
        self.gateway = gateway
        self.provider = provider
        self.route = route
        self.secret = secret
        self.template = template
        self.is_query = is_query
        self.data = data
        self.headers = headers
        self.archive = archive
        self.query_params = query_params
        self.is_transformation_rules = is_transformation_rules
        self.is_reload = is_reload


class Message(BaseModel):
    role: str
    content: str


class ChatCompletion(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]


class ModelConfig(BaseModel):
    provider: str
    name: str  # Changed from model_name to name
    api_base: Optional[str] = None
    api_key: Optional[str] = None

    class Config:
        protected_namespaces = ()  # This resolves the warning


class JavelinConfig(BaseModel):
    base_url: str = Field(default="https://api-dev.javelin.live")
    javelin_api_key: str
    javelin_virtualapikey: Optional[str] = None
    llm_api_key: Optional[str] = None
    api_version: Optional[str] = None


class RemoteModelSpec(BaseModel):
    provider: str
    model_name: str
    input_rules: List[Dict[str, Any]]
    output_rules: List[Dict[str, Any]]

    class Config:
        protected_namespaces = ()

    def to_model_spec(self) -> ModelSpec:
        return ModelSpec(
            input_rules=[TransformRule(**rule) for rule in self.input_rules],
            output_rules=[TransformRule(**rule) for rule in self.output_rules],
        )


class EndpointType(str, Enum):
    UNKNOWN = "unknown"
    CHAT = "chat"
    COMPLETION = "completion" 
    EMBED = "embed"
    INVOKE = "invoke"
    CONVERSE = "converse"
    STREAM = "stream"
    INVOKE_STREAM = "invoke_stream"
    CONVERSE_STREAM = "converse_stream"
    ALL = "all"
