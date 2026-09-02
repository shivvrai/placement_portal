"""
JD Parser — extract structured information from job description text.

Extracts:
  - Required skills
  - Preferred skills
  - CGPA / GPA requirements
  - Experience requirements
  - Eligible departments / majors
  - Salary range (if mentioned)
"""

from __future__ import annotations
import re
from typing import Optional

from app.nlp.skill_extractor import extract_skills_from_sections, SKILL_VOCAB


# ---------------------------------------------------------------------------
# Section headers commonly found in JDs
# ---------------------------------------------------------------------------
_REQUIRED_HEADERS = re.compile(
    r'(?:required|must.?have|mandatory|minimum)[^\n]*(?:skills?|qualifications?|requirements?)',
    re.IGNORECASE,
)
_PREFERRED_HEADERS = re.compile(
    r'(?:preferred|nice.?to.?have|desired|bonus|good.?to.?have)[^\n]*',
    re.IGNORECASE,
)
_CGPA_RE = re.compile(
    r'(?:cgpa|gpa|cumulative\s+gpa)\s*[>:>=≥]{0,2}\s*(\d+(?:\.\d+)?)',
    re.IGNORECASE,
)
_EXPERIENCE_RE = re.compile(
    r'(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:relevant\s+)?experience',
    re.IGNORECASE,
)
_SALARY_RE = re.compile(
    r'(?:salary|ctc|package|compensation|stipend)[^\d]*(\d+(?:[.,]\d+)?)\s*(?:to|-)\s*(\d+(?:[.,]\d+)?)\s*(lpa|lakh|lakhs|k|usd|inr)?',
    re.IGNORECASE,
)
_DEPT_KEYWORDS = {
    "cs": ["computer science", "cs", "cse"],
    "it": ["information technology", "it"],
    "ece": ["electronics", "ece", "eee", "ee"],
    "me": ["mechanical", "me"],
    "ce": ["civil", "ce"],
    "mba": ["mba", "management", "business administration"],
    "all": ["any branch", "all branches", "any degree", "any engineering"],
}


def _extract_section(text: str, header_re: re.Pattern, max_chars: int = 800) -> str:
    """Find a section starting with a matching header, return up to max_chars."""
    m = header_re.search(text)
    if not m:
        return ""
    start = m.end()
    snippet = text[start: start + max_chars]
    # Stop at the next section header (blank line + capitalised header)
    stop = re.search(r'\n\n[A-Z]', snippet)
    if stop:
        snippet = snippet[:stop.start()]
    return snippet.strip()


def parse_jd(text: str) -> dict:
    """
    Parse a job description and return a structured dict.

    Returns:
        {
          "required_skills": [...],
          "preferred_skills": [...],
          "all_skills": [...],
          "min_cgpa": float | None,
          "min_experience_years": int | None,
          "salary_min": float | None,
          "salary_max": float | None,
          "eligible_departments": [...],
        }
    """
    # Skills
    required_section = _extract_section(text, _REQUIRED_HEADERS)
    preferred_section = _extract_section(text, _PREFERRED_HEADERS)

    req_skills = extract_skills_from_sections(required_section)["combined"] if required_section else []
    pref_skills = extract_skills_from_sections(preferred_section)["combined"] if preferred_section else []
    all_skills = extract_skills_from_sections(text)["combined"]

    # CGPA
    cgpa_match = _CGPA_RE.search(text)
    min_cgpa = float(cgpa_match.group(1)) if cgpa_match else None

    # Experience
    exp_match = _EXPERIENCE_RE.search(text)
    min_exp = int(exp_match.group(1)) if exp_match else None

    # Salary
    sal_match = _SALARY_RE.search(text)
    sal_min = sal_max = None
    if sal_match:
        try:
            sal_min = float(sal_match.group(1).replace(",", ""))
            sal_max = float(sal_match.group(2).replace(",", ""))
        except ValueError:
            pass

    # Eligible departments
    text_lower = text.lower()
    eligible_depts = []
    for code, keywords in _DEPT_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            if code == "all":
                eligible_depts = []  # open to all
                break
            eligible_depts.append(code.upper())

    return {
        "required_skills": req_skills or all_skills[:10],
        "preferred_skills": pref_skills,
        "all_skills": all_skills,
        "min_cgpa": min_cgpa,
        "min_experience_years": min_exp,
        "salary_min": sal_min,
        "salary_max": sal_max,
        "eligible_departments": eligible_depts,
    }


def extract_role_from_jd(text: str) -> Optional[str]:
    """Heuristic: extract the job role from the first few lines of a JD."""
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    if not lines:
        return None

    # Common JD title patterns
    title_re = re.compile(
        r'(?:role|position|job title|designation)[:\s]+([^\n]+)',
        re.IGNORECASE,
    )
    m = title_re.search("\n".join(lines[:10]))
    if m:
        return m.group(1).strip()

    # First non-boilerplate line is usually the role
    for line in lines[:5]:
        if len(line) > 3 and not re.match(r'^(dear|hello|we are|about|company)', line, re.IGNORECASE):
            return line
    return None
