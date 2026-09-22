# 🧑‍💻 Yash's Task Sheet (Sprint 3) — AI-Powered Learning Infrastructure: Mock Interview Engine V2, BoS Curriculum Intelligence, Adaptive Quiz System & AI Copilot V3

> **Role:** Lead Architect & AI Learning Systems Engineer
> **Priority:** 🟠 P1 — Core AI differentiation
> **Reference Standard:** Pramp Mock Interviews, Karat AI Interviewer, Coursera Adaptive Learning, Blackboard Learn AI

---

## 📋 Industrial Context — Why This Sprint Matters

The AI Career Copilot (Gemini chat) was Sprint 1. The BoS curriculum proposal was Sprint 2. But both features currently work in isolation — the copilot doesn't know what the student's assessment scores look like, and the BoS report doesn't pull from real skill gap data. This sprint makes the entire AI pipeline context-aware and adds two brand-new industrial-grade AI features:

1. **Mock Interview V2** — from basic Q&A to a full simulated interview with opening greeting, follow-up questions, filler-word detection, pace analysis, and structured performance rubric. Think Pramp meets HireVue.
2. **BoS Curriculum Intelligence V2** — faculty can now run a gap analysis against real-time industry skill demand and generate a detailed curriculum proposal with outcome mapping, suggested resources, and expected impact on placement rates.
3. **AI Copilot V3** — fully context-aware. The copilot now knows the student's placement status, skill badges earned, assessment scores, active drives they're eligible for, and peer benchmark percentile.

---

## TASK 1: Mock Interview Engine V2

### Architecture

The mock interview is a multi-turn Gemini conversation with structured state management. Unlike the copilot (general chat), the mock interview has a defined lifecycle:

```
[START] → Welcome + Role Briefing
    ↓
[ROUND 1] → Introduction round (Tell me about yourself)
    ↓
[ROUND 2] → Technical questions (from skill taxonomy, adaptive to answers)
    ↓
[ROUND 3] → Behavioral / HR questions
    ↓
[END] → Comprehensive rubric-based feedback report
```

### Backend

#### CREATE: `backend/app/models/interview_session.py`

```python
class MockInterviewSession(Base):
    __tablename__ = "mock_interview_sessions"
    id: UUID PK
    student_id: UUID FK→students.id
    role_target: str          # "Software Engineer" | "Data Analyst" | "ML Engineer" | "Full Stack Developer"
    company_style: str        # "Product" | "Service" | "Startup" | "MNC"
    difficulty: str           # "campus" | "fresher" | "experienced"
    status: str               # "setup" | "intro" | "technical" | "behavioral" | "completed"
    transcript: JSONB         # [{role:"interviewer"|"candidate", content:str, timestamp:str, analysis:dict}]
    current_round: int default=0
    questions_asked: ARRAY(String)
    performance_scores: JSONB   # {communication:int, technical:int, confidence:int, clarity:int}
    final_report: JSONB | None  # populated when status=completed
    duration_seconds: int | None
    word_count: int | None
    filler_word_count: int | None   # "um", "uh", "like", "you know" count
    started_at: datetime
    completed_at: datetime | None
```

#### CREATE: `backend/app/services/mock_interview_service.py`

