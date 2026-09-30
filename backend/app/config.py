import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"
UPLOADS_DIR = BASE_DIR / "uploads"
KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"
DB_PATH = BASE_DIR / "resume_analyzer.db"

# Ensure runtime directories exist
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)

# Security and JWT
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "ai-resume-analyzer-super-secret-key-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# File upload constraints
ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# AI Model Configuration (Optional Gemini API Key)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
