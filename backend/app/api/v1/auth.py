"""
Auth API router — register, login, refresh, me.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

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

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user. Students require roll_number and department_code."""
    # Check if email already exists
    existing = await db.execute(select(User).where(User.email == request.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Create user
    user = User(
        email=request.email,
        password_hash=hash_password(request.password),
        role=request.role,
        first_name=request.first_name,
        last_name=request.last_name,
        phone=request.phone,
    )
    db.add(user)
    await db.flush()  # Get user.id before creating student

    # If student, create student profile
    if request.role == "student":
        if not request.roll_number or not request.department_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Students must provide roll_number and department_code",
            )

        # Look up department
        dept_result = await db.execute(
            select(Department).where(Department.code == request.department_code)
        )
        department = dept_result.scalar_one_or_none()
        if not department:
            # Auto-create department since DB is fresh
            department = Department(
                code=request.department_code, 
                name=f"{request.department_code} Department"
            )
            db.add(department)
            await db.flush()

        student = Student(
            id=user.id,
            roll_number=request.roll_number,
            department_id=department.id,
            current_semester=request.current_semester or 1,
            admission_year=request.admission_year or 2023,
        )
        db.add(student)

    elif request.role in ("faculty", "hod"):
        if not request.department_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Faculty must provide department_code",
            )
        dept_result = await db.execute(
            select(Department).where(Department.code == request.department_code)
        )
        department = dept_result.scalar_one_or_none()
        if not department:
            # Auto-create department since DB is fresh
            department = Department(
                code=request.department_code, 
                name=f"{request.department_code} Department"
            )
            db.add(department)
            await db.flush()

        faculty = Faculty(
            id=user.id,
            department_id=department.id,
            is_hod=(request.role == "hod"),
        )
        db.add(faculty)

    return user


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return JWT tokens."""
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.password_hash):
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
