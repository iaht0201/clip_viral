"""
Refactored FastAPI application with proper layered architecture.

This is the new main entry point with:
- Separated concerns (routes, services, repositories, workers)
- Async job queue with arq
- Real-time progress updates via SSE
- Thread pool for blocking operations
"""

from contextlib import asynccontextmanager
from pathlib import Path
import logging
import time

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from .config import Config
from .database import init_db, close_db, get_db
from .workers.job_queue import JobQueue
from .api.routes import tasks
from .observability import (
    TRACE_HEADER,
    clear_trace_id,
    configure_logging,
    generate_trace_id,
    get_trace_id,
    set_trace_id,
)

configure_logging()

logger = logging.getLogger(__name__)
config = Config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    # Startup
    logger.info("🚀 Starting SupoClip API...")
    try:
        await init_db()
        logger.info("✅ Database initialized")

        # Initialize job queue
        await JobQueue.get_pool()
        logger.info("✅ Job queue initialized")

        yield

    finally:
        # Shutdown
        logger.info("🛑 Shutting down SupoClip API...")
        await close_db()
        await JobQueue.close_pool()
        logger.info("✅ Cleanup complete")


# Create FastAPI app
app = FastAPI(
    title="SupoClip API",
    description="Refactored Python backend for SupoClip with async job processing",
    version="0.2.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "x-supoclip-user-id",
        "x-supoclip-ts",
        "x-supoclip-signature",
        "x-trace-id",
        "user_id",
    ],
    expose_headers=["x-trace-id"],
)


@app.middleware("http")
async def trace_and_request_logging_middleware(request: Request, call_next):
    trace_id = request.headers.get(TRACE_HEADER) or generate_trace_id()
    set_trace_id(trace_id)
    started_at = time.perf_counter()

    logger.info("Incoming request %s %s", request.method, request.url.path)

    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Unhandled exception while processing request")
        clear_trace_id()
        raise

    elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
    response.headers[TRACE_HEADER] = trace_id
    logger.info(
        "Completed request %s %s with status %s in %sms",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    clear_trace_id()
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    trace_id = get_trace_id()
    logger.warning("HTTP exception: status=%s detail=%s", exc.status_code, exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "trace_id": trace_id},
        headers={TRACE_HEADER: trace_id},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    trace_id = get_trace_id()
    logger.warning("Validation error: %s", exc.errors())
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "trace_id": trace_id},
        headers={TRACE_HEADER: trace_id},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception):
    trace_id = get_trace_id()
    logger.error("Unhandled server error: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred. Contact support with the trace ID.",
            "trace_id": trace_id,
        },
        headers={TRACE_HEADER: trace_id},
    )


# Mount static files for serving clips
clips_dir = Path(config.temp_dir) / "clips"
clips_dir.mkdir(parents=True, exist_ok=True)
app.mount("/clips", StaticFiles(directory=str(clips_dir)), name="clips")

# Include routers
app.include_router(tasks.router)

from .api.routes import tts as tts_router
app.include_router(tts_router.router)

# Keep existing utility endpoints
from .api.routes.media import router as media_router

app.include_router(media_router)

from .api.routes.feedback import router as feedback_router
app.include_router(feedback_router)

from .api.routes.waitlist import router as waitlist_router
app.include_router(waitlist_router)


@app.get("/")
def read_root():
    """Root endpoint."""
    return {
        "name": "SupoClip API",
        "version": "0.2.0",
        "status": "running",
        "docs": "/docs",
        "architecture": "refactored with job queue",
    }


@app.get("/health")
async def health_check():
    """Basic health check."""
    return {"status": "healthy"}


@app.get("/health/db")
async def check_database_health(db: AsyncSession = Depends(get_db)):
    """Check database connectivity."""
    from sqlalchemy import text

    try:
        result = await db.execute(text("SELECT COUNT(*) FROM users"))
        user_count = result.scalar()
        result = await db.execute(text("SELECT COUNT(*) FROM sources"))
        source_count = result.scalar()
        return {"status": "healthy", "database": "connected", "user_count": user_count, "source_count": source_count}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}


@app.get("/health/redis")
async def check_redis_health():
    """Check Redis connectivity."""
    try:
        pool = await JobQueue.get_pool()
        await pool.ping()
        return {"status": "healthy", "redis": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "redis": "disconnected", "error": str(e)}

@app.get("/tts/voices")
async def get_tts_voices():
    """List available Edge-TTS voices."""
    return {
        "voices": [
            {"id": "vi-VN-NamMinhNeural", "name": "Nam Minh (Vi - Nam)", "lang": "vi"},
            {"id": "vi-VN-HoaiMyNeural", "name": "Hoài My (Vi - Nữ)", "lang": "vi"},
            {"id": "en-US-AriaNeural", "name": "Aria (En - Nữ)", "lang": "en"},
            {"id": "en-US-GuyNeural", "name": "Guy (En - Nam)", "lang": "en"},
            {"id": "en-US-JennyNeural", "name": "Jenny (En - Nữ)", "lang": "en"},
            {"id": "en-US-EmmaNeural", "name": "Emma (En - Nữ)", "lang": "en"},
            {"id": "en-US-BrianNeural", "name": "Brian (En - Nam)", "lang": "en"},
            {"id": "en-US-ChristopherNeural", "name": "Chris (En - Nam)", "lang": "en"},
            {"id": "en-US-AvaNeural", "name": "Ava (En - Nữ)", "lang": "en"},
            {"id": "zh-CN-XiaoxiaoNeural", "name": "Tiêu Tiêu (CN - Nữ)", "lang": "zh"},
            {"id": "zh-CN-YunxiNeural", "name": "Vân Hi (CN - Nam)", "lang": "zh"},
            {"id": "zh-CN-YunjianNeural", "name": "Vân Kiện (CN - Nam)", "lang": "zh"},
            {"id": "zh-CN-YunxiaNeural", "name": "Vân Hạ (CN - Nam)", "lang": "zh"},
            {"id": "en-GB-SoniaNeural", "name": "Sonia (GB - Nữ)", "lang": "en-gb"},
            {"id": "en-GB-RyanNeural", "name": "Ryan (GB - Nam)", "lang": "en-gb"},
            {"id": "ja-JP-NanamiNeural", "name": "Nanami (JP - Nữ)", "lang": "ja"},
            {"id": "ja-JP-KeitaNeural", "name": "Keita (JP - Nam)", "lang": "ja"},
            {"id": "ko-KR-SunHiNeural", "name": "Sun-Hi (KR - Nữ)", "lang": "ko"},
            {"id": "ko-KR-InJoonNeural", "name": "In-Joon (KR - Nam)", "lang": "ko"},
        ]
    }

class TTSPreviewRequest(BaseModel):
    text: str = "Xin chào, đây là giọng thử nghiệm của công nghệ Edge TTS."
    voice_id: str = "vi-VN-NamMinhNeural"

@app.post("/tts/preview")
async def preview_tts(request: TTSPreviewRequest):
    import edge_tts
    import uuid
    from pathlib import Path
    from fastapi.responses import FileResponse
    from .config import Config

    config = Config()
    
    filename = f"preview_{uuid.uuid4()}.mp3"
    filepath = Path(config.temp_dir) / "clips" / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        communicate = edge_tts.Communicate(request.text, request.voice_id)
        await communicate.save(str(filepath))
        
        if filepath.exists():
            return FileResponse(path=str(filepath), media_type="audio/mpeg", background=None)
        else:
            return {"error": "Failed to generate audio file."}
    except Exception as e:
        logger.error(f"TTS preview failed: {e}")
        return {"error": str(e)}
