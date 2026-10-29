"""
Exam Upload Service — handles file parsing (PDF/Excel/CSV), data extraction,
roll-number matching, and rank computation.
"""

import uuid
import re
from pathlib import Path
from typing import Optional

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models.exam_upload import ExamUpload, ExamStudentResult
from app.models.user import Student, User


# ─── Helpers ────────────────────────────────────────────────────────

def _detect_roll_column(columns: list[str]) -> Optional[str]:
    """Try to auto-detect which column holds the roll number."""
    patterns = [
        r"roll.*no", r"roll.*num", r"roll", r"enrollment",
        r"reg.*no", r"registration", r"student.*id", r"id.*no",
        r"prn", r"usn", r"urn",
    ]
    for col in columns:
        cl = col.lower().strip()
        for pat in patterns:
            if re.search(pat, cl):
                return col
    return None


def _detect_name_column(columns: list[str]) -> Optional[str]:
    """Try to auto-detect which column holds the student name."""
    patterns = [
        r"student.*name", r"name.*student", r"full.*name",
        r"^name$", r"candidate.*name",
    ]
    for col in columns:
        cl = col.lower().strip()
        for pat in patterns:
            if re.search(pat, cl):
                return col
    return None


def _detect_section_column(columns: list[str]) -> Optional[str]:
    """Try to auto-detect which column holds section info."""
    patterns = [r"section", r"sec", r"batch", r"group"]
    for col in columns:
        cl = col.lower().strip()
        for pat in patterns:
            if re.search(pat, cl):
                return col
    return None


def _detect_department_column(columns: list[str]) -> Optional[str]:
    """Try to auto-detect which column holds department info."""
    patterns = [r"dept", r"department", r"branch", r"stream"]
    for col in columns:
        cl = col.lower().strip()
        for pat in patterns:
            if re.search(pat, cl):
                return col
    return None


def _detect_rank_column(columns: list[str]) -> Optional[str]:
    """
    Try to auto-detect the best numeric column to rank students by.
    Prefers 'total', 'marks', 'score', 'percentage', 'aggregate'.
    """
    patterns = [
        r"total.*marks", r"total.*score", r"total",
        r"aggregate", r"percentage", r"percent",
        r"marks.*obtained", r"score", r"marks",
        r"cgpa", r"sgpa", r"gpa",
    ]
    for pat in patterns:
        for col in columns:
            if re.search(pat, col.lower().strip()):
                return col
    return None


def _parse_excel(file_path: str) -> pd.DataFrame:
    """Parse Excel (.xlsx, .xls) file into DataFrame."""
    df = pd.read_excel(file_path, engine=None)
    # Drop completely empty rows and columns
    df = df.dropna(how="all").dropna(axis=1, how="all")
    # Clean column names
    df.columns = [str(c).strip() for c in df.columns]
    return df


def _parse_csv(file_path: str) -> pd.DataFrame:
    """Parse CSV file into DataFrame."""
    df = pd.read_csv(file_path)
    df = df.dropna(how="all").dropna(axis=1, how="all")
    df.columns = [str(c).strip() for c in df.columns]
    return df


def _parse_pdf(file_path: str) -> pd.DataFrame:
    """Parse PDF file — extract tables using pdfplumber."""
    import pdfplumber

    all_rows = []
    headers = None

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                if not table:
                    continue
                for i, row in enumerate(table):
                    if headers is None:
                        # First row of first table = headers
                        headers = [str(c).strip() if c else f"Column_{j}" for j, c in enumerate(row)]
                    else:
                        all_rows.append(row)

    if not headers:
        raise ValueError("No tables found in the PDF file.")

    # Ensure all rows have the same number of columns as headers
    cleaned_rows = []
    for row in all_rows:
        if len(row) < len(headers):
            row = list(row) + [None] * (len(headers) - len(row))
        elif len(row) > len(headers):
            row = row[: len(headers)]
        cleaned_rows.append(row)

    df = pd.DataFrame(cleaned_rows, columns=headers)
    df = df.dropna(how="all")
    return df


