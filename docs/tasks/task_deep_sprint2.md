# 🧑‍💻 Deep's Task Sheet (Sprint 2) — AI Mock Interview Simulator, BoS Curriculum Generator & Assessment Remediation

> **Role:** Generative AI & Curriculum Intelligence Lead
> **Priority:** 🟡 P2 — Core AI campus differentiator; turns CCIP into an active learning partner
> **Reference Standard:** Coursera Campus Intelligence, Interview Warmup by Google, Pramp, ChatGPT Interview Coach, QS Higher Ed Curriculum Benchmarking
> **Estimated Effort:** ~3–4 days

---

## 📋 Industrial Context — Why This Matters

CCIP's existing AI features are passive: the copilot answers questions, the roadmap shows tasks, the assessments quiz students. The next generation of campus AI platforms are **active** — they simulate interview panels, auto-generate formal academic proposals, and detect weak learners and immediately route them to targeted remediation.

1. **Curriculum Improvement is Still Manual:** Faculty see skill gap charts on `CurriculumMap.jsx`, but when the Board of Studies meets to update syllabi, there is no formal, printable proposal document. They are still writing these manually in Word. AI can generate it in seconds.
2. **Students Practice Interviews Alone with No Feedback:** There's a copilot for Q&A but no structured mock interview mode where the AI asks 3-5 technical questions, evaluates answers, and scores performance like a real hiring manager would.
3. **Assessments are Dead Ends:** When a student scores 40% on a "Data Structures" quiz, nothing happens automatically. Real adaptive learning platforms (Coursera, Khan Academy) immediately inject targeted remediation tasks into the learner's study plan.

---

## TASK 1: Board of Studies AI Curriculum Modernization Generator

### What the Feature Does
Faculty clicks a button on a subject card in `CurriculumMap.jsx` → AI generates a formal, structured **Syllabus Modernization Proposal** showing which modules to add, how many hours each takes, industry justification, and recommended lab experiments → Faculty can download it as a formatted document for BoS meetings.

### Files to Modify / Create
- **MODIFY:** `backend/app/api/v1/curriculum.py` — add new POST route
- **MODIFY:** `backend/app/services/gemini_client.py` — add `generate_curriculum_proposal()` method
- **CREATE:** `backend/app/services/curriculum_proposal_service.py` — orchestrates the prompt building + fallback
- **MODIFY:** `frontend/src/pages/faculty/CurriculumMap.jsx` — add "Generate BoS Proposal" button + modal

### Backend: `curriculum_proposal_service.py`

```python
class CurriculumProposalService:
    
    SYSTEM_PROMPT = """
    You are an expert academic curriculum consultant specializing in engineering education 
    in India. You help Boards of Studies (BoS) modernize their subject syllabi to align 
    with industry hiring requirements. You produce structured, formal proposals in JSON format.
    """
    
    def build_prompt(
        self,
        subject_name: str,
        current_credits: int,
        current_topics: list[str],        # Existing syllabus topics
        uncovered_skills: list[str],       # Skills in job postings not in current syllabus
        top_companies_hiring: list[str],   # e.g., Amazon, Google, Infosys
        placement_demand_pct: float,       # % of drives requiring any of uncovered_skills
    ) -> str:
        """
        Builds a detailed prompt for Gemini to generate the modernization proposal.
        Include all context in the prompt so the model can produce a grounded response.
        """
    
    async def generate(self, subject_id: uuid.UUID, db: AsyncSession) -> dict:
        """
        1. Fetch the Subject from DB by subject_id.
        2. Fetch SubjectSkill mappings (what skills the subject currently covers).
        3. Call analyticsApi (or query drives directly) to find top uncovered skills.
        4. Build the prompt.
        5. Call Gemini via gemini_client.generate_curriculum_proposal(prompt).
        6. Parse the JSON response from Gemini.
        7. If Gemini fails (API key not set, network error, JSON parse error),
           fall back to a STATIC TEMPLATE based on subject name + uncovered skills.
        8. Return the structured proposal dict.
        """
    
    def fallback_template(
        self,
        subject_name: str,
        uncovered_skills: list[str],
    ) -> dict:
        """
        Generates a reasonable static proposal when Gemini is unavailable.
        Uses predefined module templates based on skill category.
        This ensures the feature works in development without a Gemini API key.
        """
```

