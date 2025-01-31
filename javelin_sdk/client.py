from typing import Any, Coroutine, Dict, Optional, Union
from urllib.parse import urljoin, urlparse, urlunparse

import httpx

from javelin_sdk.chat_completions import Chat, Completions
from javelin_sdk.models import HttpMethod, JavelinConfig, Request
from javelin_sdk.services.gateway_service import GatewayService
from javelin_sdk.services.provider_service import ProviderService
from javelin_sdk.services.route_service import RouteService
from javelin_sdk.services.secret_service import SecretService
from javelin_sdk.services.template_service import TemplateService
from javelin_sdk.services.trace_service import TraceService

API_BASEURL = "https://api-dev.javelin.live"
API_BASE_PATH = "/v1"
API_TIMEOUT = 10


class JavelinClient:
    BEDROCK_RUNTIME_OPERATIONS = frozenset(
        {"InvokeModel", "InvokeModelWithResponseStream", "Converse", "ConverseStream"}
    )

    def __init__(self, config: JavelinConfig) -> None:
        self.config = config
        self.base_url = urljoin(config.base_url, config.api_version or "/v1")
        self._headers = {
            "x-api-key": config.javelin_api_key,
        }
        if config.llm_api_key:
            self._headers["Authorization"] = f"Bearer {config.llm_api_key}"
        if config.javelin_virtualapikey:
            self._headers["x-javelin-virtualapikey"] = config.javelin_virtualapikey
        self._client = None
        self._aclient = None

        self.gateway_service = GatewayService(self)
        self.provider_service = ProviderService(self)
        self.route_service = RouteService(self)
        self.secret_service = SecretService(self)
        self.template_service = TemplateService(self)
        self.trace_service = TraceService(self)

        self.chat = Chat(self)
        self.completions = Completions(self)

    @property
    def client(self):
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.base_url,
                headers=self._headers,
                timeout=self.config.timeout if self.config.timeout else API_TIMEOUT,
            )
        return self._client

    @property
    def aclient(self):
        if self._aclient is None:
            self._aclient = httpx.AsyncClient(
                base_url=self.base_url, headers=self._headers, timeout=API_TIMEOUT
            )
        return self._aclient

    async def __aenter__(self) -> "JavelinClient":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.aclose()

    def __enter__(self) -> "JavelinClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    async def aclose(self):
        if self._aclient:
            await self._aclient.aclose()

    def close(self):
        if self._client:
            self._client.close()

    def register_bedrock_runtime(self, client: Any) -> Any:
        """
        Register an AWS Bedrock Runtime client
        for request interception and modification.

        Args:
            client: A boto3 bedrock-runtime client instance
        Returns:
            The modified boto3 client with registered event handlers
        Raises:
            AssertionError: If client is None or not a valid bedrock-runtime client
            ValueError: If URL parsing/manipulation fails

        Example:
            >>> bedrock = boto3.client('bedrock-runtime')
            >>> modified_client = javelin_client.register_bedrock_client(bedrock)
            >>> javelin_client.register_bedrock_client(bedrock)
            >>> bedrock.invoke_model(
        """
        if client is None:
            raise AssertionError("Bedrock Runtime client cannot be None")

        # Validate client type and attributes
        if not all(
            [
                hasattr(client, "meta"),
                hasattr(client.meta, "service_model"),
                getattr(client.meta.service_model, "service_name", None)
                == "bedrock-runtime",
            ]
        ):
            raise AssertionError(
                "Invalid client type. Expected boto3 bedrock-runtime client, got: "
                f"{type(client).__name__}"
            )

        def add_custom_headers(request: Any, **kwargs) -> None:
            """Add Javelin headers to each request."""
            request.headers.update(self._headers)

        def override_endpoint_url(request: Any, **kwargs) -> None:
            """Redirect Bedrock operations to Javelin endpoint while preserving path/query."""
            try:
                original_url = urlparse(request.url)
                redirected_url = original_url._replace(
                    scheme="https",
                    netloc=urlparse(self.base_url).netloc,
                    path=f"/v1{original_url.path}",
                )
                request.url = urlunparse(redirected_url)
            except Exception as e:
                raise ValueError(f"Failed to override endpoint URL: {str(e)}") from e

        # Register header modification & URL override for specific operations
        for op in self.BEDROCK_RUNTIME_OPERATIONS:
            event_name = f"before-send.bedrock-runtime.{op}"
            client.meta.events.register(event_name, add_custom_headers)
            client.meta.events.register(event_name, override_endpoint_url)

        return client

    def _prepare_request(self, request: Request) -> tuple:
        url = self._construct_url(
            gateway_name=request.gateway,
            provider_name=request.provider,
            route_name=request.route,
            secret_name=request.secret,
            template_name=request.template,
            trace=request.trace,
            query=request.is_query,
            archive=request.archive,
            query_params=request.query_params,
            is_transformation_rules=request.is_transformation_rules,
            is_reload=request.is_reload,
        )
        headers = {**self._headers, **(request.headers or {})}
        return url, headers

    def _send_request_sync(self, request: Request) -> httpx.Response:
        return self._core_send_request(self.client, request)

    async def _send_request_async(self, request: Request) -> httpx.Response:
        return await self._core_send_request(self.aclient, request)

    def _core_send_request(
        self, client: Union[httpx.Client, httpx.AsyncClient], request: Request
    ) -> Union[httpx.Response, Coroutine[Any, Any, httpx.Response]]:
        url, headers = self._prepare_request(request)

        if request.method == HttpMethod.GET:
            return client.get(url, headers=headers)
        elif request.method == HttpMethod.POST:
            return client.post(url, json=request.data, headers=headers)
        elif request.method == HttpMethod.PUT:
            return client.put(url, json=request.data, headers=headers)
        elif request.method == HttpMethod.DELETE:
            return client.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {request.method}")

    def _construct_url(
        self,
        gateway_name: Optional[str] = "",
        provider_name: Optional[str] = "",
        route_name: Optional[str] = "",
        secret_name: Optional[str] = "",
        template_name: Optional[str] = "",
        trace: Optional[str] = "",
        query: bool = False,
        archive: Optional[str] = "",
        query_params: Optional[Dict[str, Any]] = None,
        is_transformation_rules: bool = False,
        is_reload: bool = False,
    ) -> str:
        url_parts = [self.base_url]

        if query:
            url_parts.append("query")
            if route_name is not None:
                url_parts.append(route_name)
        elif gateway_name:
            url_parts.extend(["admin", "gateways"])
            if gateway_name != "###":
                url_parts.append(gateway_name)
        elif provider_name and not secret_name:
            if is_reload:
                url_parts.extend(["providers"])
            else:
                url_parts.extend(["admin", "providers"])
            if provider_name != "###":
                url_parts.append(provider_name)
            if is_transformation_rules:
                url_parts.append("transformation-rules")
        elif route_name:
            if is_reload:
                url_parts.extend(["routes"])
            else:
                url_parts.extend(["admin", "routes"])
            if route_name != "###":
                url_parts.append(route_name)
        elif secret_name:
            if is_reload:
                url_parts.extend(["secrets"])
            else:
                url_parts.extend(["admin", "providers"])
            if provider_name != "###":
                url_parts.append(provider_name)
            url_parts.append("keyvault")
            if secret_name != "###":
                url_parts.append(secret_name)
            else:
                url_parts.append("keys")
        elif template_name:
            if is_reload:
                url_parts.extend(["processors", "dp", "templates"])
            else:
                url_parts.extend(["admin", "processors", "dp", "templates"])
            if template_name != "###":
                url_parts.append(template_name)
        elif trace:
            url_parts.extend(["admin", "traces"])
        elif archive:
            url_parts.extend(["admin", "archives"])
            if archive != "###":
                url_parts.append(archive)
        else:
            url_parts.extend(["admin", "routes"])

        url = "/".join(url_parts)

        if query_params:
            query_string = "&".join(f"{k}={v}" for k, v in query_params.items())
            url += f"?{query_string}"

        return url

    # Gateway methods
    create_gateway = lambda self, gateway: self.gateway_service.create_gateway(gateway)
    acreate_gateway = lambda self, gateway: self.gateway_service.acreate_gateway(
        gateway
    )
    get_gateway = lambda self, gateway_name: self.gateway_service.get_gateway(
        gateway_name
    )
    aget_gateway = lambda self, gateway_name: self.gateway_service.aget_gateway(
        gateway_name
    )
    list_gateways = lambda self: self.gateway_service.list_gateways()
    alist_gateways = lambda self: self.gateway_service.alist_gateways()
    update_gateway = lambda self, gateway: self.gateway_service.update_gateway(gateway)
    aupdate_gateway = lambda self, gateway: self.gateway_service.aupdate_gateway(
        gateway
    )
    delete_gateway = lambda self, gateway_name: self.gateway_service.delete_gateway(
        gateway_name
    )
    adelete_gateway = lambda self, gateway_name: self.gateway_service.adelete_gateway(
        gateway_name
    )

    # Provider methods
    create_provider = lambda self, provider: self.provider_service.create_provider(
        provider
    )
    acreate_provider = lambda self, provider: self.provider_service.acreate_provider(
        provider
    )
    get_provider = lambda self, provider_name: self.provider_service.get_provider(
        provider_name
    )
    aget_provider = lambda self, provider_name: self.provider_service.aget_provider(
        provider_name
    )
    list_providers = lambda self: self.provider_service.list_providers()
    alist_providers = lambda self: self.provider_service.alist_providers()
    update_provider = lambda self, provider: self.provider_service.update_provider(
        provider
    )
    aupdate_provider = lambda self, provider: self.provider_service.aupdate_provider(
        provider
    )
    delete_provider = lambda self, provider_name: self.provider_service.delete_provider(
        provider_name
    )
    adelete_provider = (
        lambda self, provider_name: self.provider_service.adelete_provider(
            provider_name
        )
    )
    alist_provider_secrets = (
        lambda self, provider_name: self.provider_service.alialist_provider_secrets(
            provider_name
        )
    )
    get_transformation_rules = lambda self, provider_name, model_name, endpoint: self.provider_service.get_transformation_rules(
        provider_name, model_name, endpoint
    )
    aget_transformation_rules = lambda self, provider_name, model_name, endpoint: self.provider_service.aget_transformation_rules(
        provider_name, model_name, endpoint
    )

    # Route methods
    create_route = lambda self, route: self.route_service.create_route(route)
    acreate_route = lambda self, route: self.route_service.acreate_route(route)
    get_route = lambda self, route_name: self.route_service.get_route(route_name)
    aget_route = lambda self, route_name: self.route_service.aget_route(route_name)
    list_routes = lambda self: self.route_service.list_routes()
    alist_routes = lambda self: self.route_service.alist_routes()
    update_route = lambda self, route: self.route_service.update_route(route)
    aupdate_route = lambda self, route: self.route_service.aupdate_route(route)
    delete_route = lambda self, route_name: self.route_service.delete_route(route_name)
    adelete_route = lambda self, route_name: self.route_service.adelete_route(
        route_name
    )
    query_route = lambda self, route_name, query_body, headers=None, stream=False, stream_response_path=None: self.route_service.query_route(
        route_name=route_name,
        query_body=query_body,
        headers=headers,
        stream=stream,
        stream_response_path=stream_response_path,
    )
    aquery_route = lambda self, route_name, query_body, headers=None, stream=False, stream_response_path=None: self.route_service.aquery_route(
        route_name, query_body, headers, stream, stream_response_path
    )
    query_llama = lambda self, route_name, query_body: self.route_service.query_llama(
        route_name, query_body
    )
    aquery_llama = lambda self, route_name, query_body: self.route_service.aquery_llama(
        route_name, query_body
    )

    # Secret methods
    create_secret = lambda self, secret: self.secret_service.create_secret(secret)
    acreate_secret = lambda self, secret: self.secret_service.acreate_secret(secret)
    get_secret = (
        lambda self, secret_name, provider_name: self.secret_service.get_secret(
            secret_name, provider_name
        )
    )
    aget_secret = (
        lambda self, secret_name, provider_name: self.secret_service.aget_secret(
            secret_name, provider_name
        )
    )
    list_secrets = lambda self: self.secret_service.list_secrets()
    alist_secrets = lambda self: self.secret_service.alist_secrets()
    update_secret = lambda self, secret: self.secret_service.update_secret(secret)
    aupdate_secret = lambda self, secret: self.secret_service.aupdate_secret(secret)
    delete_secret = (
        lambda self, secret_name, provider_name: self.secret_service.delete_secret(
            secret_name, provider_name
        )
    )
    adelete_secret = (
        lambda self, secret_name, provider_name: self.secret_service.adelete_secret(
            secret_name, provider_name
        )
    )

    # Template methods
    create_template = lambda self, template: self.template_service.create_template(
        template
    )
    acreate_template = lambda self, template: self.template_service.acreate_template(
        template
    )
    get_template = lambda self, template_name: self.template_service.get_template(
        template_name
    )
    aget_template = lambda self, template_name: self.template_service.aget_template(
        template_name
    )
    list_templates = lambda self: self.template_service.list_templates()
    alist_templates = lambda self: self.template_service.alist_templates()
    update_template = lambda self, template: self.template_service.update_template(
        template
    )
    aupdate_template = lambda self, template: self.template_service.aupdate_template(
        template
    )
    delete_template = lambda self, template_name: self.template_service.delete_template(
        template_name
    )
    adelete_template = (
        lambda self, template_name: self.template_service.adelete_template(
            template_name
        )
    )
    reload_data_protection = (
        lambda self, strategy_name: self.template_service.reload_data_protection(
            strategy_name
        )
    )
    areload_data_protection = (
        lambda self, strategy_name: self.template_service.areload_data_protection(
            strategy_name
        )
    )

    ## Traces methods
    get_traces = lambda self: self.trace_service.get_traces()
    aget_traces = lambda self: self.trace_service.aget_traces()

    # Archive methods
    def get_last_n_chronicle_records(self, archive_name: str, n: int) -> Dict[str, Any]:
        request = Request(
            method=HttpMethod.GET,
            archive=archive_name,
            query_params={"page": 1, "limit": n},
        )
        response = self._send_request_sync(request)
        return response

    async def aget_last_n_chronicle_records(
        self, archive_name: str, n: int
    ) -> Dict[str, Any]:
        request = Request(
            method=HttpMethod.GET,
            archive=archive_name,
            query_params={"page": 1, "limit": n},
        )
        response = await self._send_request_async(request)
        return response
