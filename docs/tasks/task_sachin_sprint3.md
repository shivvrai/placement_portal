# 🧑‍💻 Sachin's Task Sheet (Sprint 3) — AI-Powered Career Intelligence: Gemini Skill Forecasting, Personalized Learning Pathways, Assessment Analytics & Peer Benchmarking

> **Role:** AI/ML Features & Career Intelligence Engineer
> **Priority:** 🟠 P1 — Core differentiation from generic placement portals
> **Reference Standard:** LinkedIn Skills Graph, Coursera Career Academy, Karat Interview Intelligence, Workday Skills Cloud

---

## 📋 Industrial Context — Why This Sprint Matters

The ML models built in Sprint 1 (GradientBoosting matcher, sentence-transformer embeddings, gap engine) are powerful but their output is currently buried in a skill gap page that most students don't visit. Industrial career intelligence platforms like LinkedIn Skills Insights and Coursera Career Academy surface these insights proactively and continuously. This sprint:

1. **Activates the ML pipeline end-to-end** — the matcher model's scores become visible on every drive card, every company page, every roadmap step.
2. **Adds Gemini-powered skill forecasting** — "Python is projected to grow 34% in job demand this quarter based on current drive patterns."
3. **Builds a peer benchmarking engine** — a student can see exactly how they compare to their department cohort (without PII exposure).
4. **Upgrades the assessment engine** from basic MCQ to adaptive difficulty + coding sandbox questions.

---

## TASK 1: Live ML Match Score Integration (Everywhere)

The ML matcher (`app/ml/matcher.py`) runs in isolation. This task makes the match score visible across the entire frontend.

### Backend Changes

#### MODIFY: `backend/app/api/v1/drives.py` — Inject match scores for student requests

```python
# GET /drives — when called by a student:
# For each drive, compute predict_match_score(student_skills, drive_skills, student_cgpa, drive_min_cgpa)
# Inject "match_score": float into each drive object
# Sort by match_score descending when ?sort=match (default)
# This should NOT be computed synchronously for 100 drives — use asyncio.gather with executor
```

#### MODIFY: `backend/app/api/v1/matching.py`

Add richer endpoints:

```
GET  /matching/drives/{drive_id}          → detailed match breakdown for current student vs this drive
GET  /matching/my-top-drives             → top 10 drive recommendations (by ML score)
GET  /matching/skill-gap/{drive_id}      → per-skill gap: what student has vs what drive needs (using gap_engine.py)
GET  /matching/job-fit/{job_id}          → fit score for a specific job (from industry jobs table)
GET  /matching/rank-cohort               → student's ML score percentile within their dept cohort
POST /matching/what-if                   → simulate: "if I add Python skill, how does my score change?"
```

`GET /matching/drives/{drive_id}` response shape:
```json
{
  "drive_id": "...",
  "overall_score": 78.4,
  "skill_score": 82.0,
  "cgpa_score": 90.0,
  "dept_eligible": true,
  "skill_breakdown": [
    {"skill": "Python", "required_level": "required", "student_level": 0.9, "gap": 0.0, "status": "strong"},
    {"skill": "System Design", "required_level": "required", "student_level": 0.3, "gap": 0.5, "status": "gap"},
    {"skill": "Docker", "required_level": "preferred", "student_level": 0.0, "gap": 1.0, "status": "missing"}
  ],
  "recommendation": "Strong candidate. Focus on System Design and Docker before applying.",
  "rank_in_applicants": 12,
  "total_applicants": 87
}
```

#### CREATE: `backend/app/services/what_if_service.py`

```python
class WhatIfService:
    async def simulate_skill_addition(self, student_id, skill_to_add: str, drive_id: UUID) -> dict:
        # Load current student skills
        # Create hypothetical skills dict with new skill at confidence 0.8
        # Run predict_match_score() with new skills
        # Run predict_match_score() without new skill
        # Return: {current_score, simulated_score, delta, new_rank_estimate}
    
    async def simulate_cgpa_improvement(self, student_id, target_cgpa: float, drive_id: UUID) -> dict:
        # Similar: what if CGPA was target_cgpa?
```

