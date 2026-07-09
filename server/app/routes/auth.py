from fastapi import APIRouter, HTTPException, Depends, status
from app.models.schemas import UserRegisterRequest, UserLoginRequest, AuthResponse
from app.auth.auth_service import register_user, authenticate_user
from app.auth.jwt import create_access_token
from app.auth.dependencies import get_current_user
from typing import Dict, Any

router = APIRouter(prefix="/auth", tags=["User Authentication"])

@router.post("/register", response_model=Dict[str, Any])
async def signup(payload: UserRegisterRequest):
    """
    Register a new platform user profile (ADMIN, LAWYER, CLIENT).
    """
    try:
        user_info = register_user(
            name=payload.name,
            email=payload.email,
            password=payload.password,
            role="USER"
        )
        return {
            "status": "success",
            "message": "User registered successfully.",
            "user": user_info
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login", response_model=AuthResponse)
async def login(payload: UserLoginRequest):
    """
    Authenticate email credentials and distribute signed JWT authorization tokens.
    """
    user = authenticate_user(payload.email, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email address or password credentials."
        )
        
    if not user.get("is_active") or user.get("status") != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This user account has been deactivated."
        )
        
    access_token = create_access_token(data={
        "user_id": user["id"],
        "email": user["email"],
        "role": user["role"]
    })
    
    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user={
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"]
        }
    )

@router.get("/me", response_model=Dict[str, Any])
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    """
    Retrieve details of the currently authenticated active session user.
    """
    return {
        "id": current_user["id"],
        "name": current_user["name"],
        "email": current_user["email"],
        "role": current_user["role"],
        "status": current_user["status"],
        "created_at": current_user["created_at"]
    }
