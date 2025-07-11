import functools
import inspect
import json
import re
import asyncio
from typing import Any, Coroutine, Dict, Optional, Union
from urllib.parse import unquote, urljoin, urlparse, urlunparse

import httpx
from opentelemetry.semconv._incubating.attributes import gen_ai_attributes
from opentelemetry.trace import SpanKind, Status, StatusCode

from javelin_sdk.chat_completions import Chat, Completions, Embeddings
from javelin_sdk.models import HttpMethod, JavelinConfig, Request
from javelin_sdk.services.gateway_service import GatewayService
from javelin_sdk.services.modelspec_service import ModelSpecService
from javelin_sdk.services.provider_service import ProviderService
from javelin_sdk.services.route_service import RouteService
from javelin_sdk.services.secret_service import SecretService
from javelin_sdk.services.template_service import TemplateService
from javelin_sdk.services.trace_service import TraceService
from javelin_sdk.services.guardrails_service import GuardrailsService
from javelin_sdk.tracing_setup import configure_span_exporter

API_BASEURL = "https://api-dev.javelin.live"
API_BASE_PATH = "/v1"
API_TIMEOUT = 10


class JavelinRequestWrapper:
    """A wrapper around Botocore's request object to store additional metadata."""

    def __init__(self, original_request, span):
        self.original_request = original_request
        self.span = span


