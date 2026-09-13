# 🧑‍💻 Purshottam's Task Sheet — TPO Dashboard + Analytics + Student Roster

> **Role:** Make all TPO admin pages show real data from the database.
> **Priority:** 🟠 P1 (Evaluators check admin dashboards first)

---

## 📋 Project Context (READ THIS FIRST)

This is a **college placement portal** (CCIP). You're working on the **TPO Portal** — the pages that the Training & Placement Officer (admin) sees. The project uses:
- **Frontend:** React + Vite (in `d:\Projects\p1\frontend\`)
- **Backend:** FastAPI + SQLAlchemy (in `d:\Projects\p1\backend\`)
- **API Endpoints:** `frontend/src/api/endpoints.js` has `analyticsApi` and `tpoApi` functions

### THE CORE PROBLEM
All 3 TPO pages are 100% hardcoded:
1. **TPO Dashboard** — `STATS`, `TREND_DATA`, `TOP_RECRUITERS`, `DEPT_STATS`, `UPCOMING_DRIVES` — all fake
2. **TPO Analytics** — `DEPT_PLACEMENT`, `YOY_DATA`, `PACKAGE_DISTRIBUTION`, `SECTOR_PIE`, `SKILL_DEMAND` — all fake
3. **TPO Students** — `MOCK_STUDENTS` — 12 hardcoded student rows

**The backend already has a complete analytics_service.py** (200 lines) with real SQL aggregation queries. You just need to wire everything up.

---

## TASK 1: TPO Dashboard — Wire All KPI Cards + Charts

### What exists now
File: `d:\Projects\p1\frontend\src\pages\tpo\Dashboard.jsx`

Hardcoded at the top:
```js
const STATS = { total_students: 348, registered: 312, placed: 214, ... };
const TREND_DATA = [{ month: 'Oct', placed: 12 }, ...];
const TOP_RECRUITERS = [{ company: 'Google', hires: 8, avg_ctc: 38.5 }, ...];
const DEPT_STATS = [{ dept: 'CS', total: 110, placed: 82, rate: 74.5 }, ...];
const UPCOMING_DRIVES = [{ company: 'Amazon', date: '2025-03-15', ... }, ...];
```

### What you need to do

**Step 1:** Add imports and state:
```jsx
import { useState, useEffect } from 'react';
import { analyticsApi, placementApi } from '../../api/endpoints';

export default function TPODashboard() {
  const [stats, setStats] = useState(null);
  const [deptStats, setDeptStats] = useState([]);
  const [upcomingDrives, setUpcomingDrives] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
```

**Step 2:** Fetch all data on mount:
```jsx
  useEffect(() => {
    async function fetchDashboard() {
      try {
        setLoading(true);
        const [statsRes, drivesRes] = await Promise.all([
          analyticsApi.getPlacementStats(),                    // GET /api/v1/analytics/placement
          placementApi.getDrives({ status: 'upcoming' }),      // GET /api/v1/drives?status=upcoming
        ]);
        setStats(statsRes.data);
        setUpcomingDrives(drivesRes.data.data || []);
      } catch (err) {
        setError('Failed to load dashboard');
      } finally {
        setLoading(false);
      }
    }
    fetchDashboard();
  }, []);
```

**Step 3:** Replace `STATS` with `stats`. The backend returns:
```json
{
  "academic_year": "2025-26",
  "total_students": 348,
  "registered": 348,
  "placed": 214,
  "placement_pct": 61.5,
  "avg_package": 8.4,
  "median_package": null,
  "highest_package": 80.0,
  "companies_visited": 42,
  "offers_released": 256
}
```

Map to existing KPI cards:
- `STATS.total_students` → `stats?.total_students`
- `STATS.placed` → `stats?.placed`
- `STATS.placement_pct` → `stats?.placement_pct`
- `STATS.avg_ctc` → `stats?.avg_package`
- `STATS.highest_ctc` → `stats?.highest_package`

**Step 4:** Replace `UPCOMING_DRIVES` with `upcomingDrives`. The drives API returns the same shape described in Anjula's task sheet.

**Step 5:** For `DEPT_STATS`, you need to call the department stats endpoint. Check if `analyticsApi` has a `getDepartmentStats` function, or add one:

```js
// In endpoints.js, add:
getDeptPlacement: () => api.get('/analytics/placement/departments'),
```

And in the backend, add a route (if it doesn't exist) that calls `analytics_service.get_dept_placement_stats()`:
```python
# In backend/app/api/v1/analytics.py
@router.get("/placement/departments")
async def dept_placement_stats(db: AsyncSession = Depends(get_db)):
    return await analytics_service.get_dept_placement_stats(db)
```

The service function `get_dept_placement_stats()` already exists in `d:\Projects\p1\backend\app\services\analytics_service.py` at lines 74-107. It runs real SQL aggregation queries per department.

**Step 6:** For `TOP_RECRUITERS` and `TREND_DATA`, these backend endpoints may not exist yet. You need to create them in the analytics service:

```python
# Add to analytics_service.py:
async def get_top_recruiters(db: AsyncSession, limit: int = 10) -> list[RecruiterRow]:
    """Top companies by number of placements."""
    result = await db.execute(
        select(
            Company.name,
            func.count(PlacementOutcome.id).label("hires"),
            func.avg(PlacementOutcome.salary_ctc).label("avg_ctc")
        )
        .join(PlacementDrive, PlacementOutcome.drive_id == PlacementDrive.id)
        .join(Company, PlacementDrive.company_id == Company.id)
        .group_by(Company.name)
        .order_by(func.count(PlacementOutcome.id).desc())
        .limit(limit)
    )
    return [RecruiterRow(company=r.name, hires=r.hires, avg_ctc=float(r.avg_ctc) if r.avg_ctc else None) for r in result]
```

**Step 7:** Delete ALL `STATS`, `TREND_DATA`, `TOP_RECRUITERS`, `DEPT_STATS`, `UPCOMING_DRIVES` constants.

### Backend that already exists
| Service Function | File Location | What it does |
|-----------------|--------------|-------------|
| `get_placement_stats()` | `analytics_service.py` L22-71 | Total students, placed count, avg/max package |
| `get_dept_placement_stats()` | `analytics_service.py` L74-107 | Per-department breakdown |
| `get_skill_demand_vs_supply()` | `analytics_service.py` L110-149 | Skill demand vs student supply |
| `get_curriculum_gaps()` | `analytics_service.py` L152-199 | Curriculum gap analysis per subject |

---

## TASK 2: TPO Analytics — Wire All Charts

### What exists now
File: `d:\Projects\p1\frontend\src\pages\tpo\Analytics.jsx`

Hardcoded arrays:
```js
const DEPT_PLACEMENT = [{ dept: 'CS', placed: 82, total: 110, pct: 74.5 }, ...];
const YOY_DATA = [{ year: '2021-22', placed: 148, rate: 52.3, avg_pkg: 5.8 }, ...];
const PACKAGE_DISTRIBUTION = [{ range: '< 4L', count: 38 }, ...];
const SECTOR_PIE = [{ name: 'Product', value: 62 }, ...];
const SKILL_DEMAND = [{ skill: 'Python', demand: 92, supply: 75, gap: 17 }, ...];
```

### What you need to do

**Step 1:** Add state and fetch:
```jsx
const [deptPlacement, setDeptPlacement] = useState([]);
const [skillDemand, setSkillDemand] = useState([]);
const [loading, setLoading] = useState(true);

useEffect(() => {
  async function fetchAnalytics() {
    try {
      setLoading(true);
      const [deptRes, skillRes] = await Promise.all([
        analyticsApi.getPlacementStats(),        // or a specific dept stats endpoint
        analyticsApi.getSkillDemand(),            // GET /api/v1/analytics/skill-demand
      ]);
      setDeptPlacement(deptRes.data.dept_breakdown || []);
      setSkillDemand(skillRes.data);
    } catch (err) {
      console.error('Analytics fetch failed:', err);
    } finally {
      setLoading(false);
    }
  }
  fetchAnalytics();
}, []);
```

**Step 2:** For `DEPT_PLACEMENT`, replace with real dept stats from `get_dept_placement_stats()`. The backend returns:
```json
[
  { "department_code": "CS", "department_name": "Computer Science", "total": 110, "placed": 82, "placement_pct": 74.5, "avg_package": 12.3 }
]
```

Map: `dept.dept` → `dept.department_code`, `dept.pct` → `dept.placement_pct`

**Step 3:** For `SKILL_DEMAND`, replace with real data from `get_skill_demand_vs_supply()`. The backend returns:
```json
[
  { "skill_name": "Python", "demand_pct": 92.0, "supply_pct": 75.0, "gap": 17.0 }
]
```

Map: `s.skill` → `s.skill_name`, `s.demand` → `s.demand_pct`, `s.supply` → `s.supply_pct`

**Step 4:** For `YOY_DATA`, `PACKAGE_DISTRIBUTION`, and `SECTOR_PIE` — these backend endpoints may not exist. You have two options:

**Option A (Recommended):** Create new backend service functions:
```python
# In analytics_service.py, add:

async def get_package_distribution(db: AsyncSession) -> list[PackageBandRow]:
    """Count students per salary band."""
    result = await db.execute(
        select(PlacementOutcome.salary_ctc).where(PlacementOutcome.salary_ctc.isnot(None))
    )
    salaries = [float(r[0]) for r in result]
    bands = [
        ("< 4L", 0, 4), ("4–7L", 4, 7), ("7–12L", 7, 12),
        ("12–20L", 12, 20), ("20–40L", 20, 40), ("> 40L", 40, 200)
    ]
    return [
        PackageBandRow(range=label, count=sum(1 for s in salaries if low <= s < high))
        for label, low, high in bands
    ]
```

**Option B (Quick fix):** Keep the hardcoded data for YOY/Package/Sector charts for now, and focus on making the 2 most important charts real (dept placement + skill demand). Mark the others with a "Sample data" label.

**Step 5:** Add API routes in `d:\Projects\p1\backend\app\api\v1\analytics.py` for any new service functions you create.

**Step 6:** Delete all hardcoded constants from Analytics.jsx.

---

## TASK 3: TPO Students — Wire to Real Database

### What exists now
File: `d:\Projects\p1\frontend\src\pages\tpo\Students.jsx`

Hardcoded: `MOCK_STUDENTS` — 12 student objects.

### What you need to do

**Step 1:** Import and fetch:
```jsx
import { tpoApi } from '../../api/endpoints';

const [students, setStudents] = useState([]);
const [loading, setLoading] = useState(true);
const [totalStudents, setTotalStudents] = useState(0);

useEffect(() => {
  fetchStudents();
}, [dept, status, minCGPA, search]);

const fetchStudents = async () => {
  try {
    setLoading(true);
    const res = await tpoApi.getStudents({
      department_code: dept !== 'All' ? dept : undefined,
      min_cgpa: minCGPA > 0 ? minCGPA : undefined,
      page: 1,
      per_page: 50,
    });
    // Backend returns: { data: [...students], meta: { page, per_page, total, total_pages } }
    setStudents(res.data.data || []);
    setTotalStudents(res.data.meta?.total || 0);
  } catch (err) {
    console.error('Failed to load students:', err);
  } finally {
    setLoading(false);
  }
};
```

**Step 2:** Replace `MOCK_STUDENTS` with `students`. The backend returns each student as:
```json
{
  "id": "uuid",
  "roll_number": "CS21B001",
  "first_name": "Priya",
  "last_name": "Agarwal",
  "email": "priya@example.com",
  "department_code": "CS",
  "department_name": "Computer Science",
  "current_semester": 8,
  "cgpa": 9.1,
  "resume_parsed": true
}
```

Map:
- `s.name` → `s.first_name + ' ' + s.last_name`
- `s.roll` → `s.roll_number`
- `s.dept` → `s.department_code`
- `s.cgpa` → `s.cgpa`

**Step 3:** The status filter (`selected`, `shortlisted`, `applied`, `unregistered`) — the backend doesn't have this as a student field. Students don't have a single "status". Their status depends on their applications.

**You need to either:**
- Add a computed `placement_status` field in the backend's `list_students` response, OR
- Fetch applications separately and compute status client-side, OR
- Add a `status` query parameter to the backend that computes it via SQL joins

**Recommended:** Add to the backend's student list endpoint:
```python
# In student_service.py list_students(), after fetching students:
# For each student, check their latest application status
for student in students:
    latest_app = await db.execute(
        select(Application.status)
        .where(Application.student_id == student.id)
        .order_by(Application.applied_at.desc())
        .limit(1)
    )
    app_status = latest_app.scalar_one_or_none()
    student._placement_status = app_status or "unregistered"
```

**Step 4:** The "View Full Profile" button → navigate to `/tpo/students/{id}/profile` or open a modal showing student details.

**Step 5:** The "Sync UMS" button → call `tpoApi.syncUMS(rollNumber)`:
```jsx
const handleSyncUMS = async (student) => {
  try {
    await tpoApi.syncUMS(student.roll_number);
    alert('UMS sync completed');
    fetchStudents(); // refresh
  } catch (err) {
    alert('UMS sync failed: ' + (err.response?.data?.detail || 'Unknown error'));
  }
};
```

**Step 6:** Client-side search (by name/roll) should still work but now against real data:
```jsx
const filtered = students.filter(s =>
  s.first_name.toLowerCase().includes(search.toLowerCase()) ||
  s.last_name.toLowerCase().includes(search.toLowerCase()) ||
  s.roll_number.toLowerCase().includes(search.toLowerCase())
);
```

**Step 7:** Delete `MOCK_STUDENTS` constant.

### Backend API that already exists
| Endpoint | Method | What it does |
|----------|--------|-------------|
| `GET /api/v1/students` | GET | List all students (paginated, filtered) — TPO only |
| `GET /api/v1/students/{id}` | GET | Get a single student profile — TPO only |

Backend route: `d:\Projects\p1\backend\app\api\v1\students.py` lines 108-142.
Backend service: `d:\Projects\p1\backend\app\services\student_service.py` — `list_students()` at lines 49-81.

---

## TASK 4: Backend Analytics API Routes

### Check what routes exist
Look at `d:\Projects\p1\backend\app\api\v1\analytics.py`. It should have routes like:
- `GET /analytics/placement` → calls `analytics_service.get_placement_stats()`
- `GET /analytics/placement/departments` → calls `get_dept_placement_stats()`
- `GET /analytics/skill-demand` → calls `get_skill_demand_vs_supply()`
- `GET /analytics/curriculum-gaps/{dept_code}` → calls `get_curriculum_gaps()`

If any are missing, add them. The service functions all exist already in `analytics_service.py`.

Also verify the analytics router is registered in `d:\Projects\p1\backend\app\main.py`.

---

## ✅ Checklist — What "Done" Looks Like
- [ ] TPO Dashboard KPIs show real numbers from DB (no hardcoded STATS)
- [ ] Department placement breakdown shows real data
- [ ] Upcoming drives list shows real drives from DB
- [ ] Analytics page — department chart shows real data
- [ ] Analytics page — skill demand vs supply chart shows real data
- [ ] Analytics page — at least 4 of 6 charts use real data (remaining can be marked "sample data")
- [ ] Students roster loads real student data from DB
- [ ] Search, filter, and sort work on real data
- [ ] Pagination works for large student lists
- [ ] Loading states, error handling, and empty states everywhere
