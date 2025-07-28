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

        self.patched_clients = set()  # Track already patched clients
        self.patched_methods = set()  # Track already patched methods

        self.original_methods = {}

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

    def _setup_client_headers(self, openai_client, route_name):
        """Setup client headers and base URL."""

        self.openai_base_url = openai_client.base_url

        openai_client.base_url = f"{self.base_url}"

        if not hasattr(openai_client, "_custom_headers"):
            openai_client._custom_headers = {}
        else:
            pass

        openai_client._custom_headers.update(self._headers)

        if route_name is not None:
            openai_client._custom_headers["x-javelin-route"] = route_name

        # Ensure the client uses the custom headers
        if hasattr(openai_client, "default_headers"):
            # Filter out None values and openai.Omit objects
            filtered_headers = {}
            for key, value in openai_client._custom_headers.items():
                if value is not None and not (
                    hasattr(value, "__class__") and value.__class__.__name__ == "Omit"
                ):
                    filtered_headers[key] = value
            openai_client.default_headers.update(filtered_headers)
        elif hasattr(openai_client, "_default_headers"):
            # Filter out None values and openai.Omit objects
            filtered_headers = {}
            for key, value in openai_client._custom_headers.items():
                if value is not None and not (
                    hasattr(value, "__class__") and value.__class__.__name__ == "Omit"
                ):
                    filtered_headers[key] = value
            openai_client._default_headers.update(filtered_headers)
        else:
            pass

    def _store_original_methods(self, openai_client, provider_name):
        """Store original methods for the provider if not already stored."""
        if provider_name not in self.original_methods:
            self.original_methods[provider_name] = {
                "chat_completions_create": openai_client.chat.completions.create,
                "completions_create": openai_client.completions.create,
                "embeddings_create": openai_client.embeddings.create,
                "images_generate": openai_client.images.generate,
                "images_edit": openai_client.images.edit,
                "images_create_variation": openai_client.images.create_variation,
            }

    def _create_patched_method(self, method_name, original_method, openai_client):
        """Create a patched method with tracing support."""
        if inspect.iscoroutinefunction(original_method):

            async def async_patched_method(*args, **kwargs):
                return await self._execute_with_tracing(
                    original_method, method_name, args, kwargs, openai_client
                )

            return async_patched_method
        else:

            def sync_patched_method(*args, **kwargs):
                return self._execute_with_tracing(
                    original_method, method_name, args, kwargs, openai_client
                )

            return sync_patched_method

    def _execute_with_tracing(
        self,
        original_method,
        method_name,
        args,
        kwargs,
        openai_client,
    ):
        """Execute method with tracing support."""
        model = kwargs.get("model")

        self._setup_custom_headers(openai_client, model)

        operation_name = self.GEN_AI_OPERATION_MAPPING.get(method_name, method_name)
        system_name = self.GEN_AI_SYSTEM_MAPPING.get(
            self.provider_name, self.provider_name
        )
        span_name = f"{operation_name} {model}"

        if self.tracer:
            return self._execute_with_tracer(
                original_method,
                args,
                kwargs,
                span_name,
                system_name,
                operation_name,
                model,
            )
        else:
            return self._execute_without_tracer(original_method, args, kwargs)

    def _setup_custom_headers(self, openai_client, model):
        """Setup custom headers for the OpenAI client."""
        if model and hasattr(openai_client, "_custom_headers"):
            openai_client._custom_headers["x-javelin-model"] = model

        if not hasattr(openai_client, "_custom_headers"):
            return

        filtered_headers = self._filter_custom_headers(openai_client._custom_headers)

        if hasattr(openai_client, "default_headers"):
            openai_client.default_headers.update(filtered_headers)
        elif hasattr(openai_client, "_default_headers"):
            openai_client._default_headers.update(filtered_headers)

    def _filter_custom_headers(self, custom_headers):
        """Filter out None values and openai.Omit objects from custom headers."""
        filtered_headers = {}
        for key, value in custom_headers.items():
            if value is not None and not self._is_omit_object(value):
                filtered_headers[key] = value
        return filtered_headers

    def _is_omit_object(self, value):
        """Check if value is an openai.Omit object."""
        return hasattr(value, "__class__") and value.__class__.__name__ == "Omit"

    def _execute_with_tracer(
        self,
        original_method,
        args,
        kwargs,
        span_name,
        system_name,
        operation_name,
        model,
    ):
        """Execute method with tracer enabled."""
        if self.tracer is None:
            return self._execute_without_tracer(original_method, args, kwargs)

        with self.tracer.start_as_current_span(span_name, kind=SpanKind.CLIENT) as span:
            self._setup_span_attributes(
                span, system_name, operation_name, model, kwargs
            )
            try:
                if inspect.iscoroutinefunction(original_method):
                    return asyncio.run(
                        self._async_execution(span, original_method, args, kwargs)
                    )
                else:
                    return self._sync_execution(span, original_method, args, kwargs)
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("is_exception", True)
                raise

    def _execute_without_tracer(self, original_method, args, kwargs):
        """Execute method without tracer."""
        if inspect.iscoroutinefunction(original_method):
            return asyncio.run(original_method(*args, **kwargs))
        else:
            return original_method(*args, **kwargs)

    async def _async_execution(self, span, original_method, args, kwargs):
        """Execute async method with response capture."""
        response = await original_method(*args, **kwargs)
        self._capture_response_details(span, response, kwargs, self.provider_name)
        return response

    def _sync_execution(self, span, original_method, args, kwargs):
        """Execute sync method with response capture."""
        response = original_method(*args, **kwargs)
        self._capture_response_details(span, response, kwargs, self.provider_name)
        return response

    def _setup_span_attributes(self, span, system_name, operation_name, model, kwargs):
        """Setup span attributes for tracing."""
        span.set_attribute(gen_ai_attributes.GEN_AI_SYSTEM, system_name)
        span.set_attribute(gen_ai_attributes.GEN_AI_OPERATION_NAME, operation_name)
        span.set_attribute(gen_ai_attributes.GEN_AI_REQUEST_MODEL, model)

        # Request attributes
        self.set_span_attribute_if_not_none(
            span,
            gen_ai_attributes.GEN_AI_REQUEST_MAX_TOKENS,
            kwargs.get("max_completion_tokens"),
        )
        self.set_span_attribute_if_not_none(
            span,
            gen_ai_attributes.GEN_AI_REQUEST_PRESENCE_PENALTY,
            kwargs.get("presence_penalty"),
        )
        self.set_span_attribute_if_not_none(
            span,
            gen_ai_attributes.GEN_AI_REQUEST_FREQUENCY_PENALTY,
            kwargs.get("frequency_penalty"),
        )
        self.set_span_attribute_if_not_none(
            span,
            gen_ai_attributes.GEN_AI_REQUEST_STOP_SEQUENCES,
            json.dumps(kwargs.get("stop", [])) if kwargs.get("stop") else None,
        )
        self.set_span_attribute_if_not_none(
            span,
            gen_ai_attributes.GEN_AI_REQUEST_TEMPERATURE,
            kwargs.get("temperature"),
        )
        self.set_span_attribute_if_not_none(
            span, gen_ai_attributes.GEN_AI_REQUEST_TOP_K, kwargs.get("top_k")
        )
        self.set_span_attribute_if_not_none(
            span, gen_ai_attributes.GEN_AI_REQUEST_TOP_P, kwargs.get("top_p")
        )

    def _capture_response_details(self, span, response, kwargs, system_name):
        """Capture response details for tracing."""
        try:
            response_data = self._extract_response_data(response)
            if response_data is None:
                span.set_attribute("javelin.response.body", str(response))
                return

            self._set_basic_response_attributes(span, response_data)
            self._set_usage_attributes(span, response_data)
            self._add_message_events(span, kwargs, system_name)
            self._add_choice_events(span, response_data, system_name)

        except Exception as e:
            span.set_attribute("javelin.response.body", str(response))
            span.set_attribute("javelin.error", str(e))

    def _extract_response_data(self, response):
        """Extract response data from various response types."""
        if hasattr(response, "to_dict"):
            return self._extract_from_to_dict(response)
        elif hasattr(response, "model_dump"):
            return self._extract_from_model_dump(response)
        elif hasattr(response, "dict"):
            return self._extract_from_dict(response)
        elif isinstance(response, dict):
            return response
        elif hasattr(response, "__iter__") and not isinstance(
            response, (str, bytes, dict, list)
        ):
            return self._handle_streaming_response(response)
        else:
            return self._extract_from_json(response)

    def _extract_from_to_dict(self, response):
        """Extract data using to_dict method."""
        try:
            response_data = response.to_dict()
            return response_data if response_data else None
        except Exception:
            return None

    def _extract_from_model_dump(self, response):
        """Extract data using model_dump method."""
        try:
            return response.model_dump()
        except Exception:
            return None

    def _extract_from_dict(self, response):
        """Extract data using dict method."""
        try:
            return response.dict()
        except Exception:
            return None

    def _extract_from_json(self, response):
        """Extract data by parsing JSON string."""
        try:
            return json.loads(str(response))
        except (TypeError, ValueError):
            return None

    def _handle_streaming_response(self, response):
        """Handle streaming response data."""
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

    def _set_basic_response_attributes(self, span, response_data):
        """Set basic response attributes on span."""
        self.set_span_attribute_if_not_none(
            span, gen_ai_attributes.GEN_AI_RESPONSE_MODEL, response_data.get("model")
        )
        self.set_span_attribute_if_not_none(
            span, gen_ai_attributes.GEN_AI_RESPONSE_ID, response_data.get("id")
        )
        self.set_span_attribute_if_not_none(
            span,
            gen_ai_attributes.GEN_AI_OPENAI_REQUEST_SERVICE_TIER,
            response_data.get("service_tier"),
        )
        self.set_span_attribute_if_not_none(
            span,
            gen_ai_attributes.GEN_AI_OPENAI_RESPONSE_SYSTEM_FINGERPRINT,
            response_data.get("system_fingerprint"),
        )

        finish_reasons = [
            choice.get("finish_reason")
            for choice in response_data.get("choices", [])
            if choice.get("finish_reason")
        ]
        self.set_span_attribute_if_not_none(
            span,
            gen_ai_attributes.GEN_AI_RESPONSE_FINISH_REASONS,
            json.dumps(finish_reasons) if finish_reasons else None,
        )

    def _set_usage_attributes(self, span, response_data):
        """Set usage attributes on span."""
        usage = response_data.get("usage", {})
        self.set_span_attribute_if_not_none(
            span,
            gen_ai_attributes.GEN_AI_USAGE_INPUT_TOKENS,
            usage.get("prompt_tokens"),
        )
        self.set_span_attribute_if_not_none(
            span,
            gen_ai_attributes.GEN_AI_USAGE_OUTPUT_TOKENS,
            usage.get("completion_tokens"),
        )

    def _add_message_events(self, span, kwargs, system_name):
        """Add message events to span."""
        messages = kwargs.get("messages", [])

        system_message = next(
            (msg.get("content") for msg in messages if msg.get("role") == "system"),
            None,
        )
        self.add_event_with_attributes(
            span,
            "gen_ai.system.message",
            {"gen_ai.system": system_name, "content": system_message},
        )

        user_message = next(
            (msg.get("content") for msg in messages if msg.get("role") == "user"), None
        )
        self.add_event_with_attributes(
            span,
            "gen_ai.user.message",
            {"gen_ai.system": system_name, "content": user_message},
        )

    def _add_choice_events(self, span, response_data, system_name):
        """Add choice events to span."""
        choices = response_data.get("choices", [])
        for index, choice in enumerate(choices):
            choice_attributes = {"gen_ai.system": system_name, "index": index}
            message = choice.pop("message", {})
            choice.update(message)

            for key, value in choice.items():
                if isinstance(value, (dict, list)):
                    value = json.dumps(value)
                choice_attributes[key] = value if value is not None else None

            self.add_event_with_attributes(span, "gen_ai.choice", choice_attributes)

    def _patch_methods(self, openai_client, provider_name):
        """Patch client methods with tracing support."""

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
                continue

            original_method = self.original_methods[provider_name][
                method_name.replace(".", "_")
            ]
            patched_method = self._create_patched_method(
                method_name, original_method, openai_client
            )

            parent_attr, method_attr = method_name.rsplit(".", 1)
            parent_obj = get_nested_attr(openai_client, parent_attr)
            setattr(parent_obj, method_attr, patched_method)

            self.patched_methods.add(method_id)

    def register_provider(
        self, openai_client: Any, provider_name: str, route_name: str = None
    ) -> Any:
        """
        Generalized function to register OpenAI, Azure OpenAI, and Gemini clients.

        Additionally sets:
            - openai_client.base_url to self.base_url
            - openai_client._custom_headers to include self._headers
        """
        client_id = id(openai_client)
        if client_id in self.patched_clients:
            return openai_client

        self.patched_clients.add(client_id)
        self.provider_name = provider_name  # Store for use in helper methods
        if provider_name == "azureopenai":
            # Add /v1/openai to the base_url if not already present
            base_url = self.base_url.rstrip("/")
            if not base_url.endswith("openai"):
                self.base_url = f"{base_url}/openai"

        self._setup_client_headers(openai_client, route_name)
        self._store_original_methods(openai_client, provider_name)
        self._patch_methods(openai_client, provider_name)

        return openai_client

    def register_openai(self, openai_client: Any, route_name: str = None) -> Any:
        return self.register_provider(
            openai_client, provider_name="openai", route_name=route_name
        )

    def register_azureopenai(self, openai_client: Any, route_name: str = None) -> Any:
        return self.register_provider(
            openai_client, provider_name="azureopenai", route_name=route_name
        )

    def register_gemini(self, openai_client: Any, route_name: str = None) -> Any:
        return self.register_provider(
            openai_client, provider_name="gemini", route_name=route_name
        )

    def register_deepseek(self, openai_client: Any, route_name: str = None) -> Any:
        return self.register_provider(
            openai_client, provider_name="deepseek", route_name=route_name
        )

    def _setup_bedrock_clients(
        self, bedrock_runtime_client, bedrock_client, bedrock_session
    ):
        """Setup bedrock clients and validate the runtime client."""
        if bedrock_session is not None:
            self.bedrock_session = bedrock_session
            self.bedrock_client = bedrock_session.client("bedrock")
            self.bedrock_runtime_client = bedrock_session.client("bedrock-runtime")
        else:
            if bedrock_runtime_client is None:
                raise AssertionError("Bedrock Runtime client cannot be None")

        # Store the bedrock client
        self.bedrock_client = bedrock_client
        self.bedrock_session = bedrock_session
        self.bedrock_runtime_client = bedrock_runtime_client

        # Validate bedrock-runtime client type and attributes
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

    def _setup_bedrock_route(self, route_name):
        """Setup the default bedrock route."""
        if not route_name:
            route_name = "awsbedrock"

        # Store the default bedrock route
        if route_name is not None:
            self.use_default_bedrock_route = True
            self.default_bedrock_route = route_name

    def _create_bedrock_model_functions(self):
        """Create cached functions for getting model information."""

        @functools.lru_cache()
        def get_inference_model(inference_profile_identifier: str) -> str | None:
            try:
                if self.bedrock_client is None:
                    return None
                # Get the inference profile response
                response = self.bedrock_client.get_inference_profile(
                    inferenceProfileIdentifier=inference_profile_identifier
                )
                model_identifier = response["models"][0]["modelArn"]

                # Get the foundation model response
                foundation_model_response = self.bedrock_client.get_foundation_model(
                    modelIdentifier=model_identifier
                )
                model_id = foundation_model_response["modelDetails"]["modelId"]
                return model_id
            except Exception:
                # Fail silently if the model is not found
                return None

        @functools.lru_cache()
        def get_foundation_model(model_identifier: str) -> str | None:
            try:
                if self.bedrock_client is None:
                    return None
                response = self.bedrock_client.get_foundation_model(
                    modelIdentifier=model_identifier
                )
                return response["modelDetails"]["modelId"]
            except Exception:
                # Fail silently if the model is not found
                return None

        return get_inference_model, get_foundation_model

    def _extract_model_id_from_path(
        self, path, get_inference_model, get_foundation_model
    ):
        """Extract model ID from the URL path."""
        model_id = None

        # Check for inference profile ARN
        if re.match(self.PROFILE_ARN_PATTERN, path):
            match = re.match(self.PROFILE_ARN_PATTERN, path)
            if match:
                model_id = get_inference_model(match.group(0).replace("/model/", ""))

        # Check for model ARN
        elif re.match(self.MODEL_ARN_PATTERN, path):
            match = re.match(self.MODEL_ARN_PATTERN, path)
            if match:
                model_id = get_foundation_model(match.group(0).replace("/model/", ""))

        # If the model ID is not found, try to extract it from the path
        if model_id is None:
            path = path.replace("/model/", "")
            # Get the the last index of / in the path
            end_index = path.rfind("/")
            path = path[:end_index]
            model_id = path.replace("/model/", "")

        return model_id

    def _create_bedrock_request_handlers(
        self, get_inference_model, get_foundation_model
    ):
        """Create request handlers for bedrock operations."""

        def add_custom_headers(request: Any, **kwargs) -> None:
            """Add Javelin headers to each request."""
            request.headers.update(self._headers)

        def override_endpoint_url(request: Any, **kwargs) -> None:
            """
            Redirect Bedrock operations to the Javelin endpoint
            while preserving path and query.
            """
            try:
                original_url = urlparse(request.url)

                # Construct the base URL (scheme + netloc)
                base_url = f"{original_url.scheme}://{original_url.netloc}"

                # Set the header
                request.headers["x-javelin-provider"] = base_url

                if self.use_default_bedrock_route and self.default_bedrock_route:
                    request.headers["x-javelin-route"] = self.default_bedrock_route

                path = original_url.path
                path = unquote(path)

                model_id = self._extract_model_id_from_path(
                    path, get_inference_model, get_foundation_model
                )

                if model_id:
                    model_id = re.sub(r"-\d{8}(?=-)", "", model_id)
                    request.headers["x-javelin-model"] = model_id

                # Update the request URL to use the Javelin endpoint.
                parsed_base = urlparse(self.base_url)
                updated_url = original_url._replace(
                    scheme=parsed_base.scheme,
                    netloc=parsed_base.netloc,
                    path=f"/v1{original_url.path}",
                )
                request.url = urlunparse(updated_url)

            except Exception:
                pass

        return add_custom_headers, override_endpoint_url

    def _create_bedrock_tracing_handlers(self):
        """Create tracing handlers for bedrock operations."""

        def bedrock_before_call(**kwargs):
            """
            Start a new OTel span and store it in the Botocore context dict
            so it can be retrieved in after-call.
            """
            if self.tracer is None:
                return  # If no tracer, skip

            context = kwargs.get("context")
            if context is None:
                return

            event_name = kwargs.get("event_name", "")
            # e.g., "before-call.bedrock-runtime.InvokeModel"
            operation_name = event_name.split(".")[-1] if event_name else "Unknown"

            # Create & start the OTel span
            span = self.tracer.start_span(operation_name, kind=SpanKind.CLIENT)

            # Store it in the context
            context["javelin_request_wrapper"] = JavelinRequestWrapper(None, span)

        def bedrock_after_call(**kwargs):
            """
            End the OTel span by retrieving it from Botocore's context dict.
            """
            context = kwargs.get("context")
            if not context:
                return

            wrapper = context.get("javelin_request_wrapper")
            if not wrapper:
                return

            span = getattr(wrapper, "span", None)
            if not span:
                return

            # Optionally set status from the HTTP response
            http_response = kwargs.get("http_response")
            if http_response is not None and hasattr(http_response, "status_code"):
                if http_response.status_code >= 400:
                    span.set_status(
                        Status(
                            StatusCode.ERROR,
                            "HTTP %d" % http_response.status_code,
                        )
                    )
                else:
                    span.set_status(
                        Status(StatusCode.OK, "HTTP %d" % http_response.status_code)
                    )

            # End the span
            span.end()

        return bedrock_before_call, bedrock_after_call

    def _register_bedrock_event_handlers(
        self,
        add_custom_headers,
        override_endpoint_url,
        bedrock_before_call,
        bedrock_after_call,
    ):
        """Register event handlers for bedrock operations."""
        if self.bedrock_runtime_client is None:
            return

        for op in self.BEDROCK_RUNTIME_OPERATIONS:
            event_name_before_send = f"before-send.bedrock-runtime.{op}"
            event_name_before_call = f"before-call.bedrock-runtime.{op}"
            event_name_after_call = f"after-call.bedrock-runtime.{op}"
            events_client = self.bedrock_runtime_client.meta.events

            # Add headers + override endpoint
            events_client.register(
                event_name_before_send,
                add_custom_headers,
            )
            events_client.register(
                event_name_before_send,
                override_endpoint_url,
            )

            # Add OTel instrumentation
            events_client.register(
                event_name_before_call,
                bedrock_before_call,
            )
            events_client.register(
                event_name_after_call,
                bedrock_after_call,
            )

    def register_bedrock(
        self,
        bedrock_runtime_client: Any,
        bedrock_client: Any = None,
        bedrock_session: Any = None,
        route_name: Optional[str] = None,
    ) -> None:
        """
        Register an AWS Bedrock Runtime client
        for request interception and modification.

        Args:
            bedrock_runtime_client: A boto3 bedrock-runtime client instance
            bedrock_client: A boto3 bedrock client instance
            bedrock_session: A boto3 bedrock session instance
            route_name: The name of the route to use for the bedrock client
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
        self._setup_bedrock_clients(
            bedrock_runtime_client, bedrock_client, bedrock_session
        )
        self._setup_bedrock_route(route_name)

        get_inference_model, get_foundation_model = (
            self._create_bedrock_model_functions()
        )
        add_custom_headers, override_endpoint_url = (
            self._create_bedrock_request_handlers(
                get_inference_model, get_foundation_model
            )
        )
        bedrock_before_call, bedrock_after_call = (
            self._create_bedrock_tracing_handlers()
        )

        self._register_bedrock_event_handlers(
            add_custom_headers,
            override_endpoint_url,
            bedrock_before_call,
            bedrock_after_call,
        )

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
        is_model_specs: bool = False,
        is_reload: bool = False,
        univ_model: Optional[Dict[str, Any]] = None,
        guardrail: Optional[str] = None,
        list_guardrails: bool = False,
    ) -> str:
        url_parts = [self.base_url]

        # Determine the main URL path based on the primary resource type
        main_path = self._get_main_url_path(
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
        url_parts.extend(main_path)

        # Add resource-specific path segments
        resource_path = self._get_resource_path(
            gateway_name=gateway_name,
            provider_name=provider_name,
            route_name=route_name,
            secret_name=secret_name,
            template_name=template_name,
            archive=archive,
            guardrail=guardrail,
            query=query,
        )
        if resource_path:
            url_parts.extend(resource_path)

        url = "/".join(url_parts)

        if univ_model:
            endpoint_url = self.construct_endpoint_url(univ_model)
            url = urljoin(url, endpoint_url)

        if query_params:
            query_string = "&".join(f"{k}={v}" for k, v in query_params.items())
            url += f"?{query_string}"

        return url

    def _get_main_url_path(
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
    ) -> list:
        """Determine the main URL path based on the primary resource type."""
        # Define path strategies based on resource type
        path_strategies = [
            (is_model_specs, self._get_model_specs_path),
            (query, self._get_query_path),
            (gateway_name, self._get_gateway_path),
            (
                provider_name and not secret_name,
                lambda: self._get_provider_path(is_reload, is_transformation_rules),
            ),
            (route_name, lambda: self._get_route_path(is_reload)),
            (secret_name, lambda: self._get_secret_main_path(is_reload)),
            (template_name, lambda: self._get_template_path(is_reload)),
            (trace, self._get_trace_path),
            (archive, self._get_archive_path),
            (guardrail, lambda: self._get_guardrail_path(guardrail)),
            (list_guardrails, self._get_list_guardrails_path),
        ]

        # Find the first matching strategy and execute it
        for condition, strategy in path_strategies:
            if condition:
                return strategy()

        # Default fallback
        return ["admin", "routes"]

    def _get_model_specs_path(self) -> list:
        """Get path for model specs."""
        return ["admin", "modelspec"]

    def _get_query_path(self) -> list:
        """Get path for queries."""
        return ["query"]

    def _get_gateway_path(self) -> list:
        """Get path for gateways."""
        return ["admin", "gateways"]

    def _get_provider_path(
        self, is_reload: bool, is_transformation_rules: bool
    ) -> list:
        """Get path for providers."""
        base_path = ["providers"] if is_reload else ["admin", "providers"]
        if is_transformation_rules:
            base_path.append("transformation-rules")
        return base_path

    def _get_route_path(self, is_reload: bool) -> list:
        """Get path for routes."""
        return ["routes"] if is_reload else ["admin", "routes"]

    def _get_secret_main_path(self, is_reload: bool) -> list:
        """Get main path for secrets."""
        return ["secrets"] if is_reload else ["admin", "providers"]

    def _get_template_path(self, is_reload: bool) -> list:
        """Get path for templates."""
        return (
            ["processors", "dp", "templates"]
            if is_reload
            else ["admin", "processors", "dp", "templates"]
        )

    def _get_trace_path(self) -> list:
        """Get path for traces."""
        return ["admin", "traces"]

    def _get_archive_path(self) -> list:
        """Get path for archives."""
        return ["admin", "archives"]

    def _get_guardrail_path(self, guardrail: Optional[str]) -> list:
        """Get path for guardrails."""
        if guardrail == "all":
            return ["guardrails", "apply"]
        else:
            return ["guardrail", guardrail, "apply"]

    def _get_list_guardrails_path(self) -> list:
        """Get path for listing guardrails."""
        return ["guardrails", "list"]

    def _get_resource_path(
        self,
        gateway_name: Optional[str] = "",
        provider_name: Optional[str] = "",
        route_name: Optional[str] = "",
        secret_name: Optional[str] = "",
        template_name: Optional[str] = "",
        archive: Optional[str] = "",
        guardrail: Optional[str] = None,
        query: bool = False,
    ) -> list:
        """Get the resource-specific path segments."""
        if query and route_name is not None:
            return [route_name]
        elif gateway_name and gateway_name != "###":
            return [gateway_name]
        elif provider_name and provider_name != "###" and not secret_name:
            return [provider_name]
        elif route_name and route_name != "###":
            return [route_name]
        elif secret_name:
            return self._get_secret_path(provider_name, secret_name)
        elif template_name and template_name != "###":
            return [template_name]
        elif archive and archive != "###":
            return [archive]
        elif guardrail and guardrail != "all":
            return []  # Already handled in main path
        else:
            return []

    def _get_secret_path(self, provider_name: Optional[str], secret_name: str) -> list:
        """Get the path for secret-related operations."""
        path = []
        if provider_name and provider_name != "###":
            path.append(provider_name)
        path.append("keyvault")
        if secret_name != "###":
            path.append(secret_name)
        else:
            path.append("keys")
        return path

    # Gateway methods
    def create_gateway(self, gateway):
        return self.gateway_service.create_gateway(gateway)

    def acreate_gateway(self, gateway):
        return self.gateway_service.acreate_gateway(gateway)

    def get_gateway(self, gateway_name):
        return self.gateway_service.get_gateway(gateway_name)

    def aget_gateway(self, gateway_name):
        return self.gateway_service.aget_gateway(gateway_name)

    def list_gateways(self):
        return self.gateway_service.list_gateways()

    def alist_gateways(self):
        return self.gateway_service.alist_gateways()

    def update_gateway(self, gateway):
        return self.gateway_service.update_gateway(gateway)

    def aupdate_gateway(self, gateway):
        return self.gateway_service.aupdate_gateway(gateway)

    def delete_gateway(self, gateway_name):
        return self.gateway_service.delete_gateway(gateway_name)

    def adelete_gateway(self, gateway_name):
        return self.gateway_service.adelete_gateway(gateway_name)

    # Provider methods
    def create_provider(self, provider):
        return self.provider_service.create_provider(provider)

    def acreate_provider(self, provider):
        return self.provider_service.acreate_provider(provider)

    def get_provider(self, provider_name):
        return self.provider_service.get_provider(provider_name)

    def aget_provider(self, provider_name):
        return self.provider_service.aget_provider(provider_name)

    def list_providers(self):
        return self.provider_service.list_providers()

    def alist_providers(self):
        return self.provider_service.alist_providers()

    def update_provider(self, provider):
        return self.provider_service.update_provider(provider)

    def aupdate_provider(self, provider):
        return self.provider_service.aupdate_provider(provider)

    def delete_provider(self, provider_name):
        return self.provider_service.delete_provider(provider_name)

    def adelete_provider(self, provider_name):
        return self.provider_service.adelete_provider(provider_name)

    def alist_provider_secrets(self, provider_name):
        return self.provider_service.alist_provider_secrets(provider_name)

    def get_transformation_rules(self, provider_name, model_name, endpoint):
        return self.provider_service.get_transformation_rules(
            provider_name, model_name, endpoint
        )

    def aget_transformation_rules(self, provider_name, model_name, endpoint):
        return self.provider_service.aget_transformation_rules(
            provider_name, model_name, endpoint
        )

    def get_model_specs(self, provider_url, model_name):
        return self.modelspec_service.get_model_specs(provider_url, model_name)

    def aget_model_specs(self, provider_url, model_name):
        return self.modelspec_service.aget_model_specs(provider_url, model_name)

    # Route methods
    def create_route(self, route):
        return self.route_service.create_route(route)

    def acreate_route(self, route):
        return self.route_service.acreate_route(route)

    def get_route(self, route_name):
        return self.route_service.get_route(route_name)

    def aget_route(self, route_name):
        return self.route_service.aget_route(route_name)

    def list_routes(self):
        return self.route_service.list_routes()

    def alist_routes(self):
        return self.route_service.alist_routes()

    def update_route(self, route):
        return self.route_service.update_route(route)

    def delete_route(self, route_name):
        return self.route_service.delete_route(route_name)

    def adelete_route(self, route_name):
        return self.route_service.adelete_route(route_name)

    def query_route(
        self,
        route_name,
        query_body,
        headers=None,
        stream=False,
        stream_response_path=None,
    ):
        return self.route_service.query_route(
            route_name=route_name,
            query_body=query_body,
            headers=headers,
            stream=stream,
            stream_response_path=stream_response_path,
        )

    def aquery_route(
        self,
        route_name,
        query_body,
        headers=None,
        stream=False,
        stream_response_path=None,
    ):
        return self.route_service.aquery_route(
            route_name, query_body, headers, stream, stream_response_path
        )

    def query_unified_endpoint(
        self,
        provider_name,
        endpoint_type,
        query_body,
        headers=None,
        query_params=None,
        deployment=None,
        model_id=None,
        stream_response_path=None,
    ):
        return self.route_service.query_unified_endpoint(
            provider_name,
            endpoint_type,
            query_body,
            headers,
            query_params,
            deployment,
            model_id,
            stream_response_path,
        )

    def aquery_unified_endpoint(
        self,
        provider_name,
        endpoint_type,
        query_body,
        headers=None,
        query_params=None,
        deployment=None,
        model_id=None,
        stream_response_path=None,
    ):
        return self.route_service.aquery_unified_endpoint(
            provider_name,
            endpoint_type,
            query_body,
            headers,
            query_params,
            deployment,
            model_id,
            stream_response_path,
        )

    # Secret methods
    def create_secret(self, secret):
        return self.secret_service.create_secret(secret)

    def acreate_secret(self, secret):
        return self.secret_service.acreate_secret(secret)

    def get_secret(self, secret_name, provider_name):
        return self.secret_service.get_secret(secret_name, provider_name)

    def aget_secret(self, secret_name, provider_name):
        return self.secret_service.aget_secret(secret_name, provider_name)

    def list_secrets(self):
        return self.secret_service.list_secrets()

    def alist_secrets(self):
        return self.secret_service.alist_secrets()

    def update_secret(self, secret):
        return self.secret_service.update_secret(secret)

    def aupdate_secret(self, secret):
        return self.secret_service.aupdate_secret(secret)

    def delete_secret(self, secret_name, provider_name):
        return self.secret_service.delete_secret(secret_name, provider_name)

    def adelete_secret(self, secret_name, provider_name):
        return self.secret_service.adelete_secret(secret_name, provider_name)

    # Template methods
    def create_template(self, template):
        return self.template_service.create_template(template)

    def acreate_template(self, template):
        return self.template_service.acreate_template(template)

    def get_template(self, template_name):
        return self.template_service.get_template(template_name)

    def aget_template(self, template_name):
        return self.template_service.aget_template(template_name)

    def list_templates(self):
        return self.template_service.list_templates()

    def alist_templates(self):
        return self.template_service.alist_templates()

    def update_template(self, template):
        return self.template_service.update_template(template)

    def aupdate_template(self, template):
        return self.template_service.aupdate_template(template)

    def delete_template(self, template_name):
        return self.template_service.delete_template(template_name)

    def adelete_template(self, template_name):
        return self.template_service.adelete_template(template_name)

    def reload_data_protection(self, strategy_name):
        return self.template_service.reload_data_protection(strategy_name)

    def areload_data_protection(self, strategy_name):
        return self.template_service.areload_data_protection(strategy_name)

    # Guardrails methods
    def apply_trustsafety(self, text, config=None):
        return self.guardrails_service.apply_trustsafety(text, config)

    def apply_promptinjectiondetection(self, text, config=None):
        return self.guardrails_service.apply_promptinjectiondetection(text, config)

    def apply_guardrails(self, text, guardrails):
        return self.guardrails_service.apply_guardrails(text, guardrails)

    def list_guardrails(self):
        return self.guardrails_service.list_guardrails()

    # Traces methods
    def get_traces(self):
        return self.trace_service.get_traces()

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

    def _construct_azure_openai_endpoint(
        self,
        base_url: str,
        provider_name: str,
        deployment: str,
        endpoint_type: Optional[str],
    ) -> str:
        """Construct Azure OpenAI endpoint URL."""
        if not endpoint_type:
            raise ValueError("Endpoint type is required for Azure OpenAI")

        azure_deployment_url = f"{base_url}/{provider_name}/deployments/{deployment}"

        endpoint_mapping = {
            "chat": f"{azure_deployment_url}/chat/completions",
            "completion": f"{azure_deployment_url}/completions",
            "embeddings": f"{azure_deployment_url}/embeddings",
        }

        if endpoint_type not in endpoint_mapping:
            raise ValueError(f"Invalid Azure OpenAI endpoint type: {endpoint_type}")

        return endpoint_mapping[endpoint_type]

    def _construct_bedrock_endpoint(
        self, base_url: str, model_id: str, endpoint_type: Optional[str]
    ) -> str:
        """Construct Bedrock endpoint URL."""
        if not endpoint_type:
            raise ValueError("Endpoint type is required for Bedrock")

        endpoint_mapping = {
            "invoke": f"{base_url}/model/{model_id}/invoke",
            "converse": f"{base_url}/model/{model_id}/converse",
            "invoke_stream": f"{base_url}/model/{model_id}/invoke-with-response-stream",
            "converse_stream": f"{base_url}/model/{model_id}/converse-stream",
        }

        if endpoint_type not in endpoint_mapping:
            raise ValueError(f"Invalid Bedrock endpoint type: {endpoint_type}")

        return endpoint_mapping[endpoint_type]

    def _construct_anthropic_endpoint(
        self, base_url: str, endpoint_type: Optional[str]
    ) -> str:
        """Construct Anthropic endpoint URL."""
        if not endpoint_type:
            raise ValueError("Endpoint type is required for Anthropic")

        endpoint_mapping = {
            "messages": f"{base_url}/model/messages",
            "complete": f"{base_url}/model/complete",
        }

        if endpoint_type not in endpoint_mapping:
            raise ValueError(f"Invalid Anthropic endpoint type: {endpoint_type}")

        return endpoint_mapping[endpoint_type]

    def _construct_openai_compatible_endpoint(
        self, base_url: str, provider_name: str, endpoint_type: Optional[str]
    ) -> str:
        """Construct OpenAI compatible endpoint URL."""
        if not endpoint_type:
            raise ValueError(
                "Endpoint type is required for OpenAI compatible endpoints"
            )

        endpoint_mapping = {
            "chat": f"{base_url}/{provider_name}/chat/completions",
            "completion": f"{base_url}/{provider_name}/completions",
            "embeddings": f"{base_url}/{provider_name}/embeddings",
        }

        if endpoint_type not in endpoint_mapping:
            raise ValueError(
                f"Invalid OpenAI compatible endpoint type: {endpoint_type}"
            )

        return endpoint_mapping[endpoint_type]

    def construct_endpoint_url(self, request_model: Dict[str, Any]) -> str:
        """
        Constructs the endpoint URL based on the request model.

        :param request_model: The request model containing endpoint details.
        :return: The constructed endpoint URL.
        """
        provider_name = request_model.get("provider_name")
        endpoint_type = request_model.get("endpoint_type")
        deployment = request_model.get("deployment")
        model_id = request_model.get("model_id")

        if not provider_name:
            raise ValueError("Provider name is not specified in the request model.")

        base_url = self.base_url

        # Handle Azure OpenAI endpoints
        if provider_name == "azureopenai" and deployment:
            return self._construct_azure_openai_endpoint(
                base_url, provider_name, deployment, endpoint_type
            )

        # Handle Bedrock endpoints
        elif provider_name == "bedrock" and model_id:
            return self._construct_bedrock_endpoint(base_url, model_id, endpoint_type)

        # Handle Anthropic endpoints
        elif provider_name == "anthropic":
            return self._construct_anthropic_endpoint(base_url, endpoint_type)

        # Handle OpenAI compatible endpoints
        else:
            return self._construct_openai_compatible_endpoint(
                base_url, provider_name, endpoint_type
            )

    def set_headers(self, headers: Dict[str, str]) -> None:
        """
        Set or update headers for the client.

        Args:
            headers (Dict[str, str]): A dictionary of headers to set or update.
        """
        self._headers.update(headers)
