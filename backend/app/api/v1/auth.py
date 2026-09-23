"""
Auth API router — register, login, refresh, me.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import hashlib
import redis.asyncio as aioredis
from app.core.config import get_settings
from app.middleware.rate_limit import limiter

from app.core.database import get_db
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    decode_token, get_current_user,
)
from app.models.user import User, Student, Department, Faculty
from app.schemas.auth import (
    RegisterRequest, LoginRequest, RefreshRequest,
    TokenResponse, UserResponse, StudentResponse, MessageResponse,
)
from pydantic import BaseModel
class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(request: Request, data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user. Students require roll_number and department_code."""
    # Check if email already exists
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Create user
    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        role=data.role,
        first_name=data.first_name,
        last_name=data.last_name,
        phone=data.phone,
    )
    db.add(user)
    await db.flush()  # Get user.id before creating student

    # If student, create student profile
    if data.role == "student":
        if not data.roll_number or not data.department_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Students must provide roll_number and department_code",
            )

        # Look up department
        dept_result = await db.execute(
            select(Department).where(Department.code == data.department_code)
        )
        department = dept_result.scalar_one_or_none()
        if not department:
            # Auto-create department since DB is fresh
            department = Department(
                code=data.department_code, 
                name=f"{data.department_code} Department"
            )
            db.add(department)
            await db.flush()

        student = Student(
            id=user.id,
            roll_number=data.roll_number,
            department_id=department.id,
            current_semester=data.current_semester or 1,
            admission_year=data.admission_year or 2023,
        )
        db.add(student)

    elif data.role in ("faculty", "hod"):
        if not data.department_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Faculty must provide department_code",
            )
        dept_result = await db.execute(
            select(Department).where(Department.code == data.department_code)
        )
        department = dept_result.scalar_one_or_none()
        if not department:
            # Auto-create department since DB is fresh
            department = Department(
                code=data.department_code, 
                name=f"{data.department_code} Department"
            )
            db.add(department)
            await db.flush()

        faculty = Faculty(
            id=user.id,
            department_id=department.id,
            is_hod=(data.role == "hod"),
        )
        db.add(faculty)

    return user


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(request: Request, data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return JWT tokens."""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    access_token = create_access_token({"sub": str(user.id), "role": user.role})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Exchange a refresh token for a new access token."""
    payload = decode_token(request.refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type — expected refresh token",
        )

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    access_token = create_access_token({"sub": str(user.id), "role": user.role})
    new_refresh_token = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(access_token=access_token, refresh_token=new_refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return current_user

@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Reset password using JWT generated by Admin panel."""
    payload = decode_token(data.token)
    
    if payload.get("type") != "reset":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token type — expected reset token",
        )
        
    # Check single use atomicity via Redis
    token_hash = hashlib.sha256(data.token.encode()).hexdigest()
    redis_key = f"used_reset_token:{token_hash}"
    r = aioredis.from_url(get_settings().REDIS_URL, decode_responses=True)
    
    try:
        # SETNX equivalent (set if not exists)
        is_new = await r.set(redis_key, "1", ex=86400, nx=True)
        if not is_new:
            raise HTTPException(status_code=400, detail="Token has already been used.")
    finally:
        await r.aclose()
        
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.password_hash = hash_password(data.new_password)
    # Could optionally bump a user version to invalidate existing JWTs
    await db.commit()
    
    return MessageResponse(message="Password has been reset successfully.")
