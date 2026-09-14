# 🧑‍💻 Sakshi's Task Sheet (Sprint 2) — Verified Student Portfolio CRUD, Resume Extraction Confirmation & Shareable Profile

> **Role:** Student Profile & Verified Credentials Lead.
> **Priority:** 🟠 P1 (Core Student Portfolio & Hiring Showcase)
> **Reference Standard:** Handshake Student Portfolio, LinkedIn Verified Student Credentials, Superset Resume Parser

---

## 📋 Industrial Context & The Core Problem

In enterprise university placement software, student profiles are not static cards; they are verifiable digital portfolios evaluated by Fortune 500 recruiters:
1. **Projects, Certifications & Experience are Read-Only Shells:** The database defines `Project`, `Certification`, and `WorkExperience` tables in `backend/app/models/portfolio.py`, but the frontend `Profile.jsx` does not have interactive forms to create, edit, or delete student projects (with live links, repo URLs, tech tags) or upload certificate proof.
2. **Resume Parsing Has No Confirmation Workflow:** Currently, uploading a resume parses skills, but students cannot review, confirm, or reject individual extracted skills before they are permanently stamped onto their verified profile.
3. **Public Verified Portfolio Share Link:** Recruiters clicking candidate links from campus drives need a read-only, professional web view (or QR code) of the student's verified skills, academic history, and GitHub projects.

---

## TASK 1: Full Interactive CRUD for Projects, Certifications & Experience

### Files to touch
- Backend API: `backend/app/api/v1/students.py`
- Frontend UI: `frontend/src/pages/student/Profile.jsx`

### What you need to do
1. **Add Endpoints in `backend/app/api/v1/students.py`:**
   - `POST /api/v1/students/me/projects` (title, description, tech_stack: list[str], github_url, live_url, start_date, end_date)
   - `DELETE /api/v1/students/me/projects/{id}`
   - `POST /api/v1/students/me/certifications` (name, issuing_organization, issue_date, expiration_date, credential_id, credential_url)
   - `DELETE /api/v1/students/me/certifications/{id}`
   - `POST /api/v1/students/me/experience` (company_name, role, location, start_date, end_date, is_current, description)
   - `DELETE /api/v1/students/me/experience/{id}`

2. **UI Modals in `Profile.jsx`:**
   - Under the "Overview" and "Academic" tabs, build clean modals for **"+ Add Project"**, **"+ Add Certification"**, and **"+ Add Internship/Work Experience"**.
   - Include tech stack pills input (e.g., typing "FastAPI, React" creates interactive chips).
   - Display GitHub repo and demo links with clickable badges.
   - Support one-click delete with confirmation.

---

## TASK 2: Two-Step Resume Skill Confirmation Modal

### The Problem
When a student uploads a resume (`POST /api/v1/resume/upload`), the NLP engine extracts skills. But if an extraction is a false positive (e.g., extracting "Java" from "JavaScript"), the student has no chance to deselect it.

### What you need to do
1. When resume upload completes, open an interactive **"Review Extracted Skills"** modal:
   - Lists all extracted skills grouped into:
     - 🟢 *High Confidence Match* ($\ge 85\%$)
     - 🟡 *Probable Match* ($60\% - 84\%$)
   - Each skill has a toggle checkbox.
   - Allows the student to uncheck any inaccurate extraction or add an unextracted skill.
2. When the student clicks **"Confirm & Sync to Profile"**, make a bulk API call:
   - `POST /api/v1/students/me/skills/bulk` passing the confirmed list.
   - Updates student skills with source tag: `"resume_verified"`.

---

## TASK 3: Shareable Public Verified Student Portfolio View

### What you need to do
1. **Public Route:** In `frontend/src/router/AppRouter.jsx`, add an unauthenticated public route:
   `/portfolio/:studentId` (or `/verify/student/:rollNumber`).
2. **Component:** Create `frontend/src/pages/student/PublicPortfolio.jsx`:
   - Clean, recruiter-focused layout (printable / exportable to PDF).
   - Displays student name, branch, university verified CGPA seal, verified skills radar, listed GitHub projects, and certifications.
   - Includes a "Verified by University Placement Cell" security watermark.
3. **QR Code / Copy Link:** On `Profile.jsx`, add a **"Share Verified Portfolio"** button that copies the public portfolio link to clipboard.

---

## ✅ Checklist — What "Done" Looks Like
- [ ] Student can add, view, and delete Projects with GitHub & Demo URLs
- [ ] Student can add and delete Professional Certifications & Internships
- [ ] Resume upload displays an interactive skill review modal before persisting skills to DB
- [ ] Anyone with a public portfolio link can inspect the student's verified profile