```python
class MockInterviewService:
    SYSTEM_PROMPT_TEMPLATE = """
    You are a senior interviewer at a {company_style} company conducting a campus placement interview
    for a {role_target} position. The candidate is a final-year engineering student.
    
    Rules:
    1. Stay strictly in character as an interviewer — never break character.
    2. Ask one question at a time. Wait for the candidate's response before asking the next.
    3. Ask follow-up questions based on the candidate's answers (adaptive).
    4. After the introduction round (2–3 questions), transition to technical questions.
    5. After technical (3–4 questions), do behavioral/HR round (2 questions).
    6. When you have enough signal (8+ exchanges), say "Thank you, that concludes our interview."
    7. Do NOT give feedback during the interview — save all feedback for the final report.
    
    Start with a warm professional greeting and introduce yourself.
    """

    async def start_session(self, student_id, role_target, company_style, difficulty) -> MockInterviewSession:
        """Creates session, generates opening greeting via Gemini"""

    async def send_message(self, session_id: UUID, student_message: str, student_id: UUID) -> dict:
        """
        1. Validate session belongs to student
        2. Append candidate message to transcript
        3. Analyze candidate message:
           - Count filler words ("um", "uh", "like", "basically", "you know", "kind of")
           - Estimate word count
           - Basic sentiment (positive/negative/neutral)
        4. Build full conversation history as Gemini messages
        5. Call Gemini with the full context → get interviewer response
        6. Detect if Gemini signals interview end ("concludes our interview" in response)
        7. If ended → trigger generate_final_report()
        8. Append interviewer response to transcript
        9. Return: {interviewer_message, session_status, exchange_count}
        """

    async def generate_final_report(self, session_id: UUID) -> dict:
        """
        1. Build a report-generation prompt:
           "Review this interview transcript and score the candidate on:
            - Technical Knowledge (0-10): did they answer technical questions correctly?
            - Communication Clarity (0-10): were answers structured? STAR method?
            - Confidence (0-10): tone, response length, self-doubt indicators?
            - Relevance (0-10): did they answer what was asked?
            Give specific quotes from their answers as evidence.
            Identify top 2 strengths and top 3 areas for improvement.
            Provide a final verdict: Strong Hire / Hire / Borderline / No Hire
            Format as JSON."
        
        2. Call Gemini → parse JSON response
        3. Compute filler_word_rate = filler_count / total_words
        4. Store in session.final_report + session.performance_scores
        5. Trigger roadmap update: if weak in technical → add prep tasks
        6. Return complete report dict
        """

    async def get_session(self, session_id: UUID, student_id: UUID) -> MockInterviewSession: ...
    async def list_sessions(self, student_id: UUID) -> list[MockInterviewSession]: ...
```

#### MODIFY: `backend/app/api/v1/` — Create `mock_interviews.py`

```
POST /mock-interviews/start                   → start new session (body: role_target, company_style, difficulty)
POST /mock-interviews/{session_id}/message    → send candidate message, receive interviewer response
GET  /mock-interviews/{session_id}            → session detail + transcript
GET  /mock-interviews/{session_id}/report     → final report (404 if not completed)
GET  /mock-interviews/my                      → student's past sessions (paginated)
GET  /mock-interviews/my/stats                → {total_sessions, avg_technical_score, avg_communication, improvement_trend}
```

### Frontend

#### CREATE: `frontend/src/pages/student/MockInterview.jsx`

Route: `/student/mock-interview`

**Setup Screen:**

- "🎤 AI Mock Interview" heading with brief description
- Role selector: dropdown of 8 roles (SWE, Data Analyst, ML Engineer, Full Stack, DevOps, Business Analyst, Product Manager, Data Engineer)
- Company Style: radio buttons (Product Company / IT Services / Startup / MNC)
- Difficulty: Campus Fresher / Entry Level / Internship
- "My Past Sessions" card row (last 3, with scores, link to full history)
- Big "Start Interview →" button

**Active Interview Screen:**

This must feel like a real interview, not a chat:

- **Top bar:** Role badge, company style, timer (counting up), exchange count "Question 7/~10"
- **"Interviewer" section (top 60% of screen):**
  - Avatar: professional headshot placeholder (generated based on role — "Senior Engineer at Product Co.")
  - Name: "Alex Chen, Senior Software Engineer"
  - Current interviewer message in a speech-bubble style card
  - Thinking animation (3 dots) while Gemini is generating
- **"You" section (bottom 40%):**
  - Large textarea: "Your answer..." placeholder
  - Character counter
  - "Send" button + Shift+Enter shortcut
  - "Filler words this session: 3" live counter (counts as user types)
  - "Take your time — there's no rush" encouragement label

**Interview Completion → Report Screen:**

Full-page report:

- Header: "Interview Complete — {role} at {company_style} Company"
- **Verdict badge:** "Strong Hire 🏆" / "Hire ✅" / "Borderline ⚠" / "No Hire ❌"
- **Scorecard (4 gauges):**
  - Technical Knowledge: X/10
  - Communication: X/10
  - Confidence: X/10
  - Relevance: X/10
