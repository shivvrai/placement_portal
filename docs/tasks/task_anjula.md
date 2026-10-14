# 🧑‍💻 Placement Operations Task Sheet (Sprint 2) — Drive Round Scheduling, Interview Experiences Hub & Notification Bell

> **Role:** Placement Logistics & Campus Community Lead.
> **Priority:** 🟠 P1 (Core Student Placement Experience & Campus Logistics)
> **Reference Standard:** LeetCode Interview Experiences, Glassdoor College Hub, Superset Campus Notification Bell

---

## 📋 Industrial Context & The Core Problem

In university placement ecosystems, communication and institutional knowledge sharing are critical:
1. **No Drive Detail Page:** Clicking a drive card doesn't open a rich detail page showing company overview, round-by-round timeline, venue/online link, and eligible candidate attendance rosters.
2. **Institutional Interview Experience Knowledge Base is Missing:** When seniors complete interview rounds at Amazon or Google, their interview questions, coding problems, and tips are lost on WhatsApp groups. A real college portal maintains a searchable **Interview Experience Hub** for juniors.
3. **Real-time In-App Notification Bell:** Students miss critical application deadlines or interview time updates because notifications are only on specific pages. A top-bar notification center is standard across all commercial portals.

---

## TASK 1: Full Drive Detail Page with Multi-Round Logistics

### Files to touch
- Frontend: `frontend/src/pages/student/DriveDetail.jsx` (and TPO equivalent or unified view)
- Router: `frontend/src/router/AppRouter.jsx`

### What you need to do
1. **Dedicated Drive Route:** `/student/drives/:id` and `/tpo/drives/:id`.
2. **Comprehensive Drive View:**
   - **Company Profile Header:** Logo, Industry, HQ Location, About Company, Website.
   - **Package & Role Specifics:** Fixed CTC, Variable, Bond/Probation Terms, Roles offered.
   - **Round-by-Round Timeline:**
     - Round 1: Online Assessment (Date, Platform link, Duration)
     - Round 2: Technical Interview (Venue / Google Meet link, Required documents)
     - Round 3: HR / Leadership Discussion
   - **Eligibility Status Box:** Clear criteria breakdown (CGPA, Backlogs, Branches) with direct "Apply Now" CTA.
   - **TPO Attendance Sheet Download:** TPO can download the registered students roster as a PDF/CSV attendance sheet.

---

## TASK 2: Student Company Interview Experience & Question Bank Hub

### Files to touch
- Backend: `backend/app/api/v1/experiences.py`, `backend/app/models/system.py`
- Frontend: `frontend/src/pages/student/InterviewExperiences.jsx`

### What you need to do
1. **Database Model & API:**
   Table `InterviewExperience`:
   - `id`, `student_id`, `company_name`, `role`, `placement_drive_id`, `difficulty` (*Easy, Medium, Hard*), `verdict` (*Selected, Rejected, In Progress*), `overall_experience` (text), `questions_asked` (list[str]), `tips_for_juniors` (text), `created_at`.
   - Endpoints:
     - `GET /api/v1/experiences` (searchable by company, role, difficulty)
     - `POST /api/v1/experiences` (students who applied can share their experience)
2. **Frontend Knowledge Hub:**
   - Add to student navigation sidebar: **"💡 Interview Experiences"**.
   - Search bar by company (e.g. *Amazon, TCS, Infosys*).
   - Expandable cards showing real student tips, coding problems asked in Round 1/2, and technical interview questions.

---

## TASK 3: Global In-App Notification Center (Bell Dropdown)

### Files to touch
- Frontend: `frontend/src/components/AppHeader.jsx` (or topbar in layouts), `frontend/src/context/AuthContext.jsx`
- Backend: `backend/app/api/v1/notifications.py`

### What you need to do
1. **Notification System:**
   - `GET /api/v1/notifications/mine` — returns real-time alerts:
     - *"Your application for Amazon Data Engineer has been Shortlisted!"*
     - *"Google SWE Drive registration closes in 24 hours."*
     - *"New drive posted: Deloitte Technology Analyst."*
   - `PATCH /api/v1/notifications/{id}/read`
2. **Frontend UI:**
   - Interactive notification bell icon 🔔 in the top header with an unread badge counter.
   - Clicking opens a sleek floating dropdown list with time ago (e.g. *"2 hours ago"*).
   - Clicking any notification navigates directly to the relevant drive or application.

---

## ✅ Checklist — What "Done" Looks Like
- [ ] Clicking any drive opens a rich detail view with multi-round interview logistics and guidelines
- [ ] Students can browse and submit real company interview questions and experiences
- [ ] Global notification bell displays live application status alerts and drive countdowns
