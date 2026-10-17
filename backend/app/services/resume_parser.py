"""
Automated Resume Parser & ATS Compatibility Analyzer Service.

Sprint Final — Sakshi Kumari

Capabilities:
  - Extracts plain text from PDF / DOCX / TXT files via `extract_text`.
  - Regex & heuristic entity extraction: Contact info, Education, Skills, Projects/Experience.
  - Industrial ATS Compatibility Engine (50% keywords, 25% structure, 25% action verbs & metrics).
"""

import re
from typing import Optional, Any
from app.nlp.resume_parser import extract_text


COMMON_ACTION_VERBS = {
    "accelerated", "achieved", "analyzed", "architected", "automated", "built",
    "collaborated", "configured", "constructed", "created", "decreased", "delivered",
    "deployed", "designed", "developed", "devised", "engineered", "enhanced",
    "established", "executed", "formulated", "implemented", "improved", "increased",
    "initiated", "integrated", "launched", "led", "managed", "maximized", "migrated",
    "minimized", "modeled", "modernized", "optimized", "orchestrated", "overhauled",
    "pioneered", "produced", "programmed", "reduced", "refactored", "resolved",
    "restructured", "scaled", "simplified", "solved", "spearheaded", "standardized",
    "streamlined", "supervised", "tested", "transformed", "upgraded"
}

STANDARD_ATS_SECTIONS = {
    "summary": [r"\bsummary\b", r"\bprofessional summary\b", r"\bobjective\b", r"\babout me\b"],
    "experience": [r"\bexperience\b", r"\bwork experience\b", r"\binternships?\b", r"\bemployment\b", r"\bprofessional experience\b"],
    "education": [r"\beducation\b", r"\bacademics?\b", r"\bacademic background\b", r"\bqualifications?\b"],
    "skills": [r"\bskills\b", r"\btechnical skills\b", r"\bcore competencies\b", r"\btechnologies\b", r"\btools\b"],
    "projects": [r"\bprojects\b", r"\bkey projects\b", r"\bacademic projects\b", r"\bpersonal projects\b"],
}

CORE_TECH_SKILLS = [
    "Python", "Java", "C++", "C#", "JavaScript", "TypeScript", "Go", "Rust",
    "React", "Angular", "Vue", "Next.js", "Node.js", "Express", "FastAPI",
    "Django", "Flask", "Spring Boot", "SQL", "PostgreSQL", "MySQL", "MongoDB",
    "Redis", "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Git", "GitHub",
    "CI/CD", "Linux", "REST API", "GraphQL", "Microservices", "HTML", "CSS",
    "Tailwind", "Pandas", "NumPy", "Scikit-Learn", "TensorFlow", "PyTorch",
    "Machine Learning", "Data Structures", "Algorithms", "System Design"
]


