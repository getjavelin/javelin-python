# javelin_sdk/tracing_setup.py
# from opentelemetry.instrumentation.botocore import BotocoreInstrumentor
import os
from typing import Optional

from opentelemetry import trace

# from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
# Use the HTTP exporter instead of the gRPC one
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# --- OpenTelemetry Setup ---
# TRACES_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT",
#                              "https://api-dev.javelin.live/v1/admin/traces")
# TRACES_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT",
#                              "https://logfire-api.pydantic.dev/v1/traces")

TRACES_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT")
TRACES_HEADERS = os.getenv("OTEL_EXPORTER_OTLP_HEADERS")

# Initialize OpenTelemetry Tracer
resource = Resource.create({"service.name": "javelin-sdk"})
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer("javelin")  # Name of the tracer


def parse_headers(header_str: Optional[str]) -> dict:
    """
    Parses a string like 'Authorization=Bearer xyz,Custom-Header=value' into a
    dictionary.
    """
    headers = {}
    if header_str:
        for pair in header_str.split(","):
            if "=" in pair:
                key, value = pair.split("=", 1)
                headers[key.strip()] = value.strip()
    return headers


def configure_span_exporter(api_key: Optional[str] = None):
    """
    Configure OTLP Span Exporter with dynamic headers from environment and API key.
    """
    # Disable tracing if TRACES_ENDPOINT is not set
    if not TRACES_ENDPOINT:
        return None

    # Parse headers from environment variable
    otlp_headers = parse_headers(TRACES_HEADERS)

    # Add API key if provided (overrides any existing 'x-api-key')
    if api_key:
        otlp_headers["x-api-key"] = api_key

    # Setup OTLP Exporter with API key in headers
    span_exporter = OTLPSpanExporter(endpoint=TRACES_ENDPOINT, headers=otlp_headers)

    span_processor = BatchSpanProcessor(span_exporter)
    provider = trace.get_tracer_provider()
    provider.add_span_processor(span_processor)  # type: ignore

    return tracer