### Frontend Changes

#### MODIFY: `frontend/src/pages/student/PlacementDrives.jsx`

Add match score to every drive card:
- Circular progress ring (0–100%) next to company logo
  - Green: 75+, Yellow: 50–74, Red: <50
- "🎯 78% match" label
- Hover tooltip: "Based on your skills and CGPA"
- Sort by match score toggle

#### MODIFY: `frontend/src/pages/student/DriveDetail.jsx`

Add "Your Match Analysis" section:
- Overall score bar (colorized)
- Skill breakdown table: each required skill with status (✓ Strong / ⚠ Gap / ✗ Missing)
- "If you add Docker: 78% → 84% ↑" — what-if card (calls POST /matching/what-if)
- "Your rank among N applicants: #12"
- "Get Ready" button → creates roadmap tasks for the gap skills

#### MODIFY: `frontend/src/pages/student/SkillGap.jsx`

Upgrade with ML insights:
- "Skill Demand Heatmap" — grid: skills × companies, colored by demand intensity
- "Your top 3 skill gaps across all active drives" — highlighted card
- What-if simulator: "Add a skill → see score change across all drives"

---

## TASK 2: Gemini-Powered Skill Trend Forecasting

### Backend

#### CREATE: `backend/app/services/skill_trend_service.py`

```python
class SkillTrendService:
    async def compute_demand_trends(self, db) -> list[dict]:
        """
        Analyze skills across:
        - All active PlacementDrive.roles_offered
        - All IndustrySkillTrend table rows
        - All Job table required skills (JobSkill table)

        Compute per skill:
        - demand_count: how many active drives/jobs require it
        - growth_rate: (current_month_count - last_month_count) / last_month_count
        - avg_salary_requiring_skill: from drives that list this skill
        - departments_needing: which student depts benefit most

        Return sorted by demand_count descending.
        """

    async def generate_forecast_narrative(self, skill_name: str, trend_data: dict) -> str:
        """
        Call Gemini API (via gemini_client.py) with a prompt like:
        "Given that {skill_name} appears in {N} active placement drives at our college
        and shows a {growth_pct}% growth in demand, write a 2-sentence forecast for students
        on whether they should prioritize learning this skill. Be specific about job roles
        and expected CTC impact. Max 60 words."

        Returns a natural language insight string.
        """

    async def get_emerging_skills(self, db) -> list[str]:
        """Skills with growth_rate > 0.2 (20%+ growth) and demand_count > 3"""

    async def get_declining_skills(self, db) -> list[str]:
        """Skills with growth_rate < -0.1 (declining demand)"""
```

#### MODIFY: `backend/app/api/v1/analytics.py` — Add skill trend endpoints

```
GET /analytics/skill-trends           → full demand trend table
GET /analytics/skill-trends/emerging  → emerging skills list with forecast narratives
GET /analytics/skill-trends/heatmap   → dept x skill demand matrix (for heatmap chart)
GET /analytics/skill-trends/{skill}   → single skill trend detail + Gemini narrative
```

Cache skill trends for 6 hours (Redis cache, key: `skill_trends:{date}`).

### Frontend

#### CREATE: `frontend/src/pages/student/SkillTrends.jsx`

Route: `/student/skill-trends`

Full skill intelligence page:

**Trending Skills Section:**
- "🔥 Trending Now" horizontal scroll card row
- Each card: skill name, demand count bar, growth % badge (green=growing, red=declining), "N drives require this"
- Click → drill down to trend detail

**AI Forecast Panel:**
- For each emerging skill, show Gemini-generated 2-sentence insight in a styled card
- "💡 Gemini Insight:" label + italic text
- Refresh button (re-fetches from Gemini, 6h cache)

