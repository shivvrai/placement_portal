"""
Skill Extractor — pull skill mentions from raw resume/JD text.

Strategy (layered, no GPU required):
  1. Curated skill keyword list (fastest, ~2000 skills)
  2. spaCy NER for PRODUCT / ORG entities (catches tool names)
  3. Regex patterns for version-tagged skills  e.g. "Python 3", "React 18"

Returns a de-duplicated list of raw skill strings for taxonomy matching.
"""

from __future__ import annotations
import re
import unicodedata
from typing import Optional

# ---------------------------------------------------------------------------
# Curated skill vocabulary (normalised lowercase)
# This is the primary lookup — extend as needed.
# ---------------------------------------------------------------------------
SKILL_VOCAB: set[str] = {
    # Languages
    "python", "java", "javascript", "typescript", "c", "c++", "c#", "go",
    "golang", "rust", "swift", "kotlin", "r", "matlab", "scala", "ruby",
    "php", "perl", "bash", "shell", "powershell", "sql", "nosql", "dart",
    # Web / Frontend
    "html", "css", "react", "reactjs", "react.js", "angular", "angularjs",
    "vue", "vue.js", "vuejs", "next.js", "nextjs", "nuxt", "svelte",
    "jquery", "bootstrap", "tailwind", "sass", "scss", "webpack", "vite",
    "redux", "graphql", "rest", "rest api", "restful api",
    # Backend / Frameworks
    "node.js", "nodejs", "express", "fastapi", "django", "flask", "spring",
    "spring boot", "rails", "laravel", "asp.net", "dotnet", ".net",
    "hibernate", "sqlalchemy",
    # Data / ML / AI
    "machine learning", "deep learning", "artificial intelligence", "nlp",
    "natural language processing", "computer vision", "tensorflow", "pytorch",
    "keras", "scikit-learn", "sklearn", "xgboost", "lightgbm", "catboost",
    "pandas", "numpy", "scipy", "matplotlib", "seaborn", "plotly",
    "huggingface", "transformers", "bert", "gpt", "llm",
    "data science", "data analysis", "data engineering", "feature engineering",
    "statistics", "probability", "regression", "classification", "clustering",
    "reinforcement learning", "transfer learning", "fine-tuning",
    # Databases
    "postgresql", "postgres", "mysql", "mongodb", "redis", "elasticsearch",
    "cassandra", "sqlite", "oracle", "mssql", "dynamodb", "firestore",
    "neo4j", "influxdb", "hbase", "bigquery",
    # Cloud & DevOps
    "aws", "amazon web services", "gcp", "google cloud", "azure",
    "docker", "kubernetes", "k8s", "helm", "terraform", "ansible",
    "jenkins", "github actions", "gitlab ci", "circleci", "travis ci",
    "ci/cd", "devops", "sre", "linux", "nginx", "apache",
    # Data Engineering
    "spark", "apache spark", "kafka", "apache kafka", "airflow",
    "apache airflow", "hadoop", "hive", "flink", "dbt",
    "etl", "data pipeline", "data warehouse", "data lake",
    # Tools
    "git", "github", "gitlab", "bitbucket", "jira", "confluence",
    "figma", "postman", "swagger", "vs code", "intellij", "eclipse",
    "jupyter", "colab", "tableau", "power bi", "excel", "looker",
    "grafana", "kibana", "prometheus",
    # CS Fundamentals
    "data structures", "algorithms", "system design", "os", "operating systems",
    "computer networks", "networking", "dbms", "database management",
    "object oriented programming", "oop", "functional programming",
    "design patterns", "microservices", "api design", "distributed systems",
    # Soft Skills
    "communication", "leadership", "teamwork", "problem solving",
    "critical thinking", "project management", "agile", "scrum", "kanban",
    # Misc
    "blockchain", "solidity", "web3", "unity", "unreal engine",
    "android", "ios", "react native", "flutter", "firebase",
    "opencv", "ros", "embedded systems", "fpga", "vhdl", "verilog",
}

# Regex for "SkillName vX.X" patterns
_VERSION_RE = re.compile(
    r'\b(python|java|react|angular|vue|node\.?js|django|flask|spring|docker|kubernetes)\s*[\d]+[\.\d]*\b',
    re.IGNORECASE,
)

# Regex for all-caps acronyms likely to be a tech skill
_ACRONYM_RE = re.compile(r'\b[A-Z]{2,7}\b')


def _normalise(text: str) -> str:
    return unicodedata.normalize("NFKD", text).lower().strip()


def _load_spacy():
    """Lazy-load spaCy model to avoid import-time overhead."""
    try:
        import spacy
        return spacy.load("en_core_web_sm", disable=["parser", "lemmatizer"])
    except Exception:
        return None


_NLP = None


def extract_skills(text: str, use_spacy: bool = True) -> list[str]:
    """
    Extract skill mentions from free-form text.

    Args:
        text: Resume or JD plain text
        use_spacy: Whether to run spaCy NER pass (slower but catches more)

    Returns:
        Sorted, de-duplicated list of raw skill strings (original case)
    """
    global _NLP
    found: set[str] = set()
    norm_text = _normalise(text)

    # --- Pass 1: Vocab keyword matching (longest match first) ---
    sorted_vocab = sorted(SKILL_VOCAB, key=len, reverse=True)
    matched_ranges: list[tuple[int, int]] = []

    for skill in sorted_vocab:
        pattern = r'\b' + re.escape(skill) + r'\b'
        for m in re.finditer(pattern, norm_text):
            # Avoid overlapping with already-matched ranges
            start, end = m.start(), m.end()
            overlap = any(s <= start < e or s < end <= e for s, e in matched_ranges)
            if not overlap:
                found.add(skill)
                matched_ranges.append((start, end))

    # --- Pass 2: Version-tagged skills ---
    for m in _VERSION_RE.finditer(text):
        base = m.group(1).lower().rstrip(".")
        if base:
            found.add(base)

    # --- Pass 3: spaCy NER for PRODUCT / ORG entities ---
    if use_spacy:
        if _NLP is None:
            _NLP = _load_spacy()
        if _NLP is not None:
            doc = _NLP(text[:50000])  # cap to 50k chars for performance
            for ent in doc.ents:
                if ent.label_ in ("PRODUCT", "ORG", "WORK_OF_ART"):
                    candidate = _normalise(ent.text)
                    if candidate in SKILL_VOCAB:
                        found.add(candidate)

    return sorted(found)


def extract_skills_from_sections(text: str) -> dict[str, list[str]]:
    """
    Section-aware extraction — finds a 'Skills' / 'Technical Skills'
    section and gives it higher confidence.

    Returns dict: {"skills_section": [...], "full_text": [...]}
    """
    skills_section_re = re.compile(
        r'(?:technical\s+)?skills?[:\s]*\n(.*?)(?:\n\n|\Z)',
        re.IGNORECASE | re.DOTALL,
    )
    m = skills_section_re.search(text)

    section_skills: list[str] = []
    if m:
        section_text = m.group(1)
        section_skills = extract_skills(section_text, use_spacy=False)

    full_skills = extract_skills(text)
    return {
        "skills_section": section_skills,
        "full_text": full_skills,
        "combined": list(set(section_skills + full_skills)),
    }
