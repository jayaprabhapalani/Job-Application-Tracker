import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket
from fastapi.websockets import WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from prometheus_fastapi_instrumentator import Instrumentator
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from app.monitoring.tracing import init_langfuse, init_otel, flush_langfuse
from app.database import engine
from app.redis_client import init_redis, close_redis
from app.kafka.producer import start_producer, stop_producer
from app.kafka.consumer import start_consumer, stop_consumer
from app.auth.router import router as auth_router
from app.jobs.router import router as jobs_router
from app.websocket.manager import manager

limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_langfuse()
    init_otel(engine)
    await init_redis()
    await start_producer()
    consumer_task = asyncio.create_task(start_consumer())
    yield
    consumer_task.cancel()
    await stop_consumer()
    await stop_producer()
    await close_redis()
    await flush_langfuse()


app = FastAPI(title="JobPilot", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app)
FastAPIInstrumentor.instrument_app(app)
RedisInstrumentor().instrument()

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(jobs_router, prefix="/jobs", tags=["jobs"])


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    await manager.connect(websocket, job_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, job_id)
