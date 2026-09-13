# 🧑‍💻 Deep's Task Sheet — Career Roadmap + AI Copilot + Assessments

> **Role:** Make all AI-powered features actually work — roadmap generation, career chatbot, skill assessments.
> **Priority:** 🟡 P2 (WOW factor features — depends on database having data)

---

## 📋 Project Context (READ THIS FIRST)

This is a **college placement portal** (CCIP). You're working on the **AI features** — the smart features that use Gemini API and custom logic. The project uses:
- **Frontend:** React + Vite (in `d:\Projects\p1\frontend\`)
- **Backend:** FastAPI + SQLAlchemy (in `d:\Projects\p1\backend\`)
- **AI Backend:** Gemini API via `backend/app/services/gemini_client.py`
- **Assessment Engine:** `backend/app/services/assessment_engine.py`
- **Roadmap Service:** `backend/app/services/roadmap_service.py` (template-based + Gemini option)

### THE CORE PROBLEM
1. **Career Roadmap** (`Roadmap.jsx`) — uses `ROADMAP_DATA` hardcoded. Task checkboxes only update local React state, never persist. "Generate Roadmap" doesn't call backend.
2. **AI Copilot** (`Copilot.jsx`) — In mock mode, returns canned strings from `MOCK_RESPONSES`. In live mode, it has streaming code for Gemini but the API key is not configured.
3. **Assessments** (`AssessmentsList.jsx`, `AssessmentTake.jsx`) — The frontend calls real API endpoints, BUT the backend will crash because the `AssessmentQuestionBank` table is empty (no questions seeded).

---

## TASK 1: Career Roadmap — Wire to Backend

### What exists now
File: `d:\Projects\p1\frontend\src\pages\student\Roadmap.jsx`

Hardcoded at the top:
```js
const ROADMAP_DATA = {
  target_role: 'Software Engineer',
  total_weeks: 12,
  progress: 35,
  phases: [
    { week: 1, tasks: [{ id: 't1', title: 'DSA: Arrays & Strings', status: 'completed', hours: 8 }, ...] },
    ...
  ]
};
```

Task checkbox changes only update local state via `setRoadmap(...)` — never saved to backend.

### What you need to do

**Step 1:** Add imports and state:
```jsx
import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { intelligenceApi } from '../../api/endpoints';

export default function Roadmap() {
  const { user } = useAuth();
  const [roadmap, setRoadmap] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [targetRole, setTargetRole] = useState('Software Engineer');
```

**Step 2:** Fetch existing roadmap on mount:
```jsx
  useEffect(() => {
    async function fetchRoadmap() {
      try {
        setLoading(true);
        // GET /api/v1/roadmap/students/{id}
        const res = await intelligenceApi.getRoadmap(user.id);
        setRoadmap(res.data);
      } catch (err) {
        if (err.response?.status === 404) {
          setRoadmap(null); // No roadmap yet — show "Generate" button
        } else {
          console.error('Failed to load roadmap:', err);
        }
      } finally {
        setLoading(false);
      }
    }
    if (user?.id) fetchRoadmap();
  }, [user]);
```

**Step 3:** Wire the "Generate Roadmap" button:
```jsx
  const handleGenerate = async () => {
    try {
      setGenerating(true);
      // POST /api/v1/roadmap/students/{id}/generate
      const res = await intelligenceApi.generateRoadmap(user.id, targetRole);
      setRoadmap(res.data);
    } catch (err) {
      alert('Failed to generate roadmap: ' + (err.response?.data?.detail || 'Unknown error'));
    } finally {
      setGenerating(false);
    }
  };
```

**Step 4:** Wire task status toggles to persist to backend:
```jsx
  const handleTaskToggle = async (taskId, newStatus) => {
    try {
      // PATCH /api/v1/roadmap/tasks/{taskId}
      await intelligenceApi.updateTask(taskId, newStatus);
      
      // Update local state
      setRoadmap(prev => ({
        ...prev,
        tasks: prev.tasks.map(t => 
          t.id === taskId ? { ...t, status: newStatus } : t
        ),
      }));
    } catch (err) {
      console.error('Failed to update task:', err);
    }
  };
```

**Step 5:** The backend returns a roadmap like:
```json
{
  "id": "uuid",
  "student_id": "uuid",
  "target_role": "Software Engineer",
  "total_weeks": 12,
  "status": "active",
  "progress_pct": 35.0,
  "generated_at": "2025-03-01T10:00:00Z",
  "tasks": [
    {
      "id": "uuid",
      "title": "DSA: Arrays & Strings",
      "description": "LeetCode Easy/Medium — 20 problems",
      "week_number": 1,
      "order_in_week": 1,
      "estimated_hours": 8,
      "status": "completed",
      "completed_at": "2025-03-05T10:00:00Z"
    }
  ]
}
```

Map to existing UI:
- Group tasks by `week_number` to create "phases"
- `task.status` values: "pending", "in_progress", "completed"
- `roadmap.progress_pct` for the progress bar

**Step 6:** Delete `ROADMAP_DATA` constant.

### Backend API that already exists
| Endpoint | Method | What it does |
|----------|--------|-------------|
| `GET /api/v1/roadmap/students/{id}` | GET | Fetch student's active roadmap with tasks |
| `POST /api/v1/roadmap/students/{id}/generate` | POST | Generate a new roadmap (archives old one) |
| `PATCH /api/v1/roadmap/tasks/{taskId}` | PATCH | Update task status (pending/in_progress/completed) |

Backend service: `d:\Projects\p1\backend\app\services\roadmap_service.py` (169 lines)
- `get_student_roadmap()` at line 69 — fetches active roadmap with tasks
- `generate_roadmap()` at line 82 — uses template ROLE_ROADMAPS (predefined for "Data Analyst", "Software Engineer", "ML Engineer")
- `update_task_status()` at line 136 — updates task, recalculates progress_pct

### ⚠️ CHECK: Roadmap API route file
Look at `d:\Projects\p1\backend\app\api\v1\roadmap.py`. Verify these routes exist. If not, create them:

```python
# In roadmap.py
from app.services import roadmap_service

@router.get("/students/{student_id}")
async def get_roadmap(student_id: uuid.UUID, db = Depends(get_db), user = Depends(get_current_user)):
    roadmap = await roadmap_service.get_student_roadmap(db, student_id)
    if not roadmap:
        raise HTTPException(404, "No active roadmap")
    return roadmap

@router.post("/students/{student_id}/generate")
async def generate(student_id: uuid.UUID, data: RoadmapGenerateRequest, db = Depends(get_db), user = Depends(get_current_user)):
    return await roadmap_service.generate_roadmap(db, student_id, data)

@router.patch("/tasks/{task_id}")
async def update_task(task_id: uuid.UUID, data: TaskStatusUpdateRequest, db = Depends(get_db), user = Depends(get_current_user)):
    return await roadmap_service.update_task_status(db, task_id, data, user.id)
```

Also check that `RoadmapGenerateRequest` schema in `d:\Projects\p1\backend\app\schemas\roadmap.py` has:
```python
class RoadmapGenerateRequest(BaseModel):
    target_role: str
    weeks: int = 12
```

---

## TASK 2: AI Copilot — Connect to Gemini API

### What exists now
File: `d:\Projects\p1\frontend\src\pages\student\Copilot.jsx`

In mock mode (`VITE_USE_MOCKS=true`), it cycles through `MOCK_RESPONSES` — canned strings. In live mode, there's streaming code that calls the backend's copilot API.

### What you need to do

**Step 1: Configure Gemini API Key**

The backend needs a Google API key. In `d:\Projects\p1\backend\.env`, add:
```
GEMINI_API_KEY=your-actual-gemini-api-key
```

Then check `d:\Projects\p1\backend\app\core\config.py` — it should have:
```python
GEMINI_API_KEY: str = ""
```

The gemini client at `d:\Projects\p1\backend\app\services\gemini_client.py` (56 lines) already has:
- `is_gemini_configured()` — checks if API key exists
- `stream_chat()` — calls Gemini 1.5 Flash with streaming, converts history format, yields chunks

**Step 2: Install the Gemini Python package**

The backend needs `google-generativeai` package. Add to `requirements.txt`:
```
google-generativeai>=0.7.0
```
Then run: `pip install google-generativeai`

**Step 3: Verify the copilot backend routes exist**

Check `d:\Projects\p1\backend\app\api\v1\copilot.py`. It should have:
| Endpoint | Method | What it does |
|----------|--------|-------------|
| `GET /api/v1/copilot/conversations` | GET | List student's conversations |
| `POST /api/v1/copilot/conversations` | POST | Create new conversation |
| `POST /api/v1/copilot/conversations/{id}/messages` | POST | Send message, stream response |
| `GET /api/v1/copilot/conversations/{id}` | GET | Get conversation history |

The copilot service at `d:\Projects\p1\backend\app\services\copilot_service.py` (158 lines) already implements:
- `list_conversations()` — from DB
- `create_conversation()` — with optional initial message + Gemini response
- `add_message_stream()` — streams response via Gemini, saves to DB after completion
- `get_conversation()` — load full conversation

**Step 4: Wire the frontend**

The Copilot.jsx likely already has code for the live mode. Check if it calls `copilotApi`:
```js
// In endpoints.js:
export const copilotApi = {
  getConversations: () => api.get('/copilot/conversations'),
  createConversation: () => api.post('/copilot/conversations'),
  sendMessage: (convId, message) => api.post(`/copilot/conversations/${convId}/messages`, { message }),
  getHistory: (convId) => api.get(`/copilot/conversations/${convId}`),
};
```

**What you need to verify/fix in Copilot.jsx:**
1. When `VITE_USE_MOCKS` is NOT true, it should call `copilotApi.sendMessage()`
2. The streaming response — the backend returns a streaming response. Check if the frontend handles `EventSource` or `fetch` with readable stream
3. If it uses regular POST (not streaming), the response will contain the full assistant message after it's generated
4. Conversation list sidebar should load from `copilotApi.getConversations()`
5. When clicking a conversation, load history from `copilotApi.getHistory(convId)`

**Step 5: Test the flow**
1. Set `VITE_USE_MOCKS=false` in `d:\Projects\p1\frontend\.env`
2. Add `GEMINI_API_KEY=...` to `d:\Projects\p1\backend\.env`
3. Login as a student
4. Open Copilot page
5. Type a message like "What skills should I focus on for SDE roles?"
6. Verify the response comes from Gemini (not a canned string)
7. Verify the conversation is saved (reload page, conversation should persist)

### ⚠️ IMPORTANT: System Prompt
The `prompt_builder.py` at `d:\Projects\p1\backend\app\services\prompt_builder.py` builds a system prompt that includes the student's skills, CGPA, department, etc. Check that this function:
1. Loads the student's profile from DB
2. Builds a context-rich prompt like "You are an AI career advisor for a CS student with CGPA 8.5, skilled in Python and SQL..."
3. Is called by `copilot_service.py` before calling Gemini

---

## TASK 3: Assessments — Seed Questions + Fix Flow

### What exists now
Files:
- `d:\Projects\p1\frontend\src\pages\student\AssessmentsList.jsx` — list of available topics
- `d:\Projects\p1\frontend\src\pages\student\AssessmentTake.jsx` — take an assessment

The frontend actually calls the real API (`assessmentsApi.start()`, `assessmentsApi.submit()`). **BUT** it crashes because the `AssessmentQuestionBank` table in the database is empty — no questions exist.

### What you need to do

**Step 1: Create a question seeding script**

Create `d:\Projects\p1\backend\scripts\seed_questions.py`:

```python
"""Seed the assessment question bank with 50+ MCQ questions."""

import asyncio
from app.core.database import get_db, engine
from app.models.assessment import AssessmentQuestionBank
from sqlalchemy.ext.asyncio import AsyncSession

QUESTIONS = [
    # Python — Easy
    {
        "topic": "Python",
        "difficulty": "easy",
        "question_text": "What is the output of `print(type([]))`?",
        "options": ["<class 'list'>", "<class 'tuple'>", "<class 'dict'>", "<class 'set'>"],
        "correct_answer": "<class 'list'>",
        "explanation": "[] creates an empty list, so type() returns <class 'list'>.",
    },
    {
        "topic": "Python",
        "difficulty": "easy",
        "question_text": "Which keyword is used to define a function in Python?",
        "options": ["func", "define", "def", "function"],
        "correct_answer": "def",
        "explanation": "The 'def' keyword is used to define functions in Python.",
    },
    {
        "topic": "Python",
        "difficulty": "medium",
        "question_text": "What does `list(range(0, 10, 3))` return?",
        "options": ["[0, 3, 6, 9]", "[0, 3, 6]", "[3, 6, 9]", "[0, 1, 2, 3]"],
        "correct_answer": "[0, 3, 6, 9]",
        "explanation": "range(0, 10, 3) generates 0, 3, 6, 9 (start=0, stop=10, step=3).",
    },
    {
        "topic": "Python",
        "difficulty": "medium",
        "question_text": "What is the difference between a list and a tuple?",
        "options": ["Lists are mutable, tuples are immutable", "Tuples are mutable, lists are immutable", "No difference", "Lists use {} syntax"],
        "correct_answer": "Lists are mutable, tuples are immutable",
        "explanation": "Lists can be modified after creation (mutable), tuples cannot (immutable).",
    },
    {
        "topic": "Python",
        "difficulty": "hard",
        "question_text": "What is the output of `print([x**2 for x in range(5) if x % 2 != 0])`?",
        "options": ["[1, 9]", "[0, 4, 16]", "[1, 4, 9]", "[1, 9, 25]"],
        "correct_answer": "[1, 9]",
        "explanation": "Odd numbers in range(5) are 1, 3. Their squares are 1, 9.",
    },
    # SQL — Easy
    {
        "topic": "SQL",
        "difficulty": "easy",
        "question_text": "Which SQL clause is used to filter rows?",
        "options": ["WHERE", "HAVING", "GROUP BY", "ORDER BY"],
        "correct_answer": "WHERE",
        "explanation": "WHERE clause filters rows before grouping.",
    },
    {
        "topic": "SQL",
        "difficulty": "easy",
        "question_text": "Which SQL command is used to add a new row?",
        "options": ["INSERT INTO", "ADD ROW", "CREATE ROW", "APPEND"],
        "correct_answer": "INSERT INTO",
        "explanation": "INSERT INTO table VALUES (...) adds a new row.",
    },
    {
        "topic": "SQL",
        "difficulty": "medium",
        "question_text": "What does a LEFT JOIN return?",
        "options": [
            "All rows from left table + matching rows from right",
            "Only matching rows from both tables",
            "All rows from right table",
            "All rows from both tables"
        ],
        "correct_answer": "All rows from left table + matching rows from right",
        "explanation": "LEFT JOIN returns all records from the left table and matched records from the right table.",
    },
    {
        "topic": "SQL",
        "difficulty": "hard",
        "question_text": "Which window function gives the rank with gaps?",
        "options": ["RANK()", "DENSE_RANK()", "ROW_NUMBER()", "NTILE()"],
        "correct_answer": "RANK()",
        "explanation": "RANK() assigns the same rank to equal values and skips subsequent ranks, creating gaps.",
    },
    # React — Easy
    {
        "topic": "React",
        "difficulty": "easy",
        "question_text": "What hook is used to manage state in a functional component?",
        "options": ["useState", "useEffect", "useContext", "useReducer"],
        "correct_answer": "useState",
        "explanation": "useState is the primary hook for managing local component state.",
    },
    {
        "topic": "React",
        "difficulty": "medium",
        "question_text": "When does useEffect with an empty dependency array run?",
        "options": ["Only on mount", "On every render", "On unmount", "Never"],
        "correct_answer": "Only on mount",
        "explanation": "useEffect(() => {}, []) runs only once after the initial render (mount).",
    },
    # Machine Learning — Easy
    {
        "topic": "Machine Learning",
        "difficulty": "easy",
        "question_text": "Which algorithm is used for classification and regression based on nearest data points?",
        "options": ["K-Nearest Neighbors", "K-Means", "Decision Tree", "Linear Regression"],
        "correct_answer": "K-Nearest Neighbors",
        "explanation": "KNN classifies a data point based on how its neighbors are classified.",
    },
    {
        "topic": "Machine Learning",
        "difficulty": "medium",
        "question_text": "What metric is NOT suitable for imbalanced classification?",
        "options": ["Accuracy", "F1-Score", "Precision", "AUC-ROC"],
        "correct_answer": "Accuracy",
        "explanation": "Accuracy can be misleading for imbalanced datasets. A model that always predicts the majority class can have high accuracy.",
    },
    # Add at least 5 more per topic to reach 50+ total...
    # Make sure each topic has at least 5 questions per difficulty level
]

async def seed():
    async with engine.begin() as conn:
        # ... create tables if needed
        pass
    
    async for db in get_db():
        for q in QUESTIONS:
            question = AssessmentQuestionBank(
                topic=q["topic"],
                difficulty=q["difficulty"],
                question_text=q["question_text"],
                options=q["options"],
                correct_answer=q["correct_answer"],
                explanation=q.get("explanation", ""),
                is_active=True,
            )
            db.add(question)
        await db.commit()
        print(f"Seeded {len(QUESTIONS)} questions")

if __name__ == "__main__":
    asyncio.run(seed())
```

**YOU MUST ADD AT LEAST 50 questions total** — minimum 5 per topic per difficulty level. Cover these topics:
- Python (easy: 5, medium: 5, hard: 5)
- SQL (easy: 5, medium: 5, hard: 5)
- React (easy: 3, medium: 3, hard: 3)
- Machine Learning (easy: 3, medium: 3, hard: 3)
- Data Structures (easy: 3, medium: 3, hard: 3)

The assessment engine at `d:\Projects\p1\backend\app\services\assessment_engine.py` requires **at least 5 questions** per topic+difficulty combination (see line 29). If fewer exist, it returns an error.

**Step 2: Verify the frontend flow**

The assessment flow is:
1. **AssessmentsList.jsx** — shows available topics. Student picks topic + difficulty → clicks "Start"
2. Frontend calls `assessmentsApi.start(topic, difficulty)` → `POST /api/v1/assessments/start`
3. Backend creates a session, selects random questions, returns them (without correct answers)
4. **AssessmentTake.jsx** — renders questions as MCQ. Student answers and clicks "Submit"
5. Frontend calls `assessmentsApi.submit(sessionId, answers)` → `POST /api/v1/assessments/{id}/submit`
6. Backend evaluates, calculates score, returns results with correct answers
7. Frontend shows score + correct/incorrect per question

**Check if this flow works:**
- Look at how `AssessmentsList.jsx` calls the API — is it using `assessmentsApi.start(topic, difficulty)`?
- Look at how `AssessmentTake.jsx` sends answers — does the answer format match what the backend expects?

The backend expects:
```json
POST /api/v1/assessments/{sessionId}/submit
{
  "answers": [
    { "question_id": "uuid", "selected_option": "answer text" }
  ]
}
```

Check `d:\Projects\p1\backend\app\schemas\assessment.py` for the exact schema.

**Step 3: Verify score saves to student's skill profile**

After submission, the backend calls `update_student_skill_from_assessment()` (line 123 in assessment_engine.py). This should update the student's skill confidence based on their assessment score.

Check `d:\Projects\p1\backend\app\services\skill_profile_service.py` — make sure this function exists and works correctly.

**Step 4: Assessment history**

The `AssessmentsList.jsx` should also show past assessment results:
```jsx
// Fetch history
const res = await assessmentsApi.getHistory();
// Returns: [{ id, topic, difficulty, score, percentage, status, started_at, completed_at }]
```

---

## TASK 4: Verify Roadmap Template Content

### What exists
`d:\Projects\p1\backend\app\services\roadmap_service.py` lines 21-66 have `ROLE_ROADMAPS` with templates for 3 roles:
- Data Analyst (14 tasks over 12 weeks)
- Software Engineer (12 tasks over 12 weeks)
- ML Engineer (12 tasks over 12 weeks)

### What to verify
1. The templates make sense (titles, descriptions, hours)
2. The role selector on the frontend includes these 3 roles
3. If a role is not in the template, it falls back to "Software Engineer"
4. Generated tasks have proper week assignments

### Optional enhancement
Add more roles to the template:
- "Full Stack Developer"
- "DevOps Engineer"
- "Data Scientist"

---

## ✅ Checklist — What "Done" Looks Like
- [ ] Roadmap page loads real data from backend (no ROADMAP_DATA remains)
- [ ] "Generate Roadmap" creates a real roadmap in DB
- [ ] Task checkboxes persist to DB (not just local state)
- [ ] Progress bar updates when tasks are completed
- [ ] AI Copilot connects to Gemini API (not canned responses)
- [ ] Copilot conversations are saved to DB and persist across page reloads
- [ ] Gemini API key is configured in .env
- [ ] Assessment question bank has 50+ questions seeded
- [ ] Start assessment → answer → submit → see results flow works end-to-end
- [ ] Assessment score updates student's skill profile
- [ ] Assessment history shows past attempts with scores
- [ ] Loading and error states everywhere
