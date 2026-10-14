# 🧑‍💻 Sachin's Task Sheet (Sprint 2) — Explainable Match Diagnostics, Talent Cohort Builder & Skill Trend Forecasting

> **Role:** Machine Learning & Talent Intelligence Lead
> **Priority:** 🟠 P1 — Core ML differentiator and smart recruitment engine
> **Reference Standard:** HireVue Match Scoring, Eightfold.ai Talent Intelligence, LinkedIn Recruiter Smart Search, Gartner Talent Analytics
> **Estimated Effort:** ~3–4 days

---

## 📋 Industrial Context — Why This Matters

The current ML pipeline computes a match score (e.g., "82%") but the number is a black box. In commercial talent intelligence platforms:

1. **Explainability is Non-Negotiable:** Students don't know *why* they scored 82%. Recruiters don't trust a number without evidence. Enterprise ATS systems break scores into transparent sub-dimensions: Academic Eligibility, Technical Skill Alignment (exact vs. semantically adjacent), and Practical Experience bonus. Students need this to act.
2. **TPOs Need Precision Talent Search:** "Show me all 2026-batch CS/IT students with CGPA > 8.0 who know Docker AND React AND have zero backlogs" — this query is not possible today. Corporate recruiters hand-deliver such requirements to TPOs before every campus drive.
3. **Skill Market Intelligence is Forward-Looking:** The platform knows what skills were required by every drive ever posted. Aggregating this gives a "skills market radar" — which technologies are surging demand vs. declining — a critical competitive intelligence tool for students choosing what to study next.

---

## TASK 1: Explainable AI Match Diagnostics Breakdown Modal

### Files to Modify
- **MODIFY:** `backend/app/ml/matcher.py` — return diagnostic breakdown alongside score
- **MODIFY:** `backend/app/schemas/matching.py` — add `MatchBreakdown` schema
- **MODIFY:** `backend/app/api/v1/matching.py` — return breakdown in response
- **MODIFY:** `frontend/src/pages/student/JobMatches.jsx` — add breakdown modal

### Backend: `MatchBreakdown` schema (add to `schemas/matching.py`)

```python
class SemanticSkillDetail(BaseModel):
    required_skill: str       # Skill required by job
    student_skill: str        # Closest skill student has
    similarity: float         # 0.0 to 1.0 cosine similarity
    match_type: Literal["direct", "adjacent", "missing"]
    # direct = exact name match, adjacent = similar via SBERT, missing = no coverage

class MatchBreakdown(BaseModel):
    academic_score: float            # 0-100: CGPA eligibility + dept match
    skills_score: float              # 0-100: weighted avg of semantic skill matches
    experience_bonus: float          # 0-20: bonus for relevant projects/internships
    total_score: float               # Weighted sum: 0.4*academic + 0.45*skills + 0.15*experience (normalized to 100)
    skill_details: list[SemanticSkillDetail]  # Per-skill breakdown
    academic_reason: str             # e.g. "CGPA 8.4 meets threshold 7.5. Branch CS is eligible."
    top_missing_skills: list[str]    # Top 3 skills student lacks
    recommendation: str             # e.g. "Adding 1 Docker project would boost this match by +14%"
```

### Backend: Modify `matcher.py`

The existing `predict_match_score()` function returns a float. Extend it to also return a `MatchBreakdown`:

```python
def compute_breakdown(
    student: StudentFeatureVector,
    job: JobFeatureVector,
    pair_features: PairFeatureVector,
) -> MatchBreakdown:
    """
    Computes the diagnostic breakdown alongside the match score.
    
    Academic Score:
      - 100 if CGPA >= min_cgpa AND dept is eligible
      - Scaled linearly if close to threshold
      - 0 if dept completely mismatch
    
    Skills Score:
      - For each required skill in the job, find the best matching student skill
        using the SBERT embedding cosine similarity (already computed in embeddings.py)
      - direct match: similarity >= 0.95
      - adjacent match: 0.60 <= similarity < 0.95
      - missing: similarity < 0.60
      - skills_score = mean(per-skill similarity * 100) across all required skills
    
    Experience Bonus:
      - +5 points for each relevant project in student profile (max 3 projects = +15)
      - Relevance: if any required skill name appears in project.tech_stack (case insensitive)
      - Hard cap: 20 points maximum
    
    Recommendation:
      - Identify the single missing skill with highest job_weight_score
      - Compute: how much would skills_score increase if that skill were added?
      - Format: "Adding {skill_name} would boost this match by +{delta}%"
    """
```

### Backend: Update `matching.py` response