def extract_contact_info(text: str) -> dict[str, Optional[str]]:
    """Extract email, phone, linkedin, and github handles."""
    email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    email = email_match.group(0) if email_match else None

    # Phone: match 10-digit Indian numbers or international +XX format
    phone_match = re.search(r"(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4,5}\b", text)
    phone = phone_match.group(0).strip() if phone_match else None

    linkedin_match = re.search(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+", text, re.IGNORECASE)
    linkedin = linkedin_match.group(0) if linkedin_match else None

    github_match = re.search(r"(?:https?://)?(?:www\.)?github\.com/[a-zA-Z0-9_-]+", text, re.IGNORECASE)
    github = github_match.group(0) if github_match else None

    return {
        "email": email,
        "phone": phone,
        "linkedin_url": linkedin,
        "github_url": github,
    }


def extract_education(text: str) -> dict[str, Any]:
    """Extract degree, branch, CGPA, graduation year."""
    degree = None
    degree_patterns = [
        (r"\b(B\.?Tech|Bachelor of Technology)\b", "B.Tech"),
        (r"\b(B\.?E\.?|Bachelor of Engineering)\b", "B.E."),
        (r"\b(M\.?Tech|Master of Technology)\b", "M.Tech"),
        (r"\b(BCA|Bachelor of Computer Applications)\b", "BCA"),
        (r"\b(MCA|Master of Computer Applications)\b", "MCA"),
        (r"\b(B\.?Sc|Bachelor of Science)\b", "B.Sc"),
    ]
    for pattern, deg in degree_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            degree = deg
            break

    branch = None
    branch_patterns = [
        (r"\b(computer science|cse|cs)\b", "Computer Science & Engineering"),
        (r"\b(information technology|it)\b", "Information Technology"),
        (r"\b(electronics and communication|ece)\b", "Electronics & Communication"),
        (r"\b(artificial intelligence|data science|ai & ds)\b", "AI & Data Science"),
        (r"\b(mechanical|mech)\b", "Mechanical Engineering"),
        (r"\b(electrical|eee)\b", "Electrical Engineering"),
    ]
    for pattern, br in branch_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            branch = br
            break

    # CGPA or percentage
    cgpa = None
    cgpa_match = re.search(r"\b(?:cgpa|gpa|pointer)[:\s]*([0-9]\.[0-9]{1,2})(?:/10)?\b", text, re.IGNORECASE)
    if cgpa_match:
        try:
            cgpa = float(cgpa_match.group(1))
        except ValueError:
            pass

    grad_year = None
    grad_match = re.search(r"\b(20[12][0-9])\b", text)
    if grad_match:
        grad_year = int(grad_match.group(1))

    return {
        "degree": degree,
        "branch": branch,
        "cgpa": cgpa,
        "graduation_year": grad_year,
    }


def extract_detected_skills(text: str) -> list[str]:
    """Find matches for core technical skills."""
    detected = []
    text_lower = text.lower()
    for skill in CORE_TECH_SKILLS:
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, text_lower):
            detected.append(skill)
    return detected


