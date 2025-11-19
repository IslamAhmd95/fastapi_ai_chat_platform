from contextlib import asynccontextmanager

from fastapi import FastAPI  
from fastapi.middleware.cors import CORSMiddleware  

from src.api.auth import router as auth_routers
from src.api.chat import router as chat_routers


@asynccontextmanager  # Special decorator to manage the lifecycle to create an asynchronous context manager
async def lifespan(app: FastAPI):   # means the whole lifespan of my app from start to finish
    print("DB ready.")   # happens at startup
    yield     # app is running here normally (requests)
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

app.include_router(auth_routers)
app.include_router(chat_routers)