# 🧑‍💻 Deep's Final Task Sheet — Generative AI Career Services: Gemini Copilot V3, Mock Interview Simulator V2, Smart Assessments & BoS Modernization

> **Role:** Generative AI, Realtime & Curriculum Intelligence Systems Engineer  
> **Priority:** 🔴 P0 — Core Interactive AI Services  
> **Reference Standard:** Google Gemini 1.5 Pro, HireVue AI Interviewer, Coursera Guided Assessments, Blackboard Curriculum AI  

---

## 📋 Industrial Context — Why This Final Submission Matters

Modern universities face two major challenges in placement readiness:
1. **Lack of Personalized 1-on-1 Guidance:** Career guidance counselors cannot conduct individual mock interviews or write personalized career roadmaps for 1,000+ graduating students.
2. **Academic Curriculum Lag:** University curriculums often lag 3–5 years behind industry demand, and Board of Studies (BoS) committees lack automated tools to analyze industry job postings and modernize subject syllabi.

In CCIP, you built the intelligent interactive layer:
- **AI Career Copilot V3:** A context-aware conversational assistant streaming real-time tokens via Server-Sent Events (SSE).
- **Mock Interview Simulator V2:** A multi-turn AI interviewer that evaluates answers across technical accuracy, communication clarity, and confidence.
- **Smart Adaptive Quiz Engine:** Anti-leakage question delivery with automated grading and skill confidence updates.
- **BoS Curriculum Modernization Engine:** An AI engine that reads subject syllabus text, compares it against industry skill demand, and drafts formal Board of Studies proposals.

---

## TASK 1: Context-Aware AI Career Copilot V3

### Token-Streaming Endpoint (`POST /copilot/chat/stream`)
In `backend/app/api/v1/copilot.py` and `backend/app/services/gemini_service.py`:
- Connect to Google Gemini 1.5 API using Server-Sent Events (`text/event-stream`).
- **Dynamic Context Injection:** Automatically inject student context into the system prompt:
  ```
  You are an expert AI Career Copilot at CCIP.
  Candidate Context:
  - Name: {student.first_name} {student.last_name}
  - Department: {student.department.name} | Semester: {student.current_semester}
  - CGPA: {student.cgpa}
  - Verified Skills: {verified_skills_list}
  - Target Role: {student.target_role or "Software Engineer"}
  - Current Readiness Score: {student.readiness_score}%
  - Eligible Upcoming Placement Drives: {drives_list}
  ```
- **Local Fallback Mode:** If `GEMINI_API_KEY` is not configured or network requests fail, execute deterministic local career guidance generator that streams realistic advice without throwing 500 errors.

### Frontend UI (`frontend/src/pages/student/Copilot.jsx`)
- Full conversational interface with smooth auto-scroll, markdown rendering, and code syntax highlighting.
- Quick-prompt action pills: "Analyze my resume for Google SDE", "Generate 6-week roadmap for DevOps", "What questions will TCS ask?".
- Sidebar storing previous conversation history sessions (`copilot_conversations` table).

---

## TASK 2: Mock Interview Simulator V2

### Multi-Turn State Machine
In `backend/app/api/v1/mock_interviews.py` and `backend/app/models/interview_session.py`:
- Defined state transitions: `setup` -> `intro` -> `technical` -> `behavioral` -> `completed`.
- Track conversation transcript in `JSONB`:
  ```json
  [
    {"role": "interviewer", "content": "Welcome! Tell me about a time you optimized a slow SQL query."},
    {"role": "candidate", "content": "In my project, I added B-Tree indexes on foreign keys..."},
    {"analysis": {"technical_depth": 8, "filler_words": 1, "clarity": 9}}
  ]
  ```

### Performance Rubric Generator (`POST /mock-interviews/{session_id}/complete`)
- Computes comprehensive scorecard across 4 metrics:
  1. Technical Correctness (0–100%)
  2. Communication Clarity (0–100%)
  3. Filler-Word Count ("um", "uh", "like")
  4. Response Pace & Depth
- Generates post-interview transcript review with actionable bullet-point recommendations.

### Frontend UI (`frontend/src/pages/student/MockInterview.jsx`)
- Interactive interview terminal with live recording timer, candidate audio waveform visualizer, and instant question progression.
- Post-interview report card download with shareable performance badge.

