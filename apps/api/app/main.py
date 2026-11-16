from contextlib import asynccontextmanager
import time
import os
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from apps.api.app.core.config import settings
from apps.api.app.api.v1.router import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup directories
    os.makedirs(settings.LOCAL_STORAGE_DIR, exist_ok=True)
    os.makedirs(settings.LOCAL_UPLOAD_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(settings.MODEL_CHECKPOINT_PATH), exist_ok=True)
    yield

app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.ALLOWED_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include v1 API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Request ID & timing middleware
@app.middleware("http")
async def add_process_time_and_request_id(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Health Probes
@app.get("/health/live", tags=["Health"], status_code=status.HTTP_200_OK)
async def liveness_probe():
    return {
        "status": "alive",
        "service": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "timestamp": time.time(),
    }

@app.get("/health/ready", tags=["Health"], status_code=status.HTTP_200_OK)
async def readiness_probe():
    # Verify storage directories
    storage_ok = os.path.exists(settings.LOCAL_STORAGE_DIR) and os.path.exists(settings.LOCAL_UPLOAD_DIR)
    
    return {
        "status": "ready" if storage_ok else "degraded",
        "storage": "ok" if storage_ok else "unreachable",
        "database": "configured",
        "timestamp": time.time(),
    }

@app.get("/", tags=["Root"])
async def root():
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "api_docs": f"{settings.API_V1_STR}/docs",
        "status": "active"
    }