- **Stats row:** Duration: 18 min | Words spoken: 1,247 | Filler words: 12 (0.9%)
- **Strengths section:** 2 bullet points with quotes from transcript as evidence
- **Improvement Areas:** 3 bullet points with specific actionable advice
- **Transcript viewer:** collapsible full transcript with alternating interviewer/candidate styling
- **"Practice These Topics" section:** Roadmap tasks auto-created from weak areas
- **Action buttons:** "Try Again" | "New Role" | "Share Report" (generates image card) | "Add to Portfolio"

#### CREATE: `frontend/src/pages/student/MockInterviewHistory.jsx`

Route: `/student/mock-interview/history`

- Table/card list of past sessions
- Each: role, company style, verdict badge, 4 score pills, date, "View Report" button
- Progress chart: Communication and Technical scores over time (line chart)

---

## TASK 2: BoS Curriculum Intelligence V2 (Faculty Portal)

### Backend

#### MODIFY: `backend/app/services/curriculum_proposal_service.py`

Completely enhance the existing service:

```python
class CurriculumProposalService:
    async def run_full_gap_analysis(self, department_code: str, db) -> dict:
        """
        Full pipeline:
        1. Load all subjects in this department from Subjects table
        2. Load their mapped skills from CurriculumSkill table
        3. Load all active PlacementDrives targeting this department
        4. Load JobSkill table for this dept's common roles
        5. Aggregate: what skills are REQUIRED by industry vs what subjects TEACH
        6. Compute:
           - coverage_pct: % of industry-required skills covered in curriculum
           - gap_skills: skills required by industry, not in any subject
           - redundant_topics: subjects with low industry demand (skills not in any drive)
           - high_demand_uncovered: skills in 3+ drives, not in curriculum
        7. Return structured gap analysis dict
        """

    async def generate_full_proposal(self, department_code: str, academic_year: str, db) -> dict:
        """
        1. Run run_full_gap_analysis()
        2. Build Gemini prompt with full gap data
        3. Prompt instructs Gemini to:
           a) Suggest 3-5 new elective subjects to add, each with:
              - Subject name, code suggestion, credits, semester
              - Topics list (10+ topics)
              - Learning outcomes (NBA format: CO1, CO2, CO3...)
              - Textbooks (2–3 real standard textbooks)
              - Mapped skills (5+ skills this subject covers)
              - Industry demand score (based on gap data)
           b) Suggest modifications to 2–3 existing subjects
           c) Suggest 1–2 subjects to phase out (low relevance)
           d) Expected impact: "Adding these subjects would increase placement coverage from 67% to 84%"
        4. Parse Gemini JSON response
        5. Store in DB (ProposalRecord table)
        6. Return complete proposal
        """

    async def export_proposal_to_word(self, proposal_id: UUID) -> bytes:
        """
        Generate a formatted .docx using python-docx:
        - University letterhead placeholder
        - BoS proposal sections (as per university template)
        - Tables for subject details
        - NBA outcome mapping table
        Return docx bytes for download
        """

    async def submit_proposal_for_review(self, proposal_id: UUID, faculty_id: UUID) -> None:
        """Mark proposal as submitted, notify HOD users via notification service"""
```

#### CREATE DB MODEL: `backend/app/models/curriculum_proposal.py`

```python
class CurriculumProposal(Base):
    __tablename__ = "curriculum_proposals"
    id: UUID PK
    department_code: str
    academic_year: str
    created_by: UUID FK→users.id (faculty)
    status: str default="draft"  # "draft" | "submitted" | "approved" | "rejected"
    gap_analysis: JSONB           # raw gap analysis results
    proposed_subjects: JSONB      # Gemini-generated proposal
    impact_projection: JSONB      # estimated placement coverage improvement
    hod_comments: str | None
    reviewed_by: UUID | None FK→users.id
    reviewed_at: datetime | None
    created_at: datetime
```

#### MODIFY: `backend/app/api/v1/curriculum.py`

```
GET  /curriculum/gap-analysis/{dept}              → run and return gap analysis
POST /curriculum/proposals                         → start new proposal (triggers Gemini)
GET  /curriculum/proposals                         → list all proposals for faculty's dept
GET  /curriculum/proposals/{id}                    → proposal detail
PATCH /curriculum/proposals/{id}/status            → HOD approves/rejects
GET  /curriculum/proposals/{id}/download           → download as .docx
POST /curriculum/proposals/{id}/submit             → faculty submits to HOD
GET  /curriculum/coverage-heatmap/{dept}           → subject × skill demand heatmap data
```

