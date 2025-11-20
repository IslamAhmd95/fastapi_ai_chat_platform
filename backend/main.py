from contextlib import asynccontextmanager

from fastapi import FastAPI  
from fastapi.middleware.cors import CORSMiddleware  
from redis.asyncio import Redis
from fastapi_limiter import FastAPILimiter

from src.api import (
    auth, chat, ws
)


@asynccontextmanager  # Special decorator to manage the lifecycle to create an asynchronous context manager
async def lifespan(app: FastAPI):   # means the whole lifespan of my app from start to finish
    print("Startup ready.")   # happens at startup
    redis_connection = Redis.from_url("redis://localhost:6379", encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(redis_connection)

    yield     # app is running here normally (requests)

    await FastAPILimiter.close()
    print("Shutdown...")  # happens at shutdown



app = FastAPI(
    title="FastAPI Gemini Ai App",
    lifespan=lifespan
)

origins = [
    "http://localhost:8080",  # Your frontend's local URL
    "http://127.0.0.1:8080",  # Another way the browser might reference localhost
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,         # which sites can talk to backend
    allow_credentials=True,
    allow_methods=["*"],           # GET, POST, PUT, DELETE...
    allow_headers=["*"],           # Authorization, Content-Type...
)

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(ws.router)