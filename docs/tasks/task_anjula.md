# 🧑‍💻 Anjula's Task Sheet — Placement Drives + Applications

> **Role:** Make the entire placement drive lifecycle work — TPO creates drives → students apply → track applications.
> **Priority:** 🟠 P1 (Core placement feature)

---

## 📋 Project Context (READ THIS FIRST)

This is a **college placement portal** (CCIP). You're working on **Placement Drives** — the flow where the TPO (Training & Placement Officer) creates placement drives for companies, and students can browse and apply to them. The project uses:
- **Frontend:** React + Vite (in `d:\Projects\p1\frontend\`)
- **Backend:** FastAPI + SQLAlchemy (in `d:\Projects\p1\backend\`)
- **API Endpoints:** `frontend/src/api/endpoints.js` has pre-defined `placementApi` functions

### THE CORE PROBLEM
There are two drive-related pages:
1. **TPO Drives page** (`d:\Projects\p1\frontend\src\pages\tpo\Drives.jsx`) — TPO manages drives. Has a "Create Drive" modal that **submits to nowhere**. All drives shown are from `MOCK_DRIVES`.
2. **Student PlacementDrives page** (`d:\Projects\p1\frontend\src\pages\student\PlacementDrives.jsx`) — Students browse and apply. All drives from `MOCK_DRIVES`. "Apply Now" button **just flips a local boolean**, never calls the backend.

**The backend already has a complete drive service** — `drive_service.py` (193 lines) and `drives.py` API routes (150 lines) — with create, list, update, apply, get shortlisted. You just need to wire the frontend to it.

---

## TASK 1: TPO — Make "Create Drive" Actually Create a Drive

### What exists now
File: `d:\Projects\p1\frontend\src\pages\tpo\Drives.jsx`

There's a "Create Drive" button that opens a modal with form fields (company name, title, description, date, CTC, min CGPA, etc.). When submitted, it does... nothing. The drives list is populated from `MOCK_DRIVES` (hardcoded array of ~8 objects).

### What you need to do

**Step 1:** Import the API:
```jsx
import { placementApi } from '../../api/endpoints';
```

**Step 2:** Add state for real data:
```jsx
const [drives, setDrives] = useState([]);
const [loading, setLoading] = useState(true);
const [creating, setCreating] = useState(false);
```

**Step 3:** Fetch drives from backend on mount:
```jsx
useEffect(() => {
  fetchDrives();
}, []);

const fetchDrives = async () => {
  try {
    setLoading(true);
    const res = await placementApi.getDrives();
    // Backend returns: { data: [...drives], meta: { page, per_page, total, total_pages } }
    setDrives(res.data.data || []);
  } catch (err) {
    console.error('Failed to load drives:', err);
  } finally {
    setLoading(false);
  }
};
```

**Step 4:** Wire the "Create Drive" form submission:
```jsx
const handleCreateDrive = async (formData) => {
  try {
    setCreating(true);
    // The backend expects this shape (see DriveCreateRequest schema):
    await placementApi.createDrive({
      company_name: formData.companyName,
      company_industry: formData.industry || null,
      company_location: formData.location || null,
      title: formData.title,
      description: formData.description,
      drive_date: formData.driveDate,           // ISO date string "2025-03-15"
      registration_deadline: formData.deadline,  // ISO date string
      min_cgpa: parseFloat(formData.minCGPA) || null,
      eligible_departments: formData.departments || [],  // ["CS", "IT", "ECE"]
      max_backlogs: parseInt(formData.maxBacklogs) || 0,
      roles_offered: formData.roles || [],       // ["SDE-1", "Data Analyst"]
      salary_ctc: parseFloat(formData.ctc) || null,
      academic_year: formData.academicYear || "2025-26",
    });
    
    // Success! Close modal and refresh list
    setShowCreateModal(false);
    await fetchDrives(); // Re-fetch to show new drive
    // Show success toast/message
  } catch (err) {
    alert(err.response?.data?.detail || 'Failed to create drive');
  } finally {
    setCreating(false);
  }
};
```

**Step 5:** Replace all `MOCK_DRIVES` references with `drives` state variable. Map the fields:
The backend returns each drive as:
```json
{
  "id": "uuid",
  "company": { "id": "uuid", "name": "Google", "industry": "Tech", "location": "Bangalore" },
  "title": "SDE-1 Hiring",
  "description": "...",
  "drive_date": "2025-03-15",
  "registration_deadline": "2025-03-10",
  "min_cgpa": 7.0,
  "eligible_departments": ["CS", "IT"],
  "max_backlogs": 0,
  "roles_offered": ["SDE-1"],
  "salary_ctc": 18.5,
  "status": "upcoming",
  "academic_year": "2025-26",
  "registered_count": 45,
  "shortlisted_count": 12,
  "selected_count": 3,
  "has_applied": false
}
```

Map to existing UI:
- `MOCK_DRIVES[i].company` → `drive.company?.name`
- `MOCK_DRIVES[i].ctc` → `drive.salary_ctc` (in lakhs)
- `MOCK_DRIVES[i].status` → `drive.status` (values: "upcoming", "open", "in_progress", "completed")
- `MOCK_DRIVES[i].registered` → `drive.registered_count`
- `MOCK_DRIVES[i].shortlisted` → `drive.shortlisted_count`
- `MOCK_DRIVES[i].selected` → `drive.selected_count`

**Step 6:** Delete `MOCK_DRIVES` constant entirely.

### Backend API that already exists (NO backend changes needed)
| Endpoint | Method | What it does |
|----------|--------|-------------|
| `GET /api/v1/drives` | GET | List all drives (paginated), with status filter |
| `POST /api/v1/drives` | POST | Create a new drive (TPO only) |
| `GET /api/v1/drives/{id}` | GET | Get single drive detail |
| `PATCH /api/v1/drives/{id}` | PATCH | Update a drive (TPO only) |

Backend route file: `d:\Projects\p1\backend\app\api\v1\drives.py` (lines 1-150)
Backend service file: `d:\Projects\p1\backend\app\services\drive_service.py` (lines 1-193)
- `create_drive()` at line 58 — auto-creates Company if it doesn't exist
- `list_drives()` at line 33 — supports status filter and pagination

---

## TASK 2: TPO — Make "Edit Drive" Work

### What exists now
Each drive card has an "Edit" button. Clicking it currently does nothing or opens a blank modal.

### What you need to do

**Step 1:** When "Edit" is clicked, populate the modal with existing drive data:
```jsx
const handleEditClick = (drive) => {
  setEditingDrive(drive);
  setEditFormData({
    title: drive.title,
    description: drive.description,
    drive_date: drive.drive_date,
    registration_deadline: drive.registration_deadline,
    min_cgpa: drive.min_cgpa,
    status: drive.status,
    salary_ctc: drive.salary_ctc,
    // ... etc
  });
  setShowEditModal(true);
};
```

**Step 2:** When "Save" is clicked:
```jsx
const handleUpdateDrive = async () => {
  try {
    await placementApi.updateDrive(editingDrive.id, editFormData);
    setShowEditModal(false);
    await fetchDrives(); // Refresh list
  } catch (err) {
    alert(err.response?.data?.detail || 'Failed to update drive');
  }
};
```

Backend: `PATCH /api/v1/drives/{id}` — accepts partial updates. Send only changed fields.

---

## TASK 3: TPO — Make "View Applications" / "View Shortlisted" Work

### What exists now
Each drive card has "View Shortlisted" which opens a modal showing `SHORTLISTED_STUDENTS` (hardcoded). The buttons in it do nothing.

### What you need to do

**Step 1:** When "View Shortlisted" is clicked, fetch from backend:
```jsx
const handleViewShortlisted = async (driveId) => {
  try {
    const res = await placementApi.shortlistStudents(driveId);
    // res.data = [{ application_id, student_id, roll_number, first_name, last_name, cgpa, status, current_stage, applied_at }]
    setShortlistedStudents(res.data);
    setShowShortlistModal(true);
  } catch (err) {
    alert('Failed to load shortlisted students');
  }
};
```

Backend: `GET /api/v1/drives/{driveId}/shortlisted` — returns students with status "shortlisted", "in_progress", or "selected".

Backend route: `d:\Projects\p1\backend\app\api\v1\drives.py` lines 129-149.

---

## TASK 4: Student — Make "Apply Now" Actually Submit an Application

### What exists now
File: `d:\Projects\p1\frontend\src\pages\student\PlacementDrives.jsx`

There's an "Apply Now" button on each drive card. When clicked, it does:
```js
setApplied(prev => ({ ...prev, [driveId]: true }));
```
This just flips a local variable. The application is never sent to the backend.

### What you need to do

**Step 1:** Add state and fetch drives from backend:
```jsx
const [drives, setDrives] = useState([]);
const [loading, setLoading] = useState(true);

useEffect(() => {
  async function fetchDrives() {
    try {
      setLoading(true);
      const res = await placementApi.getDrives();
      setDrives(res.data.data || []);
    } catch (err) {
      setError('Failed to load drives');
    } finally {
      setLoading(false);
    }
  }
  fetchDrives();
}, []);
```

**Step 2:** Replace the "Apply Now" handler:
```jsx
const handleApply = async (driveId) => {
  try {
    // POST /api/v1/drives/{driveId}/apply
    await placementApi.apply(driveId);
    
    // Update local state to show "Applied ✓"
    setDrives(prev => prev.map(d => 
      d.id === driveId ? { ...d, has_applied: true } : d
    ));
    
    // Show success message
  } catch (err) {
    if (err.response?.status === 409) {
      alert('You have already applied to this drive');
    } else if (err.response?.status === 400) {
      alert(err.response?.data?.detail || 'Cannot apply — drive is closed');
    } else {
      alert('Failed to apply');
    }
  }
};
```

**Step 3:** Use `drive.has_applied` from the backend to show the applied state. The backend's `list_drives` endpoint already computes `has_applied` for student users (it checks if the current student has an application record for each drive).

**Step 4:** Delete `MOCK_DRIVES` from PlacementDrives.jsx.

### Backend API that already exists
| Endpoint | Method | What it does |
|----------|--------|-------------|
| `POST /api/v1/drives/{driveId}/apply` | POST | Creates an application record. Returns 409 if already applied, 400 if drive not open |

Backend route: `d:\Projects\p1\backend\app\api\v1\drives.py` lines 119-126.
Backend service: `d:\Projects\p1\backend\app\services\drive_service.py` — `apply_to_drive()` at lines 133-157.

The service checks:
- Duplicate application → 409
- Drive status must be "open" or "upcoming" → 400

---

## TASK 5: Student — "My Applications" Tab — Wire to Real Data

### What exists now
In PlacementDrives.jsx, there's a "My Applications" tab/section showing `MOCK_APPLICATIONS` — hardcoded application objects with stages like "Resume Screen → Technical → HR".

### What you need to do

**Step 1:** Fetch real applications:
```jsx
const [myApps, setMyApps] = useState([]);

useEffect(() => {
  async function fetchMyApps() {
    const res = await placementApi.getMyApplications();
    // res.data = [{ id, drive: { title, company, ... }, status, current_stage, applied_at, stages: [...] }]
    setMyApps(res.data);
  }
  fetchMyApps();
}, []);
```

**Step 2:** Replace `MOCK_APPLICATIONS` with `myApps`. Each application from the backend has:
```json
{
  "id": "uuid",
  "drive": {
    "title": "SDE-1 Hiring",
    "company": { "name": "Google", "location": "Bangalore" },
    "salary_ctc": 18.5
  },
  "status": "shortlisted",
  "current_stage": "Technical Interview",
  "applied_at": "2025-03-01T10:00:00Z",
  "stages": [
    { "stage_name": "Resume Screen", "status": "cleared", "date": "..." },
    { "stage_name": "Technical Interview", "status": "scheduled", "date": "..." }
  ]
}
```

### ⚠️ CHECK: Applications API Route
The `endpoints.js` has `getMyApplications: () => api.get('/applications/mine')`. But the actual backend route might be different. Check if there's an applications route or if it's under drives. If `GET /api/v1/applications/mine` doesn't exist, you need to create it:

In a new file `d:\Projects\p1\backend\app\api\v1\applications.py`:
```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.drive_service import get_my_applications

router = APIRouter(prefix="/applications", tags=["Applications"])

@router.get("/mine")
async def get_my_applications_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    applications = await get_my_applications(db, current_user.id)
    return [
        {
            "id": app.id,
            "drive": {
                "id": app.drive.id,
                "title": app.drive.title,
                "company": {"name": app.drive.company.name} if app.drive.company else None,
                "salary_ctc": float(app.drive.salary_ctc) if app.drive.salary_ctc else None,
            },
            "status": app.status,
            "current_stage": app.current_stage,
            "applied_at": app.applied_at,
        }
        for app in applications
    ]
```

Then register this router in the main app (`d:\Projects\p1\backend\app\main.py`).

The service function `get_my_applications()` already exists in `drive_service.py` at lines 160-173.

---

## TASK 6: Show Eligibility Info on Drive Cards

### What to do
When displaying drives to students, show eligibility status:
- ✅ "Eligible" — student meets CGPA and department requirements
- ❌ "Not Eligible" — with reason (e.g., "Requires CGPA ≥ 7.5, yours is 6.8")

The backend's `list_drives` returns `has_applied` per drive, and the drive itself has `min_cgpa` and `eligible_departments`. Compare with the student's profile:

```jsx
const isEligible = (drive) => {
  if (drive.min_cgpa && profile?.cgpa < drive.min_cgpa) return false;
  if (drive.eligible_departments?.length > 0 && !drive.eligible_departments.includes(profile?.department?.code)) return false;
  return true;
};
```

If not eligible, disable the "Apply Now" button and show the reason.

---

## ✅ Checklist — What "Done" Looks Like
- [ ] TPO can create a new drive via modal → it saves to DB and appears in the list
- [ ] TPO can edit an existing drive → changes save to DB
- [ ] TPO can view shortlisted students for a drive from real DB data
- [ ] Student sees real drives from backend (no MOCK_DRIVES remains)
- [ ] Student can click "Apply Now" → application is created in DB
- [ ] "Apply Now" button shows "Applied ✓" after successful application
- [ ] Duplicate application shows "Already applied" error
- [ ] "My Applications" tab shows real applications with status
- [ ] Drive eligibility is shown (eligible/not eligible with reason)
- [ ] Loading states, error handling, and empty states are implemented