---

## TASK 3: Anti-Leakage Adaptive Assessment & Smart Quiz Engine

### Anti-Leakage Delivery Protocol
In `backend/app/api/v1/assessments.py` and `backend/app/services/assessment_engine.py`:
- **Security Rule:** Correct answers (`is_correct`, option IDs) MUST NEVER be sent to the client browser during test taking.
- Verification in `backend/tests/test_assessments.py::test_answer_leakage_prevention`:
  ```python
  response = await client.get(f"/api/v1/assessments/{session_id}/questions")
  data = response.json()
  for q in data["questions"]:
      for opt in q["options"]:
          assert "is_correct" not in opt
  ```

### Adaptive Question Selection (`POST /assessments/start`)
- Select questions dynamically from `questions` table based on target skill and difficulty (Beginner, Intermediate, Advanced).
- Automatic timer countdown with tab-switching detection.
- **Skill Confidence Update:** When a student scores $\ge 70\%$, automatically increase their verified skill confidence in `student_skills` and record assessment audit trail.

---

## TASK 4: BoS Curriculum Modernization Engine

### Syllabus Text Parsing & Gap Detection
In `backend/app/api/v1/curriculum.py`:
- Fetch subject syllabus from `subjects` table.
- Extract embedded technical competencies using rapidfuzz taxonomy matcher.
- Compare subject syllabus against real-time industry skill demand for the active academic year.

### AI Proposal Generator (`POST /curriculum/subjects/{subject_id}/generate-proposal`)
- Generates structured Board of Studies (BoS) proposal:
  1. Title of proposed curriculum revision.
  2. Detailed rationale explaining gap between current syllabus and employer demands.
  3. Proposed new modules (e.g., "Module 5: Docker Containerization & Microservices Architecture").
  4. Course Learning Outcomes (CLOs) mapped to NBA/NAAC standards.
  5. Recommended textbooks and online lab resources.
- Stored in `curriculum_proposals` table.

### Faculty Proposal Manager (`frontend/src/pages/faculty/ProposalManager.jsx`)
- Review submitted BoS proposals, edit proposed module text, and manage status workflow (`Draft` -> `Submitted to BoS` -> `Approved`).
- Accessible directly from `FacultyLayout.jsx` sidebar navigation.

---

## TASK 5: Real-time Notification Engine & WebSocket Heartbeat

### WebSocket Service (`backend/app/api/v1/websocket.py`)
- WebSocket endpoint `/ws/{user_id}` supporting connection keep-alive pings.
- Event broadcasting: Instantly notify students when new placement drives are announced or when application status changes (e.g. "You have been shortlisted for Amazon Coding Round").
- Notification Bell component in `frontend/src/components/NotificationBell.jsx` with unread count indicator and instant toast popups.

---

## 🛠️ Verification & Test Runbook

```powershell
# 1. Run assessment, curriculum, and notification tests
cd d:\Projects\p1\backend
.\.venv\Scripts\pytest.exe tests/test_assessments.py tests/test_curriculum.py tests/test_experiences_and_notifications.py -v

# 2. Specifically verify anti-leakage security test
.\.venv\Scripts\pytest.exe tests/test_assessments.py -k "test_answer_leakage_prevention" -v

# 3. Verify frontend build
cd d:\Projects\p1\frontend
npm run build
```

---

## 🎓 Viva Defense Talking Points (For External Examiners)

1. **How Do You Prevent Cheating in Online Assessments?**  
   *"We use an anti-leakage question delivery pipeline. The question schema sent to the frontend client contains only the question text and option labels. Correct answer keys remain strictly on the backend server, and grading is performed asynchronously upon submission."*
2. **What is Server-Sent Events (SSE) and Why Not Plain REST for AI Chat?**  
   *"Generative LLMs take several seconds to generate complete responses. Plain HTTP REST forces the user to wait with a frozen screen. SSE streams tokens incrementally as they are synthesized, delivering a responsive user experience identical to ChatGPT."*
3. **How Does the BoS Curriculum Modernization Tool Impact Accreditation?**  
   *"NBA and NAAC accreditation criteria heavily emphasize Curriculum Relevance and Continuous Improvement. Our tool provides empirical proof that university course coordinators analyze live recruitment data and revise syllabi accordingly."*
