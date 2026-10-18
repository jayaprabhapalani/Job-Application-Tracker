import asyncio
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, Request
from fastapi.websockets import WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
import redis.asyncio as aioredis
from sqlalchemy import text

from app.config import settings
from app.monitoring.tracing import init_langfuse, init_otel, flush_langfuse
import app.monitoring.metrics  # registers custom prometheus metrics
from app.database import engine, Base
import app.auth.models  # registers User table
import app.jobs.models  # registers Application, Resume, DocumentChunk tables
from app.redis_client import init_redis, close_redis
from app.kafka.producer import start_producer, stop_producer
from app.kafka.consumer import start_consumer, stop_consumer
from app.auth.router import router as auth_router
from app.jobs.router import router as jobs_router
from app.websocket.manager import manager

limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-initialize pgvector extension and create all database tables
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)

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
app.add_middleware(SlowAPIMiddleware)

origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()]
if not origins:
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
@limiter.limit("100/minute")
async def health_check(request: Request):
    return {"status": "ok"}


@app.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    await manager.connect(websocket, job_id)

    # Send current pipeline status immediately so UI has a baseline
    from app.database import AsyncSessionLocal
    from sqlalchemy import select
    from app.jobs.models import Application
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Application).where(Application.id == job_id))
        app_row = result.scalar_one_or_none()
        if app_row:
            await websocket.send_json({
                "type": "sync",
                "pipeline_status": app_row.pipeline_status,
            })

    r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    pubsub = r.pubsub()
    await pubsub.subscribe(f"ws:{job_id}")

    async def _redis_listener():
        try:
            async for msg in pubsub.listen():
                if msg and msg.get("type") == "message":
                    data = json.loads(msg["data"])
                    await websocket.send_json(data)
        except Exception:
            pass

    listener_task = asyncio.create_task(_redis_listener())
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        listener_task.cancel()
        try:
            await pubsub.unsubscribe(f"ws:{job_id}")
            await pubsub.aclose()
            await r.aclose()
        except Exception:
            pass
        manager.disconnect(websocket, job_id)