def _parse_file(file_path: str, file_type: str) -> pd.DataFrame:
    """Route to the right parser based on file type."""
    if file_type in ("xlsx", "xls"):
        return _parse_excel(file_path)
    elif file_type == "csv":
        return _parse_csv(file_path)
    elif file_type == "pdf":
        return _parse_pdf(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")


def _compute_ranks(results: list[ExamStudentResult], rank_column: str):
    """Compute ranks for student results based on the rank column (descending)."""
    # Extract numeric values
    scored = []
    for r in results:
        val = r.row_data.get(rank_column)
        try:
            numeric_val = float(val) if val is not None else None
        except (ValueError, TypeError):
            numeric_val = None
        scored.append((r, numeric_val))

    # Sort descending by score (None values go last)
    scored.sort(key=lambda x: (x[1] is None, -(x[1] or 0)))

    # Assign ranks (1-based, dense ranking)
    current_rank = 0
    last_val = None
    for i, (result, val) in enumerate(scored):
        if val is None:
            result.rank = None
        else:
            if val != last_val:
                current_rank = i + 1
            result.rank = current_rank
            last_val = val


# ─── Main Service ───────────────────────────────────────────────────

async def process_exam_upload(
    db: AsyncSession,
    upload_id: uuid.UUID,
) -> ExamUpload:
    """
    Parse the uploaded file, extract student data, match roll numbers,
    compute ranks, and save everything to the database.
    """
    upload = await db.get(ExamUpload, upload_id)
    if not upload:
        raise ValueError(f"Upload {upload_id} not found")

    try:
        # Parse the file
        df = _parse_file(upload.file_path, upload.file_type)

        if df.empty:
            upload.status = "failed"
            await db.commit()
            raise ValueError("No data found in the uploaded file.")

        columns = list(df.columns)
        upload.column_headers = columns
        upload.total_rows = len(df)
        upload.total_columns = len(columns)

        # Auto-detect special columns
        roll_col = _detect_roll_column(columns)
        name_col = _detect_name_column(columns)
        section_col = _detect_section_column(columns)
        dept_col = _detect_department_column(columns)
        rank_col = upload.rank_column or _detect_rank_column(columns)

        if rank_col:
            upload.rank_column = rank_col

        # Load existing students for roll number matching
        roll_to_student = {}
        if roll_col:
            roll_values = df[roll_col].dropna().astype(str).str.strip().tolist()
            if roll_values:
                stmt = select(Student).where(Student.roll_number.in_(roll_values))
                result = await db.execute(stmt)
                for student in result.scalars().all():
                    roll_to_student[student.roll_number.upper()] = student.id

        # Create student result records
        student_results = []
        for _, row in df.iterrows():
            row_data = {}
            for col in columns:
                val = row[col]
                # Convert NaN to None, and everything else to string for JSON
                if pd.isna(val):
                    row_data[col] = None
                elif isinstance(val, (int, float)):
                    row_data[col] = val
                else:
                    row_data[col] = str(val)

            roll = str(row_data.get(roll_col, "")).strip().upper() if roll_col else None
            name = str(row_data.get(name_col, "")).strip() if name_col else None
            section = str(row_data.get(section_col, "")).strip() if section_col else upload.section
            dept = str(row_data.get(dept_col, "")).strip() if dept_col else upload.department

            student_result = ExamStudentResult(
                exam_upload_id=upload_id,
                roll_number=roll if roll and roll != "NONE" and roll != "NAN" else None,
                student_name=name if name and name != "NONE" and name != "NAN" else None,
                student_id=roll_to_student.get(roll) if roll else None,
                row_data=row_data,
                section=section if section and section != "None" else None,
                department=dept if dept and dept != "None" else None,
            )
            student_results.append(student_result)

        # Compute ranks if rank column exists
        if rank_col:
            _compute_ranks(student_results, rank_col)

        db.add_all(student_results)
        upload.status = "completed"
        await db.commit()
        await db.refresh(upload)

        return upload

    except Exception as e:
        upload.status = "failed"
        await db.commit()
        raise


async def list_uploads(
    db: AsyncSession,
    department: Optional[str] = None,
    section: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[ExamUpload]:
    """List all exam uploads, optionally filtered by department/section."""
    stmt = select(ExamUpload).order_by(ExamUpload.created_at.desc())
    if department:
        stmt = stmt.where(ExamUpload.department == department)
    if section:
        stmt = stmt.where(ExamUpload.section == section)
    stmt = stmt.limit(limit).offset(offset)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_upload_detail(
    db: AsyncSession,
    upload_id: uuid.UUID,
) -> dict:
    """Get full upload details including all student results."""
    upload = await db.get(ExamUpload, upload_id)
    if not upload:
        return None

    stmt = (
        select(ExamStudentResult)
        .where(ExamStudentResult.exam_upload_id == upload_id)
        .order_by(ExamStudentResult.rank.asc().nullslast())
    )
    result = await db.execute(stmt)
    results = list(result.scalars().all())

    return {
        "upload": upload,
        "results": results,
    }


async def get_student_results(
    db: AsyncSession,
    student_id: uuid.UUID = None,
    roll_number: str = None,
) -> list[dict]:
    """Get all exam results for a specific student."""
    stmt = select(ExamStudentResult).options(
        selectinload(ExamStudentResult.exam_upload)
    )
    if student_id:
        stmt = stmt.where(ExamStudentResult.student_id == student_id)
    elif roll_number:
        stmt = stmt.where(ExamStudentResult.roll_number == roll_number.upper())
    else:
        return []

    stmt = stmt.order_by(ExamStudentResult.created_at.desc())
    result = await db.execute(stmt)
    results = list(result.scalars().all())

    out = []
    for r in results:
        upload = r.exam_upload
        out.append({
            "id": str(r.id),
            "exam_title": upload.title if upload else "Unknown",
            "exam_type": upload.exam_type if upload else None,
            "department": r.department or (upload.department if upload else None),
            "section": r.section or (upload.section if upload else None),
            "roll_number": r.roll_number,
            "student_name": r.student_name,
            "row_data": r.row_data,
            "rank": r.rank,
            "total_students": upload.total_rows if upload else None,
            "rank_column": upload.rank_column if upload else None,
            "exam_date": upload.created_at.isoformat() if upload else None,
        })
    return out


async def get_section_results(
    db: AsyncSession,
    upload_id: uuid.UUID,
    section: Optional[str] = None,
    department: Optional[str] = None,
) -> list[ExamStudentResult]:
    """Get results for a specific section/department within an upload."""
    stmt = (
        select(ExamStudentResult)
        .where(ExamStudentResult.exam_upload_id == upload_id)
    )
    if section:
        stmt = stmt.where(ExamStudentResult.section == section)
    if department:
        stmt = stmt.where(ExamStudentResult.department == department)
    stmt = stmt.order_by(ExamStudentResult.rank.asc().nullslast())

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_upload_stats(db: AsyncSession, upload_id: uuid.UUID) -> dict:
    """Get statistics for an uploaded exam."""
    upload = await db.get(ExamUpload, upload_id)
    if not upload or not upload.rank_column:
        return {}

    stmt = select(ExamStudentResult).where(ExamStudentResult.exam_upload_id == upload_id)
    result = await db.execute(stmt)
    results = list(result.scalars().all())

    if not results:
        return {}

    rank_col = upload.rank_column
    scores = []
    for r in results:
        val = r.row_data.get(rank_col)
        try:
            scores.append(float(val))
        except (ValueError, TypeError):
            pass

    if not scores:
        return {}

    return {
        "total_students": len(results),
        "rank_column": rank_col,
        "highest": max(scores),
        "lowest": min(scores),
        "average": round(sum(scores) / len(scores), 2),
        "median": round(sorted(scores)[len(scores) // 2], 2),
        "above_average": sum(1 for s in scores if s >= sum(scores) / len(scores)),
        "pass_count": sum(1 for s in scores if s >= 0.4 * max(scores)),  # 40% passing
        "fail_count": sum(1 for s in scores if s < 0.4 * max(scores)),
    }


async def delete_upload(db: AsyncSession, upload_id: uuid.UUID) -> bool:
    """Delete an upload and all associated results."""
    upload = await db.get(ExamUpload, upload_id)
    if not upload:
        return False
    await db.delete(upload)
    await db.commit()
    return True