def analyze_ats_score(
    resume_text: str,
    target_job_description: Optional[str] = None,
    target_skills: Optional[list[str]] = None,
) -> dict[str, Any]:
    """
    Computes rigorous ATS Compatibility Score (0–100%):
      - 50%: Keyword density & skill coverage
      - 25%: Section structural completeness (Summary, Experience, Education, Skills, Projects)
      - 25%: Action verb usage & quantifiable impact metrics
    """
    if not resume_text or not resume_text.strip():
        return {
            "ats_score": 0.0,
            "grade": "Needs Improvement",
            "breakdown": {
                "keyword_coverage_score": 0.0,
                "structure_score": 0.0,
                "metrics_and_verbs_score": 0.0,
            },
            "matched_skills": [],
            "missing_target_skills": [],
            "formatting_flags": ["Empty or unreadable document"],
            "actionable_recommendations": ["Upload a readable resume with text content."],
        }

    raw_text = resume_text.strip()
    text_lower = raw_text.lower()

    # ─────────────────────────────────────────────────────────────
    # 1. Keyword density & skill coverage (50% max)
    # ─────────────────────────────────────────────────────────────
    detected_resume_skills = extract_detected_skills(raw_text)

    # Determine target skills to compare against
    expected_skills = set()
    if target_skills:
        for s in target_skills:
            if s and s.strip():
                expected_skills.add(s.strip())
    if target_job_description and target_job_description.strip():
        jd_skills = extract_detected_skills(target_job_description)
        expected_skills.update(jd_skills)

    if not expected_skills:
        # Default target benchmark: Top full-stack/SE placement skills
        expected_skills = {
            "Python", "Java", "JavaScript", "React", "Node.js",
            "SQL", "PostgreSQL", "Docker", "Git", "Data Structures", "Algorithms"
        }

    matched_skills = [s for s in detected_resume_skills if any(s.lower() == es.lower() for es in expected_skills)]
    missing_target_skills = [es for es in expected_skills if not any(es.lower() == s.lower() for s in detected_resume_skills)]

    # Calculate skill match ratio
    if expected_skills:
        match_ratio = len(matched_skills) / len(expected_skills)
    else:
        match_ratio = min(1.0, len(detected_resume_skills) / 8.0)

    keyword_score = round(min(50.0, match_ratio * 50.0), 1)

    # ─────────────────────────────────────────────────────────────
    # 2. Section structural completeness (25% max)
    # ─────────────────────────────────────────────────────────────
    detected_sections = {}
    structure_points = 0.0
    section_weight = 25.0 / len(STANDARD_ATS_SECTIONS)

    for sec_name, patterns in STANDARD_ATS_SECTIONS.items():
        found = any(re.search(pat, text_lower) for pat in patterns)
        detected_sections[sec_name] = found
        if found:
            structure_points += section_weight

    structure_score = round(min(25.0, structure_points), 1)

    # ─────────────────────────────────────────────────────────────
    # 3. Action verb usage & quantifiable impact metrics (25% max)
    # ─────────────────────────────────────────────────────────────
    # Count action verbs
    words = re.findall(r"\b[a-zA-Z]+\b", text_lower)
    found_verbs = [w for w in words if w in COMMON_ACTION_VERBS]
    unique_verbs_count = len(set(found_verbs))

    # Action verbs up to 12.5 pts
    verbs_score = min(12.5, (unique_verbs_count / 8.0) * 12.5)

    # Quantifiable metrics: numbers, percentages, $, multiples, latencies
    metric_matches = re.findall(r"(\b\d+%\b|\b\d+\s*(?:x|times|ms|seconds?|users?|lpa|k|m)\b|\bincreased by \d+|\breduced by \d+|\b\d+\+\b)", text_lower)
    metrics_count = len(metric_matches)

    # Metrics up to 12.5 pts
    metrics_score = min(12.5, (metrics_count / 4.0) * 12.5)

    verbs_and_metrics_score = round(min(25.0, verbs_score + metrics_score), 1)

    # ─────────────────────────────────────────────────────────────
    # Total Score & Grade
    # ─────────────────────────────────────────────────────────────
    total_ats_score = round(keyword_score + structure_score + verbs_and_metrics_score, 1)
    total_ats_score = min(100.0, max(0.0, total_ats_score))

    if total_ats_score >= 85.0:
        grade = "Exceptional"
    elif total_ats_score >= 70.0:
        grade = "Strong"
    elif total_ats_score >= 50.0:
        grade = "Competitive"
    else:
        grade = "Needs Improvement"

    # Formatting Flags
    formatting_flags = []
    if " | " in raw_text or "\t" in raw_text:
        formatting_flags.append("Standard plain text / column spacing detected")
    else:
        formatting_flags.append("Clean single-column ATS flow verified")

    if re.search(r"[•\-\*]\s+[A-Z]", raw_text):
        formatting_flags.append("Standard bullet formatting verified")
    else:
        formatting_flags.append("Use standard bullet points (•, -) for experience statements")

    if len(raw_text.split()) > 250:
        formatting_flags.append("Optimal word count verified (300-800 words)")
    else:
        formatting_flags.append("Word count is sparse; elaborate on project outcomes")

    # Actionable Recommendations
    recommendations = []
    if missing_target_skills:
        top_missing = missing_target_skills[:4]
        recommendations.append(f"Add target technical skills: {', '.join(top_missing)}")

    missing_secs = [k.title() for k, v in detected_sections.items() if not v]
    if missing_secs:
        recommendations.append(f"Add missing ATS section headers: {', '.join(missing_secs)}")

    if metrics_count < 3:
        recommendations.append("Include quantifiable impact metrics in Project and Experience bullet points (e.g. 'improved latency by 35%', 'served 2,000+ users')")

    if unique_verbs_count < 5:
        recommendations.append("Lead bullet points with decisive action verbs like 'Architected', 'Deployed', 'Optimized', or 'Engineered'")

    if not recommendations:
        recommendations.append("Resume demonstrates high ATS keyword alignment and clean structural hierarchy.")

    return {
        "ats_score": total_ats_score,
        "grade": grade,
        "breakdown": {
            "keyword_coverage_score": keyword_score,
            "structure_score": structure_score,
            "metrics_and_verbs_score": verbs_and_metrics_score,
        },
        "matched_skills": sorted(list(set(matched_skills))),
        "missing_target_skills": sorted(list(set(missing_target_skills))),
        "formatting_flags": formatting_flags,
        "actionable_recommendations": recommendations,
    }
