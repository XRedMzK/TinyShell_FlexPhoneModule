from __future__ import annotations

import logging
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator, Mapping

from .config import Settings

logger = logging.getLogger(__name__)

try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.propagate import extract
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
except Exception:  # pragma: no cover - covered by runtime fallback behavior
    trace = None
    extract = None
    OTLPSpanExporter = None
    Resource = None
    TracerProvider = None
    BatchSpanProcessor = None
    ConsoleSpanExporter = None


@dataclass
class TracingRuntime:
    enabled: bool = False
    exporter: str = "none"
    provider: object | None = None
    tracer: object | None = None


class _NoopSpan:
    def set_attribute(self, key: str, value: object) -> None:
        return

    def record_exception(self, exc: BaseException) -> None:
        return


runtime = TracingRuntime()


def configure_tracing(settings: Settings) -> None:
    exporter = settings.otel_exporter.strip().lower()

    if trace is None or TracerProvider is None or BatchSpanProcessor is None:
        runtime.enabled = False
        runtime.exporter = "none"
        runtime.provider = None
        runtime.tracer = None
        if exporter != "none":
            logger.warning(
                "OpenTelemetry SDK is unavailable. Tracing disabled despite exporter=%s",
                exporter,
            )
        return

    if exporter == "none":
        runtime.enabled = False
        runtime.exporter = "none"
        runtime.provider = None
        runtime.tracer = None
        return

    resource = Resource.create({"service.name": settings.otel_service_name})
    provider = TracerProvider(resource=resource)

    if exporter == "otlp":
        if OTLPSpanExporter is None:
            runtime.enabled = False
            runtime.exporter = "none"
            runtime.provider = None
            runtime.tracer = None
            logger.warning("OTLP exporter requested but unavailable. Tracing disabled.")
            return
        span_exporter = OTLPSpanExporter(endpoint=settings.otel_otlp_endpoint)
    else:
        span_exporter = ConsoleSpanExporter()

    provider.add_span_processor(BatchSpanProcessor(span_exporter))
    runtime.enabled = True
    runtime.exporter = exporter
    runtime.provider = provider
    runtime.tracer = provider.get_tracer("flexphone.server")


def shutdown_tracing() -> None:
    provider = runtime.provider
    if provider is None:
        return
    try:
        provider.shutdown()
    except Exception:  # pragma: no cover - defensive shutdown
        logger.exception("Failed to shutdown tracing provider cleanly")


def extract_context(headers: Mapping[str, str]) -> object | None:
    if not runtime.enabled or extract is None:
        return None
    try:
        return extract(headers)
    except Exception:  # pragma: no cover - defensive
        logger.exception("Failed to extract tracing context from headers")
        return None


@contextmanager
def start_span(
    name: str,
    *,
    attributes: Mapping[str, object] | None = None,
    context: object | None = None,
) -> Iterator[object]:
    tracer = runtime.tracer
    if not runtime.enabled or tracer is None:
        yield _NoopSpan()
        return

    with tracer.start_as_current_span(name, context=context) as span:
        if attributes:
            for key, value in attributes.items():
                if value is not None:
                    span.set_attribute(key, value)
        yield span
