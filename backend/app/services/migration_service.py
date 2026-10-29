"""
CCIP Institutional Migration & Bulk Ingestion Service.

Handles:
  1. Student Master Roster onboarding (Excel / CSV) with auto-provisioning
     - Auto-generates student email if omitted ({roll}@ccip.edu)
     - Sets default initial password (e.g. student123 or custom)
     - Exports downloadable credentials CSV for administrative distribution
  2. Template generation (.xlsx / .csv) for student roster
"""

import io
import re
import uuid
import secrets
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.security import hash_password
from app.models.user import User, Student, Department
from app.models.skill import Skill, StudentSkill


# ─── Dynamic Column Name Matcher ──────────────────────────────────────────────

COLUMN_ALIASES = {
    "roll_number": ["roll_number", "roll_no", "rollno", "roll", "reg_no", "regno", "registration_no", "registration_number", "urn", "student_id", "id_number", "enrollment_no"],
    "name": ["name", "student_name", "full_name", "candidate_name"],
    "first_name": ["first_name", "firstname", "first"],
    "last_name": ["last_name", "lastname", "last", "surname"],
    "email": ["email", "student_email", "mail_id", "email_id", "email_address"],
    "phone": ["phone", "mobile", "contact", "phone_number", "mobile_number", "cell"],
    "department": ["department", "dept", "branch", "stream", "course", "program", "discipline"],
    "semester": ["semester", "sem", "current_semester", "current_sem"],
    "admission_year": ["admission_year", "joining_year", "batch_start", "year_of_admission", "batch"],
    "cgpa": ["cgpa", "gpa", "overall_cgpa", "aggregate_cgpa", "score"],
    "skills": ["skills", "technical_skills", "skill_set", "key_skills", "competencies"],
}


def _match_column(col_name: str) -> Optional[str]:
    """Matches a messy column header from Excel/CSV to a canonical key."""
    norm = re.sub(r'[^a-zA-Z0-9_]', '_', str(col_name).strip().lower())
    norm = re.sub(r'_+', '_', norm).strip('_')
    for canonical, aliases in COLUMN_ALIASES.items():
        if norm in aliases or any(alias in norm for alias in aliases):
            return canonical
    return None


