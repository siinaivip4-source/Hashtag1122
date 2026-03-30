import os
from contextlib import asynccontextmanager
from typing import Optional

import time
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware

from src.api.routes import auth, debug, health, image
from src.core.config import config
from src.core.logger import get_logger

load_dotenv()

logger = get_logger(__name__)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

inference_executor: Optional[ThreadPoolExecutor] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global inference_executor
    inference_executor = ThreadPoolExecutor(max_workers=config.inference_threads)
    image.inference_executor = inference_executor
    logger.info(f"Started inference executor with {config.inference_threads} workers")
    yield
    if inference_executor:
        inference_executor.shutdown(wait=True)
        logger.info("Shutting down inference executor")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.time()
        logger.info(f"Incoming {request.method} {request.url.path}")
        try:
            response = await call_next(request)
            return response
        finally:
            logger.info(f"Done {request.method} {request.url.path} after {time.time() - start_time:.3f}s")

app = FastAPI(
    title="Image Hashtag API",
    lifespan=lifespan,
)

app.add_middleware(LoggingMiddleware)
app.add_middleware(
    SessionMiddleware,
    secret_key=config.session_secret,
    session_cookie="session",
    max_age=14 * 24 * 3600,
    same_site="lax",
    https_only=True,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(auth.router)
app.include_router(image.router)
app.include_router(health.router)
app.include_router(debug.router)


def _user_allowed(request) -> bool:
    user = request.session.get("user")
    if not user:
        return False
    return config.is_email_allowed(user.get("email"))


@app.get("/login")
async def login_page():
    login_path = os.path.join(STATIC_DIR, "login.html")
    if not os.path.exists(login_path):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Login page not found")
    return FileResponse(login_path)


@app.get("/")
async def index(request: Request):
    if config.auth_enabled and not _user_allowed(request):
        return RedirectResponse(url="/login", status_code=302)
    index_path = os.path.join(STATIC_DIR, "index.html")
    if not os.path.exists(index_path):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Web interface not found")
    return FileResponse(index_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=config.host, port=config.port, reload=config.reload)
