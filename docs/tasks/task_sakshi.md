# 🧑‍💻 Sakshi's Task Sheet — Student Profile + Resume + Skills

> **Role:** Make the entire Student Profile page fully functional with real data.
> **Priority:** 🟠 P1 (Core feature — do this FIRST)

---

## 📋 Project Context (READ THIS FIRST)

This is a **college placement portal** (CCIP). You are working on the **Student Portal** — the pages a student sees after logging in. The project uses:
- **Frontend:** React + Vite (in `d:\Projects\p1\frontend\`)
- **Backend:** FastAPI + SQLAlchemy (in `d:\Projects\p1\backend\`)
- **API Client:** Axios with JWT interceptors at `frontend/src/api/client.js`
- **API Endpoints:** Pre-defined function wrappers at `frontend/src/api/endpoints.js`

### THE CORE PROBLEM
The `Profile.jsx` page currently uses **hardcoded mock data** like `MOCK_PROFILE`, `MOCK_CGPA_TREND`, `MOCK_SUBJECTS`, `MOCK_SKILLS`. None of it comes from the backend. All "Edit" and "Save" buttons do **nothing**. Your job is to **replace all mocks with real API calls** and **make all buttons actually work**.

---

## TASK 1: Wire Student Profile to Real Backend API

### What exists now
File: `d:\Projects\p1\frontend\src\pages\student\Profile.jsx`

At the top of this file, there are hardcoded objects:
```js
const MOCK_PROFILE = { name: 'Arjun Sharma', roll: 'CS21B042', ... };
const MOCK_CGPA_TREND = [ { sem: 1, gpa: 7.8 }, ... ];
const MOCK_SUBJECTS = [ { code: 'CS301', name: 'DSA', ... } ];
const MOCK_SKILLS = [ { name: 'Python', level: 85, category: 'language' }, ... ];
```

### What you need to do

**Step 1:** Add imports and state management at the top of `Profile.jsx`:
```jsx
import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { studentApi } from '../../api/endpoints';
```

**Step 2:** Inside the component function, add API fetching:
```jsx
export default function StudentProfile() {
  const { user } = useAuth();
  const [profile, setProfile] = useState(null);
  const [skills, setSkills] = useState([]);
  const [academicRecords, setAcademicRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchProfile() {
      try {
        setLoading(true);
        // These call: GET /api/v1/students/me, GET /api/v1/students/me/skills, etc.
        const [profileRes, skillsRes, recordsRes] = await Promise.all([
          studentApi.getProfile(user.id),
          studentApi.getSkills(user.id),
          studentApi.getAcademicRecords(user.id),
        ]);
        setProfile(profileRes.data);
        setSkills(skillsRes.data);
        setAcademicRecords(recordsRes.data);
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to load profile');
      } finally {
        setLoading(false);
      }
    }
    if (user?.id) fetchProfile();
  }, [user]);
  
  if (loading) return <div className="page-body" style={{textAlign:'center',padding:'4rem'}}>Loading profile...</div>;
  if (error) return <div className="page-body" style={{color:'#ef4444',textAlign:'center',padding:'4rem'}}>{error}</div>;
  // ... rest of component
}
```

**Step 3:** Replace all references to `MOCK_PROFILE` with `profile`:
- `MOCK_PROFILE.name` → `profile?.first_name + ' ' + profile?.last_name`
- `MOCK_PROFILE.roll` → `profile?.roll_number`
- `MOCK_PROFILE.email` → `profile?.email`
- `MOCK_PROFILE.phone` → `profile?.phone`
- `MOCK_PROFILE.cgpa` → `profile?.cgpa`
- `MOCK_PROFILE.department` → `profile?.department?.name` or `profile?.department?.code`
- `MOCK_PROFILE.semester` → `profile?.current_semester`
- `MOCK_PROFILE.github` → `profile?.github_url`
- `MOCK_PROFILE.linkedin` → `profile?.linkedin_url`
- `MOCK_PROFILE.portfolio` → `profile?.portfolio_url`
- `MOCK_PROFILE.bio` → `profile?.bio`

**Step 4:** Replace `MOCK_SKILLS` with `skills` array. The backend returns:
```json
[
  { "id": "uuid", "skill": { "id": "uuid", "name": "Python", "category": "language" }, "confidence": 0.85, "source": "assessment" }
]
```
So map it: `skills.map(s => ({ name: s.skill.name, level: Math.round(s.confidence * 100), category: s.skill.category }))`

**Step 5:** Replace `MOCK_SUBJECTS` with `academicRecords`. The backend returns:
```json
[
  { "id": "uuid", "subject": { "code": "CS301", "name": "DSA", "credits": 4 }, "grade": "A", "score": 9.0 }
]
```

**Step 6:** Delete all the `MOCK_*` constants from the top of the file.

### Backend API that already exists (no backend changes needed for this task)
| Endpoint | Method | What it does |
|----------|--------|-------------|
| `/api/v1/students/me` | GET | Returns full student profile |
| `/api/v1/students/me/skills` | GET | Returns student's skills with confidence scores |
| `/api/v1/students/me/academic-records` | GET | Returns semester-wise grades |

Backend file: `d:\Projects\p1\backend\app\api\v1\students.py` — routes are at lines 56-103.
Service file: `d:\Projects\p1\backend\app\services\student_service.py` — queries at lines 19-134.

### ⚠️ IMPORTANT
The API endpoints in `frontend/src/api/endpoints.js` currently use `studentApi.getProfile(id)` which calls `/students/${id}`. But the backend has a `/students/me` endpoint that uses the JWT token to identify the student. **You need to update `endpoints.js`** to add:
```js
export const studentApi = {
  getMyProfile: () => api.get('/students/me'),
  updateMyProfile: (data) => api.patch('/students/me', data),
  getMySkills: () => api.get('/students/me/skills'),
  getMyAcademicRecords: () => api.get('/students/me/academic-records'),
  updateMyConsent: (consent) => api.patch('/students/me/consent', consent),
  // ... keep existing ones too
};
```

---

## TASK 2: Make "Edit Profile" Actually Save

### What exists now
There's an "Edit Profile" button in the profile header area. Currently it does absolutely nothing.

### What you need to do

**Step 1:** Add edit state:
```jsx
const [isEditing, setIsEditing] = useState(false);
const [editData, setEditData] = useState({});
const [saving, setSaving] = useState(false);
```

**Step 2:** When "Edit Profile" is clicked:
```jsx
onClick={() => {
  setEditData({
    bio: profile?.bio || '',
    phone: profile?.phone || '',
    github_url: profile?.github_url || '',
    linkedin_url: profile?.linkedin_url || '',
    portfolio_url: profile?.portfolio_url || '',
  });
  setIsEditing(true);
}}
```

**Step 3:** Build an edit form (modal or inline) with inputs for: bio, phone, github_url, linkedin_url, portfolio_url.

**Step 4:** When "Save" is clicked:
```jsx
const handleSave = async () => {
  try {
    setSaving(true);
    const res = await api.patch('/students/me', editData);
    setProfile(res.data); // Update local state with server response
    setIsEditing(false);
  } catch (err) {
    alert(err.response?.data?.detail || 'Failed to save');
  } finally {
    setSaving(false);
  }
};
```

### Backend API that already exists (no backend changes needed)
| Endpoint | Method | Body |
|----------|--------|------|
| `/api/v1/students/me` | PATCH | `{ "bio": "...", "phone": "...", "github_url": "...", "linkedin_url": "...", "portfolio_url": "..." }` |

Backend file: `d:\Projects\p1\backend\app\api\v1\students.py` — route at line 66-74.
The `StudentUpdateRequest` schema accepts: `bio`, `phone`, `github_url`, `linkedin_url`, `portfolio_url`.

---

## TASK 3: Resume Upload — Make It Actually Upload and Parse

### What exists now
In the "Resume" tab of Profile.jsx, there's a file picker and an "Upload & Parse Skills" button. When you select a file, it shows the filename. But clicking "Upload & Parse Skills" does nothing real — it just shows a hardcoded list `['Python', 'SQL', 'React']`.

### What you need to do

**Step 1:** After user selects a file, upload it to the backend:
```jsx
const handleResumeUpload = async (file) => {
  try {
    setUploadStatus('uploading');
    const form = new FormData();
    form.append('file', file);
    
    const res = await api.post('/resume/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    
    setUploadStatus('processing'); // NLP parsing started in background
    
    // Poll for completion
    pollResumeStatus();
  } catch (err) {
    setUploadStatus('error');
    alert(err.response?.data?.detail || 'Upload failed');
  }
};
```

**Step 2:** Poll the parse status:
```jsx
const pollResumeStatus = async () => {
  const interval = setInterval(async () => {
    try {
      const res = await api.get('/resume/status');
      if (res.data.resume_parsed) {
        clearInterval(interval);
        setUploadStatus('done');
        // Refresh skills list to show newly parsed skills
        const skillsRes = await api.get('/students/me/skills');
        setSkills(skillsRes.data);
      }
    } catch { /* ignore */ }
  }, 3000); // check every 3 seconds
};
```

**Step 3:** Remove the hardcoded `['Python', 'SQL', 'React']` parsed skills. Instead show real skills from the `skills` state after they are updated by the parse.

### Backend API that already exists
| Endpoint | Method | What it does |
|----------|--------|-------------|
| `/api/v1/resume/upload` | POST (multipart) | Saves PDF, kicks off NLP parse in background |
| `/api/v1/resume/status` | GET | Returns `{ resume_url, resume_parsed: true/false, consent_resume_analysis }` |
| `/api/v1/resume/reparse` | POST | Re-run NLP on existing resume |

Backend file: `d:\Projects\p1\backend\app\api\v1\resume.py` — full implementation exists at lines 1-182.
NLP pipeline: `d:\Projects\p1\backend\app\nlp\pipeline.py` — the `process_resume()` function extracts text from PDF, matches skills from taxonomy, saves them to the student_skills table.

### ⚠️ POTENTIAL ISSUE
The NLP pipeline imports from `app.nlp.pipeline`. Check if this module exists and has a working `process_resume` function. If it doesn't, you need to create a basic one that:
1. Reads PDF bytes with `pdfplumber` or `PyPDF2`
2. Extracts text
3. Matches skill names from the `Skill` table (case-insensitive substring match)
4. Creates `StudentSkill` records with confidence=0.7 and source='resume'

---

## TASK 4: Data Consent Toggles — Make Them Persist

### What exists now
In the "Settings" or "Privacy" section of Profile.jsx, there are toggle switches for:
- "Allow resume analysis" 
- "Make profile visible to recruiters"

These look nice but changing them does nothing — they only update local React state.

### What you need to do

```jsx
const handleConsentChange = async (field, value) => {
  try {
    await api.patch('/students/me/consent', { [field]: value });
    setProfile(prev => ({ ...prev, [field]: value }));
  } catch (err) {
    alert('Failed to update consent');
    // Revert toggle
  }
};

// In JSX:
<input
  type="checkbox"
  checked={profile?.consent_resume_analysis || false}
  onChange={(e) => handleConsentChange('consent_resume_analysis', e.target.checked)}
/>

<input
  type="checkbox"
  checked={profile?.consent_profile_visible || false}
  onChange={(e) => handleConsentChange('consent_profile_visible', e.target.checked)}
/>
```

### Backend API that already exists
`PATCH /api/v1/students/me/consent` — accepts `{ consent_resume_analysis: bool, consent_profile_visible: bool }`

Backend file: `d:\Projects\p1\backend\app\api\v1\students.py` — route at lines 77-85.

---

## TASK 5: Skills Tab — Add/Remove Skills

### What exists now
The Skills tab shows skills from `MOCK_SKILLS` (hardcoded). There's an "Add Skill" button that does nothing.

### What you need to do

**Step 1:** Create an "Add Skill" modal:
- Searchable dropdown that searches from skills taxonomy
- Proficiency slider (0-100)
- "Add" button that calls API

```jsx
// Search skills taxonomy
const searchSkills = async (query) => {
  const res = await api.get('/skills/search', { params: { q: query } });
  return res.data; // returns [{ id, name, category }]
};

// Add skill to student profile
const addSkill = async (skillId, confidence) => {
  await api.post('/students/me/skills', { 
    skill_id: skillId, 
    confidence: confidence / 100 // normalize to 0-1 
  });
  // Refresh skills list
  const res = await api.get('/students/me/skills');
  setSkills(res.data);
};
```

**Step 2:** ⚠️ **The backend may not have a POST endpoint for adding skills directly.** Check `d:\Projects\p1\backend\app\api\v1\students.py`. If it doesn't exist, you need to add one:

```python
# In students.py
@router.post("/me/skills", status_code=201)
async def add_my_skill(
    data: AddSkillRequest,  # { skill_id: UUID, confidence: float }
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    student_skill = StudentSkill(
        student_id=current_user.id,
        skill_id=data.skill_id,
        confidence=data.confidence,
        source="self_reported",
    )
    db.add(student_skill)
    await db.commit()
    return {"message": "Skill added"}
```

And create the `AddSkillRequest` schema in `d:\Projects\p1\backend\app\schemas\skill.py`:
```python
class AddSkillRequest(BaseModel):
    skill_id: uuid.UUID
    confidence: float = Field(ge=0.0, le=1.0)
```

---

## TASK 6 (BONUS): Faculty Dashboard + Curriculum Map

> Do this only AFTER Tasks 1-5 are complete.

### Files:
- `d:\Projects\p1\frontend\src\pages\faculty\Dashboard.jsx`
- `d:\Projects\p1\frontend\src\pages\faculty\CurriculumMap.jsx`

### Problem:
Both pages use 100% hardcoded mock data: `DEPT_KPIS`, `SKILL_RADAR`, `COVERAGE_DONUT`, `AT_RISK`, `SUBJECTS_BY_SEM`.

### What to do:
1. Replace mock data in Faculty Dashboard with calls to `analyticsApi.getDepartmentOverview(deptCode)`
2. Replace mock data in CurriculumMap with calls to `curriculumApi.getSubjects(dept, semester)`
3. The "Apply All Suggestions" button in CurriculumMap should call `curriculumApi.suggestSkillMappings()`
4. The "View All At-Risk Students" button should navigate to a filtered student list

### Backend APIs available:
- `GET /api/v1/analytics/curriculum-gaps/{dept_code}` — returns gap analysis per subject
- `GET /api/v1/curriculum/subjects?dept=CS&semester=7` — returns subjects with skill mappings

---

## ✅ Checklist — What "Done" Looks Like
- [ ] Profile page loads real data from backend (no MOCK_ constants remain)
- [ ] Profile edit form saves to database and UI updates
- [ ] Resume upload sends file to backend and triggers NLP parse
- [ ] Resume parse status is polled and skills refresh after parsing
- [ ] Consent toggles persist to database
- [ ] Add Skill flow works (search → select → save)
- [ ] Loading spinners shown while API calls are in progress
- [ ] Error messages shown when API calls fail
- [ ] Empty states shown when no data exists (e.g., "No skills added yet")
