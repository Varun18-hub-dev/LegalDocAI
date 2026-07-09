import os
import sqlite3
from pathlib import Path
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.models.database import init_db, get_db_conn
from app.models.schemas import HealthResponse
from app.routes import kb, documents, chat, auth, admin
from app.utils.exceptions import LegalException
from app.utils.logging import get_logger
from scripts.vector_store import get_vector_store

log = get_logger("main")

def seed_admin_user():
    """Create the admin user from environment variables if not already present."""
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")
    admin_name = os.getenv("ADMIN_NAME", "LegalDocAI Admin")
    
    if not admin_email or not admin_password:
        log.warning("ADMIN_EMAIL or ADMIN_PASSWORD not configured. Skipping admin seeding.")
        return
        
    from app.models.database import get_user_by_email
    from app.auth.auth_service import register_user
    
    email_clean = admin_email.lower().strip()
    try:
        user = get_user_by_email(email_clean)
        if not user:
            log.info(f"Seeding ADMIN account for '{email_clean}'...")
            register_user(
                name=admin_name,
                email=email_clean,
                password=admin_password,
                role="ADMIN"
            )
            log.info("ADMIN account seeded successfully.")
        else:
            log.info(f"ADMIN account for '{email_clean}' already exists. Seeding skipped.")
    except Exception as e:
        log.error(f"Failed to seed ADMIN account: {e}", exc_info=True)

# Initialize database tables on startup
try:
    log.info("Initializing SQLite database tables...")
    init_db()
    seed_admin_user()
except Exception as e:
    log.critical(f"Database initialization failed: {e}", exc_info=True)

# Create FastAPI App
app = FastAPI(
    title="LegalDocAI API Backend",
    description="REST API Backend for Indian Legal Knowledge Base and Document Q&A RAG Engine.",
    version="1.0.0"
)

# Determine allowed CORS origins
cors_origins_env = os.getenv("CORS_ORIGINS")
frontend_url_env = os.getenv("FRONTEND_URL")

allowed_origins = [
    "http://localhost:5173", 
    "http://127.0.0.1:5173", 
    "http://localhost:8000", 
    "http://127.0.0.1:8000"
]
if cors_origins_env:
    allowed_origins.extend([o.strip() for o in cors_origins_env.split(",") if o.strip()])
if frontend_url_env:
    allowed_origins.append(frontend_url_env.strip())

# Deduplicate
allowed_origins = list(set(allowed_origins))

# In development mode (APP_ENV != "production"), allow all origins
if os.getenv("APP_ENV") != "production":
    allowed_origins = ["*"]

allow_creds = True
if "*" in allowed_origins:
    allow_creds = False

# CORS Middleware for main app
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_creds,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler for LegalException
@app.exception_handler(LegalException)
async def legal_exception_handler(request: Request, exc: LegalException):
    log.error(f"Global exception handler caught: {exc.message} (status: {exc.status_code})")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "error_type": exc.__class__.__name__,
            "message": exc.message
        }
    )

# Include API Routers under /api/v1
api_v1 = FastAPI()
api_v1.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_creds,
    allow_methods=["*"],
    allow_headers=["*"],
)
api_v1.include_router(auth.router)
api_v1.include_router(admin.router)
api_v1.include_router(kb.router)
api_v1.include_router(documents.router)
api_v1.include_router(chat.router)

# Mount /api/v1 to the main app
app.mount("/api/v1", api_v1)

# Health endpoint (root level and versioned)
@app.get("/api/health", response_model=HealthResponse)
@api_v1.get("/health", response_model=HealthResponse)
async def check_health():
    """
    Detailed health check verifying SQLite read/write, ChromaDB collections,
    uploads directory write permission, and Gemini config state.
    """
    # 1. SQLite Read/Write Check
    sqlite_status = "ok"
    try:
        with get_db_conn() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS health_check (id INTEGER PRIMARY KEY, ts TEXT)")
            conn.execute("INSERT INTO health_check (ts) VALUES (datetime('now'))")
            conn.execute("DELETE FROM health_check")
    except Exception as e:
        log.error(f"Health Check: SQLite failed: {e}")
        sqlite_status = "failed"
        
    # 2. Check ChromaDB
    chroma_status = "ok"
    try:
        store = get_vector_store()
        store.get_or_create_collection(name="case_documents")
    except Exception as e:
        log.error(f"Health Check: ChromaDB failed: {e}")
        chroma_status = "failed"
        
    # 3. Check Uploads directory
    uploads_status = "ok"
    try:
        from app.config import UPLOAD_DIR
        test_file = Path(UPLOAD_DIR) / ".health_check_temp"
        test_file.write_text("healthcheck")
        test_file.unlink()
    except Exception as e:
        log.error(f"Health Check: Uploads failed: {e}")
        uploads_status = "failed"
        
    # 4. Check Gemini API key
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    is_dummy_key = not gemini_key or gemini_key.lower() in ("your_api_key_here", "dummy", "placeholder", "")
    gemini_status = "configured" if not is_dummy_key else "not_configured"
    
    # Overall state
    overall_status = "healthy"
    if "failed" in (sqlite_status, chroma_status, uploads_status) or gemini_status == "not_configured":
        overall_status = "degraded"
        
    return HealthResponse(
        status=overall_status,
        environment=os.getenv("APP_ENV", "development"),
        sqlite=sqlite_status,
        chromadb=chroma_status,
        uploads=uploads_status,
        gemini=gemini_status,
        kb_version="v2.0"
    )

# Serve compiled React frontend if static build exists
static_dir = Path(__file__).resolve().parent / "static"
if static_dir.exists():
    log.info(f"Serving React static frontend from: {static_dir}")
    
    # Mount assets folder if exists
    assets_dir = static_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
        
    @app.get("/{catchall:path}", response_class=HTMLResponse)
    async def serve_spa(request: Request, catchall: str):
        # Exclude backend-specific paths to allow 404 falling back correctly
        if (
            catchall.startswith("api/") or 
            catchall in ("docs", "redoc", "openapi.json") or
            catchall.startswith("assets/")
        ):
            raise HTTPException(status_code=404)
            
        index_path = static_dir / "index.html"
        if index_path.exists():
            with open(index_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read(), status_code=200)
        return HTMLResponse(content="Frontend build index.html not found.", status_code=404)
else:
    log.warning(f"Static directory not found at: {static_dir}. SPA static routing disabled.")
    
    @app.get("/")
    async def root():
        return {
            "message": "Welcome to LegalDocAI API Backend. Access API Swagger documentation at /docs or versioned API at /api/v1/docs."
        }
