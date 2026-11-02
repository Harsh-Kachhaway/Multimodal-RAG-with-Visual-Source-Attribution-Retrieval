import os
import re
import urllib.parse
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import logger
from app.api.v1.router import api_router
from app.api.v1.endpoints.query import router as direct_query_router
from app.api.v1.endpoints.health import router as direct_health_router


def find_image_file(raw_name: str) -> str:
    if not raw_name:
        return ""
    decoded_name = urllib.parse.unquote(raw_name).strip()
    clean_name = decoded_name.split("/")[-1].split("\\")[-1].strip()
    if clean_name == "local_path_placeholder" or not clean_name:
        return ""

    candidates = [
        clean_name,
        f"{clean_name}.png",
        f"{clean_name}).png",
        f"{clean_name}.jpg"
    ]
    for candidate in candidates:
        candidate_path = os.path.join(settings.images_dir, candidate)
        if os.path.exists(candidate_path):
            return candidate_path

    digit_match = re.search(r'\((\d+)\)', decoded_name) or re.search(r'(\d+)', decoded_name)
    if digit_match:
        digit = digit_match.group(1)
        fallback_name = f"images ({digit}).png"
        fallback_path = os.path.join(settings.images_dir, fallback_name)
        if os.path.exists(fallback_path):
            return fallback_path
    return ""


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name} in {settings.app_environment} mode")
    yield
    logger.info(f"Shutting down {settings.app_name}")


app = FastAPI(
    title=settings.app_name,
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/images/{image_path:path}")
async def serve_textbook_image(image_path: str):
    located_image = find_image_file(image_path)
    if located_image and os.path.exists(located_image):
        return FileResponse(located_image, media_type="image/png")
    raise HTTPException(status_code=404, detail="Image not found")


if os.path.exists("frontend"):
    app.mount("/static", StaticFiles(directory="frontend"), name="frontend_static")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exception: Exception):
    logger.error(f"Global unhandled error at {request.url}: {exception}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred while processing your request.",
            "detail": str(exception)
        }
    )


app.include_router(api_router, prefix=settings.api_v1_prefix)
app.include_router(direct_query_router)
app.include_router(direct_health_router)


@app.get("/")
async def serve_index_page():
    index_file = os.path.join("frontend", "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {
        "message": f"Welcome to {settings.app_name}",
        "documentation": "/docs",
        "api_prefix": settings.api_v1_prefix
    }
