from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from prometheus_fastapi_instrumentator import Instrumentator
from app.redis_client import init_redis, close_redis
from app.auth import router as auth_router

limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])


async def start_kafka_consumer():
    # TODO: initialize and start Kafka consumer
    pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_redis()
    await start_kafka_consumer()
    yield
    await close_redis()


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

app.include_router(auth_router.router, prefix="/auth", tags=["auth"])


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    # TODO: delegate to websocket manager
    await websocket.accept()
    await websocket.close()
