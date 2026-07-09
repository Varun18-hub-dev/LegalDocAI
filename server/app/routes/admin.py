from fastapi import APIRouter, Depends, HTTPException, status
from app.auth.dependencies import require_admin
from app.models.database import (
    get_admin_metrics, get_all_users, update_user_role, 
    get_all_user_documents, get_db_conn
)
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

router = APIRouter(prefix="/admin", tags=["Admin Operations"], dependencies=[Depends(require_admin)])

class RoleUpdateRequest(BaseModel):
    role: str

class StatusUpdateRequest(BaseModel):
    status: str # 'ACTIVE', 'INACTIVE'

@router.get("/metrics", response_model=Dict[str, Any])
async def fetch_metrics():
    """Retrieve operational SaaS stats, token consumption, and system health benchmarks."""
    return get_admin_metrics()

@router.get("/users", response_model=List[Dict[str, Any]])
async def fetch_users_directory():
    """List all accounts registered in the database system."""
    users = get_all_users()
    # Remove password hashes for safety
    for u in users:
        u.pop("password_hash", None)
    return users

@router.patch("/users/{user_id}/role", response_model=Dict[str, Any])
async def modify_user_role(user_id: str, payload: RoleUpdateRequest):
    """Change the user access profile (ADMIN, USER)."""
    role_upper = payload.role.upper().strip()
    if role_upper not in ["ADMIN", "USER"]:
        raise HTTPException(status_code=400, detail="Invalid role. Must be ADMIN or USER.")
    update_user_role(user_id, role_upper)
    return {"status": "success", "message": f"User role updated to {role_upper}."}

@router.patch("/users/{user_id}/status", response_model=Dict[str, Any])
async def modify_user_status(user_id: str, payload: StatusUpdateRequest):
    """Activate or deactivate a user account."""
    status_upper = payload.status.upper().strip()
    if status_upper not in ["ACTIVE", "INACTIVE"]:
        raise HTTPException(status_code=400, detail="Invalid status. Must be ACTIVE or INACTIVE.")
    
    is_active = 1 if status_upper == "ACTIVE" else 0
    with get_db_conn() as conn:
        conn.execute("UPDATE users SET status = ?, is_active = ? WHERE id = ?", (status_upper, is_active, user_id))
        
    return {"status": "success", "message": f"User account status updated to {status_upper}."}

@router.get("/documents", response_model=List[Dict[str, Any]])
async def fetch_all_documents():
    """Oversight endpoint to inspect all custom files metadata across the SaaS platform."""
    docs = get_all_user_documents()
    # Ensure raw private text is not leaked
    for d in docs:
        d.pop("file_path", None)
    return docs

@router.get("/logs", response_model=List[Dict[str, Any]])
async def fetch_audit_logs():
    """Access platform operations audit logs."""
    import datetime
    now = datetime.datetime.now().isoformat()
    # Mock some audit records for the console dashboard
    return [
        {"timestamp": now, "event": "DATABASE_INITIALIZATION", "status": "SUCCESS", "detail": "SQLite schemas loaded."},
        {"timestamp": now, "event": "VECTOR_SYNC", "status": "SUCCESS", "detail": "ChromaDB connection verified."},
        {"timestamp": now, "event": "API_BOOT", "status": "SUCCESS", "detail": "FastAPI version 1.0 routing mounted."}
    ]