### Frontend: Enhance `frontend/src/pages/faculty/CurriculumMap.jsx`

Current state: basic curriculum mapping.

**Add new sections:**

**Gap Analysis Dashboard:**
- Big "Run Gap Analysis" button → POST /curriculum/gap-analysis/{dept}
- Loading state with Gemini spinner animation
- Results:
  - Coverage meter: "Your curriculum covers 67% of industry-required skills"
  - Gap skills list: skills not in any subject (color-coded by demand intensity)
  - Redundant topics: subjects with very low placement relevance
  - Quick action: "Generate BoS Proposal →"

**BoS Proposal Generator:**
- "Generate Full BoS Curriculum Proposal for AY 2026-27"
- Gemini working animation (realistic — 5–10 second wait)
- Proposal preview:
  - Proposed new subjects (accordion cards, each with full detail)
  - Suggested modifications (diff-style: what changes)
  - Phase-out recommendations
  - Impact projection: before/after coverage gauge
- Actions: "Download .docx" | "Submit to HOD" | "Save as Draft"

**Coverage Heatmap:**
- Matrix: rows=subjects, cols=top 20 industry skills
- Green cell = skill taught in subject, grey = not covered
- Red border = high-demand skill not covered by anything

#### CREATE: `frontend/src/pages/faculty/ProposalManager.jsx`

Route: `/faculty/proposals`

- List of all proposals: department, created_by, status badge, created_at, actions
- Status badges: Draft (grey) / Submitted (blue) / Approved (green) / Rejected (red)
- HOD view: "Review" button → opens proposal with approve/reject + comments

---

## TASK 3: AI Career Copilot V3 — Context-Aware

### Backend

#### MODIFY: `backend/app/services/copilot_service.py`

The copilot currently gets only the student's skill profile. Upgrade to full context injection.

```python
class CopilotContextBuilder:
    async def build_full_context(self, student_id: UUID, db) -> str:
        """
        Assembles a rich context string to prepend to every Gemini conversation:
        
        - Student profile: name, dept, CGPA, semester
        - Verified skill badges (from SkillBadge table)
        - Assessment performance: per-topic avg scores + trend
        - Active placement drives they're eligible for (top 5 by match score)
        - Current applications: company, role, status
        - Peer benchmark: percentile in dept (CGPA, skill count, match score)
        - Career goal: target role, target companies
        - Roadmap progress: X of Y tasks completed
        - Recent interview experience submissions (if any)
        
        Returns a compact context string (max 1500 tokens) for Gemini system prompt
        """

async def build_system_prompt(self, context: str, conversation_type: str) -> str:
    """
    conversation_type: "career_advice" | "interview_prep" | "company_research" | "resume_help"
    Returns role-appropriate system prompt with context injected
    """
```

#### MODIFY: `backend/app/api/v1/copilot.py`

Add conversation types and context:
```
POST /copilot/conversations                        → create conversation (body: type, initial_message)
POST /copilot/conversations/{id}/messages          → send message (uses full context)
GET  /copilot/conversations/{id}/context           → what context is currently injected (debug view for students)
GET  /copilot/suggestions                          → proactive suggestions based on profile (3 action cards)
```

Proactive suggestions:
```python
async def generate_suggestions(student_id) -> list[dict]:
    """
    Based on student's profile, return 3 suggestions like:
    - "You're 78% match for Amazon SDE drive — apply before Nov 1"
    - "Your Docker skill is in 5 active drives — take the Docker assessment to get verified"
    - "67% of CS students have filed 4+ applications — you have 2"
    Returns: [{title, message, action_label, action_link, priority}]
    """
```

### Frontend

#### MODIFY: `frontend/src/pages/student/Copilot.jsx` — Major upgrade

**Conversation Types:**
- Sidebar panel: conversation categories
  - 🎯 Career Advice (default)
  - 🎤 Interview Prep
  - 🏢 Company Research  
  - 📄 Resume Help
- Each type pre-loads a relevant opening from Gemini

