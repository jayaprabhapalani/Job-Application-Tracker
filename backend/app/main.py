from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.redis_client import init_redis, close_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_redis()
    yield
    await close_redis()


app = FastAPI(lifespan=lifespan)