**Demand Heatmap:**
- Grid: Rows = departments (CS, IT, ECE), Columns = top 15 skills
- Cell color = demand intensity (light yellow → dark orange → red)
- Hover tooltip: "N active drives in CS require Python"
- "Your skills" overlay toggle: highlights cells where student already has the skill

**Your Exposure Gap:**
- "Of the top 10 trending skills, you are strong in 4, weak in 3, missing 3"
- Action buttons: "Add to Roadmap" per missing skill

---

## TASK 3: Peer Benchmarking Engine (Anonymized Cohort Comparison)

### Backend

#### CREATE: `backend/app/services/benchmarking_service.py`

```python
class BenchmarkingService:
    async def get_cohort_stats(self, student_id: UUID, scope: str = "department") -> dict:
        """
        scope: "department" | "year" | "college"
        
        1. Load all students in same dept (and same admission_year if scope="year")
        2. Compute cohort metrics:
           - CGPA: percentile of this student, mean, median, 25th/75th percentile
           - Skills: avg skill count, this student's count, percentile
           - Assessment scores: avg, this student's avg, percentile
           - Application activity: avg applications filed, this student's count
           - Match scores: median ML match score across top 5 drives, this student's vs cohort
        3. All data anonymized — no names, just aggregates + percentile ranks
        4. Return structured benchmark dict
        """

    async def get_department_leaderboard(self, dept_code: str, metric: str) -> list[dict]:
        """
        metric: "cgpa" | "skill_count" | "avg_match_score" | "applications_filed"
        Returns top 10 students with anonymized labels: "Student #1", "Student #2"
        Current student's own row marked with is_me: true
        No other identifying info.
        """

    async def get_readiness_score(self, student_id: UUID) -> dict:
        """
        Composite 'placement readiness' score (0–100):
        - Profile completeness (resume, photo, bio, linkedin): 20 pts
        - CGPA component (vs dept avg): 20 pts
        - Skill depth (match score avg across all open drives): 30 pts
        - Assessment performance (avg score vs cohort): 15 pts
        - Activity (applications, experiences submitted, roadmap tasks done): 15 pts
        
        Returns: {total_score, components, percentile_in_dept, label: "Placement Ready" | "Needs Work" | "At Risk"}
        """
```

#### MODIFY: `backend/app/api/v1/matching.py`

```
GET /matching/benchmark               → cohort comparison for current student
GET /matching/leaderboard/{dept}      → anonymized dept leaderboard
GET /matching/readiness               → readiness score for current student
```

### Frontend

#### CREATE: `frontend/src/pages/student/Benchmark.jsx`

Route: `/student/benchmark`

**Placement Readiness Score Hero:**
- Big circular gauge (0–100), colored by tier:
  - 80–100: Green — "Placement Ready 🎯"
  - 60–79: Yellow — "Almost There 📈"
  - 0–59: Orange — "Needs Work 🛠"
- 5 component bars: Profile, CGPA, Skills, Assessments, Activity
- "Top X% in your department" label

**Cohort Comparison Cards:**
- CGPA: "Your CGPA: 8.4 | Dept Avg: 7.9 | You're in top 28%"
  - Mini bell curve chart with student's position marked
- Skills: "You have 12 skills | Dept median: 8 | Top 15%"
- Match Score: "Your avg match score: 76 | Dept median: 61 | Top 20%"
- Applications: "Filed 5 applications | Dept avg: 3.2"

**Anonymized Leaderboard:**
- "Top Students in Your Dept" table
- Columns: Rank, Label, CGPA, Skills, Match Score
- Current student row highlighted in blue
- Metric selector: CGPA / Skills / Match Score

**Improvement Suggestions:**
- "To move from top 28% → top 15%, you need to:"
- Actionable items: "Add 2 more skills" / "Complete 2 more assessments" / "Apply to 1 more drive"

---

## TASK 4: Adaptive Assessment Engine Upgrade

### Backend