### Expected Gemini Response Schema

```json
{
  "subject_name": "Cloud Computing",
  "revision_rationale": "78% of hiring companies in recent campus drives require containerization and Infrastructure as Code skills, which are not covered in the current syllabus (Modules 1-3 cover only theoretical cloud concepts).",
  "industry_alignment_score": "+35% estimated improvement in graduate employability",
  "proposed_modules": [
    {
      "module_title": "Module 4: Container Orchestration with Kubernetes",
      "hours": 8,
      "topics": ["Pods, Deployments, Services", "ConfigMaps & Secrets", "Ingress Controllers", "Horizontal Pod Autoscaling"],
      "justification": "Required by Amazon, Google, and 62% of product company campus drives."
    },
    {
      "module_title": "Module 5: Infrastructure as Code with Terraform",
      "hours": 6,
      "topics": ["HCL Syntax", "Terraform State Management", "AWS Provider Setup", "Modules & Workspaces"],
      "justification": "Required skill in 43% of cloud/DevOps campus drives."
    }
  ],
  "recommended_lab_experiments": [
    "Deploy a 3-tier web application (React + FastAPI + PostgreSQL) on a local Minikube cluster.",
    "Provision an AWS VPC, EC2 instance, and RDS database using Terraform from scratch.",
    "Implement Blue/Green deployment strategy using Kubernetes deployments."
  ],
  "obsolete_topics_to_remove": [
    { "topic": "Introduction to Mainframe Computing", "reason": "No campus drive in the last 3 years has required this skill." }
  ],
  "references": [
    "NASSCOM Future Skills Report 2026",
    "AWS Campus Hiring Technical Requirements Q2 2026"
  ]
}
```

### Backend API Route (add to `curriculum.py`)

```python
@router.post("/subjects/{subject_id}/generate-proposal")
async def generate_bos_proposal(
    subject_id: uuid.UUID,
    current_user: User = Depends(_faculty_or_tpo),  # Both faculty and TPO can access
    db: AsyncSession = Depends(get_db),
):
    """
    Generates an AI-powered Board of Studies syllabus modernization proposal
    for the specified subject.
    Returns the full proposal JSON.
    Generation can take 5-15 seconds — return a 202 Accepted with a task ID
    if you want to make it async, OR just run synchronously (simpler).
    """
```

### Frontend: `CurriculumMap.jsx` — Generate BoS Proposal Feature

On each subject card in the curriculum map, add a prominent button:
**"📄 Generate BoS Modernization Proposal"**

Clicking triggers:
1. A loading overlay on the card: "🧠 AI is analyzing industry requirements..."
2. POST to `/curriculum/subjects/{subjectId}/generate-proposal`
3. On success: open a full-screen modal displaying the proposal

**Proposal Modal Design:**
```
┌───── BoS Modernization Proposal — Cloud Computing ────────────────────────┐
│  Generated by AI on Sep 14, 2026                    [📥 Download Document]│
│                                                                            │
│  Revision Rationale                                                        │
│  78% of hiring companies require containerization and IaC skills...       │
│  Industry Alignment Score: +35% improvement in graduate employability     │
│                                                                            │
│  Proposed New Modules                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ Module 4: Container Orchestration with Kubernetes     8 hours       │  │
│  │ Topics: Pods & Deployments · Services · ConfigMaps · HPA            │  │
│  │ Industry Justification: Required by Amazon, Google, 62% of drives   │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ Module 5: Infrastructure as Code with Terraform       6 hours       │  │
│  │ Topics: HCL Syntax · State Management · AWS Provider               │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  Recommended Lab Experiments                                               │
│  1. Deploy a 3-tier app on Minikube cluster                               │
│  2. Provision AWS infrastructure with Terraform                            │
│                                                                            │
│  Topics Recommended for Removal                                            │
│  Mainframe Computing (no campus drives require this since 2023)            │
│                                                                            │
│                          [Close]   [📥 Download Formal BoS Document]      │
└────────────────────────────────────────────────────────────────────────────┘
```

**"Download Formal BoS Document"** button:
- Serializes the proposal JSON into a well-formatted HTML document.
- Uses `window.print()` with print-specific CSS to produce a clean printable PDF.
- The printed document should look like an official university BoS proposal form (include institution logo placeholder, date, subject name, department).

---

## TASK 2: Interactive AI Mock Technical Interview Simulator

