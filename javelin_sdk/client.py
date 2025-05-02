import functools
import inspect
import json
import re
import asyncio
import trace
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
import inspect
from opentelemetry.trace import SpanKind
from opentelemetry.trace import Status, StatusCode
from opentelemetry.semconv._incubating.attributes import gen_ai_attributes

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
            print (f"Client {client_id} already patched")
            return openai_client  # Skip if already patched

        self.patched_clients.add(client_id)  # Mark as patched

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

        # Store the original methods only if not already stored
        if provider_name not in self.original_methods:
            self.original_methods[provider_name] = {
                "chat_completions_create": openai_client.chat.completions.create,
                "completions_create": openai_client.completions.create,
                "embeddings_create": openai_client.embeddings.create,
            }

        # Patch methods with tracing and header updates
        def create_patched_method(method_name, original_method):
            # Check if the original method is asynchronous
            if inspect.iscoroutinefunction(original_method):
                # Async Patched Method
                async def patched_method(*args, **kwargs):
                    return await _execute_with_tracing(
                        original_method, method_name, args, kwargs
                    )

            else:
                # Sync Patched Method
                def patched_method(*args, **kwargs):
                    return _execute_with_tracing(
                        original_method, method_name, args, kwargs
                    )

            return patched_method

        def _execute_with_tracing(original_method, method_name, args, kwargs):
            model = kwargs.get("model")

            if model and hasattr(openai_client, "_custom_headers"):
                openai_client._custom_headers["x-javelin-model"] = model

            # Use well-known operation names, fallback to method_name if not mapped
            operation_name = self.GEN_AI_OPERATION_MAPPING.get(method_name, method_name)
            system_name = self.GEN_AI_SYSTEM_MAPPING.get(
                provider_name, provider_name
            )  # Fallback if provider is custom
            span_name = f"{operation_name} {model}"

            async def _async_execution(span):
                response = await original_method(*args, **kwargs)
                _capture_response_details(span, response, kwargs, system_name)
                return response

            def _sync_execution(span):
                response = original_method(*args, **kwargs)
                _capture_response_details(span, response, kwargs, system_name)
                return response

            # Only create spans if tracing is enabled
            if self.tracer:
                with self.tracer.start_as_current_span(
                    span_name, kind=SpanKind.CLIENT
                ) as span:
                    span.set_attribute(gen_ai_attributes.GEN_AI_SYSTEM, system_name)
                    span.set_attribute(
                        gen_ai_attributes.GEN_AI_OPERATION_NAME, operation_name
                    )
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
                        (
                            json.dumps(kwargs.get("stop", []))
                            if kwargs.get("stop")
                            else None
                        ),
                    )
                    JavelinClient.set_span_attribute_if_not_none(
                        span,
                        gen_ai_attributes.GEN_AI_REQUEST_TEMPERATURE,
                        kwargs.get("temperature"),
                    )
                    JavelinClient.set_span_attribute_if_not_none(
                        span,
                        gen_ai_attributes.GEN_AI_REQUEST_TOP_K,
                        kwargs.get("top_k"),
                    )
                    JavelinClient.set_span_attribute_if_not_none(
                        span,
                        gen_ai_attributes.GEN_AI_REQUEST_TOP_P,
                        kwargs.get("top_p"),
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

        # Helper to capture response details
        def _capture_response_details(span, response, kwargs, system_name):
            try:
                # print(f"type(response) = {type(response)}")
                if hasattr(response, "to_dict"):
                    # print("Response is a model object (has to_dict).")
                    try:
                        response_data = response.to_dict()
                        # print(f"DEBUG: after to_dict(), response_data = {response_data}")
                        if not response_data:
                            # print("response.to_dict() returned None or empty. Fallback.")
                            response_data = None
                    except Exception as e:
                        # print(f"to_dict() raised exception: {e}")
                        response_data = None
                elif hasattr(response, "model_dump"):
                    # print("Response is likely Pydantic 2.x (has model_dump).")
                    try:
                        response_data = response.model_dump()
                    except Exception as e:
                        # print(f"model_dump() failed: {e}")
                        response_data = None
                elif hasattr(response, "dict"):
                    # print("Response might be Pydantic 1.x (has .dict).")
                    try:
                        response_data = response.dict()
                    except Exception as e:
                        print(f"dict() failed: {e}")
                        response_data = None
                elif isinstance(response, dict):
                    # print("Response is already a dictionary.")
                    response_data = response
                elif hasattr(response, "__iter__") and not isinstance(response, (str, bytes, dict, list)):
                    # print("DEBUG: Response is a stream/iterator (likely streaming).")
                    response_data = {"object": "thread.message.delta", "streamed_text": ""}

                    # Iterate over chunks from the streaming response
                    for index, chunk in enumerate(response):
                        # print(f"DEBUG: Received chunk #{index}: {chunk}")

                        # **Fix: Convert `ChatCompletionChunk` to a dictionary**
                        if hasattr(chunk, "to_dict"):
                            chunk = chunk.to_dict()  # Convert chunk to a dictionary

                        if not isinstance(chunk, dict):
                            # print("DEBUG: Chunk is still not a dict; skipping.")
                            continue

                        choices = chunk.get("choices", [])
                        if not choices:
                            # print("DEBUG: No 'choices' in chunk; skipping.")
                            continue

                        # Extract the delta
                        delta_dict = choices[0].get("delta", {})
                        # print(f"DEBUG: delta_dict = {delta_dict}")

                        # Get streamed text content
                        streamed_text = delta_dict.get("content", "")
                        # print(f"DEBUG: streamed_text extracted = '{streamed_text}'")

                        # Accumulate the streamed text
                        response_data["streamed_text"] += streamed_text
                        # print(f"DEBUG: accumulated streamed_text so far = '{response_data['streamed_text']}'")

                        '''
                        # Fire OpenTelemetry event for each chunk
                        JavelinClient.add_event_with_attributes(
                            span,
                            "gen_ai.streaming.delta",
                            {
                                "gen_ai.system": system_name,
                                "streamed_content": streamed_text,
                                "chunk_index": index,
                            },
                        )
                        '''

                    # Store the final streamed text in the span
                    final_text = response_data["streamed_text"]
                    # print(f"DEBUG: Final accumulated streamed_text = '{final_text}'")
                    JavelinClient.set_span_attribute_if_not_none(span, gen_ai_attributes.GEN_AI_COMPLETION, final_text)

                    return  # Exit early since we've handled streaming

                else:
                    # print(f"Trying to parse JSON from response: {response}")
                    try:
                        response_data = json.loads(str(response))
                    except (TypeError, ValueError):
                        # print("Response is not valid JSON.")
                        response_data = None

                # If response_data is still None, set the raw response
                if response_data is None:
                    span.set_attribute("javelin.response.body", str(response))
                    return

                # Set basic response attributes
                JavelinClient.set_span_attribute_if_not_none(
                    span,
                    gen_ai_attributes.GEN_AI_RESPONSE_MODEL,
                    response_data.get("model"),
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
                    choice.get('finish_reason')
                    for choice in response_data.get('choices', [])
                    if choice.get('finish_reason')
                ]
                JavelinClient.set_span_attribute_if_not_none(
                    span,
                    gen_ai_attributes.GEN_AI_RESPONSE_FINISH_REASONS,
                    json.dumps(finish_reasons) if finish_reasons else None
                )

                # Token usage
                usage = response_data.get('usage', {})
                JavelinClient.set_span_attribute_if_not_none(span, gen_ai_attributes.GEN_AI_USAGE_INPUT_TOKENS, usage.get('prompt_tokens'))
                JavelinClient.set_span_attribute_if_not_none(span, gen_ai_attributes.GEN_AI_USAGE_OUTPUT_TOKENS, usage.get('completion_tokens'))

                # System message event
                system_message = next(
                    (msg.get('content') for msg in kwargs.get('messages', []) if msg.get('role') == 'system'),
                    None
                )
                JavelinClient.add_event_with_attributes(span, "gen_ai.system.message", {"gen_ai.system": system_name, "content": system_message})

                # User message event
                user_message = next(
                    (msg.get('content') for msg in kwargs.get('messages', []) if msg.get('role') == 'user'),
                    None
                )
                JavelinClient.add_event_with_attributes(span, "gen_ai.user.message", {"gen_ai.system": system_name, "content": user_message})

                # Choice events
                choices = response_data.get('choices', [])
                for index, choice in enumerate(choices):
                    choice_attributes = {"gen_ai.system": system_name, "index": index}
                    message = choice.pop("message", {})
                    choice.update(message)

                    for key, value in choice.items():
                        if isinstance(value, (dict, list)):
                            value = json.dumps(value)
                        choice_attributes[key] = value if value is not None else None

                    JavelinClient.add_event_with_attributes(span, "gen_ai.choice", choice_attributes)

            except Exception as e:
                span.set_attribute("javelin.response.body", str(response))
                span.set_attribute("javelin.error", str(e))

        
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
            patched_method = create_patched_method(method_name, original_method)

            parent_attr, method_attr = method_name.rsplit(".", 1)
            parent_obj = get_nested_attr(openai_client, parent_attr)
            setattr(parent_obj, method_attr, patched_method)

            self.patched_methods.add(method_id)

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

    def register_bedrock(
        self,
        bedrock_runtime_client: Any,
        bedrock_client: Any = None,
        bedrock_session: Any = None,
        route_name: str = None,
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

        # Store the default bedrock route
        if route_name is not None:
            self.use_default_bedrock_route = True
            self.default_bedrock_route = route_name

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

        def add_custom_headers(request: Any, **kwargs) -> None:
            """Add Javelin headers to each request."""
            request.headers.update(self._headers)

        """
        We don't want to make a request to the bedrock client for each request.
        So we cache the results of the inference profile and 
        foundation model requests.
        """

        @functools.lru_cache()
        def get_inference_model(inference_profile_identifier: str) -> str:
            try:
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
            except Exception as e:
                # Fail silently if the model is not found
                return None

        @functools.lru_cache()
        def get_foundation_model(model_identifier: str) -> str:
            try:
                response = self.bedrock_client.get_foundation_model(
                    modelIdentifier=model_identifier
                )
                return response["modelDetails"]["modelId"]
            except Exception as e:
                # Fail silently if the model is not found
                return None

        def override_endpoint_url(request: Any, **kwargs) -> None:
            """
            Redirect Bedrock operations to the Javelin endpoint while preserving path and query.

            - If self.use_default_bedrock_route is True and self.default_bedrock_route is not None,
            the header 'x-javelin-route' is set to self.default_bedrock_route.

            - In all cases, the function extracts an identifier from the URL path (after '/model/').
                a. First, by treating it as a profile ARN (via get_inference_profile) and then retrieving
                the model ARN and foundation model details.
                b. If that fails, by treating it directly as a model ARN and getting the foundation model detail

            - If it fails to find a model ID, it will try to extract it the model id from the path

            - Once the model ID is found, any date portion is removed, and the header
            'x-javelin-model' is set with this model ID.

            - Finally, the request URL is updated to point to the Javelin endpoint (using self.base_url)
            with the original path prefixed by '/v1'.

            Raises:
                ValueError: If any part of the process fails.
            """
            try:

                original_url = urlparse(request.url)

                # Construct the base URL (scheme + netloc)
                base_url = f"{original_url.scheme}://{original_url.netloc}"

                # Set the header
                request.headers["x-javelin-provider"] = base_url

                # If default routing is enabled and a default route is provided, set the x-javelin-route header.
                if self.use_default_bedrock_route and self.default_bedrock_route:
                    request.headers["x-javelin-route"] = self.default_bedrock_route

                path = original_url.path
                path = unquote(path)

                model_id = None

                # Check for inference profile ARN
                if re.match(self.PROFILE_ARN_PATTERN, path):
                    match = re.match(self.PROFILE_ARN_PATTERN, path)
                    model_id = get_inference_model(
                        match.group(0).replace("/model/", "")
                    )

                # Check for model ARN
                elif re.match(self.MODEL_ARN_PATTERN, path):
                    match = re.match(self.MODEL_ARN_PATTERN, path)
                    model_id = get_foundation_model(
                        match.group(0).replace("/model/", "")
                    )

                # If the model ID is not found, try to extract it from the path
                if model_id is None:
                    path = path.replace("/model/", "")
                    # Get the the last index of / in the path
                    end_index = path.rfind("/")
                    path = path[:end_index]
                    model_id = path.replace("/model/", "")

                if model_id:
                    # Remove the date portion if present (e.g., transform "anthropic.claude-3-haiku-20240307-v1:0"
                    # to "anthropic.claude-3-haiku-v1:0").
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

            except Exception as e:
                print(f"Failed to override endpoint URL: {str(e)}")
                pass

        def debug_before_send(*args, **kwargs):
            print("DEBUG: debug_before_send was invoked!")
            print("DEBUG: args =", args)
            print("DEBUG: kwargs =", kwargs)
    
        def bedrock_before_send(http_request, model, context, event_name, **kwargs):
            """Creates a new OTel span for each Bedrock invocation."""

            if self.tracer is None:
                return  # If no tracer, skip

            operation_name = kwargs.get("operation_name", "InvokeModel")
            system_name = "aws.bedrock"
            model = http_request.headers.get("x-javelin-model", "unknown-model")
            span_name = f"{operation_name} {model}"

            # Start the span
            span = self.tracer.start_span(span_name, kind=trace.SpanKind.CLIENT)

            # Set semantic attributes
            span.set_attribute(gen_ai_attributes.GEN_AI_SYSTEM, system_name)
            span.set_attribute(gen_ai_attributes.GEN_AI_OPERATION_NAME, operation_name)
            span.set_attribute(gen_ai_attributes.GEN_AI_REQUEST_MODEL, model)

            # Store in the BOTOCORE context dictionary
            context["javelin_request_wrapper"] = JavelinRequestWrapper(http_request, span)

            print(f"DEBUG: Bedrock span created: {span_name}")

        def debug_before_call(*args, **kwargs):
            print("DEBUG: debug_before_call invoked!")
            print("  args =", args)
            print("  kwargs =", kwargs)

        def debug_after_call(*args, **kwargs):
            print("DEBUG: debug_after_call invoked!")
            print("  args =", args)
            print("  kwargs =", kwargs)
    
        '''
        def bedrock_after_call(**kwargs):
            """Ends the OTel span after the Bedrock request completes."""

            # (1) Pull from kwargs:
            http_response = kwargs.get("http_response")
            parsed = kwargs.get("parsed")
            model = kwargs.get("model")
            context = kwargs.get("context")
            event_name = kwargs.get("event_name")  # e.g., "after-call.bedrock-runtime.InvokeModel"

            # (2) If you want to parse the operation name, you can do:
            #     operation_name = op_string.split(".")[-1]  # "InvokeModel", etc.
            # from event_name = "after-call.bedrock-runtime.InvokeModel"
            if event_name and event_name.startswith("after-call.bedrock-runtime."):
                operation_name = event_name.split(".")[-1]
            else:
                operation_name = "UnknownOperation"

            # (3) If you need a reference to the request object to retrieve attached spans,
            #     you'll notice it's NOT in kwargs by default for Bedrock. 
            #     Instead, you can do your OTel instrumentation purely via context:
            wrapper = context.get("javelin_request_wrapper")
            if not wrapper:
                print("DEBUG: No wrapped request object found in context.")
                return

            span = getattr(wrapper, "span", None)
            if not span:
                print("DEBUG: No span found for the request.")
                return

            try:
                http_status = getattr(http_response, "status_code", None)
                if http_status is not None:
                    if http_status >= 400:
                        span.set_status(Status(StatusCode.ERROR, f"HTTP {http_status}"))
                    else:
                        span.set_status(Status(StatusCode.OK, f"HTTP {http_status}"))

                    span.add_event(
                        name="bedrock.response",
                        attributes={
                            "http.status_code": http_status,
                            "parsed_response": str(parsed)[:500],
                        },
                    )
            finally:
                print(f"DEBUG: Bedrock span ended: {span.name}")
                span.end()
        '''

        def bedrock_before_call(**kwargs):
            """
            Start a new OTel span and store it in the Botocore context dict
            so it can be retrieved in after-call.
            """

            if self.tracer is None:
                return  # If no tracer, skip

            context = kwargs.get("context")
            if context is None:
                print("DEBUG: No context. Cannot store OTel span.")
                return

            event_name = kwargs.get("event_name", "")
            # e.g., "before-call.bedrock-runtime.InvokeModel"
            operation_name = event_name.split(".")[-1] if event_name else "Unknown"

            # Create & start the OTel span
            span = self.tracer.start_span(operation_name, kind=trace.SpanKind.CLIENT)

            # Store it in the context
            # Optionally wrap it in a JavelinRequestWrapper or something else
            context["javelin_request_wrapper"] = JavelinRequestWrapper(None, span)

            print(f"DEBUG: Span created for {operation_name}")

        def bedrock_after_call(**kwargs):
            """
            End the OTel span by retrieving it from Botocore's context dict.
            """
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

            # Optionally set status from the HTTP response
            http_response = kwargs.get("http_response")
            if http_response is not None and hasattr(http_response, "status_code"):
                if http_response.status_code >= 400:
                    span.set_status(Status(StatusCode.ERROR, "HTTP %d" % http_response.status_code))
                else:
                    span.set_status(Status(StatusCode.OK, "HTTP %d" % http_response.status_code))

            # End the span
            print(f"DEBUG: Ending span: {span.name}")
            span.end()


        # Register header modification & URL override for specific operations
        for op in self.BEDROCK_RUNTIME_OPERATIONS:
            event_name_before_send = f"before-send.bedrock-runtime.{op}"
            event_name_before_call = f"before-call.bedrock-runtime.{op}"
            event_name_after_call = f"after-call.bedrock-runtime.{op}"

            # Add headers + override endpoint just like your existing code
            self.bedrock_runtime_client.meta.events.register(event_name_before_send, add_custom_headers)
            self.bedrock_runtime_client.meta.events.register(event_name_before_send, override_endpoint_url)

            # Add OTel instrumentation
            # self.bedrock_runtime_client.meta.events.register(event_name_before_send, bedrock_before_send)
            self.bedrock_runtime_client.meta.events.register(event_name_before_call, bedrock_before_call)
            self.bedrock_runtime_client.meta.events.register(event_name_after_call, bedrock_after_call)
            # self.bedrock_runtime_client.meta.events.register(event_name_before_call, debug_before_call)
            # self.bedrock_runtime_client.meta.events.register(event_name_after_call, debug_after_call)


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

        if is_model_specs:
            url_parts.extend(["admin", "modelspec"])
        elif query:
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
        elif guardrail:
            if guardrail == "all":
                url_parts.extend(["guardrails", "apply"])
            else:
                url_parts.extend(["guardrail", guardrail, "apply"])
        elif list_guardrails:
            url_parts.extend(["guardrails", "list"])
        else:
            url_parts.extend(["admin", "routes"])

        url = "/".join(url_parts)

        if univ_model:
            endpoint_url = self.construct_endpoint_url(univ_model)
            url = urljoin(url, endpoint_url)

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
    get_model_specs = (
        lambda self, provider_url, model_name: self.modelspec_service.get_model_specs(
            provider_url, model_name
        )
    )
    aget_model_specs = (
        lambda self, provider_url, model_name: self.modelspec_service.aget_model_specs(
            provider_url, model_name
        )
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
    query_unified_endpoint = lambda self, provider_name, endpoint_type, query_body, headers=None, query_params=None, deployment=None, model_id=None, stream_response_path=None: self.route_service.query_unified_endpoint(
        provider_name,
        endpoint_type,
        query_body,
        headers,
        query_params,
        deployment,
        model_id,
        stream_response_path,
    )
    aquery_unified_endpoint = lambda self, provider_name, endpoint_type, query_body, headers=None, query_params=None, deployment=None, model_id=None, stream_response_path=None: self.route_service.aquery_unified_endpoint(
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

    # Guardrails methods
    apply_trustsafety = lambda self, text, config=None: self.guardrails_service.apply_trustsafety(text, config)
    apply_promptinjectiondetection = lambda self, text, config=None: self.guardrails_service.apply_promptinjectiondetection(text, config)
    apply_guardrails = lambda self, text, guardrails: self.guardrails_service.apply_guardrails(text, guardrails)
    list_guardrails = lambda self: self.guardrails_service.list_guardrails()

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

    def construct_endpoint_url(self, request_model: Dict[str, Any]) -> str:
        """
        Constructs the endpoint URL based on the request model.

        :param base_url: The base URL for the API.
        :param request_model: The request model containing endpoint details.
        :return: The constructed endpoint URL.
        """
        base_url = self.base_url
        provider_name = request_model.get("provider_name")
        endpoint_type = request_model.get("endpoint_type")
        deployment = request_model.get("deployment")
        model_id = request_model.get("model_id")
        if not provider_name:
            raise ValueError("Provider name is not specified in the request model.")

        if provider_name == "azureopenai" and deployment:
            # Handle Azure OpenAI endpoints
            if endpoint_type == "chat":
                return f"{base_url}/{provider_name}/deployments/{deployment}/chat/completions"
            elif endpoint_type == "completion":
                return (
                    f"{base_url}/{provider_name}/deployments/{deployment}/completions"
                )
            elif endpoint_type == "embeddings":
                return f"{base_url}/{provider_name}/deployments/{deployment}/embeddings"
        elif provider_name == "bedrock" and model_id:
            # Handle Bedrock endpoints
            if endpoint_type == "invoke":
                return f"{base_url}/model/{model_id}/invoke"
            elif endpoint_type == "converse":
                return f"{base_url}/model/{model_id}/converse"
            elif endpoint_type == "invoke_stream":
                return f"{base_url}/model/{model_id}/invoke-with-response-stream"
            elif endpoint_type == "converse_stream":
                return f"{base_url}/model/{model_id}/converse-stream"
        elif provider_name == "anthropic":
            if endpoint_type == "messages":
                return f"{base_url}/model/messages"
            elif endpoint_type == "complete":
                return f"{base_url}/model/complete"
        else:
            # Handle OpenAI compatible endpoints
            if endpoint_type == "chat":
                return f"{base_url}/{provider_name}/chat/completions"
            elif endpoint_type == "completion":
                return f"{base_url}/{provider_name}/completions"
            elif endpoint_type == "embeddings":
                return f"{base_url}/{provider_name}/embeddings"

        raise ValueError("Invalid request model configuration")

    def set_headers(self, headers: Dict[str, str]) -> None:
        """
        Set or update headers for the client.

        Args:
            headers (Dict[str, str]): A dictionary of headers to set or update.
        """
        self._headers.update(headers)

    # Guardrails methods
    apply_trustsafety = lambda self, text, config=None: self.guardrails_service.apply_trustsafety(text, config)
    apply_promptinjectiondetection = lambda self, text, config=None: self.guardrails_service.apply_promptinjectiondetection(text, config)
    apply_guardrails = lambda self, text, guardrails: self.guardrails_service.apply_guardrails(text, guardrails)
    list_guardrails = lambda self: self.guardrails_service.list_guardrails()
