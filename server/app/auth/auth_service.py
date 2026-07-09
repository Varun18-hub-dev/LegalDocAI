import uuid
from app.auth.password import hash_password, verify_password
from app.models.database import get_user_by_email, insert_user, get_user_by_id
from typing import Optional, Dict, Any

def register_user(name: str, email: str, password: str, role: str) -> Dict[str, Any]:
    """Register a new user in the platform database."""
    email_clean = email.lower().strip()
    existing_user = get_user_by_email(email_clean)
    if existing_user:
        raise ValueError("A user with this email address already exists.")
        
    # Check valid role
    role_upper = role.upper().strip()
    if role_upper not in ["ADMIN", "USER"]:
        raise ValueError("Invalid user role. Allowed: ADMIN, USER")
        
    user_id = "usr_" + uuid.uuid4().hex[:12]
    pw_hash = hash_password(password)
    
    insert_user(
        user_id=user_id,
        name=name,
        email=email_clean,
        password_hash=pw_hash,
        role=role_upper
    )
    
    # Return user details without password
    return {
        "id": user_id,
        "name": name,
        "email": email_clean,
        "role": role_upper,
        "status": "ACTIVE"
    }

def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate credentials and return user context if matching."""
    user = get_user_by_email(email)
    if not user:
        return None
        
    if not verify_password(password, user["password_hash"]):
        return None
        
    return user
