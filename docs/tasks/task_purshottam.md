# 🧑‍💻 Purshottam's Task Sheet (Sprint 2) — Applicant Stage Workflow, Offer Letter Management & Drive Broadcasts

> **Role:** Placement Operations & Applicant Pipeline Lead.
> **Priority:** 🟠 P1 (Core Placement Operations — Day-to-Day TPO Workflow)
> **Reference Standard:** Superset Placement Management, HirePro Applicant Tracking, CoCubes Drive Operations

---

## 📋 Industrial Context & The Core Problem

Placement Officers on campus do not just look at numbers — they manage real hiring rounds:
1. **Applicants Cannot Be Advanced Through Rounds:** Currently, when students apply, their status stays stuck at `"applied"`. TPOs have no interactive screen to mark an applicant as *"Shortlisted for OA"*, *"Cleared Tech Round 1"*, *"Scheduled for HR"*, or *"Rejected"*.
2. **Offer Letter & Salary Verification is Missing:** When a company selects candidates, TPOs need to record the formal offer: designation, final offered CTC (Fixed + Variable), joining date, and offer letter document. This is what feeds institutional placement statistics.
3. **Campus Placement Broadcasts / Announcements:** When an interview schedule changes, or dress code/venue details are announced, TPOs need to post drive-specific broadcast announcements visible to registered students.

---

## TASK 1: Build the Interactive Drive Applicant Reviewer & Stage Transition Workflow

### Files to touch
- Backend: `backend/app/api/v1/drives.py`, `backend/app/services/drive_service.py`
- Frontend: `frontend/src/pages/tpo/Drives.jsx` (or new dedicated modal/drawer: `DriveApplicantReviewer.jsx`)

### What you need to do
1. **Add Backend Endpoint for Stage Updates:**
   `PATCH /api/v1/drives/{drive_id}/applications/{application_id}`
   Payload:
   ```json
   {
     "status": "shortlisted", // "applied", "shortlisted", "in_progress", "selected", "rejected"
     "current_stage": "Technical Interview 1",
     "stage_status": "passed", // "scheduled", "passed", "failed"
     "feedback": "Strong problem solving in graphs, weak on SQL indexing.",
     "scheduled_at": "2026-09-25T14:30:00"
   }
   ```
2. **Build Applicant Reviewer UI:**
   On each Drive card in `tpo/Drives.jsx`, add **"📋 Review Applicants"**:
   - Opens a full-width drawer or dedicated modal listing all registered applicants.
   - Shows Roll Number, Name, CGPA, Branch, and Current Stage.
   - Each applicant has quick action buttons:
     - ⏩ **Advance Stage** (dropdown: *OA, Tech Round 1, Tech Round 2, HR, Final Selection*)
     - 📅 **Schedule Interview** (date/time picker + virtual meeting link input)
     - ❌ **Reject / Drop** (with optional internal notes)
   - When advanced, the student's `PlacementDrives.jsx` (My Applications tab) immediately reflects the updated stage and interview schedule!

---

## TASK 2: Offer Letter Recording & CTC Verification

### What you need to do
1. **When an applicant's status is changed to `"selected"`:**
   Prompt the TPO with an **"Record Official Offer"** modal:
   - Final Offered CTC (₹ LPA)
   - Fixed Component vs Variable Component
   - Job Designation (e.g. *"Associate Software Engineer"*)
   - Joining Date / Tentative Date
   - Offer Letter Reference Number
2. **Database Persistence:**
   - Save offer details into `Application` record.
   - Automatically update student's profile status to `"placed"`.
   - Update institutional placement KPI cards (Average CTC, Median CTC, Percentage Placed) in real-time.

---

## TASK 3: Real-Time Drive Announcements & Broadcasts

### What you need to do
1. **Backend Model & API:**
   Add `DriveAnnouncement` (`id`, `drive_id`, `author_id`, `title`, `message`, `urgency`, `created_at`).
   - `POST /api/v1/drives/{drive_id}/announcements` (TPO post)
   - `GET /api/v1/drives/{drive_id}/announcements` (Student view)
2. **UI Integration:**
   - On `tpo/Drives.jsx`: **"+ Post Drive Announcement"** (e.g., *"Interview venue shifted to CS Seminar Hall 2, be seated by 9:30 AM"*).
   - On student `PlacementDrives.jsx`: Registered drives show a prominent 📢 **Announcements Notice Banner** with timestamps.

---

## ✅ Checklist — What "Done" Looks Like
- [ ] TPO can open an applicant review drawer and advance students through interview rounds
- [ ] Scheduling an interview immediately updates the student's pipeline timeline with date & link
- [ ] TPO can record official job offers with CTC breakdowns, automatically marking students as placed
- [ ] TPO can post drive announcements that display immediately to all registered students
