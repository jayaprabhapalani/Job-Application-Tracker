from langfuse import Langfuse, observe, get_client
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from app.config import settings

langfuse: Langfuse | None = None
_tracer_provider: TracerProvider | None = None


def init_langfuse() -> None:
    global langfuse
    langfuse = Langfuse(
        public_key=settings.LANGFUSE_PUBLIC_KEY,
        secret_key=settings.LANGFUSE_SECRET_KEY,
        host=settings.LANGFUSE_HOST,
    )


def init_otel(engine) -> None:
    global _tracer_provider
    if _tracer_provider is not None:
        return
    resource = Resource.create({"service.name": "jobpilot-backend"})
    _tracer_provider = TracerProvider(resource=resource)
    _tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(_tracer_provider)
    SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)


def get_tracer(name: str = "jobpilot") -> trace.Tracer:
    return trace.get_tracer(name)


async def flush_langfuse() -> None:
    client = get_client()
    client.flush()


__all__ = ["langfuse", "init_langfuse", "init_otel", "get_tracer", "flush_langfuse", "observe"]