Modify `GET /matching/me` and `GET /matching/students/{id}` to include `breakdown: MatchBreakdown` in each `JobMatchResponse` item.

### Frontend: `JobMatches.jsx` — Breakdown Modal

**Current state:** Each job card shows a circular match % score. Clicking opens a basic detail modal.

**New behavior:** Clicking the match circle OR a new "📊 Why this score?" link opens a **Match Diagnostic Breakdown Modal**:

```
┌────────── Match Diagnostic: Amazon SDE-I ──────────────────────────────────┐
│                                                                              │
│  Overall Match: 82%    ━━━━━━━━━━━━━━━━░░░                                 │
│                                                                              │
│  ┌─ Academic Fit ──────────────────── 95 / 100 ─────────────────────────┐  │
│  │  ✅ CGPA 8.4 ≥ 7.5 required                                          │  │
│  │  ✅ Branch: CS — Eligible (CS, IT, ECE)                              │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌─ Technical Skills ──────────────── 78 / 100 ─────────────────────────┐  │
│  │  🟢 Python          Direct Match (100%)                               │  │
│  │  🟢 React           Direct Match (100%)                               │  │
│  │  🔵 FastAPI         Adjacent Match → Flask (84% similar)              │  │
│  │  🔵 PostgreSQL      Adjacent Match → MySQL (79% similar)              │  │
│  │  🔴 Kubernetes      Missing (0%)                                      │  │
│  │  🔴 System Design   Missing (0%)                                      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌─ Practical Experience ────────── 12 / 20 ────────────────────────────┐  │
│  │  ✅ Project: "Real-time Chat App" (React, FastAPI, PostgreSQL)        │  │
│  │  ✅ Project: "ML Price Predictor" (Python, scikit-learn)              │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  💡 Recommendation: Adding 1 Kubernetes project would boost this            │
│     match by +14%. Learn Kubernetes via "CKA Crash Course" on Udemy.       │
│                                                                              │
│  [→ Add Kubernetes to my Roadmap]              [✕ Close]                    │
└──────────────────────────────────────────────────────────────────────────────┘
```

**Color coding for skill tags:**
- 🟢 Direct Match → green badge
- 🔵 Adjacent Match → blue badge with similarity % shown
- 🔴 Missing → red badge

**"Add to Roadmap" CTA:** Clicking calls `intelligenceApi.generateRoadmap(targetRole)` with the job's target role pre-filled. Navigates to `/student/roadmap` after success.

---

## TASK 2: TPO Talent Pool Cohort Builder

### Files to Create / Modify
- **CREATE:** `backend/app/models/cohort.py` — `StudentCohort` model
- **MODIFY:** `backend/app/models/__init__.py` — import
- **CREATE:** `backend/app/api/v1/tpo.py` — new file with cohort endpoints
- **MODIFY:** `backend/app/main.py` — register new router
- **MODIFY:** `frontend/src/pages/tpo/Students.jsx` — full cohort builder UI
- **MODIFY:** `frontend/src/api/endpoints.js` — add `tpoApi.queryStudents()`, `tpoApi.saveCohort()`, etc.

### Backend: `models/cohort.py`

```python
class StudentCohort(Base):
    __tablename__ = "student_cohorts"

    id = Column(UUIDType, primary_key=True, default=uuid.uuid4)
    name = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    created_by = Column(UUIDType, ForeignKey("users.id"), nullable=False)
    criteria = Column(JSONB_COMPAT, nullable=False)   # The filter payload used to generate this cohort
    student_ids = Column(JSONB_COMPAT, nullable=False)  # List of student UUIDs at time of creation
    student_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_archived = Column(Boolean, default=False)
```

### Backend: `api/v1/tpo.py`