### What the Feature Does
Student opens Copilot → switches to "Mock Interview" mode → selects target role and difficulty → AI asks 3-5 technical questions, evaluates each answer, gives feedback + score → generates a Final Interview Readiness Scorecard.

### Files to Modify
- **MODIFY:** `backend/app/services/copilot_service.py` — add mock interview session management
- **MODIFY:** `backend/app/api/v1/copilot.py` — add mock interview start/respond endpoints
- **MODIFY:** `frontend/src/pages/student/Copilot.jsx` — add Mock Interview mode UI

### Backend: Mock Interview State Machine

```python
# Add to copilot_service.py

INTERVIEW_SYSTEM_PROMPT = """
You are a senior technical interviewer at a top-tier technology company.
You are conducting a structured technical interview for the role of {role} at {difficulty} level.
Your name is "Alex" (friendly but professional).

INSTRUCTIONS:
1. Ask exactly one technical question per turn.
2. After the student answers, evaluate their response:
   - Strengths (what they got right)
   - Missing Concepts (what they missed or said incorrectly)
   - Score for this question: 1-10
3. Then ask the next question or (after question {total_questions}) generate the Final Scorecard.

QUESTION TYPES to cover:
- {role}-specific technical concepts
- Data structures / algorithms (1-2 questions)
- System design concept (1 question for mid/senior level)
- Behavioral/STAR format (1 question)

FINAL SCORECARD FORMAT (output when all questions done):
=== FINAL INTERVIEW SCORECARD ===
Technical Knowledge: X/10
Communication: X/10
Problem Solving: X/10
Overall Readiness: {level} (Not Ready / Getting There / Interview Ready / Hire Immediately)
Key Strengths: [bullet list]
Areas to Improve: [bullet list]
Recommended Resources: [bullet list with specific course/book names]
=== END SCORECARD ===
"""

class MockInterviewSession:
    """
    A stateless session managed purely by conversation history.
    No DB table needed — use existing CopilotConversation with a special metadata tag.
    """
    
    @staticmethod
    def get_initial_message(role: str, difficulty: str, total_questions: int = 4) -> str:
        """Returns the AI's opening message for the mock interview."""
        return f"""
        Hello! I'm Alex, your technical interviewer today. 
        We'll be doing a mock {difficulty}-level interview for the {role} role.
        I'll ask you {total_questions} questions, evaluate each response, and give you a 
        final readiness scorecard at the end.
        
        Take your time with each answer — there's no rush. Ready to begin?
        
        **Question 1/{total_questions}:**
        [First question here based on role]
        """
```

### Backend: API Endpoints (add to `copilot.py`)

```python
@router.post("/mock-interview/start")
async def start_mock_interview(
    role: str,                           # e.g. "Backend Engineer", "Data Analyst"
    difficulty: Literal["Intern", "Junior SDE", "Mid-Level SDE"],
    total_questions: int = Query(default=4, ge=3, le=6),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Creates a new CopilotConversation tagged as a mock interview session.
    Sends the initial greeting + Question 1 from Gemini.
    Returns: { "conversation_id": str, "initial_message": str, "role": str, "difficulty": str }
    """

@router.post("/mock-interview/{conversation_id}/respond")
async def respond_in_mock_interview(
    conversation_id: uuid.UUID,
    student_answer: str = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Student submits their answer to the current question.
    Sends the full conversation history to Gemini with mock interview system prompt.
    Gemini evaluates the answer and either asks the next question or generates the scorecard.
    Returns: { "ai_response": str, "is_complete": bool }
    """
```

### Frontend: `Copilot.jsx` — Mock Interview Mode

**Add a "Switch to Mock Interview" toggle/tab at the top of the Copilot page:**

```
[ 💬 Career Q&A ]  [ 🎙️ Mock Interview ]
```

**When "Mock Interview" tab is selected, show the setup panel:**

```
┌──────────── Start Mock Technical Interview ─────────────────────────┐
│                                                                      │
│  Target Role:    [Backend Engineer ▾]                                │
│  Difficulty:     ( ) Intern  (●) Junior SDE  ( ) Mid-Level SDE      │
│  Questions:      [4 ▾]                                               │
│                                                                      │
│       [🎙️ Begin Mock Interview]                                      │
└──────────────────────────────────────────────────────────────────────┘
```

