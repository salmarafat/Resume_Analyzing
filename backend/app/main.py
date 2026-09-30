import os
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from app.config import FRONTEND_DIR, BASE_DIR
from app.database import init_db
from app.services.seed_data import seed_initial_data
from app.services.rag_engine import rag_engine
from app.routers import (
    auth_router,
    resume_router,
    jobs_router,
    recommendation_router,
    career_router
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle event handler: runs database migrations and seeds initial data."""
    logger.info("Initializing database...")
    init_db()
    logger.info("Seeding initial dataset...")
    seed_initial_data()
    logger.info(f"RAG Engine loaded with {len(rag_engine.documents)} documents.")
    yield
    logger.info("Application shutdown.")

app = FastAPI(
    title="AI Resume Analyzer API",
    description="A multi-agent, RAG-powered intelligent career assistant and resume evaluation platform.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth_router.router)
app.include_router(resume_router.router)
app.include_router(jobs_router.router)
app.include_router(recommendation_router.router)
app.include_router(career_router.router)

# Health check
@app.get("/api/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "rag_documents_indexed": len(rag_engine.documents),
        "version": "1.0.0"
    }

# Validation error formatting
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_messages = []
    for err in exc.errors():
        field = " -> ".join([str(loc) for loc in err["loc"] if loc != "body"])
        error_messages.append(f"{field}: {err['msg']}")
    return JSONResponse(
        status_code=422,
        content={"detail": "; ".join(error_messages)}
    )

# Static file serving for Frontend (Vanilla HTML, CSS, JavaScript)
if FRONTEND_DIR.exists():
    css_dir = FRONTEND_DIR / "css"
    js_dir = FRONTEND_DIR / "js"
    if css_dir.exists():
        app.mount("/css", StaticFiles(directory=str(css_dir)), name="css")
    if js_dir.exists():
        app.mount("/js", StaticFiles(directory=str(js_dir)), name="js")

    samples_dir = BASE_DIR / "sample_resumes"
    if samples_dir.exists():
        app.mount("/sample_resumes", StaticFiles(directory=str(samples_dir)), name="samples")

    @app.get("/", include_in_schema=False)
    async def serve_index():
        index_file = FRONTEND_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"message": "Frontend not found, but API is live at /docs"}