```python
router = APIRouter(prefix="/tpo", tags=["TPO Operations"])

class CohortQuery(BaseModel):
    min_cgpa: Optional[float] = None             # e.g., 7.5
    max_cgpa: Optional[float] = None
    max_backlogs: Optional[int] = None            # e.g., 0
    departments: Optional[list[str]] = None       # e.g., ["CS", "IT"]
    must_have_skills: Optional[list[str]] = None  # All skills must be present
    any_of_skills: Optional[list[str]] = None     # At least one skill must be present
    min_skill_score: Optional[float] = None       # e.g., 70 (skill profile score)
    placement_status: Optional[str] = None        # "placed" | "unplaced" | "unregistered"
    graduation_year: Optional[int] = None         # e.g., 2026

@router.post("/cohorts/query")
async def query_students(
    query: CohortQuery,
    page: int = 1,
    page_size: int = 50,
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Executes a multi-condition search against the student database.
    Returns: { "students": [...], "total": int, "query_id": str (temp cache key) }
    
    Implementation:
    1. Build SQLAlchemy query with AND conditions for all non-None criteria
    2. For skill filters: JOIN to StudentSkill and Skill tables
    3. For min_skill_score: use ML matching_service or a stored score column
    4. Return StudentSummary schema (not full profile — faster)
    """

@router.post("/cohorts")
async def save_cohort(
    name: str,
    description: Optional[str],
    query: CohortQuery,
    student_ids: list[str],  # The IDs from the query result to save
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    """Saves a named cohort to the database. student_ids come from the query result."""

@router.get("/cohorts")
async def list_cohorts(
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    """Lists all saved cohorts for this TPO user."""

@router.get("/cohorts/{cohort_id}/export")
async def export_cohort_csv(
    cohort_id: uuid.UUID,
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns a CSV file with columns:
    Roll Number, Name, Email, Branch, CGPA, Skills, Placement Status, Phone
    Formatted for distribution to corporate recruiters.
    """

@router.post("/cohorts/{cohort_id}/invite-to-drive")
async def batch_invite_to_drive(
    cohort_id: uuid.UUID,
    drive_id: uuid.UUID,
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Creates Notification records for all students in the cohort,
    inviting them to apply to the specified drive.
    """
```

### Frontend: `Students.jsx` — Full Cohort Builder Redesign

The existing students page shows a simple table. Add a "Cohort Builder" panel as a right-side collapsible panel or a top tab toggle.

**Filter Panel (left side, collapsible):**
```
┌────────── Build Talent Cohort ──────────────────────────────────────────┐
│  CGPA:       Min [7.5 ___] Max [10.0 ___]                               │
│  Backlogs:   Max [0 ___]                                                 │
│  Branches:   [✓] CS  [✓] IT  [ ] ECE  [ ] ME                           │
│  Year:       [2026 ▾]                                                    │
│  Status:     (●) Any  ( ) Unplaced only  ( ) Placed                     │
│                                                                          │
│  Must-Have Skills:    [Docker ✕] [Python ✕]   [+ Add Skill]             │
│  Any-Of Skills:       [Kubernetes ✕]           [+ Add Skill]            │
│                                                                          │
│  [🔍 Run Query]   [🔄 Reset Filters]                                    │
└─────────────────────────────────────────────────────────────────────────┘
```

**Results Table (main content area):**
- Sortable columns: Name, Roll No, Branch, CGPA, Skills Count, Status
- Each row has a checkbox for manual selection
- "Select All" checkbox in header
- Sticky action bar appears at bottom when any rows selected:
  ```
  [47 students selected]  [💾 Save as Cohort]  [📥 Export CSV]  [📩 Invite to Drive]
  ```

**Saved Cohorts Panel (tab or section):**
```
📚 Saved Cohorts
─────────────────────────────────────────────────────────────────
  Tier-1 Product Companies 2026       47 students   Saved Sep 12
  CS/IT CGPA 8+ Shortlist             23 students   Saved Sep 10
  [📥 Export] [📩 Invite] [🗑 Archive]
```

---

## TASK 3: Predictive Skill Demand Trend Engine

### Files to Modify / Create
- **MODIFY:** `backend/app/api/v1/analytics.py` — add `GET /analytics/skills/trends`
- **MODIFY:** `backend/app/services/analytics_service.py` — add `compute_skill_trends()` method
- **MODIFY:** `frontend/src/pages/tpo/Analytics.jsx` — add Market Trends section
- **MODIFY:** `frontend/src/pages/student/SkillGap.jsx` — add Market Radar panel
- **MODIFY:** `frontend/src/api/endpoints.js` — add `analyticsApi.getSkillTrends()`

### Backend: `compute_skill_trends()` in `analytics_service.py`

```python
async def compute_skill_trends(self) -> dict:
    """
    Analyzes skill demand trends across all placement drives in the database.
    
    Algorithm:
    1. Fetch all PlacementDrives, grouped by their drive_date month.
    2. For each drive, extract the required skills (from job_postings or drive descriptions
       if parsed by NLP pipeline). If not available, use company_industry to generate a
       representative skill set from a hardcoded industry_skills dict.
    3. Compute frequency of each skill in current_quarter vs previous_quarter.
    4. Calculate growth_rate = (current - previous) / (previous + 1) * 100
    5. Classify:
       - growth_rate > 30% → "surging"
       - -10% <= growth_rate <= 30% → "stable"
       - growth_rate < -10% → "declining"
    6. Return top 10 surging, top 10 stable, top 5 declining skills.
    
    Returns:
    {
        "surging": [{"skill": "LangChain", "growth_pct": 145, "demand_count": 23}, ...],
        "stable": [{"skill": "Python", "growth_pct": 3, "demand_count": 87}, ...],
        "declining": [{"skill": "jQuery", "growth_pct": -34, "demand_count": 8}, ...],
        "computed_at": "2026-09-14T...",
        "based_on_drives": 42,
    }
    """
```

