from fastapi import APIRouter, HTTPException, Depends, status
from app.models.schemas import ChatHistoryResponse, MessageResponse
from app.models.database import (
    get_chat_session, create_chat_session, get_chat_sessions_by_user,
    insert_chat_message, get_chat_messages, delete_chat_session_db,
    update_chat_session_title, toggle_pin_session, toggle_favorite_session
)
from app.auth.dependencies import get_current_user
from app.utils.logging import get_logger
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

log = get_logger("routes.chat")
router = APIRouter(prefix="/chat", tags=["Multi-User Chat sessions"])

class SessionCreateRequest(BaseModel):
    title: str
    tags: Optional[List[str]] = None

class SessionUpdateRequest(BaseModel):
    title: Optional[str] = None
    pinned: Optional[bool] = None
    favorite: Optional[bool] = None

@router.get("/sessions", response_model=List[Dict[str, Any]])
async def list_chat_sessions(current_user: dict = Depends(get_current_user)):
    """List all chat sessions for the authenticated user."""
    return get_chat_sessions_by_user(current_user["id"])

@router.post("/sessions", response_model=Dict[str, Any])
async def create_new_session(payload: SessionCreateRequest, current_user: dict = Depends(get_current_user)):
    """Create a new user chat session."""
    import uuid
    session_id = "sess_" + uuid.uuid4().hex[:12]
    create_chat_session(
        session_id=session_id,
        user_id=current_user["id"],
        title=payload.title,
        tags_list=payload.tags
    )
    return {
        "status": "success",
        "session_id": session_id,
        "title": payload.title
    }

@router.patch("/sessions/{session_id}", response_model=MessageResponse)
async def update_session_meta(session_id: str, payload: SessionUpdateRequest, current_user: dict = Depends(get_current_user)):
    """Update title, pinned, or favorite status on a chat session."""
    session = get_chat_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found.")
    if session["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Permission denied. You do not own this session.")
        
    if payload.title is not None:
        update_chat_session_title(session_id, payload.title)
    if payload.pinned is not None:
        toggle_pin_session(session_id, payload.pinned)
    if payload.favorite is not None:
        toggle_favorite_session(session_id, payload.favorite)
        
    return MessageResponse(status="success", message="Chat session metadata updated successfully.")

@router.delete("/sessions/{session_id}", response_model=MessageResponse)
async def delete_session(session_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a chat session and all its associated messages."""
    session = get_chat_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found.")
    if session["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Permission denied. You do not own this session.")
        
    delete_chat_session_db(session_id)
    return MessageResponse(status="success", message="Chat session deleted successfully.")

# ------------------------------------------------------------
# Legacy Frontend Compatibility Endpoints (Secured & Redirected)
# ------------------------------------------------------------

@router.get("/{session_id}", response_model=ChatHistoryResponse)
async def fetch_chat_history(session_id: str, current_user: dict = Depends(get_current_user)):
    """Retrieve all logged question-answer history for a specific chat session (Legacy Adapter)."""
    # 1. Enforce session check or dynamically create session if missing (to prevent legacy crash)
    session = get_chat_session(session_id)
    if not session:
        # Create session placeholder for the current user
        create_chat_session(
            session_id=session_id,
            user_id=current_user["id"],
            title="Chat QA Workspace"
        )
    elif session["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Permission denied. You do not own this session.")
        
    messages = get_chat_messages(session_id)
    history = []
    
    # Pair messages: odds are question, evens are answer
    i = 0
    while i < len(messages):
        msg = messages[i]
        if msg["role"] == "user":
            question = msg["message"]
            answer = ""
            sources = []
            created_at = msg["created_at"]
            
            # Look at next message to find answer
            if i + 1 < len(messages) and messages[i + 1]["role"] == "assistant":
                answer = messages[i + 1]["message"]
                sources = messages[i + 1]["citations"]
                i += 2
            else:
                i += 1
                
            history.append({
                "id": msg["id"],
                "session_id": session_id,
                "question": question,
                "answer": answer,
                "sources": sources,
                "created_at": created_at
            })
        else:
            i += 1
            
    return ChatHistoryResponse(
        session_id=session_id,
        history=history
    )

@router.delete("/{session_id}", response_model=MessageResponse)
async def clear_chat_history(session_id: str, current_user: dict = Depends(get_current_user)):
    """Clear and delete all question-answer logs for a specific chat session (Legacy Adapter)."""
    session = get_chat_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found.")
    if session["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Permission denied. You do not own this session.")
        
    delete_chat_session_db(session_id)
    return MessageResponse(
        status="success",
        message=f"Chat history for session '{session_id}' cleared successfully."
    )
