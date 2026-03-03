from fastapi import APIRouter
import threading
import time
import os
import psutil

router = APIRouter(prefix="/debug", tags=["debug"])

start_time = time.time()

@router.get("/stats")
async def get_stats():
    process = psutil.Process(os.getpid())
    return {
        "uptime_seconds": time.time() - start_time,
        "active_threads": threading.active_count(),
        "memory_info": process.memory_info()._asdict(),
        "cpu_percent": process.cpu_percent(),
        "open_files": len(process.open_files()),
        "connections": len(process.connections()),
        "thread_pool_executor": "dedicated_20_threads"
    }