**Fallback for sparse data:** If fewer than 10 drives exist in DB, use a hardcoded "industry standard" trend dataset (a static Python dict) so the feature always shows meaningful data.

### Backend: API Route (add to `analytics.py`)

```python
@router.get("/skills/trends")
async def get_skill_trends(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns skill demand trend classification: surging, stable, declining.
    Cached for 6 hours (use a module-level dict with timestamp, no Redis needed yet).
    """
```

### Frontend: `Analytics.jsx` — Market Trends Section

Add a **"📈 Skill Market Trends"** section in the TPO Analytics page:

```
┌──────────────────── Skill Market Trends (Last 90 Days) ─────────────────────────────┐
│                                                                                       │
│  🚀 Surging Demand (High Growth)                                                      │
│  [LangChain +145%] [PyTorch +89%] [Kubernetes +67%] [Go +52%] [Terraform +41%]       │
│                                                                                       │
│  ⚖️ Stable Core Skills                                                                │
│  [Python] [React] [SQL] [Git] [FastAPI] [Docker] [Node.js] [Java]                    │
│                                                                                       │
│  📉 Declining Demand                                                                  │
│  [jQuery -34%] [PHP -28%] [Visual Basic -61%]                                        │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

**Design:** Each skill badge is a pill with growth % indicator. Surging badges are green with 🚀. Declining are red with 📉. Hovering a badge shows a mini tooltip: "Required by 23 drives this quarter".

### Frontend: `SkillGap.jsx` — Market Intelligence Panel

Add a **"Market Radar"** sidebar panel next to the existing skill gap analysis:

```
📡 Market Radar — What's Hot
──────────────────────────────────────────
  🚀 LangChain      In 68% of AI drives
  🚀 Kubernetes     In 52% of SDE drives
  ⚖️  Python         In 92% of all drives
  ⚖️  SQL            In 87% of all drives
  📉  jQuery         Only 8% of drives now

  💡 You have: Python ✓, SQL ✓, Docker ✓
     Gap: LangChain, Kubernetes
     → [Add to my Roadmap]
```

**Personalization:** Cross-reference surging skills against the student's current skills. Skills the student already has are marked ✓ in green. Missing surging skills are shown in amber with "Add to Roadmap" CTA.

---

## Checklist — What "Done" Looks Like

- [ ] Clicking the match score circle on any job card opens the 3-part diagnostic breakdown modal
- [ ] Breakdown modal shows direct vs. adjacent (with %) vs. missing skills with color coding
- [ ] Breakdown modal shows academic score, skills score, experience bonus with progress bars
- [ ] "Add to Roadmap" button in breakdown modal navigates to student's roadmap
- [ ] TPO can build multi-filter queries (CGPA, departments, skills, status) and see results instantly
- [ ] TPO can save a query result as a named cohort
- [ ] TPO can export any cohort as a recruiter-ready CSV
- [ ] TPO can batch-invite an entire cohort to a specific drive (creates notifications)
- [ ] Analytics page shows skill demand trends with surging/stable/declining classification
- [ ] Student SkillGap page shows personalized Market Radar highlighting their skill gaps vs market demand

---

## File Touch Summary

| Action | File |
|--------|------|
| MODIFY | `backend/app/ml/matcher.py` |
| MODIFY | `backend/app/schemas/matching.py` |
| MODIFY | `backend/app/api/v1/matching.py` |
| MODIFY | `frontend/src/pages/student/JobMatches.jsx` |
| CREATE | `backend/app/models/cohort.py` |
| CREATE | `backend/app/api/v1/tpo.py` |
| MODIFY | `frontend/src/pages/tpo/Students.jsx` |
| MODIFY | `backend/app/services/analytics_service.py` |
| MODIFY | `backend/app/api/v1/analytics.py` |
| MODIFY | `frontend/src/pages/tpo/Analytics.jsx` |
| MODIFY | `frontend/src/pages/student/SkillGap.jsx` |
| MODIFY | `frontend/src/api/endpoints.js` |
