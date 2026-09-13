# 🧑‍💻 Sachin's Task Sheet — Job Matching + Skill Gap + Student Dashboard

> **Role:** Make the AI/ML-powered matching features actually work end-to-end.
> **Priority:** 🟠 P1 (This is the "AI differentiator" of the entire project)

---

## 📋 Project Context (READ THIS FIRST)

This is a **college placement portal** (CCIP). You're working on the **AI brain** — the features that match students to jobs and analyze skill gaps. The project uses:
- **Frontend:** React + Vite (in `d:\Projects\p1\frontend\`)
- **Backend:** FastAPI + SQLAlchemy (in `d:\Projects\p1\backend\`)
- **ML Layer:** Custom ML models in `backend/app/ml/` — gap_engine.py, matcher.py, features.py, embeddings.py
- **API Client:** Axios at `frontend/src/api/client.js`
- **API Endpoints:** Function wrappers at `frontend/src/api/endpoints.js`

### THE CORE PROBLEM
The Job Matches page uses `MOCK_JOBS` (16 hardcoded job objects). The Skill Gap page uses a `SKILL_DATA` constant. The Student Dashboard uses `MOCK_STATS`, `MOCK_TOP_MATCHES`, etc. **Nothing calls the real backend.** The backend has a working ML matching service with a trained GBT model (`matcher_model.pkl`) and a semantic gap engine — but the frontend never calls it.

---

## TASK 1: Wire Job Matches Page to Real Backend

### What exists now
File: `d:\Projects\p1\frontend\src\pages\student\JobMatches.jsx`

At the top, there's a massive `MOCK_JOBS` array with 16 hardcoded job objects like:
```js
const MOCK_JOBS = [
  { id: 1, title: 'SDE-1', company: 'Google', match: 92, ... },
  ...
];
```
The entire page renders from this static array. Filters work client-side on this static list.

### What you need to do

**Step 1:** Add imports and state:
```jsx
import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { intelligenceApi } from '../../api/endpoints';

export default function JobMatches() {
  const { user } = useAuth();
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({ role: 'all', location: 'all', minMatch: 0 });
```

**Step 2:** Fetch matches from the ML backend:
```jsx
  useEffect(() => {
    async function fetchMatches() {
      try {
        setLoading(true);
        // This calls: GET /api/v1/matching/students/{id}/jobs
        const res = await intelligenceApi.getMatches(user.id, filters);
        setJobs(res.data);
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to load job matches');
      } finally {
        setLoading(false);
      }
    }
    if (user?.id) fetchMatches();
  }, [user, filters]);
```

**Step 3:** Replace all references to `MOCK_JOBS` with `jobs`. The backend returns objects shaped like:
```json
{
  "job_id": "uuid",
  "title": "SDE-1",
  "company_name": "Google",
  "location": "Bangalore",
  "salary_ctc_min": 12.0,
  "salary_ctc_max": 25.0,
  "role_category": "Software Engineering",
  "match_score": 87.5,
  "skill_match_pct": 78.3,
  "matched_skills": ["Python", "SQL", "React"],
  "missing_skills": ["Docker", "Kubernetes"],
  "eligible": true
}
```

**Map the fields:**
- `job.company` → `job.company_name`
- `job.match` → `job.match_score` (this is 0-100 from the ML model)
- `job.salary` → format from `job.salary_ctc_min` / `job.salary_ctc_max` (these are in lakhs)
- `job.skills` → `job.matched_skills`
- `job.missing` → `job.missing_skills`
- `job.eligible` → `job.eligible` (boolean — false if CGPA/dept doesn't qualify)

**Step 4:** The job detail modal — when you click "View Details" on a job, it shows a modal. Update it to show:
- Real matched vs missing skills
- ML match score with explanation
- Eligibility status with reason (why eligible/not)
- A "View Skill Gap" button that navigates to `/student/skill-gap?role=${job.role_category}`

**Step 5:** Delete the `MOCK_JOBS` constant entirely.

**Step 6:** Add loading and error states:
```jsx
if (loading) return <div className="page-body" style={{textAlign:'center',padding:'4rem'}}>Calculating your matches...</div>;
if (error) return <div className="page-body" style={{color:'#ef4444',textAlign:'center',padding:'4rem'}}>{error}</div>;
if (jobs.length === 0) return <div className="page-body" style={{textAlign:'center',padding:'4rem',color:'var(--text-muted)'}}>No job matches found. Complete your profile and add skills to see matches.</div>;
```

### Backend API that already exists
| Endpoint | Method | What it does |
|----------|--------|-------------|
| `/api/v1/matching/students/{id}/jobs` | GET | Runs ML matcher against all active jobs, returns scored + ranked list |

Backend service file: `d:\Projects\p1\backend\app\services\matching_service.py` — the `compute_job_matches()` function at lines 100-185:
1. Loads student's skills from DB
2. Loads all active jobs with their required skills
3. Runs `predict_match_score()` from the ML matcher (uses GBT model or heuristic fallback)
4. Checks eligibility (CGPA, department constraints)
5. Returns sorted list

ML matcher: `d:\Projects\p1\backend\app\ml\matcher.py` — uses `matcher_model.pkl` (a trained Gradient Boosted Tree model).

### ⚠️ IMPORTANT: Check the API route file
Look at `d:\Projects\p1\backend\app\api\v1\matching.py`. Verify the route `/matching/students/{student_id}/jobs` exists and calls `matching_service.compute_job_matches()`. If it doesn't, you need to create it:

```python
@router.get("/students/{student_id}/jobs", response_model=list[JobMatchResponse])
async def get_student_job_matches(
    student_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    student = await student_service.get_student_full(db, student_id)
    matches = await matching_service.compute_job_matches(
        db=db,
        student_id=student_id,
        student_cgpa=float(student.cgpa) if student.cgpa else None,
        student_dept_code=student.department.code if student.department else None,
    )
    return matches
```

---

## TASK 2: Wire Skill Gap Analysis to ML Backend

### What exists now
File: `d:\Projects\p1\frontend\src\pages\student\SkillGap.jsx`

There's a hardcoded `SKILL_DATA` object:
```js
const SKILL_DATA = {
  overall_score: 72,
  target_role: 'Software Engineer',
  gaps: [
    { name: 'Docker', category: 'tools', current: 20, required: 75, gap: 55, severity: 'critical' },
    ...
  ]
};
```

### What you need to do

**Step 1:** Add state and API fetching:
```jsx
import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { intelligenceApi } from '../../api/endpoints';

export default function SkillGap() {
  const { user } = useAuth();
  const [gapData, setGapData] = useState(null);
  const [targetRole, setTargetRole] = useState('Software Engineer');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchGap() {
      try {
        setLoading(true);
        // This calls the ML gap engine
        const res = await intelligenceApi.getSkillGap(user.id, targetRole);
        setGapData(res.data);
      } catch (err) {
        console.error('Skill gap fetch failed:', err);
      } finally {
        setLoading(false);
      }
    }
    if (user?.id) fetchGap();
  }, [user, targetRole]);
```

**Step 2:** The backend returns:
```json
{
  "student_id": "uuid",
  "target_role": "Software Engineer",
  "overall_score": 72,
  "gaps": [
    {
      "skill_name": "Docker",
      "category": "tools",
      "current_score": 0.2,
      "required_score": 0.75,
      "gap": 0.55,
      "severity": "critical"
    }
  ]
}
```

**Step 3:** Map the data:
- `SKILL_DATA.overall_score` → `gapData?.overall_score`
- `SKILL_DATA.target_role` → `gapData?.target_role`
- `SKILL_DATA.gaps` → `gapData?.gaps` (map `current_score * 100` and `required_score * 100` for display as percentages)

**Step 4:** When the role selector dropdown changes, update `targetRole` and re-fetch.

**Step 5:** Delete `SKILL_DATA` constant.

### ⚠️ CHECK THE API ROUTE
The endpoint in `endpoints.js` is defined as:
```js
getSkillGap: (studentId, jobId) => mockOr('skill_gap.json', () => api.get(`/gaps/students/${studentId}/jobs/${jobId}`))
```
But the matching_service.py's `compute_skill_gap()` takes a `target_role` string, not a `jobId`. **You may need to:**
1. Update the `endpoints.js` to: `getSkillGap: (studentId, targetRole) => api.get(`/matching/students/${studentId}/gap`, { params: { target_role: targetRole } })`
2. Add a route in `backend/app/api/v1/matching.py`:
```python
@router.get("/students/{student_id}/gap", response_model=SkillGapResponse)
async def get_skill_gap(
    student_id: uuid.UUID,
    target_role: str = Query("Software Engineer"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await matching_service.compute_skill_gap(db, student_id, target_role)
```

### Backend ML that already exists
- Gap engine: `d:\Projects\p1\backend\app\ml\gap_engine.py` — `compute_gap_scores()` uses semantic embeddings to detect partial skill coverage
- Embeddings: `d:\Projects\p1\backend\app\ml\embeddings.py` — provides sentence-transformer based skill embeddings

---

## TASK 3: Wire Student Dashboard to Real Data

### What exists now
File: `d:\Projects\p1\frontend\src\pages\student\Dashboard.jsx`

Hardcoded constants at the top:
```js
const MOCK_STATS = { skill_score: 72, match_count: 14, ... };
const MOCK_SKILL_RADAR = [...];
const MOCK_TOP_MATCHES = [...];
const MOCK_SKILL_GAPS = [...];
const MOCK_DRIVES = [...];
```

### What you need to do

The Dashboard should aggregate data from multiple API calls:

```jsx
useEffect(() => {
  async function fetchDashboard() {
    try {
      setLoading(true);
      const [matchesRes, gapRes, drivesRes, profileRes] = await Promise.all([
        intelligenceApi.getMatches(user.id, { limit: 3 }),         // top 3 matches
        intelligenceApi.getSkillGap(user.id, 'Software Engineer'), // overall skill gap
        placementApi.getDrives({ status: 'upcoming', per_page: 5 }),// upcoming drives
        studentApi.getMyProfile(),                                  // profile + skill score
      ]);

      setStats({
        skill_score: gapRes.data.overall_score,
        match_count: matchesRes.data.length,
        // ... compute from real data
      });
      setTopMatches(matchesRes.data.slice(0, 3));
      setSkillGaps(gapRes.data.gaps.slice(0, 5));
      setUpcomingDrives(drivesRes.data.data?.slice(0, 5) || []);
    } catch (err) {
      setError('Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  }
  if (user?.id) fetchDashboard();
}, [user]);
```

Replace ALL `MOCK_*` constants with the real API data. Delete all mock constants.

### Add these imports at the top:
```jsx
import { intelligenceApi, placementApi, studentApi } from '../../api/endpoints';
```

---

## TASK 4: Validate ML Models Work

### What to test
1. **Start the backend:** `cd d:\Projects\p1\backend && python -m uvicorn app.main:app --reload`
2. **Register a test student** via API or frontend
3. **Add some skills** to the student (via API)
4. **Call the matching endpoint** and verify scores are reasonable:
   ```bash
   curl http://localhost:8000/api/v1/matching/students/{id}/jobs -H "Authorization: Bearer {token}"
   ```
5. **Call the gap endpoint** and verify gaps make sense

### If ML models fail
If `predict_match_score()` crashes, the service has a **heuristic fallback** in `matcher.py`. Make sure that fallback path works so the feature doesn't break even without the `.pkl` model.

### Files to check:
- `d:\Projects\p1\backend\app\ml\matcher.py` — the `predict_match_score()` function
- `d:\Projects\p1\backend\app\ml\gap_engine.py` — the `compute_gap_scores()` function
- `d:\Projects\p1\backend\app\ml\features.py` — feature extraction for the ML model
- `d:\Projects\p1\backend\app\ml\matcher_model.pkl` — the trained model file (405 KB)

---

## ✅ Checklist — What "Done" Looks Like
- [ ] Job Matches page loads real matches from ML backend (no MOCK_JOBS remains)
- [ ] Match scores come from the real ML model (not hardcoded)
- [ ] Skill Gap page fetches real gaps from the gap engine (no SKILL_DATA remains)
- [ ] Changing target role re-computes the gap analysis
- [ ] Student Dashboard shows real stats from multiple API calls (no MOCK_STATS remains)
- [ ] Loading spinners while ML computations are in progress
- [ ] Error handling when backend is down or returns errors
- [ ] Empty states when no jobs/skills exist ("Add skills to see matches")
- [ ] ML model produces reasonable scores (0-100 range, not all zeros/hundreds)
