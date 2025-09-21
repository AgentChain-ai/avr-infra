"""
Authentication API endpoints
Simple authentication system for admin access
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
import jwt
from datetime import datetime, timedelta
import hashlib

from ..config import settings

# Authentication models
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_info: dict

class UserInfo(BaseModel):
    username: str
    role: str = "admin"
    permissions: list[str] = ["read", "write", "admin"]

# Router setup
router = APIRouter()
security = HTTPBearer(auto_error=False)

# Simple user storage (in production, use proper database)
USERS = {
    settings.admin_username: {
        "password_hash": hashlib.sha256(settings.admin_password.encode()).hexdigest(),
        "role": "admin",
        "permissions": ["read", "write", "admin"]
    }
}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm="HS256")
    return encoded_jwt

def decode_token(token: str) -> dict:
    """Decode JWT token"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    payload = decode_token(credentials.credentials)
    username = payload.get("sub")
    
    if username not in USERS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    user_data = USERS[username]
    return UserInfo(
        username=username,
        role=user_data["role"],
        permissions=user_data["permissions"]
    )

@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """Authenticate user and return access token"""
    
    # Check if user exists
    if login_data.username not in USERS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    user_data = USERS[login_data.username]
    
    # Verify password
    if not verify_password(login_data.password, user_data["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Create access token
    access_token_expires = timedelta(hours=24)
    access_token = create_access_token(
        data={"sub": login_data.username, "role": user_data["role"]},
        expires_delta=access_token_expires
    )
    
    return LoginResponse(
        access_token=access_token,
        expires_in=24 * 3600,  # 24 hours in seconds
        user_info={
            "username": login_data.username,
            "role": user_data["role"],
            "permissions": user_data["permissions"]
        }
    )

@router.get("/me", response_model=UserInfo)
async def get_current_user_info(current_user: UserInfo = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@router.post("/logout")
async def logout(current_user: UserInfo = Depends(get_current_user)):
    """Logout user (client should discard token)"""
    return {"message": f"User {current_user.username} logged out successfully"}

@router.get("/status")
async def auth_status():
    """Check authentication system status"""
    return {
        "status": "active",
        "users_configured": len(USERS),
        "token_expiry_hours": 24
    }
