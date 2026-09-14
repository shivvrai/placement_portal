# 🧑‍💻 Deep's Task Sheet (Sprint 2) — AI Mock Interview Simulator, Curriculum Modernization Engine & Assessment Remediation

> **Role:** Generative AI & Curriculum Intelligence Lead.
> **Priority:** 🟡 P2 (Core Innovation & AI Campus Differentiator)
> **Reference Standard:** Coursera Campus Intelligence, ChatGPT Interview Coach, QS Higher Ed Curriculum Benchmarking

---

## 📋 Industrial Context & The Core Problem

In university curriculum intelligence, academic deans don't just want charts showing skill gaps — they want automated remediation and tools that prepare students for actual technical interviews:
1. **Curriculum Gap Analysis Needs Actionable Modernization Reports:** Currently, faculty can view missing skills on `CurriculumMap.jsx`. But when the Academic Council or Board of Studies (BoS) meets, they need a formal **Curriculum Modernization Proposal** (suggested syllabus updates, laboratory practicals, industry justification).
2. **Copilot is Only a General Q&A Chatbot:** It lacks an interactive **"Mock Technical Interview Mode"** where the AI acts as a hiring manager (asking 3-5 technical questions based on the student's target role, evaluating their answers, and rating their readiness).
3. **Quizzes Don't Bridge Back to Learning:** When a student scores poorly on an assessment in `AssessmentsList.jsx`, the system should automatically generate focused remediation tasks and inject them into their `Roadmap.jsx`.

---

## TASK 1: Board of Studies (BoS) AI Curriculum Modernization Generator

### Files to touch
- Backend: `backend/app/api/v1/curriculum.py`, `backend/app/services/gemini_client.py`
- Frontend: `frontend/src/pages/faculty/CurriculumMap.jsx`

### What you need to do
1. **Backend Generator Endpoint:**
   `POST /api/v1/curriculum/subjects/{subject_id}/generate-proposal`
   - Uses Gemini (or offline fallback template) with a prompt incorporating:
     - Current subject syllabus & credits
     - Uncovered industry skills (e.g. *Docker, Kafka, FastAPI, Kubernetes*)
     - Employer hiring demand statistics from placement drives
   - Generates a structured **Syllabus Modernization Proposal**:
     ```json
     {
       "subject_name": "Cloud Computing",
       "revision_rationale": "Over 78% of hiring companies require containerization and IaC...",
       "proposed_modules": [
         { "module_title": "Module 4: Container Orchestration with Kubernetes", "hours": 8, "topics": ["Pods, Deployments, Services", "ConfigMaps & Secrets", "Ingress controllers"] },
         { "module_title": "Module 5: Infrastructure as Code with Terraform", "hours": 6, "topics": ["HCL syntax", "Terraform State", "AWS Provider Setup"] }
       ],
       "recommended_lab_experiments": [
         "Deploy a multi-tier microservices application on a local Minikube cluster.",
         "Provision an AWS VPC and EC2 instance automatically using Terraform scripts."
       ],
       "industry_alignment_score": "+35% improvement in graduate employability"
     }
     ```
2. **Frontend UI in `CurriculumMap.jsx`:**
   - Add a prominent **"📄 Generate Board of Studies Modernization Dossier"** button on each subject card.
   - Displays the formatted syllabus proposal with a **"Download Formal BoS PDF/Document"** export option for faculty meetings.

---

## TASK 2: Interactive AI Mock Technical Interview Simulator

### Files to touch
- Backend: `backend/app/services/copilot_service.py`, `backend/app/api/v1/copilot.py`
- Frontend: `frontend/src/pages/student/Copilot.jsx`

### What you need to do
1. **Mock Interview Mode Session:**
   - Add a tab or toggle in `Copilot.jsx`: **"🎙️ Start Mock Interview"**.
   - Student selects Target Role (e.g. *Frontend Developer, Backend Engineer, Data Analyst*) and Difficulty (*Intern, Junior SDE, Mid-Level*).
2. **Conversation State Machine:**
   - AI generates Question 1 (e.g. *"Can you explain the difference between processes and threads, and how the OS handles context switching?"*).
   - Student types their response.
   - AI evaluates the response, gives constructive feedback (Strengths, Missing Concepts), assigns a rating (1-10), and asks the next question.
   - After 3-5 rounds, AI generates a **Final Interview Readiness Scorecard** with specific improvement tips.

---

## TASK 3: Automated Quiz Remediation to Career Roadmap Injection

### What you need to do
1. When a student completes an assessment in `AssessmentTake.jsx`:
   - If score is $< 70\%$, detect the weak sub-topics.
   - Automatically call `POST /api/v1/roadmap/me/tasks` to append a **"Remedial Practice"** milestone to their active Roadmap.
2. In `frontend/src/pages/student/Roadmap.jsx`:
   - Highlight auto-injected remedial tasks with a badge: `🎯 Quiz Remediation (Score: 50%)`.
   - Provide direct learning resource links (documentation, tutorials, coding challenges) to master the topic.

---

## ✅ Checklist — What "Done" Looks Like
- [ ] Faculty can generate and export a formal Board of Studies syllabus modernization dossier with modules & lab practicals
- [ ] Students can launch an interactive AI Mock Interview in Copilot with question-by-question scoring and feedback
- [ ] Scoring low on an assessment automatically creates remediation learning tasks in the student's Career Roadmap