**Proactive Suggestions Widget (top of Copilot):**
- 3 action cards below heading (fetched from /copilot/suggestions)
- Each card: title, short message, action button → navigates to relevant page
- Dismissable, re-fetches every 24h
- "Powered by Gemini AI" footer badge

**Context Inspector (collapsible):**
- "ℹ What does the AI know about you?" collapsible section
- Lists injected context items as readable bullets
- "Update Profile" link if context seems outdated

**Message Formatting:**
- Gemini responses with code blocks: render with syntax highlighting
- Numbered lists: render as actual `<ol>` lists
- Bold text: render with `<strong>`
- Skills mentioned in response: auto-link to student's skill page

**Suggested Prompts (empty state):**
- 6 suggestion chips: "Help me prepare for a technical interview", "Which skills should I prioritize?", "Review my resume for ATS", "Which drive should I apply to first?", "Tell me about TCS interview process", "Generate a 30-day study plan"

---

## TASK 4: Smart Quiz & Remediation System V2

### Backend

#### MODIFY: `backend/app/api/v1/assessments.py`

```
POST /assessments/quiz/quick                  → 5-question quick quiz on a topic (for profile gaps)
GET  /assessments/quiz/recommended            → AI-recommended quiz topics based on gap analysis
POST /assessments/quiz/{session_id}/remediate → after failing, generate targeted remediation roadmap tasks
GET  /assessments/performance/trends          → score trends per topic over time
```

#### MODIFY: `backend/app/services/assessment_engine.py`

**Remediation Roadmap Generator:**
```python
async def generate_remediation_plan(self, session_id: UUID, student_id: UUID, db) -> list[RoadmapTask]:
    """
    After a session with score < 60%:
    1. Identify which questions student got wrong
    2. Map wrong questions to sub-topics
    3. Call Gemini: "For a student weak in {sub_topics} of {skill}, generate 5 specific learning tasks
       with resource types (video/article/practice problem) and estimated time"
    4. Create RoadmapTask records for each task
       - source="quiz_remediation"
       - title from Gemini
       - estimated_hours from Gemini
       - Link to free resource (YouTube, GeeksForGeeks, LeetCode) if Gemini suggests one
    5. Return created tasks
    """
```

**Recommended Quiz Engine:**
```python
async def get_recommended_quizzes(self, student_id: UUID, db) -> list[dict]:
    """
    1. Load student's assessment history (per-topic scores)
    2. Load student's active drive skill requirements
    3. Cross-reference: skills needed for drives that student hasn't assessed recently
    4. Return top 5 recommended quiz topics with reason:
       [{"topic": "System Design", "reason": "Required in Amazon drive (78% match)", "urgency": "high"}]
    """
```

### Frontend

#### CREATE: `frontend/src/pages/student/QuizCenter.jsx`

Route: `/student/quiz`

**Recommended Quizzes Section:**
- "Recommended for You" row with 3–5 topic cards
- Each card: topic emoji, topic name, reason badge (e.g., "Needed for Amazon Drive"), urgency indicator, "Start 5-min Quiz →" button

**Quick Quiz Mode:**
- 5 questions, timed (30s per question, progress bar)
- After completion: immediate feedback + score + badge status update
- If score < 60%: "Remediation Plan Generated" toast → roadmap updated

**Full Assessment History:**
- Table: topic, score, date, badge earned (if any), "Retry →" button
- Filter by topic, sort by date/score

---

## Verification Checklist

- [ ] Mock interview starts with a professional greeting from Gemini
- [ ] Follow-up questions are contextually relevant to previous answers
- [ ] Filler word counter increments correctly as user types (regex-based)
- [ ] Final report shows all 4 scores + strengths/improvements with transcript quotes
- [ ] Verdict ("Strong Hire"/"No Hire") is visible with appropriate styling
- [ ] Transcript viewer shows full conversation in interviewer/candidate alternating format
- [ ] BoS gap analysis correctly identifies skills in 3+ drives but not in curriculum
- [ ] Curriculum proposal .docx downloads with proper structure
- [ ] Copilot knows student's active applications when asked "which drives should I apply to?"
- [ ] Copilot context inspector shows correct injected data
- [ ] Quick quiz remediation creates roadmap tasks after failed session
- [ ] Recommended quiz shows topic linked to student's weakest skill for active drives
- [ ] Mock interview session history shows trend of improving scores