**During interview, show a structured chat interface (different from regular copilot):**

```
Interview: Backend Engineer | Junior SDE Level
Question 2 of 4  ────────────────────────────────────

  🤵 Alex (Interviewer)
  ──────────────────────
  Good answer on REST API design! You correctly mentioned idempotency.
  One thing you missed: you didn't mention HTTP status codes for error cases.
  Score for Q1: 7/10

  Next question:

  "You need to design a caching strategy for an API that serves 1 million
  requests per day. Walk me through your approach, including what you'd cache,
  the eviction policy, and how you'd handle cache invalidation."
  ─────────────────────────────────────────────────────────────────────
  
  Your Answer:
  ┌──────────────────────────────────────────────────────────────────┐
  │                                                                  │
  │                                                                  │
  │  [Type your answer here. Think aloud — explain your reasoning!]  │
  └──────────────────────────────────────────────────────────────────┘
                                          [Submit Answer →]
```

**Scorecard display (when `is_complete: true`):**

Parse the `=== FINAL INTERVIEW SCORECARD ===` block from the AI response and render it as a beautiful scorecard card, not raw text:

```
┌─────────────── Final Interview Readiness Scorecard ─────────────────────┐
│                              🎙️ Mock Interview Complete                   │
│                                                                           │
│  Technical Knowledge  ████████░░  8/10                                   │
│  Communication        ███████░░░  7/10                                   │
│  Problem Solving      ████████░░  8/10                                   │
│                                                                           │
│  Overall Readiness:  ★ Interview Ready  ★                                │
│                                                                           │
│  Key Strengths                                                            │
│  ✅ Strong understanding of REST API principles                           │
│  ✅ Good knowledge of database indexing strategies                        │
│                                                                           │
│  Areas to Improve                                                         │
│  ⚠️ System design at scale (caching, load balancing)                     │
│  ⚠️ Time complexity analysis — practice Big O notation                   │
│                                                                           │
│  Recommended Resources                                                    │
│  📚 "System Design Interview" by Alex Xu                                  │
│  🎯 LeetCode — 30-day plan for Backend interviews                         │
│                                                                           │
│  [🔄 Start New Interview]    [📋 Save to Profile]    [📤 Share]          │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## TASK 3: Automated Quiz Remediation → Career Roadmap Injection

### What the Feature Does
Student completes an assessment and scores below 70% → system detects weak sub-topics → automatically creates "Remedial Practice" tasks in their Career Roadmap → student sees these labeled tasks in `Roadmap.jsx`.

### Files to Modify
- **MODIFY:** `frontend/src/pages/student/AssessmentTake.jsx` — trigger remediation after submission
- **MODIFY:** `backend/app/api/v1/roadmap.py` — add `POST /roadmap/me/tasks` (individual task injection)
- **MODIFY:** `frontend/src/pages/student/Roadmap.jsx` — display remediation tasks with special badge

### Backend: Add task injection endpoint to `roadmap.py`

```python
class RemedialTaskCreate(BaseModel):
    title: str              # e.g. "Remedial Practice: Dynamic Programming (Score: 45%)"
    description: str        # e.g. "Your assessment revealed gaps in DP tabulation and memoization..."
    phase: int = 1          # Which roadmap phase to inject into (default: Phase 1 = current)
    hours_estimated: float = 3.0
    resources: list[dict]   # [{"title": "DP on LeetCode", "url": "...", "type": "practice"}]
    source: str = "quiz_remediation"
    assessment_topic: str   # The quiz topic
    assessment_score: float # The score that triggered this (0.0 - 1.0)