#### MODIFY: `backend/app/services/assessment_engine.py`

**Adaptive Difficulty:**
```python
# Current: fixed difficulty per session
# New: start at 'medium', adjust after each answer
# - Correct answer → next question difficulty +1 level
# - Wrong answer → stay at current level
# - After 3 consecutive correct → jump to next level
# - After 2 consecutive wrong → drop one level
# Track current difficulty in AssessmentSession.metadata JSONB
```

**Coding Question Support:**
```python
class QuestionType(Enum):
    MCQ = "mcq"
    CODING = "coding"   # NEW
    SHORT_ANSWER = "short_answer"  # NEW

# Coding questions have:
# - problem_statement: str
# - input_format: str
# - output_format: str
# - sample_inputs: list[str]
# - sample_outputs: list[str]
# - test_cases: JSONB (hidden)
# - difficulty: str
# - language: str ("python" | "java" | "any")
```

**Code Execution (sandboxed):**
```python
async def run_code(code: str, language: str, test_cases: list) -> dict:
    # Use Judge0 API (free tier: 50 req/day) or subprocess with timeout
    # Judge0: POST /submissions, poll GET /submissions/{token}
    # Timeout: 3 seconds per test case
    # Return: {passed: N, failed: N, total: N, error: str|None, time_ms: float}
```

#### MODIFY: `backend/app/api/v1/assessments.py`

```
POST /assessments/{session_id}/submit-code    → submit code for a coding question
GET  /assessments/history/detailed            → per-session breakdown with adaptive trajectory
GET  /assessments/analytics/my                → skill-wise performance over time
GET  /assessments/analytics/cohort/{skill}    → cohort performance on a skill
```

#### CREATE: `backend/app/api/v1/questions.py` (TPO/Faculty can add questions)

```
GET  /questions                       → list questions (filter by topic, difficulty, type)
POST /questions                       → create question (MCQ or coding)
PATCH /questions/{id}                 → edit question
DELETE /questions/{id}                → delete (only if not used in past sessions)
GET  /questions/{id}/usage-stats      → how often asked, avg correct rate
```

### Frontend

#### MODIFY: `frontend/src/pages/student/AssessmentTake.jsx`

**Adaptive difficulty indicator:**
- Top bar: "Current difficulty: Medium 🟡" (updates after each answer)
- Streak tracker: "🔥 3 in a row correct → next: Hard"

**Coding question UI:**
- Monaco Editor (or CodeMirror) for code input
- Language selector (Python/Java/C++)
- "▶ Run Tests" button → POST /assessments/{id}/submit-code
- Test case results panel: passes/fails with actual vs expected output
- Time limit and memory limit display

#### CREATE: `frontend/src/pages/student/AssessmentAnalytics.jsx`

Route: `/student/assessments/analytics`

**Your Performance Over Time:**
- Line chart: assessment score over time (x=date, y=score)
- Topic breakdown radar chart: Python, DSA, SQL, System Design, Aptitude scored 0–100
- "Weakest topic: System Design (avg 44%)" → "Start Preparation" button

**Cohort Comparison:**
- "Department avg for Python: 72% | You: 85% | Top 18%"
- Per-topic percentile bars

---

## Verification Checklist

- [ ] Drive list shows ML match score circle on every drive card
- [ ] DriveDetail match breakdown shows correct per-skill status (Strong/Gap/Missing)
- [ ] What-if simulation: adding a skill shows score delta correctly
- [ ] Skill trends heatmap loads with correct demand data
- [ ] Gemini narrative shows for each emerging skill (or graceful fallback if API down)
- [ ] Benchmark readiness score computes all 5 components correctly
- [ ] Cohort leaderboard is fully anonymized (no emails, no real names)
- [ ] Assessment adaptive difficulty increases after 3 consecutive correct answers
- [ ] Code submission runs against hidden test cases and shows pass/fail counts
- [ ] Assessment analytics radar chart shows per-topic performance
