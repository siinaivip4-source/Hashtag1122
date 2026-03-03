import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import time
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.config import config
from src.api.routes import image, health, debug

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.time()
        print(f"==> Incoming {request.method} {request.url.path}", flush=True)
        try:
            response = await call_next(request)
            return response
        finally:
            print(f" <== Done {request.method} {request.url.path} after {time.time() - start_time:.3f}s", flush=True)

app = FastAPI(
    title="Image Hashtag API",
    lifespan=lifespan,
)

app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(image.router)
app.include_router(health.router)
app.include_router(debug.router)

@app.get("/")
async def index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if not os.path.exists(index_path):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Web interface not found")
    from fastapi.responses import FileResponse
    return FileResponse(index_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=config.host, port=config.port, reload=config.reload)
