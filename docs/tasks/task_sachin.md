# 🧑‍💻 Sachin's Task Sheet (Sprint 2) — Explainable Match Diagnostics, Recruiter Cohort Builder & Skill Forecasting

> **Role:** Machine Learning & Talent Intelligence Lead.
> **Priority:** 🟠 P1 (Core ML Differentiator & Smart Recruitment Engine)
> **Reference Standard:** HireVue Match Scoring, Eightfold.ai Talent Intelligence, LinkedIn Recruiter Smart Search

---

## 📋 Industrial Context & The Core Problem

In commercial placement platforms, a black-box percentage like *"82% match"* leaves students confused and recruiters skeptical:
1. **Match Score Lacks Explainability:** Students don't know *why* they got an 82% vs 95%. Enterprise systems break down match scores into transparent diagnostic vectors:
   - Academic Eligibility Weight (CGPA + Department match)
   - Core Technical Skill Alignment (exact matches vs adjacent semantic skills via SBERT)
   - Practical Experience & Project Relevancy bonus
2. **Recruiters & TPOs Need a "Talent Pool Cohort Builder":** TPOs currently have to scroll through students. Corporate recruiters ask: *"Give me all 2026 CS/IT students with CGPA > 8.0 who have Docker and React projects"*. TPOs cannot create, name, or export targeted student cohorts.
3. **Skill Demand Trend Forecasting:** There is no forward-looking analytics showing which skills are rising vs declining across hiring cycles.

---

## TASK 1: Explainable AI Match Diagnostics Breakdown Modal

### Files to touch
- Backend: `backend/app/ml/matcher.py`, `backend/app/api/v1/matching.py`
- Frontend: `frontend/src/pages/student/JobMatches.jsx`

### What you need to do
1. **Update Backend Response Schema in `backend/app/schemas/matching.py`:**
   Add `MatchDiagnosticBreakdown`:
   ```python
   class MatchBreakdown(BaseModel):
       academic_score: float      # e.g., 90/100 (CGPA, branch eligibility)
       skills_score: float        # e.g., 78/100 (cosine similarity of normalized embeddings)
       experience_bonus: float    # e.g., 10/100 (relevant projects & internships)
       semantic_overlap_details: list[dict] # [{"required_skill": "FastAPI", "student_skill": "Flask", "similarity": 0.84, "type": "adjacent"}]
   ```
2. **Expose Detailed Diagnostic in `JobMatches.jsx`:**
   When clicking on a job card or the match circle, open a **"Match Diagnostic Breakdown"** modal:
   - Visual progress bars for Academic Fit, Technical Alignment, and Practical Projects.
   - Distinct tags for:
     - 🟢 **Direct Match** (e.g. `Python` $\leftrightarrow$ `Python`)
     - 🔵 **Adjacent Match via SBERT** (e.g. `FastAPI` $\leftrightarrow$ `Flask` (84% semantic similarity))
     - 🔴 **Missing Critical Skill** (e.g. `Kubernetes` — 0% coverage)
   - Actionable remediation recommendation: *"Adding 1 project with Docker will boost this match by +14%"*.

---

## TASK 2: TPO Talent Pool Cohort Builder (Smart Search & Export)

### Files to touch
- Backend: `backend/app/api/v1/tpo.py`
- Frontend: `frontend/src/pages/tpo/Students.jsx`

### What you need to do
1. **Multi-Condition Search Endpoint:**
   `POST /api/v1/tpo/cohorts/query`
   Accepts filter criteria:
   ```json
   {
     "min_cgpa": 7.5,
     "max_backlogs": 0,
     "departments": ["CS", "IT"],
     "must_have_skills": ["Docker", "Python"],
     "min_skill_score": 70,
     "placement_status": "unregistered"
   }
   ```
2. **Cohort Management:**
   - Allow TPO to save the filtered result as a named cohort (e.g., *"Tier-1 Product Company Candidates — Batch 2026"*).
   - Saved cohorts persist in DB table `StudentCohort` (`id`, `name`, `criteria`, `student_ids`, `created_at`).
3. **One-Click Export & Invite:**
   - **"Export Cohort CSV"**: Downloads a structured spreadsheet formatted for corporate recruiters.
   - **"Batch Invite to Drive"**: Invites the entire cohort to apply to a specific upcoming drive with a single click.

---

## TASK 3: Predictive Skill Demand Trend Engine

### What you need to do
1. In `backend/app/api/v1/analytics.py`, implement an analytics aggregator:
   `GET /api/v1/analytics/skills/trends`
   - Computes hiring demand trends by comparing skill frequencies across job postings over the last 12 months.
   - Categorizes skills into:
     - 🚀 **High Growth / Surging** (e.g., *LangChain, PyTorch, Kubernetes, Go*)
     - ⚖️ **Stable Core** (e.g., *SQL, Python, React, Git*)
     - 📉 **Declining Demand** (e.g., *jQuery, PHP, Visual Basic*)
2. In `frontend/src/pages/tpo/Analytics.jsx` and `frontend/src/pages/student/SkillGap.jsx`:
   - Display a **"Market Trends Radar"** showing students which skills give them the highest competitive advantage in upcoming campus placements.

---

## ✅ Checklist — What "Done" Looks Like
- [ ] Clicking any job match shows a 3-part diagnostic breakdown (Academic, Skills, Experience) with SBERT semantic adjacency
- [ ] TPO can build complex multi-skill filter queries and save named student cohorts
- [ ] TPO can export any filtered cohort directly to CSV
- [ ] Skill demand trend engine classifies surging vs declining market competencies
