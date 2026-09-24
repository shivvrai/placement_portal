import csv
import io
import uuid
from typing import Optional
import secrets
from fastapi import APIRouter, Depends, Query, UploadFile, File, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from jose import jwt
from datetime import datetime, timedelta, timezone

from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker, hash_password
from app.core.config import get_settings
from app.core.audit import record_audit_event
from app.models.user import User, Student, Department
from app.schemas.common import PaginatedResponse, PaginationMeta

router = APIRouter(prefix="/admin", tags=["Admin Panel"])
_admin_only = RoleChecker(["admin"])
settings = get_settings()

@router.get("/users")
async def get_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    role: Optional[str] = None,
    current_user: User = Depends(_admin_only),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(User)
    if role:
        stmt = stmt.where(User.role == role)
        
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = await db.execute(count_stmt)
    total = total.scalar_one()
    
    stmt = stmt.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(stmt)
    users = result.scalars().all()
    
    data = []
    for u in users:
        data.append({
            "id": u.id,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": u.created_at
        })
        
    return PaginatedResponse(
        data=data,
        meta=PaginationMeta(page=page, per_page=per_page, total=total, total_pages=(total + per_page - 1) // per_page)
    )

@router.patch("/users/{user_id}/role")
async def update_user_role(
    user_id: uuid.UUID,
    new_role: str = Query(...),
    request: Request = None,
    current_user: User = Depends(_admin_only),
    db: AsyncSession = Depends(get_db)
):
    valid_roles = ["student", "tpo", "faculty", "hod", "admin"]
    if new_role not in valid_roles:
        raise HTTPException(status_code=400, detail="Invalid role")
        
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    old_role = user.role
    user.role = new_role
    
    await record_audit_event(
        db, current_user.id, "USER_ROLE_UPDATED", "User", str(user.id),
        {"old_role": old_role, "new_role": new_role},
        request.client.host if request else None
    )
    
    await db.commit()
    return {"message": "Role updated successfully"}

@router.patch("/users/{user_id}/status")
async def update_user_status(
    user_id: uuid.UUID,
    is_active: bool = Query(...),
    request: Request = None,
    current_user: User = Depends(_admin_only),
    db: AsyncSession = Depends(get_db)
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    old_status = user.is_active
    user.is_active = is_active
    
    await record_audit_event(
        db, current_user.id, "USER_STATUS_UPDATED", "User", str(user.id),
        {"old_active": old_status, "new_active": is_active},
        request.client.host if request else None
    )
    
    await db.commit()
    return {"message": "Status updated successfully"}

@router.post("/users/{user_id}/generate-reset-link")
async def generate_reset_link(
    user_id: uuid.UUID,
    request: Request = None,
    current_user: User = Depends(_admin_only),
    db: AsyncSession = Depends(get_db)
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    payload = {"sub": str(user_id), "type": "reset", "exp": expire}
    reset_token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    await record_audit_event(
        db, current_user.id, "PASSWORD_RESET_LINK_GENERATED", "User", str(user.id),
        {}, request.client.host if request else None
    )
    await db.commit()
    
    # In a real app we might construct a fully qualified domain based on origin
    return {"reset_link": f"/reset-password?token={reset_token}"}

@router.post("/users/bulk-import")
async def bulk_import_users(
    file: UploadFile = File(...),
    request: Request = None,
    current_user: User = Depends(_admin_only),
    db: AsyncSession = Depends(get_db)
):
    content = await file.read()
    text = content.decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(text))
    
    results = []
    
    for row in csv_reader:
        try:
            email = row['email'].strip()
            first_name = row['first_name'].strip()
            last_name = row['last_name'].strip()
            roll_number = row.get('roll_number', '').strip()
            department_code = row.get('department', '').strip()
            
            # Check exist
            existing = await db.execute(select(User).where(User.email == email))
            if existing.scalar_one_or_none():
                results.append({"email": email, "status": "failed", "reason": "Email already exists"})
                continue
                
            # Random securely hashed password since it's inaccessible
            raw_pass = secrets.token_urlsafe(16)
            hashed = hash_password(raw_pass)
            
            user = User(
                email=email,
                first_name=first_name,
                last_name=last_name,
                password_hash=hashed,
                role="student"
            )
            db.add(user)
            await db.flush()
            
            if department_code:
                dept_res = await db.execute(select(Department).where(Department.code == department_code))
                dept = dept_res.scalar_one_or_none()
                if not dept:
                    dept = Department(code=department_code, name=f"{department_code} Department")
                    db.add(dept)
                    await db.flush()
            else:
                 # Default generic dept if missing
                 dept_res = await db.execute(select(Department).where(Department.code == "GEN"))
                 dept = dept_res.scalar_one_or_none()
                 if not dept:
                     dept = Department(code="GEN", name="General Department")
                     db.add(dept)
                     await db.flush()
                     
            student = Student(
                id=user.id,
                roll_number=roll_number or str(user.id)[:8],
                department_id=dept.id,
                current_semester=1,
                admission_year=datetime.utcnow().year
            )
            db.add(student)
            
            # Generate reset token for export
            expire = datetime.now(timezone.utc) + timedelta(hours=24)
            payload = {"sub": str(user.id), "type": "reset", "exp": expire}
            reset_token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
            
            results.append({"email": email, "status": "success", "reset_link": f"/reset-password?token={reset_token}"})
            
        except Exception as e:
            results.append({"email": row.get('email', 'unknown'), "status": "failed", "reason": str(e)})

    await record_audit_event(
        db, current_user.id, "BULK_IMPORT_EXECUTED", "System", "bulk",
        {"total_processed": len(results)}, request.client.host if request else None
    )
    
    await db.commit()
    return {"results": results}

@router.get("/metrics/summary")
async def get_metrics_summary(current_user: User = Depends(_admin_only), db: AsyncSession = Depends(get_db)):
    tot_users = await db.execute(select(func.count(User.id)))
    act_students = await db.execute(select(func.count(Student.id)).join(User).where(User.is_active == True))
    
    from app.models.placement import PlacementDrive, Application
    drives_open = await db.execute(select(func.count(PlacementDrive.id)).where(PlacementDrive.status == "open"))
    # Approx for today
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    apps_today = await db.execute(select(func.count(Application.id)).where(Application.applied_at >= today))
    
    return {
        "total_users": tot_users.scalar_one(),
        "active_students": act_students.scalar_one(),
        "drives_open": drives_open.scalar_one(),
        "applications_today": apps_today.scalar_one(),
        "error_rate_24h": 0.0  # Placeholder unless queried from AuditLog
    }

@router.get("/settings")
async def get_settings_dummy(current_user: User = Depends(_admin_only)):
    return {
         "academic_year": "2026-2027",
         "cgpa_floor": 6.0,
         "student_self_reg": True
    }

@router.patch("/settings")
async def update_settings_dummy(data: dict, current_user: User = Depends(_admin_only)):
    return {"message": "Settings updated"}