def parse_spreadsheet(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Reads Excel (.xlsx, .xls) or CSV into a clean pandas DataFrame."""
    fn = filename.lower()
    if fn.endswith('.csv'):
        try:
            df = pd.read_csv(io.BytesIO(file_bytes), encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(io.BytesIO(file_bytes), encoding='latin1')
    elif fn.endswith(('.xlsx', '.xls')):
        df = pd.read_excel(io.BytesIO(file_bytes))
    else:
        raise ValueError(f"Unsupported file format '{filename}'. Please upload .xlsx, .xls, or .csv")

    df = df.dropna(how='all')
    df = df.dropna(how='all', axis=1)
    return df


# ─── Schema Guidance & Descriptions ──────────────────────────────────────────

STUDENT_SCHEMA_GUIDE = [
    {
        "field": "roll_number",
        "label": "Roll Number / Registration No",
        "required": True,
        "sample": "CS21B012",
        "aliases": "Roll No, Reg No, Registration Number, URN, Student ID",
        "description": "Unique institutional student registration or roll number.",
        "fallback": "Strictly required. Cannot be empty."
    },
    {
        "field": "name",
        "label": "Student Full Name",
        "required": True,
        "sample": "Aarav Sharma",
        "aliases": "Full Name, Student Name, or separate First Name / Last Name columns",
        "description": "Student's legal name. Can be one column or separate First/Last.",
        "fallback": "Strictly required. If single name given, defaults last name to student's initial."
    },
    {
        "field": "department",
        "label": "Department / Branch",
        "required": True,
        "sample": "CSE",
        "aliases": "Dept, Branch, Stream, Discipline",
        "description": "Academic department (e.g. CSE, IT, ECE, ME, CE, AI, DS).",
        "fallback": "If department code doesn't exist, CCIP will auto-create it."
    },
    {
        "field": "email",
        "label": "Email Address",
        "required": False,
        "sample": "aarav.sharma@ccip.edu",
        "aliases": "Mail ID, Email ID",
        "description": "Student email address for platform notifications and login.",
        "fallback": "⚡ Auto-generated if omitted: {roll_number.lower()}@ccip.edu"
    },
    {
        "field": "phone",
        "label": "Phone Number",
        "required": False,
        "sample": "9876543210",
        "aliases": "Mobile, Contact No",
        "description": "Primary contact number.",
        "fallback": "Optional (left blank if not provided)."
    },
    {
        "field": "current_semester",
        "label": "Current Semester",
        "required": False,
        "sample": "6",
        "aliases": "Sem, Current Sem",
        "description": "Current semester number (1 to 8).",
        "fallback": "Defaults to semester 1 if not specified."
    },
    {
        "field": "admission_year",
        "label": "Admission Year",
        "required": False,
        "sample": "2022",
        "aliases": "Joining Year, Batch",
        "description": "Year student enrolled in the institution.",
        "fallback": "Defaults to current calendar year if omitted."
    },
    {
        "field": "cgpa",
        "label": "Cumulative GPA (CGPA)",
        "required": False,
        "sample": "8.45",
        "aliases": "GPA, Aggregate CGPA",
        "description": "Overall academic performance out of 10.0.",
        "fallback": "Optional. Defaults to null until entered."
    },
    {
        "field": "skills",
        "label": "Known Skills (Comma-separated)",
        "required": False,
        "sample": "Python, React, SQL, Data Structures",
        "aliases": "Technical Skills, Skillset",
        "description": "Skills to automatically tag onto student's profile.",
        "fallback": "Optional."
    },
]


# ─── Preview & Validation Logic ───────────────────────────────────────────────

async def preview_student_migration(file_bytes: bytes, filename: str, db: AsyncSession) -> Dict[str, Any]:
    """Analyzes a student roster file and generates a validation preview."""
    df = parse_spreadsheet(file_bytes, filename)
    
    col_mapping = {}
    for col in df.columns:
        canonical = _match_column(col)
        if canonical:
            col_mapping[col] = canonical

    mapped_canonicals = set(col_mapping.values())
    has_name = "name" in mapped_canonicals or ("first_name" in mapped_canonicals and "last_name" in mapped_canonicals)
    has_roll = "roll_number" in mapped_canonicals
    has_dept = "department" in mapped_canonicals

    missing_required = []
    if not has_roll: missing_required.append("Roll Number / Registration No")
    if not has_name: missing_required.append("Student Name")
    if not has_dept: missing_required.append("Department / Branch")

    existing_rolls_res = await db.execute(select(Student.roll_number))
    existing_rolls = {r.strip().lower() for (r,) in existing_rolls_res.all()}

    preview_rows = []
    valid_count = 0
    duplicate_count = 0
    seen_rolls_in_sheet = set()

    for idx, row in df.iterrows():
        record = {}
        for original_col, canonical in col_mapping.items():
            val = row[original_col]
            if pd.notna(val):
                record[canonical] = str(val).strip()

        roll = record.get("roll_number", "").strip()
        if not roll:
            continue

        roll_lower = roll.lower()
        is_dup = roll_lower in existing_rolls or roll_lower in seen_rolls_in_sheet
        seen_rolls_in_sheet.add(roll_lower)

        name = record.get("name", "")
        if not name:
            fname = record.get("first_name", "")
            lname = record.get("last_name", "")
            name = f"{fname} {lname}".strip() or f"Student {roll}"

        raw_email = record.get("email", "")
        auto_email = False
        if not raw_email or "@" not in raw_email:
            email = f"{roll_lower}@ccip.edu"
            auto_email = True
        else:
            email = raw_email.lower()

        dept = record.get("department", "CSE").upper()
        cgpa_val = None
        if record.get("cgpa"):
            try:
                cgpa_val = float(record.get("cgpa"))
            except:
                pass

        row_info = {
            "row_number": idx + 2,
            "roll_number": roll,
            "name": name,
            "email": email,
            "auto_generated_email": auto_email,
            "department": dept,
            "cgpa": cgpa_val,
            "semester": int(float(record.get("semester", 1))) if record.get("semester") else 1,
            "phone": record.get("phone", ""),
            "status": "conflict" if is_dup else "ready",
            "conflict_reason": "Roll number already registered in platform or duplicate in sheet" if is_dup else None,
        }

        if is_dup:
            duplicate_count += 1
        else:
            valid_count += 1

        if len(preview_rows) < 10:
            preview_rows.append(row_info)

    return {
        "filename": filename,
        "total_rows_found": len(df),
        "valid_rows_count": valid_count,
        "duplicate_rows_count": duplicate_count,
        "can_import": len(missing_required) == 0 and (valid_count > 0 or duplicate_count > 0),
        "missing_required_columns": missing_required,
        "detected_columns": col_mapping,
        "preview_sample": preview_rows,
        "default_password": "student123",
    }


# ─── Execution & Database Commit ─────────────────────────────────────────────

async def execute_student_migration(
    file_bytes: bytes,
    filename: str,
    db: AsyncSession,
    default_password: str = "student123",
    conflict_strategy: str = "skip",
) -> Dict[str, Any]:
    """Imports verified student records, provisions accounts, and returns credentials sheet."""
    df = parse_spreadsheet(file_bytes, filename)

    col_mapping = {}
    for col in df.columns:
        canonical = _match_column(col)
        if canonical:
            col_mapping[col] = canonical

    existing_rolls_res = await db.execute(select(Student.roll_number))
    existing_rolls = {r.strip().lower() for (r,) in existing_rolls_res.all()}

    existing_emails_res = await db.execute(select(User.email))
    existing_emails = {e.strip().lower() for (e,) in existing_emails_res.all()}

    depts_res = await db.execute(select(Department))
    dept_map = {d.code.upper(): d for d in depts_res.scalars().all()}

    pwd_hash = hash_password(default_password)

    imported_credentials = []
    new_imported_count = 0
    updated_count = 0
    skipped_count = 0
    seen_in_batch = set()

    def safe_float(v, default=None):
        try:
            return float(v) if v is not None and str(v).strip() != '' else default
        except:
            return default

    def safe_int(v, default=1):
        try:
            return int(float(v)) if v is not None and str(v).strip() != '' else default
        except:
            return default

    for _, row in df.iterrows():
        record = {}
        for original_col, canonical in col_mapping.items():
            val = row[original_col]
            if pd.notna(val):
                record[canonical] = str(val).strip()

        roll = record.get("roll_number", "").strip()
        if not roll:
            skipped_count += 1
            continue

        roll_lower = roll.lower()

        # Discard repeated duplicate rows inside the same uploaded spreadsheet
        if roll_lower in seen_in_batch:
            skipped_count += 1
            continue
        seen_in_batch.add(roll_lower)

        name = record.get("name", "").strip()
        if not name:
            first_name = record.get("first_name", "Student").strip()
            last_name = record.get("last_name", roll).strip()
            name = f"{first_name} {last_name}".strip()
        else:
            parts = name.split(maxsplit=1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else "."

        raw_email = record.get("email", "").strip().lower()
        if not raw_email or "@" not in raw_email:
            email = f"{roll_lower}@ccip.edu"
        else:
            email = raw_email

        dept_code = record.get("department", "CSE").strip().upper()
        dept = dept_map.get(dept_code)
        if not dept:
            dept = Department(code=dept_code, name=f"{dept_code} Department")
            db.add(dept)
            await db.flush()
            dept_map[dept_code] = dept

        sem = safe_int(record.get("semester", 1), 1)
        adm_year = safe_int(record.get("admission_year", datetime.now().year), datetime.now().year)
        cgpa_val = safe_float(record.get("cgpa"))
        phone = record.get("phone", None)
        skills_str = record.get("skills", "")

        # ── Handle Existing Student Conflicts ──
        if roll_lower in existing_rolls:
            if conflict_strategy == "update":
                st_stmt = select(Student).where(func.lower(Student.roll_number) == roll_lower)
                existing_st = (await db.execute(st_stmt)).scalar_one_or_none()
                if existing_st:
                    # Overwrite/update academic properties
                    if cgpa_val is not None:
                        existing_st.cgpa = cgpa_val
                    existing_st.current_semester = sem
                    existing_st.admission_year = adm_year
                    existing_st.department_id = dept.id

                    # Update user details
                    existing_user = await db.get(User, existing_st.id)
                    if existing_user:
                        if name:
                            existing_user.first_name = first_name
                            existing_user.last_name = last_name
                        if phone:
                            existing_user.phone = phone

                    # Link new skills if present
                    if skills_str:
                        skill_tokens = [s.strip() for s in str(skills_str).split(",") if s.strip()]
                        for token in skill_tokens[:10]:
                            sk_res = await db.execute(select(Skill).where(func.lower(Skill.name) == token.lower()))
                            sk = sk_res.scalars().first()
                            if not sk:
                                sk = Skill(name=token, normalized_name=token.strip().lower(), category="tool")
                                db.add(sk)
                                await db.flush()

                            chk_res = await db.execute(
                                select(StudentSkill).where(
                                    StudentSkill.student_id == existing_st.id,
                                    StudentSkill.skill_id == sk.id
                                )
                            )
                            if not chk_res.scalars().first():
                                st_sk = StudentSkill(
                                    student_id=existing_st.id,
                                    skill_id=sk.id,
                                    source="manual",
                                    proficiency_level="Intermediate",
                                    is_verified=True
                                )
                                db.add(st_sk)

                    updated_count += 1
                    imported_credentials.append({
                        "roll_number": roll,
                        "name": name,
                        "email": existing_user.email if existing_user else email,
                        "department": dept.code,
                        "temporary_password": "(Existing Password Unchanged)",
                        "status": "Updated Existing Record",
                        "login_url": "/login"
                    })
                    continue
            else:
                # Default "skip" strategy
                skipped_count += 1
                continue

        # ── Provision New Student ──
        if email in existing_emails:
            email = f"{roll_lower}_{secrets.token_hex(2)}@ccip.edu"
        existing_emails.add(email)

        # Create User
        user = User(
            email=email,
            password_hash=pwd_hash,
            role="student",
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            is_active=True,
        )
        db.add(user)
        await db.flush()

        # Create Student profile with only valid columns
        student = Student(
            id=user.id,
            roll_number=roll,
            department_id=dept.id,
            current_semester=sem,
            admission_year=adm_year,
            cgpa=cgpa_val,
        )
        db.add(student)

        # If skills specified, link skills
        if skills_str:
            skill_tokens = [s.strip() for s in str(skills_str).split(",") if s.strip()]
            for token in skill_tokens[:10]:
                sk_res = await db.execute(select(Skill).where(func.lower(Skill.name) == token.lower()))
                sk = sk_res.scalars().first()
                if not sk:
                    sk = Skill(name=token, normalized_name=token.strip().lower(), category="tool")
                    db.add(sk)
                    await db.flush()
                st_sk = StudentSkill(
                    student_id=student.id,
                    skill_id=sk.id,
                    source="manual",
                    proficiency_level="Intermediate",
                    is_verified=True
                )
                db.add(st_sk)

        new_imported_count += 1
        imported_credentials.append({
            "roll_number": roll,
            "name": name,
            "email": email,
            "department": dept.code,
            "temporary_password": default_password,
            "status": "New Student Provisioned",
            "login_url": "/login"
        })

    await db.commit()

    return {
        "success": True,
        "imported_count": new_imported_count,
        "updated_count": updated_count,
        "skipped_count": skipped_count,
        "conflict_strategy_applied": conflict_strategy,
        "default_password": default_password,
        "credentials": imported_credentials,
    }


# ─── Sample Template Generators (.xlsx & .csv) ────────────────────────────────

def generate_sample_student_template(format_type: str = "xlsx") -> bytes:
    """Generates a pre-formatted sample spreadsheet with headers and realistic student records."""
    sample_data = [
        {
            "Roll Number": "CS21B001",
            "Student Name": "Aarav Sharma",
            "Department": "CSE",
            "Email": "aarav.sharma@ccip.edu",
            "Phone": "9876543210",
            "Semester": 6,
            "Admission Year": 2022,
            "CGPA": 8.75,
            "Skills": "Python, React, SQL, Git"
        },
        {
            "Roll Number": "CS21B002",
            "Student Name": "Ananya Verma",
            "Department": "CSE",
            "Email": "",  # Blank to show auto-generation feature!
            "Phone": "9876543211",
            "Semester": 6,
            "Admission Year": 2022,
            "CGPA": 9.10,
            "Skills": "Java, Spring Boot, AWS, Docker"
        },
        {
            "Roll Number": "IT21B015",
            "Student Name": "Rohan Patel",
            "Department": "IT",
            "Email": "rohan.patel@ccip.edu",
            "Phone": "9876543212",
            "Semester": 6,
            "Admission Year": 2022,
            "CGPA": 7.85,
            "Skills": "C++, Data Structures, Linux"
        },
        {
            "Roll Number": "EC21B030",
            "Student Name": "Sneha Reddy",
            "Department": "ECE",
            "Email": "",  # Blank to show auto-generation feature!
            "Phone": "9876543213",
            "Semester": 6,
            "Admission Year": 2022,
            "CGPA": 8.40,
            "Skills": "Embedded Systems, Python, Verilog"
        },
        {
            "Roll Number": "AI21B005",
            "Student Name": "Devansh Gupta",
            "Department": "AI",
            "Email": "devansh.g@ccip.edu",
            "Phone": "9876543214",
            "Semester": 6,
            "Admission Year": 2022,
            "CGPA": 9.35,
            "Skills": "Machine Learning, PyTorch, Pandas, Scikit-Learn"
        }
    ]

    df = pd.DataFrame(sample_data)

    if format_type == "csv":
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        return buf.getvalue().encode('utf-8')
    else:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name="Student Master Roster")
        return buf.getvalue()