class JavelinClient:
    BEDROCK_RUNTIME_OPERATIONS = frozenset(
        {"InvokeModel", "InvokeModelWithResponseStream", "Converse", "ConverseStream"}
    )
    PROFILE_ARN_PATTERN = re.compile(
        r"/model/arn:aws:bedrock:[^:]+:\d+:application-inference-profile/[^/]+"
    )
    MODEL_ARN_PATTERN = re.compile(
        r"/model/arn:aws:bedrock:[^:]+::foundation-model/[^/]+"
    )

    # Mapping provider_name to well-known gen_ai.system values
    GEN_AI_SYSTEM_MAPPING = {
        "openai": "openai",
        "azureopenai": "az.ai.openai",
        "bedrock": "aws.bedrock",
        "gemini": "gemini",
        "deepseek": "deepseek",
        "cohere": "cohere",
        "mistral_ai": "mistral_ai",
        "anthropic": "anthropic",
        "vertex_ai": "vertex_ai",
        "perplexity": "perplexity",
        "groq": "groq",
        "ibm": "ibm.watsonx.ai",
        "xai": "xai",
    }

    # Mapping method names to well-known operation names
    GEN_AI_OPERATION_MAPPING = {
        "chat.completions.create": "chat",
        "completions.create": "text_completion",
        "embeddings.create": "embeddings",
        "images.generate": "image_generation",
        "images.edit": "image_editing",
        "images.create_variation": "image_variation",
    }

    def __init__(self, config: JavelinConfig) -> None:
        self.config = config
        self.base_url = urljoin(config.base_url, config.api_version or "/v1")

        self._headers = {"x-javelin-apikey": config.javelin_api_key}
        if config.llm_api_key:
            self._headers["Authorization"] = f"Bearer {config.llm_api_key}"
        if config.javelin_virtualapikey:
            self._headers["x-javelin-virtualapikey"] = config.javelin_virtualapikey
        self._client = None
        self._aclient = None
        self.bedrock_client = None
        self.bedrock_runtime_client = None
        self.bedrock_session = None
        self.default_bedrock_route = None
        self.use_default_bedrock_route = False
        self.client_is_async = None
        self.openai_base_url = None

        self.gateway_service = GatewayService(self)
        self.provider_service = ProviderService(self)
        self.route_service = RouteService(self)
        self.secret_service = SecretService(self)
        self.template_service = TemplateService(self)
        self.trace_service = TraceService(self)
        self.modelspec_service = ModelSpecService(self)
        self.guardrails_service = GuardrailsService(self)

        self.chat = Chat(self)
        self.completions = Completions(self)
        self.embeddings = Embeddings(self)

        self.tracer = configure_span_exporter()

        self.patched_clients: set = set()  # Track already patched clients
        self.patched_methods: set = set()  # Track already patched methods

        self.original_methods: dict = {}

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

    @staticmethod
    def set_span_attribute_if_not_none(span, key, value):
        """Helper function to set span attributes only if the value is not None."""
        if value is not None:
            span.set_attribute(key, value)

    @staticmethod
    def add_event_with_attributes(span, event_name, attributes):
        """Helper function to add events only with non-None attributes."""
        filtered_attributes = {k: v for k, v in attributes.items() if v is not None}
        if filtered_attributes:  # Add event only if there are valid attributes
            span.add_event(name=event_name, attributes=filtered_attributes)

    def _setup_client_headers(
        self, openai_client: Any, provider_name: str, route_name: Optional[str] = None
    ) -> None:
        """Setup client headers and base URL."""
        # Store the OpenAI base URL
        self.openai_base_url = openai_client.base_url

        # Point the OpenAI client to Javelin's base URL
        openai_client.base_url = f"{self.base_url}"

        if not hasattr(openai_client, "_custom_headers"):
            openai_client._custom_headers = {}
        openai_client._custom_headers.update(self._headers)

        base_url_str = str(self.openai_base_url).rstrip(
            "/"
        )  # Remove trailing slash if present

        # Update Javelin headers into the client's _custom_headers
        openai_client._custom_headers["x-javelin-provider"] = base_url_str
        openai_client._custom_headers["x-javelin-route"] = route_name

    def _store_original_methods(self, openai_client: Any, provider_name: str) -> None:
        """Store original methods for the provider."""
        if provider_name not in self.original_methods:
            self.original_methods[provider_name] = {
                "chat_completions_create": openai_client.chat.completions.create,
                "completions_create": openai_client.completions.create,
                "embeddings_create": openai_client.embeddings.create,
                "images_generate": openai_client.images.generate,
                "images_edit": openai_client.images.edit,
                "images_create_variation": openai_client.images.create_variation,
            }

    def _create_patched_method(
        self,
        method_name: str,
        original_method: Any,
        openai_client: Any,
        provider_name: str,
    ) -> Any:
        """Create a patched method with tracing and header updates."""
        if inspect.iscoroutinefunction(original_method):

            async def async_patched_method(*args, **kwargs):
                return await self._execute_with_tracing(
                    original_method,
                    method_name,
                    args,
                    kwargs,
                    openai_client,
                    provider_name,
                )

            return async_patched_method
        else:

            def sync_patched_method(*args, **kwargs):
                return self._execute_with_tracing(
                    original_method,
                    method_name,
                    args,
                    kwargs,
                    openai_client,
                    provider_name,
                )

            return sync_patched_method

    def _execute_with_tracing(
        self,
        original_method: Any,
        method_name: str,
        args: tuple,
        kwargs: dict,
        openai_client: Any,
        provider_name: str,
    ) -> Any:
        """Execute method with tracing and span attributes."""
        model = kwargs.get("model")

        if model and hasattr(openai_client, "_custom_headers"):
            openai_client._custom_headers["x-javelin-model"] = model

        # Use well-known operation names, fallback to method_name if not mapped
        operation_name = self.GEN_AI_OPERATION_MAPPING.get(method_name, method_name)
        system_name = self.GEN_AI_SYSTEM_MAPPING.get(provider_name, provider_name)
        span_name = f"{operation_name} {model}"

        async def _async_execution(span):
            response = await original_method(*args, **kwargs)
            self._capture_response_details(span, response, kwargs, system_name)
            return response

        def _sync_execution(span):
            response = original_method(*args, **kwargs)
            self._capture_response_details(span, response, kwargs, system_name)
            return response

        # Only create spans if tracing is enabled
        if self.tracer:
            with self.tracer.start_as_current_span(
                span_name, kind=SpanKind.CLIENT
            ) as span:
                self._set_span_attributes(
                    span, system_name, operation_name, model, kwargs
                )
                try:
                    if inspect.iscoroutinefunction(original_method):
                        return asyncio.run(_async_execution(span))
                    else:
                        return _sync_execution(span)
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.set_attribute("is_exception", True)
                    raise
        else:
            # Tracing is disabled
            if inspect.iscoroutinefunction(original_method):
                return asyncio.run(original_method(*args, **kwargs))
            else:
                return original_method(*args, **kwargs)

    def _set_span_attributes(
        self,
        span: Any,
        system_name: str,
        operation_name: str,
        model: Optional[str],
        kwargs: dict,
    ) -> None:
        """Set span attributes for the request."""
        span.set_attribute(gen_ai_attributes.GEN_AI_SYSTEM, system_name)
        span.set_attribute(gen_ai_attributes.GEN_AI_OPERATION_NAME, operation_name)
        if model:
            span.set_attribute(gen_ai_attributes.GEN_AI_REQUEST_MODEL, model)

        # Request attributes
        JavelinClient.set_span_attribute_if_not_none(
            span,
            gen_ai_attributes.GEN_AI_REQUEST_MAX_TOKENS,
            kwargs.get("max_completion_tokens"),
        )
        JavelinClient.set_span_attribute_if_not_none(
            span,
            gen_ai_attributes.GEN_AI_REQUEST_PRESENCE_PENALTY,
            kwargs.get("presence_penalty"),
        )
        JavelinClient.set_span_attribute_if_not_none(
            span,
            gen_ai_attributes.GEN_AI_REQUEST_FREQUENCY_PENALTY,
            kwargs.get("frequency_penalty"),
        )
        JavelinClient.set_span_attribute_if_not_none(
            span,
            gen_ai_attributes.GEN_AI_REQUEST_STOP_SEQUENCES,
            json.dumps(kwargs.get("stop", [])) if kwargs.get("stop") else None,
        )
        JavelinClient.set_span_attribute_if_not_none(
            span,
            gen_ai_attributes.GEN_AI_REQUEST_TEMPERATURE,
            kwargs.get("temperature"),
        )
        JavelinClient.set_span_attribute_if_not_none(
            span, gen_ai_attributes.GEN_AI_REQUEST_TOP_K, kwargs.get("top_k")
        )
        JavelinClient.set_span_attribute_if_not_none(
            span, gen_ai_attributes.GEN_AI_REQUEST_TOP_P, kwargs.get("top_p")
        )

    def _capture_response_details(
        self, span: Any, response: Any, kwargs: dict, system_name: str
    ) -> None:
        """Capture response details and set span attributes."""
        try:
            response_data = self._extract_response_data(response)
            if response_data is None:
                span.set_attribute("javelin.response.body", str(response))
                return

            self._set_response_attributes(span, response_data, kwargs, system_name)

        except Exception as e:
            span.set_attribute("javelin.response.body", str(response))
            span.set_attribute("javelin.error", str(e))

    def _extract_from_to_dict(self, response: Any) -> Optional[dict]:
        try:
            response_data = response.to_dict()
            return response_data if response_data else None
        except Exception:
            return None

    def _extract_from_model_dump(self, response: Any) -> Optional[dict]:
        try:
            return response.model_dump()
        except Exception:
            return None

    def _extract_from_dict_method(self, response: Any) -> Optional[dict]:
        try:
            return response.dict()
        except Exception as e:
            print(f"dict() failed: {e}")
            return None

    def _extract_from_dict(self, response: Any) -> Optional[dict]:
        return response if isinstance(response, dict) else None

    def _extract_from_stream(self, response: Any) -> Optional[dict]:
        return self._handle_streaming_response(response)

    def _extract_from_json_str(self, response: Any) -> Optional[dict]:
        try:
            return json.loads(str(response))
        except (TypeError, ValueError):
            return None

    def _extract_response_data(self, response: Any) -> Optional[dict]:
        """Extract response data from various response types."""
        if hasattr(response, "to_dict"):
            return self._extract_from_to_dict(response)
        elif hasattr(response, "model_dump"):
            return self._extract_from_model_dump(response)
        elif hasattr(response, "dict"):
            return self._extract_from_dict_method(response)
        elif isinstance(response, dict):
            return self._extract_from_dict(response)
        elif hasattr(response, "__iter__") and not isinstance(
            response, (str, bytes, dict, list)
        ):
            return self._extract_from_stream(response)
        else:
            return self._extract_from_json_str(response)

    def _handle_streaming_response(self, response: Any) -> dict:
        """Handle streaming response and accumulate text."""
        response_data = {
            "object": "thread.message.delta",
            "streamed_text": "",
        }

        for index, chunk in enumerate(response):
            if hasattr(chunk, "to_dict"):
                chunk = chunk.to_dict()

            if not isinstance(chunk, dict):
                continue

            choices = chunk.get("choices", [])
            if not choices:
                continue

            delta_dict = choices[0].get("delta", {})
            streamed_text = delta_dict.get("content", "")
            response_data["streamed_text"] += streamed_text

        return response_data

    def _set_response_attributes(
        self, span: Any, response_data: dict, kwargs: dict, system_name: str
    ) -> None:
        """Set response attributes on the span."""
        # Set basic response attributes
        JavelinClient.set_span_attribute_if_not_none(
            span, gen_ai_attributes.GEN_AI_RESPONSE_MODEL, response_data.get("model")
        )
        JavelinClient.set_span_attribute_if_not_none(
            span, gen_ai_attributes.GEN_AI_RESPONSE_ID, response_data.get("id")
        )
        JavelinClient.set_span_attribute_if_not_none(
            span,
            gen_ai_attributes.GEN_AI_OPENAI_REQUEST_SERVICE_TIER,
            response_data.get("service_tier"),
        )
        JavelinClient.set_span_attribute_if_not_none(
            span,
            gen_ai_attributes.GEN_AI_OPENAI_RESPONSE_SYSTEM_FINGERPRINT,
            response_data.get("system_fingerprint"),
        )

        # Finish reasons for choices
        finish_reasons = [
            choice.get("finish_reason")
            for choice in response_data.get("choices", [])
            if choice.get("finish_reason")
        ]
        JavelinClient.set_span_attribute_if_not_none(
            span,
            gen_ai_attributes.GEN_AI_RESPONSE_FINISH_REASONS,
            json.dumps(finish_reasons) if finish_reasons else None,
        )

        # Token usage
        usage = response_data.get("usage", {})
        JavelinClient.set_span_attribute_if_not_none(
            span,
            gen_ai_attributes.GEN_AI_USAGE_INPUT_TOKENS,
            usage.get("prompt_tokens"),
        )
        JavelinClient.set_span_attribute_if_not_none(
            span,
            gen_ai_attributes.GEN_AI_USAGE_OUTPUT_TOKENS,
            usage.get("completion_tokens"),
        )

        # System message event
        system_message = next(
            (
                msg.get("content")
                for msg in kwargs.get("messages", [])
                if msg.get("role") == "system"
            ),
            None,
        )
        JavelinClient.add_event_with_attributes(
            span,
            "gen_ai.system.message",
            {"gen_ai.system": system_name, "content": system_message},
        )

        # User message event
        user_message = next(
            (
                msg.get("content")
                for msg in kwargs.get("messages", [])
                if msg.get("role") == "user"
            ),
            None,
        )
        JavelinClient.add_event_with_attributes(
            span,
            "gen_ai.user.message",
            {"gen_ai.system": system_name, "content": user_message},
        )

        # Choice events
        choices = response_data.get("choices", [])
        for index, choice in enumerate(choices):
            choice_attributes = {"gen_ai.system": system_name, "index": index}
            message = choice.pop("message", {})
            choice.update(message)

            for key, value in choice.items():
                if isinstance(value, (dict, list)):
                    value = json.dumps(value)
                choice_attributes[key] = value if value is not None else None

            JavelinClient.add_event_with_attributes(
                span, "gen_ai.choice", choice_attributes
            )

    def register_provider(
        self, openai_client: Any, provider_name: str, route_name: Optional[str] = None
    ) -> Any:
        """
        Generalized function to register OpenAI, Azure OpenAI, and Gemini clients.

        Additionally sets:
            - openai_client.base_url to self.base_url
            - openai_client._custom_headers to include self._headers
        """
        client_id = id(openai_client)
        if client_id in self.patched_clients:
            print(f"Client {client_id} already patched")
            return openai_client  # Skip if already patched

        self.patched_clients.add(client_id)  # Mark as patched

        # Setup client headers and base URL
        self._setup_client_headers(openai_client, provider_name, route_name)

        # Store original methods
        self._store_original_methods(openai_client, provider_name)

        # Patch methods with tracing and header updates
        def get_nested_attr(obj, attr_path):
            attrs = attr_path.split(".")
            for attr in attrs:
                obj = getattr(obj, attr)
            return obj

        for method_name in [
            "chat.completions.create",
            "completions.create",
            "embeddings.create",
        ]:
            method_ref = get_nested_attr(openai_client, method_name)
            method_id = id(method_ref)

            if method_id in self.patched_methods:
                continue  # Skip if already patched

            original_method = self.original_methods[provider_name][
                method_name.replace(".", "_")
            ]
            patched_method = self._create_patched_method(
                method_name, original_method, openai_client, provider_name
            )

            parent_attr, method_attr = method_name.rsplit(".", 1)
            parent_obj = get_nested_attr(openai_client, parent_attr)
            setattr(parent_obj, method_attr, patched_method)

            self.patched_methods.add(method_id)

        return openai_client

    def register_openai(
        self, openai_client: Any, route_name: Optional[str] = None
    ) -> Any:
        return self.register_provider(
            openai_client, provider_name="openai", route_name=route_name
        )

    def register_azureopenai(
        self, openai_client: Any, route_name: Optional[str] = None
    ) -> Any:
        return self.register_provider(
            openai_client, provider_name="azureopenai", route_name=route_name
        )

    def register_gemini(
        self, openai_client: Any, route_name: Optional[str] = None
    ) -> Any:
        return self.register_provider(
            openai_client, provider_name="gemini", route_name=route_name
        )

    def register_deepseek(
        self, openai_client: Any, route_name: Optional[str] = None
    ) -> Any:
        return self.register_provider(
            openai_client, provider_name="deepseek", route_name=route_name
        )

    def _bedrock_set_clients(
        self, bedrock_runtime_client, bedrock_client, bedrock_session
    ):
        if bedrock_session is not None:
            self.bedrock_session = bedrock_session
            self.bedrock_client = bedrock_session.client("bedrock")
            self.bedrock_runtime_client = bedrock_session.client("bedrock-runtime")
        else:
            if bedrock_runtime_client is None:
                raise AssertionError("Bedrock Runtime client cannot be None")
            self.bedrock_client = bedrock_client
            self.bedrock_session = bedrock_session
            self.bedrock_runtime_client = bedrock_runtime_client

    def _bedrock_validate_client(self, bedrock_runtime_client):
        if not all(
            [
                hasattr(bedrock_runtime_client, "meta"),
                hasattr(bedrock_runtime_client.meta, "service_model"),
                getattr(bedrock_runtime_client.meta.service_model, "service_name", None)
                == "bedrock-runtime",
            ]
        ):
            raise AssertionError(
                "Invalid client type. Expected boto3 bedrock-runtime client, got: "
                f"{type(bedrock_runtime_client).__name__}"
            )

    def _bedrock_add_custom_headers(self, request: Any, **kwargs) -> None:
        request.headers.update(self._headers)

    def _bedrock_before_call(self, **kwargs):
        if self.tracer is None:
            return  # If no tracer, skip
        context = kwargs.get("context")
        if context is None:
            print("DEBUG: No context. Cannot store OTel span.")
            return
        event_name = kwargs.get("event_name", "")
        operation_name = event_name.split(".")[-1] if event_name else "Unknown"
        span = self.tracer.start_span(operation_name, kind=SpanKind.CLIENT)
        context["javelin_request_wrapper"] = JavelinRequestWrapper(None, span)
        print(f"DEBUG: Span created for {operation_name}")

    def _bedrock_after_call(self, **kwargs):
        context = kwargs.get("context")
        if not context:
            print("DEBUG: No context. Cannot retrieve OTel span.")
            return
        wrapper = context.get("javelin_request_wrapper")
        if not wrapper:
            print("DEBUG: No wrapped request object found in context.")
            return
        span = getattr(wrapper, "span", None)
        if not span:
            print("DEBUG: No span found in the wrapper.")
            return
        http_response = kwargs.get("http_response")
        if http_response is not None and hasattr(http_response, "status_code"):
            if http_response.status_code >= 400:
                span.set_status(
                    Status(StatusCode.ERROR, "HTTP %d" % http_response.status_code)
                )
            else:
                span.set_status(
                    Status(StatusCode.OK, "HTTP %d" % http_response.status_code)
                )
        print(f"DEBUG: Ending span: {span.name}")
        span.end()

    @functools.lru_cache()
    def _bedrock_get_inference_model(
        self, inference_profile_identifier: str
    ) -> Optional[str]:
        try:
            if self.bedrock_client:
                response = self.bedrock_client.get_inference_profile(
                    inferenceProfileIdentifier=inference_profile_identifier
                )
                model_identifier = response["models"][0]["modelArn"]
                foundation_model_response = self.bedrock_client.get_foundation_model(
                    modelIdentifier=model_identifier
                )
                model_id = foundation_model_response["modelDetails"]["modelId"]
                return model_id
        except Exception:
            pass
        return None

    @functools.lru_cache()
    def _bedrock_get_foundation_model(self, model_identifier: str) -> Optional[str]:
        try:
            if self.bedrock_client:
                response = self.bedrock_client.get_foundation_model(
                    modelIdentifier=model_identifier
                )
                return response["modelDetails"]["modelId"]
        except Exception:
            pass
        return None

    def _bedrock_override_endpoint_url(self, request: Any, **kwargs) -> None:
        try:
            original_url = urlparse(request.url)
            base_url = f"{original_url.scheme}://{original_url.netloc}"
            request.headers["x-javelin-provider"] = base_url
            if self.use_default_bedrock_route and self.default_bedrock_route:
                request.headers["x-javelin-route"] = self.default_bedrock_route
            path = original_url.path
            path = unquote(path)
            model_id = None
            match = re.match(self.PROFILE_ARN_PATTERN, path)
            if match:
                model_id = self._bedrock_get_inference_model(
                    match.group(0).replace("/model/", "")
                )
            elif re.match(self.MODEL_ARN_PATTERN, path):
                match = re.match(self.MODEL_ARN_PATTERN, path)
                if match:
                    model_id = self._bedrock_get_foundation_model(
                        match.group(0).replace("/model/", "")
                    )
            if model_id is None:
                path = path.replace("/model/", "")
                end_index = path.rfind("/")
                path = path[:end_index]
                model_id = path.replace("/model/", "")
            if model_id:
                model_id = re.sub(r"-\d{8}(?=-)", "", model_id)
                request.headers["x-javelin-model"] = model_id
            parsed_base = urlparse(self.base_url)
            updated_url = original_url._replace(
                scheme=parsed_base.scheme,
                netloc=parsed_base.netloc,
                path=f"/v1{original_url.path}",
            )
            request.url = urlunparse(updated_url)
        except Exception as e:
            print(f"Failed to override endpoint URL: {str(e)}")
            pass

    def _bedrock_register_event_handlers(self):
        for op in self.BEDROCK_RUNTIME_OPERATIONS:
            event_name_before_send = f"before-send.bedrock-runtime.{op}"
            event_name_before_call = f"before-call.bedrock-runtime.{op}"
            event_name_after_call = f"after-call.bedrock-runtime.{op}"
            if self.bedrock_runtime_client and hasattr(
                self.bedrock_runtime_client, "meta"
            ):
                self.bedrock_runtime_client.meta.events.register(
                    event_name_before_send, self._bedrock_add_custom_headers
                )
                self.bedrock_runtime_client.meta.events.register(
                    event_name_before_send, self._bedrock_override_endpoint_url
                )
                self.bedrock_runtime_client.meta.events.register(
                    event_name_before_call, self._bedrock_before_call
                )
                self.bedrock_runtime_client.meta.events.register(
                    event_name_after_call, self._bedrock_after_call
                )

    def register_bedrock(
        self,
        bedrock_runtime_client: Any,
        bedrock_client: Any = None,
        bedrock_session: Any = None,
        route_name: Optional[str] = None,
    ) -> None:
        self._bedrock_set_clients(
            bedrock_runtime_client, bedrock_client, bedrock_session
        )
        if not route_name:
            route_name = "awsbedrock"
        if route_name is not None:
            self.use_default_bedrock_route = True
            self.default_bedrock_route = str(route_name)
        self._bedrock_validate_client(self.bedrock_runtime_client)
        self._bedrock_register_event_handlers()

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
            is_model_specs=request.is_model_specs,
            is_reload=request.is_reload,
            univ_model=request.univ_model_config,
            guardrail=request.guardrail,
            list_guardrails=request.list_guardrails,
        )
        headers = {**self._headers, **(request.headers or {})}
        return url, headers

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

    def _send_request_sync(self, request: Request) -> httpx.Response:
        result = self._core_send_request(self.client, request)
        if isinstance(result, httpx.Response):
            return result
        else:
            raise RuntimeError("Expected sync response but got async")

    async def _send_request_async(self, request: Request) -> httpx.Response:
        result = self._core_send_request(self.aclient, request)
        if isinstance(result, httpx.Response):
            return result
        elif hasattr(result, "__await__"):
            return await result
        else:
            raise RuntimeError("Expected async response but got sync")

    def _url_for_model_specs(self, url_parts):
        url_parts.extend(["admin", "modelspec"])

    def _url_for_query(self, url_parts, route_name):
        url_parts.append("query")
        if route_name is not None:
            url_parts.append(route_name)

    def _url_for_gateway(self, url_parts, gateway_name):
        url_parts.extend(["admin", "gateways"])
        if gateway_name != "###":
            url_parts.append(gateway_name)

    def _url_for_provider(
        self, url_parts, provider_name, is_reload, is_transformation_rules
    ):
        if is_reload:
            url_parts.extend(["providers"])
        else:
            url_parts.extend(["admin", "providers"])
        if provider_name != "###":
            url_parts.append(str(provider_name))
        if is_transformation_rules:
            url_parts.append("transformation-rules")

    def _url_for_route(self, url_parts, route_name, is_reload):
        if is_reload:
            url_parts.extend(["routes"])
        else:
            url_parts.extend(["admin", "routes"])
        if route_name and route_name != "###":
            url_parts.append(route_name)

    def _url_for_secret(self, url_parts, provider_name, secret_name, is_reload):
        if is_reload:
            url_parts.extend(["secrets"])
        else:
            url_parts.extend(["admin", "providers"])
        if provider_name != "###":
            url_parts.append(str(provider_name))
        url_parts.append("keyvault")
        if secret_name != "###":
            url_parts.append(str(secret_name))
        else:
            url_parts.append("keys")

    def _url_for_template(self, url_parts, template_name, is_reload):
        if is_reload:
            url_parts.extend(["processors", "dp", "templates"])
        else:
            url_parts.extend(["admin", "processors", "dp", "templates"])
        if template_name != "###":
            url_parts.append(template_name)

    def _url_for_trace(self, url_parts):
        url_parts.extend(["admin", "traces"])

    def _url_for_archive(self, url_parts, archive):
        url_parts.extend(["admin", "archives"])
        if archive != "###":
            url_parts.append(archive)

    def _url_for_guardrail(self, url_parts, guardrail):
        if guardrail == "all":
            url_parts.extend(["guardrails", "apply"])
        else:
            url_parts.extend(["guardrail", guardrail, "apply"])

    def _url_for_list_guardrails(self, url_parts):
        url_parts.extend(["guardrails", "list"])

    def _url_for_default(self, url_parts):
        url_parts.extend(["admin", "routes"])

    def _get_condition_checks(self):
        """Get a list of condition checks in priority order."""
        return [
            ("is_model_specs", "model_specs"),
            ("query", "query"),
            ("gateway_name", "gateway"),
            ("provider_name_without_secret", "provider"),
            ("route_name", "route"),
            ("secret_name", "secret"),
            ("template_name", "template"),
            ("trace", "trace"),
            ("archive", "archive"),
            ("guardrail", "guardrail"),
            ("list_guardrails", "list_guardrails"),
        ]

    def _check_condition(self, condition_name: str, kwargs: dict) -> bool:
        """Check if a specific condition is met."""
        if condition_name == "provider_name_without_secret":
            return bool(kwargs.get("provider_name") and not kwargs.get("secret_name"))
        return bool(kwargs.get(condition_name))

    def _check_primary_conditions(self, **kwargs) -> Optional[str]:
        """Check primary conditions that determine URL type."""
        for condition, url_type in self._get_condition_checks():
            if self._check_condition(condition, kwargs):
                return url_type
        return None

    def _determine_url_type(
        self,
        gateway_name: Optional[str] = "",
        provider_name: Optional[str] = "",
        route_name: Optional[str] = "",
        secret_name: Optional[str] = "",
        template_name: Optional[str] = "",
        trace: Optional[str] = "",
        query: bool = False,
        archive: Optional[str] = "",
        is_transformation_rules: bool = False,
        is_model_specs: bool = False,
        is_reload: bool = False,
        guardrail: Optional[str] = None,
        list_guardrails: bool = False,
    ) -> str:
        """Determine the URL type and return the appropriate method name."""
        url_type = self._check_primary_conditions(
            is_model_specs=is_model_specs,
            query=query,
            gateway_name=gateway_name,
            provider_name=provider_name,
            secret_name=secret_name,
            route_name=route_name,
            template_name=template_name,
            trace=trace,
            archive=archive,
            guardrail=guardrail,
            list_guardrails=list_guardrails,
        )
        return url_type if url_type else "default"

    def _get_url_builder_method(self, url_type: str):
        """Get the appropriate URL builder method based on URL type."""
        url_builders = {
            "model_specs": self._url_for_model_specs,
            "query": self._url_for_query,
            "gateway": self._url_for_gateway,
            "provider": self._url_for_provider,
            "route": self._url_for_route,
            "secret": self._url_for_secret,
            "template": self._url_for_template,
            "trace": self._url_for_trace,
            "archive": self._url_for_archive,
            "guardrail": self._url_for_guardrail,
            "list_guardrails": self._url_for_list_guardrails,
            "default": self._url_for_default,
        }
        return url_builders.get(url_type, self._url_for_default)

    def _build_url_parts(
        self,
        url_type: str,
        gateway_name: Optional[str] = "",
        provider_name: Optional[str] = "",
        route_name: Optional[str] = "",
        secret_name: Optional[str] = "",
        template_name: Optional[str] = "",
        trace: Optional[str] = "",
        archive: Optional[str] = "",
        is_reload: bool = False,
        is_transformation_rules: bool = False,
        guardrail: Optional[str] = None,
    ) -> list:
        """Build URL parts based on the determined URL type."""
        url_parts = [self.base_url]
        builder_method = self._get_url_builder_method(url_type)

        # Call the appropriate builder method with the right parameters
        if url_type == "query":
            builder_method(url_parts, route_name)
        elif url_type == "gateway":
            builder_method(url_parts, gateway_name)
        elif url_type == "provider":
            builder_method(url_parts, provider_name, is_reload, is_transformation_rules)
        elif url_type == "route":
            builder_method(url_parts, route_name, is_reload)
        elif url_type == "secret":
            builder_method(url_parts, provider_name, secret_name, is_reload)
        elif url_type == "template":
            builder_method(url_parts, template_name, is_reload)
        elif url_type == "archive":
            builder_method(url_parts, archive)
        elif url_type == "guardrail":
            builder_method(url_parts, guardrail)
        else:
            builder_method(url_parts)

        return url_parts

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
        is_model_specs: bool = False,
        is_reload: bool = False,
        univ_model: Optional[Dict[str, Any]] = None,
        guardrail: Optional[str] = None,
        list_guardrails: bool = False,
    ) -> str:
        url_type = self._determine_url_type(
            gateway_name=gateway_name,
            provider_name=provider_name,
            route_name=route_name,
            secret_name=secret_name,
            template_name=template_name,
            trace=trace,
            query=query,
            archive=archive,
            is_transformation_rules=is_transformation_rules,
            is_model_specs=is_model_specs,
            is_reload=is_reload,
            guardrail=guardrail,
            list_guardrails=list_guardrails,
        )

        url_parts = self._build_url_parts(
            url_type=url_type,
            gateway_name=gateway_name,
            provider_name=provider_name,
            route_name=route_name,
            secret_name=secret_name,
            template_name=template_name,
            trace=trace,
            archive=archive,
            is_reload=is_reload,
            is_transformation_rules=is_transformation_rules,
            guardrail=guardrail,
        )

        url = "/".join(url_parts)

        if univ_model:
            endpoint_url = self.construct_endpoint_url(univ_model)
            url = urljoin(url, endpoint_url)

        if query_params:
            query_string = "&".join(f"{k}={v}" for k, v in query_params.items())
            url += f"?{query_string}"

        return url

    def _azureopenai_endpoint_url(
        self, base_url, provider_name, endpoint_type, deployment
    ):
        if endpoint_type == "chat":
            provider_base_url = f"{base_url}/{provider_name}/deployments/"
            return f"{provider_base_url}/{deployment}/chat/completions"
        elif endpoint_type == "completion":
            return f"{base_url}/{provider_name}/deployments/{deployment}/completions"
        elif endpoint_type == "embeddings":
            return f"{base_url}/{provider_name}/deployments/{deployment}/embeddings"
        return None

    def _bedrock_endpoint_url(self, base_url, model_id, endpoint_type):
        if endpoint_type == "invoke":
            return f"{base_url}/model/{model_id}/invoke"
        elif endpoint_type == "converse":
            return f"{base_url}/model/{model_id}/converse"
        elif endpoint_type == "invoke_stream":
            return f"{base_url}/model/{model_id}/invoke-with-response-stream"
        elif endpoint_type == "converse_stream":
            return f"{base_url}/model/{model_id}/converse-stream"
        return None

    def _anthropic_endpoint_url(self, base_url, endpoint_type):
        if endpoint_type == "messages":
            return f"{base_url}/model/messages"
        elif endpoint_type == "complete":
            return f"{base_url}/model/complete"
        return None

    def _openai_compatible_endpoint_url(self, base_url, provider_name, endpoint_type):
        if endpoint_type == "chat":
            return f"{base_url}/{provider_name}/chat/completions"
        elif endpoint_type == "completion":
            return f"{base_url}/{provider_name}/completions"
        elif endpoint_type == "embeddings":
            return f"{base_url}/{provider_name}/embeddings"
        return None

    def construct_endpoint_url(self, request_model: Dict[str, Any]) -> str:
        base_url = self.base_url
        provider_name = request_model.get("provider_name")
        endpoint_type = request_model.get("endpoint_type")
        deployment = request_model.get("deployment")
        model_id = request_model.get("model_id")
        if not provider_name:
            raise ValueError("Provider name is not specified in the request model.")
        if provider_name == "azureopenai" and deployment:
            url = self._azureopenai_endpoint_url(
                base_url, provider_name, endpoint_type, deployment
            )
            if url:
                return url
        elif provider_name == "bedrock" and model_id:
            url = self._bedrock_endpoint_url(base_url, model_id, endpoint_type)
            if url:
                return url
        elif provider_name == "anthropic":
            url = self._anthropic_endpoint_url(base_url, endpoint_type)
            if url:
                return url
        else:
            url = self._openai_compatible_endpoint_url(
                base_url, provider_name, endpoint_type
            )
            if url:
                return url
        raise ValueError("Invalid request model configuration")

    def set_headers(self, headers: Dict[str, str]) -> None:
        """
        Set or update headers for the client.

        Args:
            headers (Dict[str, str]): A dictionary of headers to set or update.
        """
        self._headers.update(headers)