@router.post("/me/tasks")
async def inject_remedial_task(
    data: RemedialTaskCreate,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """
    Injects a remedial task into the student's active roadmap.
    If no roadmap exists yet, create a minimal roadmap with this task.
    Adds the task to the FIRST phase of the roadmap.
    Returns the created RoadmapTask.
    """
```

### Frontend: `AssessmentTake.jsx` — Post-Submission Remediation Trigger

In the existing `AssessmentTake.jsx`, after the student submits and the score is computed:

```javascript
// After successful assessment submission:
const score = result.score;  // 0.0 to 1.0
const topic = assessment.topic;

if (score < 0.70) {
    // Generate remediation resources based on weak topic
    const resources = getRemediationResources(topic, result.weak_subtopics || []);
    
    // Inject remedial task into roadmap
    await intelligenceApi.injectRemedialTask({
        title: `Remedial Practice: ${topic} (Score: ${Math.round(score * 100)}%)`,
        description: `Your ${topic} assessment revealed gaps in: ${(result.weak_subtopics || [topic]).join(', ')}. 
                      Complete these targeted resources before your next attempt.`,
        assessment_topic: topic,
        assessment_score: score,
        hours_estimated: score < 0.4 ? 8.0 : 3.0,  // More hours if very low score
        resources: resources,
        source: "quiz_remediation",
    });
    
    // Show notification: "We've added remediation tasks to your roadmap!"
    setRemediationInjected(true);
}

function getRemediationResources(topic, weakSubtopics) {
    // Hardcoded resource map by topic
    const RESOURCE_MAP = {
        "Data Structures": [
            { title: "Stacks & Queues — Visualized", url: "https://visualgo.net/en/list", type: "tool" },
            { title: "LeetCode DS Practice Set", url: "https://leetcode.com/tag/array/", type: "practice" },
        ],
        "Algorithms": [
            { title: "Sorting Algorithms Animated", url: "https://www.sorting.at/", type: "tool" },
        ],
        "Python": [
            { title: "Python OOP Crash Course", url: "https://realpython.com/python3-object-oriented-programming/", type: "article" },
        ],
        // Add entries for: SQL, Machine Learning, System Design, OS, DBMS, etc.
    };
    return RESOURCE_MAP[topic] || [
        { title: `${topic} — Practice Problems`, url: `https://leetcode.com/search/?q=${encodeURIComponent(topic)}`, type: "practice" }
    ];
}
```

**Post-submission Result Screen Enhancement:**

After score is shown, if remediation was injected, show a blue info banner:

```
┌────────────────────────────────────────────────────────────────┐
│  🎯 Remediation tasks added to your Career Roadmap             │
│  We've created focused practice tasks to help you improve on   │
│  Dynamic Programming and Graph Algorithms. Visit your Roadmap  │
│  to start working through them.                                │
│                                                       [→ Roadmap]│
└────────────────────────────────────────────────────────────────┘
```

### Frontend: `Roadmap.jsx` — Display Remediation Tasks

In the existing Roadmap page, tasks injected with `source: "quiz_remediation"` must be visually distinguished:

1. Add a special badge on the task card: `🎯 Quiz Remediation`
2. Show the assessment score that triggered it: `(Score: 45%)`
3. Color the left border of the task card in amber/orange (different from regular blue tasks)
4. Show the learning resources as clickable links below the task description

**Filter option:** Add a "Filter: All / Remediation Only / Regular" toggle at the top of the Roadmap so students can focus on their remediation backlog.

---

## Checklist — What "Done" Looks Like

- [ ] Faculty can click "Generate BoS Proposal" on any subject card
- [ ] Loading animation shows while AI generates (5-15 seconds)
- [ ] Full structured proposal appears in a modal with modules, hours, topics, lab experiments
- [ ] "Download Formal BoS Document" triggers a printable document
- [ ] Student can start a Mock Interview by selecting role and difficulty level
- [ ] AI asks 3-5 technical questions, evaluates each answer, scores 1-10
- [ ] After all questions, a structured Final Scorecard card is rendered
- [ ] Scoring below 70% on any assessment automatically creates a Remediation task in Roadmap
- [ ] Remediation tasks in Roadmap show a special badge and the quiz score that triggered them
- [ ] Remediation tasks include clickable learning resource links

---

## File Touch Summary

| Action | File |
|--------|------|
| CREATE | `backend/app/services/curriculum_proposal_service.py` |
| MODIFY | `backend/app/api/v1/curriculum.py` |
| MODIFY | `frontend/src/pages/faculty/CurriculumMap.jsx` |
| MODIFY | `backend/app/services/copilot_service.py` |
| MODIFY | `backend/app/api/v1/copilot.py` |
| MODIFY | `frontend/src/pages/student/Copilot.jsx` |
| MODIFY | `frontend/src/pages/student/AssessmentTake.jsx` |
| MODIFY | `backend/app/api/v1/roadmap.py` |
| MODIFY | `frontend/src/pages/student/Roadmap.jsx` |
| MODIFY | `frontend/src/api/endpoints.js` |
