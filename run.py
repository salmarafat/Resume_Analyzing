import sys
from pathlib import Path

# Ensure UTF-8 output encoding on Windows terminals
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("Starting AI Resume Analyzer (FastAPI + SQLite + Vanilla JS)")
    print("Web Application: http://127.0.0.1:8000")
    print("API Documentation (Swagger): http://127.0.0.1:8000/docs")
    print("ReDoc API Documentation: http://127.0.0.1:8000/redoc")
    print("=" * 60)
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)
