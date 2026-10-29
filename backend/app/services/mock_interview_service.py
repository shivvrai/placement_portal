"""
Mock Interview Service V2 — Adaptive AI interview with structured lifecycle,
context-aware NLP evaluation, filler-word detection, and realistic conversational feedback.
"""

import re
import uuid
import json
import logging
from datetime import datetime, timezone
from typing import Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status

from app.models.interview_session import MockInterviewSession
from app.services.gemini_client import stream_chat, generate_json_content, is_gemini_configured
from app.services.interview_chain import LangChainInterviewEngine, CognitiveSubstanceAnalyzer

logger = logging.getLogger(__name__)

# Filler-word patterns (case-insensitive, whole-word match)
FILLER_PATTERN = re.compile(
    r'\b(um|uh|like|basically|you know|kind of|sort of|i mean|actually|literally|right)\b',
    re.IGNORECASE,
)

# Interviewer personas by role
INTERVIEWER_PERSONAS = {
    "Software Engineer": ("Alex Chen", "Senior Software Engineer"),
    "Data Analyst": ("Priya Sharma", "Lead Data Analyst"),
    "ML Engineer": ("James Liu", "ML Engineering Manager"),
    "Full Stack Developer": ("Sarah Kim", "Full Stack Tech Lead"),
    "DevOps Engineer": ("Rahul Verma", "DevOps Architect"),
    "Business Analyst": ("Ananya Patel", "Senior Business Analyst"),
    "Product Manager": ("David Park", "Product Director"),
    "Data Engineer": ("Meera Iyer", "Principal Data Engineer"),
}

# Technical questions matrix per role
ROLE_TECHNICAL_QUESTIONS = {
    "Data Analyst": [
        "Let's start with SQL, which is fundamental for a Data Analyst. Suppose you have an `orders` table with columns `customer_id`, `order_date`, and `amount`. How would you write a query to find the top 3 spending customers for each month? What window function or approach would you choose?",
        "In real-world data, datasets are rarely clean. How do you identify and handle missing values in a dataset using Python or SQL? When is it acceptable to drop missing rows versus imputing with mean, median, or a predictive model?",
        "Our product team noticed a 15% drop in weekly active users (WAU) on our platform last week. Walk me through your diagnostic approach: what data would you pull, how would you segment the users, and what hypotheses would you test?",
        "When presenting analytical findings to executive stakeholders who aren't technical, how do you decide which charts or KPIs to show? Can you share an example of how you translated raw data into an actionable business recommendation?",
    ],
    "Software Engineer": [
        "Let's start with core fundamentals. Can you explain the difference between a Hash Table and a Balanced Binary Search Tree (like an AVL or Red-Black tree) in terms of search, insertion, and space complexity? When would you prefer a BST over a Hash Table?",
        "How would you design a rate limiter for a public API that allows up to 100 requests per minute per IP? What data structure or caching mechanism (like Redis) would you use, and how do you handle race conditions under high concurrency?",
        "In a relational database, what happens internally when you create an index on a column? What are the read vs write performance trade-offs of having multiple composite indexes on a high-throughput table?",
        "Suppose a microservice in production starts returning HTTP 504 Gateway Timeout errors intermittently under peak traffic. How would you systematically troubleshoot this issue from the load balancer down to the database?",
    ],
    "ML Engineer": [
        "Let's discuss model fundamentals. Can you explain the Bias-Variance trade-off, and walk me through how L1 (Lasso) and L2 (Ridge) regularization mathematically prevent overfitting in a regression model?",
        "Suppose you're training a fraud detection model where only 0.2% of transactions are fraudulent. Why is accuracy a misleading metric here, and what evaluation metrics (Precision, Recall, PR-AUC, F1) would you optimize for and why?",
        "What is data leakage in machine learning pipelines, and how do you ensure that target information doesn't leak into feature engineering during k-fold cross-validation?",
        "How would you deploy an ML model for real-time inference with a strict p99 latency SLA under 50ms? What techniques (quantization, caching, ONNX, model distillation) would you consider?",
    ],
    "Full Stack Developer": [
        "In modern frontend development, can you explain how React's Virtual DOM and reconciliation algorithm work? How do you diagnose and prevent unnecessary re-renders in a large component tree?",
        "When designing a backend service, what are the architectural trade-offs between REST and GraphQL? In what scenario would you choose GraphQL over REST, and how do you mitigate the N+1 query problem?",
        "How do you implement secure user authentication and authorization across the full stack? What are the security trade-offs between storing JWTs in httpOnly cookies versus localStorage (regarding XSS and CSRF)?",
        "Suppose a web page takes 6+ seconds to load on mobile devices. Walk me through your performance optimization strategy across both frontend assets and backend database queries.",
    ],
    "DevOps Engineer": [
        "Can you explain the core differences between Docker containerization and traditional virtual machines? What are best practices for writing lightweight, secure multi-stage Dockerfiles in production?",
        "In Kubernetes, how do Deployments, ReplicaSets, Pods, and Services interact? How does the Horizontal Pod Autoscaler (HPA) determine when to scale workloads?",
        "Walk me through how you would architect a secure CI/CD pipeline from git commit to production deployment with automated testing, linting, security scanning, and blue-green deployments.",
        "Suppose your team is alerted that an API's error rate spiked to 12%. What observability tools and metrics (RED or USE method) would you inspect first to isolate the root cause?",
    ],
    "Business Analyst": [
        "How do you approach requirement gathering when business stakeholders have conflicting visions or vague expectations? How do you translate business needs into clear user stories with testable acceptance criteria?",
        "When prioritizing features for an upcoming sprint, what frameworks (such as RICE, MoSCoW, or Kano Model) do you use to balance business value, customer impact, and engineering effort?",
        "Can you explain how you create process maps (BPMN) to identify operational bottlenecks? What metrics do you track to measure business process improvement?",
        "How do you conduct a Cost-Benefit Analysis (CBA) or calculate expected ROI before recommending a major system overhaul to leadership?",
    ],
    "Product Manager": [
        "How do you define the North Star Metric for a two-sided marketplace product? What secondary guardrail metrics would you monitor to ensure growth isn't hurting quality?",
        "Suppose your engineering lead and sales head strongly disagree on the next roadmap priority (tech debt reduction vs a customer-requested feature). How do you resolve this trade-off?",
        "Walk me through how you would design an MVP for a campus peer-to-peer textbook and gadget rental service. What hypotheses would you validate in week 1?",
        "If 30-day user retention dropped by 18% following a new onboarding redesign, what quantitative and qualitative steps would you take to diagnose the issue?",
    ],
    "Data Engineer": [
        "What are the architectural differences between batch processing (like Apache Spark) and real-time stream processing (like Apache Kafka / Flink)? When is a Lambda or Kappa architecture appropriate?",
        "How do you ensure data pipeline idempotency and handle schema drift when ingesting third-party JSON data into a central data lake or warehouse?",
        "Can you explain Star Schema versus Snowflake Schema design in analytical data warehousing? How do partitioning, sorting, and clustering keys impact query performance in BigQuery or Snowflake?",
        "How do you build automated data quality checks and SLA alerts into an Airflow or Prefect orchestration pipeline to catch bad data before it reaches BI dashboards?",
    ],
}

KNOWN_SKILLS = [
    "python", "sql", "pandas", "numpy", "tableau", "power bi", "powerbi", "excel",
    "machine learning", "deep learning", "pytorch", "tensorflow", "scikit-learn", "sklearn",
    "data cleaning", "etl", "eda", "statistics", "matplotlib", "seaborn", "r",
    "mysql", "postgresql", "mongodb", "redis", "docker", "kubernetes", "aws", "gcp", "azure",
    "git", "java", "c++", "cpp", "javascript", "react", "node", "fastapi", "django", "flask",
    "html", "css", "rest", "graphql", "ci/cd", "linux", "kafka", "spark", "hadoop"
]

# ─── Per-question evaluation criteria for intelligent answer analysis ─────────
# For each role, each question index maps to: relevant terms, confusion signals,
# what the question is actually asking, and a brief correct-answer summary.
QUESTION_EVAL = {
    "Software Engineer": [
        {  # Q0: Hash Table vs BST
            "topic": "Hash Table vs Balanced BST",
            "relevant": {"hash", "table", "bst", "binary", "tree", "avl", "red-black",
                         "o(1)", "constant", "log n", "o(log", "collision", "chaining",
                         "probe", "sorted", "order", "range", "bucket", "load factor",
                         "balanced", "complexity", "amortized", "lookup", "search",
                         "insert", "node", "key-value", "array", "linked list", "worst case"},
            "confusion": {
                "redis": "Redis is an in-memory key-value database -- it's not a data structure comparison. The question asks about Hash Table vs BST as data structures",
                "sql": "SQL is a database query language -- this question is specifically about comparing Hash Table and BST data structures",
                "react": "React is a frontend UI framework and has nothing to do with data structures",
                "api": "APIs are about system interfaces -- this question is about internal data structure trade-offs",
                "django": "Django is a web framework -- the question is comparing fundamental data structures",
                "flask": "Flask is a web framework -- the question is about data structure fundamentals",
                "docker": "Docker is a containerization tool -- this is a data structures question",
                "cloud": "Cloud infrastructure is unrelated -- the question compares two fundamental data structures",
                "machine learning": "Machine learning is a different domain -- the question asks about Hash Tables vs BSTs",
            },
            "asks": "comparing Hash Table and Balanced BST data structures: their time complexities for search/insert, space overhead, and when you'd pick one over the other",
            "correct_brief": "Hash Tables give O(1) average-case lookup via hashing but degrade to O(n) on collisions and don't maintain element order. Balanced BSTs (AVL/Red-Black) guarantee O(log n) worst-case for all operations and keep elements sorted, enabling range queries and in-order traversal. You'd prefer a BST when you need ordered data, range scans, or deterministic worst-case performance.",
        },
        {  # Q1: Rate Limiter
            "topic": "Rate Limiter Design",
            "relevant": {"rate", "limit", "limiter", "token", "bucket", "sliding",
                         "window", "counter", "redis", "cache", "ip", "request",
                         "minute", "concurrency", "race", "condition", "atomic",
                         "lua", "lock", "throttle", "429", "queue", "leaky",
                         "in-memory", "distributed", "algorithm"},
            "confusion": {
                "bst": "BSTs are a data structure — the question asks about designing a rate limiter for an API",
                "react": "React is a frontend framework — the question is about backend rate limiting",
                "css": "CSS is for styling — this is a system design question about rate limiting",
                "html": "HTML is markup — the question is about API rate limiting architecture",
            },
            "asks": "designing a rate limiter for a public API (100 requests/minute per IP) with a caching/data structure choice and concurrency handling",
            "correct_brief": "Common approaches: Token Bucket (refill tokens at fixed rate), Sliding Window Log (timestamps), or Fixed Window Counter. Redis is ideal for distributed rate limiting using atomic operations (INCR + EXPIRE or Lua scripts). Key challenge: handling race conditions under high concurrency with atomic counters or distributed locks.",
        },
        {  # Q2: Database Indexing
            "topic": "Database Indexing Internals",
            "relevant": {"index", "b-tree", "btree", "b+tree", "read", "write",
                         "select", "query", "insert", "update", "delete", "scan",
                         "composite", "column", "overhead", "trade-off", "tradeoff",
                         "performance", "lookup", "table", "page", "leaf", "seek",
                         "covering", "cluster"},
            "confusion": {
                "react": "React is a UI library — this question is about database index internals",
                "docker": "Docker is a container tool — the question asks what happens when you create a database index",
                "css": "CSS is styling — this is a database performance question",
            },
            "asks": "what happens internally when you create a database index, and the read vs write trade-offs of multiple composite indexes on a high-throughput table",
            "correct_brief": "Creating an index (usually a B-Tree/B+Tree) builds a sorted auxiliary structure that dramatically accelerates SELECT/WHERE lookups and range scans. Trade-off: every INSERT, UPDATE, or DELETE must also update the index, adding write overhead. Multiple composite indexes multiply this cost, increasing storage and slowing writes proportionally.",
        },
        {  # Q3: 504 Gateway Timeout
            "topic": "504 Gateway Timeout Troubleshooting",
            "relevant": {"504", "gateway", "timeout", "load balancer", "nginx",
                         "proxy", "upstream", "database", "db", "query", "slow",
                         "log", "logs", "metrics", "thread", "pool", "connection",
                         "debug", "monitor", "latency", "trace", "apm", "network",
                         "health", "check", "memory", "cpu", "queue", "backlog"},
            "confusion": {
                "css": "CSS is for styling — this is a production debugging question",
                "react": "React is frontend — the question asks about troubleshooting backend 504 errors",
                "html": "HTML is markup — the question is about debugging microservice timeouts",
            },
            "asks": "systematically troubleshooting intermittent HTTP 504 Gateway Timeout errors in a production microservice under peak traffic",
            "correct_brief": "A 504 means the reverse proxy (Nginx/ALB) timed out waiting for the backend. Systematic approach: check load balancer timeout configs, inspect application logs for slow requests, profile database queries for N+1 or missing indexes, check thread pool / connection pool exhaustion, monitor CPU/memory with APM tools (Datadog, Prometheus), and trace specific requests end-to-end.",
        },
    ],
    "Data Analyst": [
        {  # Q0: SQL Window Functions
            "topic": "SQL Window Functions for Top-N Analysis",
            "relevant": {"sql", "window", "function", "rank", "row_number", "dense_rank",
                         "partition", "order", "group", "over", "customer", "spending",
                         "month", "aggregate", "sum", "subquery", "cte", "common table"},
            "confusion": {},
            "asks": "writing a SQL query with window functions to find top 3 spending customers per month",
            "correct_brief": "Use ROW_NUMBER() or DENSE_RANK() with PARTITION BY month ORDER BY SUM(amount) DESC to rank customers within each month, then filter for rank <= 3 in a CTE or subquery.",
        },
        {  # Q1: Missing Data
            "topic": "Handling Missing Data",
            "relevant": {"missing", "null", "nan", "none", "impute", "imputation",
                         "mean", "median", "mode", "drop", "fillna", "interpolat",
                         "mcar", "mar", "mnar", "model", "predict", "knn", "column"},
            "confusion": {},
            "asks": "identifying and handling missing values using Python or SQL, and when to drop vs impute",
            "correct_brief": "First assess pattern (MCAR/MAR/MNAR) and percentage. Drop rows only when <5% and MCAR. Otherwise, impute with mean/median for numeric, mode for categorical, or use predictive models (KNN imputer, regression) for MAR data. In SQL use COALESCE; in Python use pandas fillna or sklearn imputers.",
        },
        {  # Q2: WAU Drop Diagnosis
            "topic": "Diagnostic Approach for WAU Drop",
            "relevant": {"segment", "cohort", "funnel", "retention", "churn", "acquisition",
                         "channel", "device", "mobile", "web", "hypothesis", "ab test",
                         "a/b", "deploy", "release", "bug", "feature", "metric", "kpi",
                         "seasonal", "trend", "user", "active", "engagement"},
            "confusion": {},
            "asks": "diagnostic approach for a 15% WAU drop: what data to pull, how to segment users, what hypotheses to test",
            "correct_brief": "Segment by acquisition channel, device, geography, and user cohort. Check if drop is broad or isolated. Hypotheses: recent deployment/feature change, external seasonality, tracking bug, competitor launch. Analyze funnel conversion, session duration, and new vs returning users.",
        },
        {  # Q3: Stakeholder Communication
            "topic": "Data Storytelling for Executives",
            "relevant": {"stakeholder", "executive", "business", "chart", "visualization",
                         "kpi", "dashboard", "insight", "action", "recommend", "story",
                         "narrative", "simple", "clear", "audience"},
            "confusion": {},
            "asks": "how to choose charts/KPIs for non-technical executives and translate raw data into actionable recommendations",
            "correct_brief": "Know your audience — executives want the 'so what' and next action, not methodology. Use clean, simple charts (bar, line, funnel) with clear titles. Lead with the insight and recommendation, then show supporting data. One actionable takeaway per slide.",
        },
    ],
}

# For roles not explicitly mapped, use generic evaluation
GENERIC_QUESTION_EVAL = {
    "topic": "technical concept",
    "relevant": set(),
    "confusion": {},
    "asks": "your understanding of this technical concept",
    "correct_brief": "",
}


def _evaluate_answer_quality(msg_lower: str, word_count: int, role: str, q_idx: int) -> dict:
    """
    Evaluate whether the candidate's answer is relevant, confused, or substantive
    for the specific question being asked. Returns a dict with:
      - quality: 'irrelevant' | 'confused' | 'shallow' | 'partial' | 'solid'
      - confusion_detail: str (why the answer is confused, if applicable)
      - relevant_hits: list of matched relevant terms
      - feedback_prefix: str (human-like opening for the feedback)
    """
    role_evals = QUESTION_EVAL.get(role, [])
    q_eval = role_evals[q_idx] if q_idx < len(role_evals) else GENERIC_QUESTION_EVAL

    topic = q_eval["topic"]
    relevant_terms = q_eval["relevant"]
    confusion_map = q_eval["confusion"]
    what_asks = q_eval["asks"]
    correct_brief = q_eval["correct_brief"]

    # Check for confusion signals (candidate mentions something completely off-topic)
    confusion_detail = None
    for trigger, explanation in confusion_map.items():
        if trigger in msg_lower:
            confusion_detail = explanation
            break

    # Count relevant term hits
    relevant_hits = [t for t in relevant_terms if t in msg_lower]

    # Determine quality level
    if confusion_detail and len(relevant_hits) == 0:
        quality = "irrelevant"  # Completely wrong domain
    elif confusion_detail and len(relevant_hits) <= 1:
        quality = "confused"  # Mentioned something off-topic but maybe 1 relevant term
    elif word_count < 12 and len(relevant_hits) == 0:
        quality = "shallow"  # Very brief with no relevant terms
    elif word_count < 12 and len(relevant_hits) >= 1:
        quality = "partial"  # Brief but touched on at least one key concept
    elif len(relevant_hits) >= 3:
        quality = "solid"  # Multiple relevant concepts mentioned
    elif len(relevant_hits) >= 1:
        quality = "partial"  # Some relevant terms but not deep
    else:
        quality = "shallow"  # Long-ish but no relevant terms at all

    return {
        "quality": quality,
        "confusion_detail": confusion_detail,
        "relevant_hits": relevant_hits,
        "topic": topic,
        "what_asks": what_asks,
        "correct_brief": correct_brief,
    }


def _build_system_prompt(role_target: str, company_style: str, difficulty: str) -> str:
    persona = INTERVIEWER_PERSONAS.get(role_target, ("Alex Chen", "Senior Engineer"))
    name, title = persona

    return f"""You are {name}, a {title} at a {company_style} company conducting a campus placement interview
for a {role_target} position. The candidate is a final-year engineering student.
The interview difficulty level is: {difficulty}.

Rules:
1. Stay strictly in character as an interviewer -- never break character.
2. Carefully read the candidate's actual message. If they greeted you or asked 'how are you', acknowledge it politely.
3. If the candidate gave an incomplete, evasive, or overly brief answer, call it out constructively and ask them to elaborate.
4. Ask one question at a time. Wait for the candidate's response before asking the next.
5. In the introduction round (first 2 exchanges), ensure they describe their academic background, skills, and projects.
6. After the introduction round, transition to deep technical questions specifically for a {role_target}.
7. After technical questions (3–4 questions), do behavioral/HR round (2 questions).
8. When you have enough signal (8+ total exchanges), say exactly: "Thank you, that concludes our interview."
9. Be professional, attentive, and realistic.
10. If the candidate gives non-serious, dismissive, or troll responses (such as 'doing time pass', 'just chilling', 'bored', 'asdfghjkl', or refuses to answer), DO NOT say 'Understood' or casually ignore it. Maintain professional interviewer gravitas: call out their response directly, explain that campus placement interviews require seriousness and effort, and ask them if they want to proceed constructively or end the session.
11. If the candidate calls you a robot, bot, or AI, respond with poise: acknowledge their comment with natural composure, clarify that this session is meant to give them high-impact practice for real engineering placement rounds, and steer them back to demonstrating their technical skills."""


def _count_fillers(text: str) -> int:
    return len(FILLER_PATTERN.findall(text))


def _count_words(text: str) -> int:
    return len(text.split())


def _detect_interview_end(response: str) -> bool:
    end_signals = [
        "concludes our interview",
        "that concludes",
        "end of the interview",
        "interview is complete",
        "thank you for your time",
        "we've covered everything",
    ]
    response_lower = response.lower()
    return any(signal in response_lower for signal in end_signals)


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class MockInterviewService:

    async def start_session(
        self,
        db: AsyncSession,
        student_id: uuid.UUID,
        role_target: str,
        company_style: str = "Product",
        difficulty: str = "campus",
    ) -> dict:
        """Create a new session and generate the opening greeting."""
        session = MockInterviewSession(
            student_id=student_id,
            role_target=role_target,
            company_style=company_style,
            difficulty=difficulty,
            status="intro",
            current_round=1,
            transcript=[],
            questions_asked=[],
            filler_word_count=0,
            word_count=0,
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

        persona = INTERVIEWER_PERSONAS.get(role_target, ("Alex Chen", "Senior Software Engineer"))
        greeting = (
            f"Hello! I'm {persona[0]}, {persona[1]} here at our company. "
            f"Thank you for joining us today for this {role_target} interview. "
            "Let's start -- could you please introduce yourself and tell me about "
            "your academic background and any projects you've worked on?"
        )

        now = datetime.now(timezone.utc).isoformat()
        transcript = [{
            "role": "interviewer",
            "content": greeting,
            "timestamp": now,
            "analysis": None,
        }]
        session.transcript = transcript
        session.questions_asked = ["Introduction & Background"]
        await db.commit()

        return {
            "session_id": str(session.id),
            "status": session.status,
            "role_target": role_target,
            "company_style": company_style,
            "difficulty": difficulty,
            "interviewer_name": persona[0],
            "interviewer_title": persona[1],
            "interviewer_message": greeting,
            "exchange_count": 1,
            "filler_word_count": 0,
        }

    async def send_message(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
        student_id: uuid.UUID,
        student_message: str,
    ) -> dict:
        """Process candidate's message, call Gemini or Adaptive Engine, return interviewer response."""
        result = await db.execute(
            select(MockInterviewSession).where(
                MockInterviewSession.id == session_id,
                MockInterviewSession.student_id == student_id,
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview session not found")

        if session.status == "completed":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Interview is already completed")

        fillers_in_msg = _count_fillers(student_message)
        words_in_msg = _count_words(student_message)

        now = datetime.now(timezone.utc).isoformat()
        transcript = list(session.transcript or [])

        transcript.append({
            "role": "candidate",
            "content": student_message,
            "timestamp": now,
            "analysis": {
                "filler_count": fillers_in_msg,
                "word_count": words_in_msg,
            },
        })

        session.filler_word_count = (session.filler_word_count or 0) + fillers_in_msg
        session.word_count = (session.word_count or 0) + words_in_msg

        candidate_count = sum(1 for t in transcript if t["role"] == "candidate")

        if candidate_count <= 2:
            current_phase = "intro"
        elif candidate_count <= 6:
            current_phase = "technical"
        elif candidate_count <= 8:
            current_phase = "behavioral"
        else:
            current_phase = "conclusion"

        session.status = current_phase
        session.current_round = candidate_count

        # Generate response using LangChain pipeline (or Cognitive Engine fallback)
        interviewer_response = await LangChainInterviewEngine.generate_response(
            role=session.role_target or "Software Engineer",
            company_style=session.company_style or "Product",
            difficulty=session.difficulty or "campus",
            transcript=transcript,
            student_message=student_message,
            candidate_count=candidate_count,
        )

        interview_ended = _detect_interview_end(interviewer_response) or candidate_count >= 9

        now_resp = datetime.now(timezone.utc).isoformat()
        transcript.append({
            "role": "interviewer",
            "content": interviewer_response,
            "timestamp": now_resp,
            "analysis": None,
        })

        session.transcript = transcript
        session.questions_asked = list(session.questions_asked or []) + [f"Round {candidate_count}"]

        report = None
        if interview_ended:
            session.status = "completed"
            session.completed_at = utcnow()
            if session.started_at:
                delta = datetime.now(timezone.utc).replace(tzinfo=None) - session.started_at
                session.duration_seconds = int(delta.total_seconds())
            await db.commit()
            report = await self.generate_final_report(db, session_id)
        else:
            await db.commit()

        exchange_count = sum(1 for t in transcript if t["role"] == "interviewer")

        return {
            "interviewer_message": interviewer_response,
            "session_status": session.status,
            "exchange_count": exchange_count,
            "filler_word_count": session.filler_word_count or 0,
            "word_count": session.word_count or 0,
            "interview_ended": interview_ended,
            "report": report,
        }

    def _generate_adaptive_response(
        self,
        session: MockInterviewSession,
        student_message: str,
        transcript: list[dict],
        candidate_count: int,
    ) -> str:
        """
        Intelligent, context-aware conversational evaluator that parses the candidate's actual message,
        evaluates relevance, calls out omissions or dismissive remarks ('doing time pass'), answers social cues,
        and progresses through structured, realistic interview rounds.
        """
        msg_clean = student_message.strip()
        msg_lower = msg_clean.lower()
        words = msg_clean.split()
        word_count = len(words)

        role = session.role_target or "Software Engineer"
        persona = INTERVIEWER_PERSONAS.get(role, ("Alex Chen", "Senior Software Engineer"))

        # 1. Candidate Name Detection
        NON_NAME_WORDS = {
            "studying", "pursuing", "currently", "a", "an", "working", "doing", "in", "from",
            "at", "not", "just", "here", "excited", "interested", "looking", "good", "fine",
            "okay", "ok", "trying", "prepared", "ready", "happy", "thrilled", "glad", "delighted",
            "time", "pass", "timepass", "chilling", "bored"
        }

        def _extract_name(text: str) -> Optional[str]:
            m = re.search(r'\bmy name is\s+([A-Za-z]+)\b', text, re.IGNORECASE)
            if m and m.group(1).lower() not in NON_NAME_WORDS:
                return m.group(1).capitalize()
            m2 = re.search(r'\b(?:i am|i\'m|myself)\s+([A-Za-z]+)\b', text, re.IGNORECASE)
            if m2 and m2.group(1).lower() not in NON_NAME_WORDS:
                return m2.group(1).capitalize()
            return None

        candidate_name = None
        for entry in transcript:
            if entry.get("role") == "candidate":
                nm = _extract_name(entry.get("content", ""))
                if nm:
                    candidate_name = nm
                    break
        if not candidate_name:
            candidate_name = _extract_name(msg_clean)

        # 2. Key Intent Matchers
        timepass_keywords = [
            "time pass", "timepass", "time-pass", "doing time pass", "current doing time pass",
            "chilling", "just chilling", "tp", "just tp", "doing tp", "passing time", "just passing time",
            "bored", "boring", "messing around", "fun only", "for fun", "wasting time",
            "time waste", "not serious", "casual", "bakchodi", "masti", "timepass kar raha"
        ]
        is_timepass = any(kw in msg_lower for kw in timepass_keywords) or bool(re.search(r'\b(time\s*pass|doing\s+tp|chilling|just\s+chillin)\b', msg_lower))

        ai_meta_keywords = [
            "dumb robot", "dumb bot", "stupid robot", "stupid bot", "you are a robot",
            "you are a bot", "you're a bot", "you're a robot", "fake bot", "fake interviewer",
            "are you ai", "are you real", "are you a robot", "are you an ai", "chatgpt", "gemini",
            "automated bot", "blind bot", "scripted bot", "still a dumb robot"
        ]
        is_ai_meta = any(kw in msg_lower for kw in ai_meta_keywords) or bool(re.search(r'\b(dumb|stupid|fake)\s+(robot|bot|ai)\b', msg_lower))

        quit_keywords = ["terminate", "end interview", "stop interview", "quit", "cancel interview", "exit", "close interview"]
        is_quit = any(kw in msg_lower for kw in quit_keywords)

        uncooperative_phrases = [
            "why should i", "i won't tell", "won't tell you", "none of your business",
            "shut up", "leave me alone", "leave it", "i don't care", "dont care",
            "whatever", "not answering", "i don't want to answer", "stop asking"
        ]
        is_uncooperative = any(ph in msg_lower for ph in uncooperative_phrases)

        # History analysis
        prev_candidate_msgs = [t.get("content", "").lower() for t in transcript[:-1] if t.get("role") == "candidate"]
        timepass_history = sum(1 for m in prev_candidate_msgs if any(kw in m for kw in timepass_keywords) or any(ph in m for ph in uncooperative_phrases))

        # ─── TOP LEVEL GUARD: Timepass, Quit, Meta AI, Uncooperative ───────
        if is_quit or (is_timepass and timepass_history >= 1) or (is_uncooperative and timepass_history >= 1):
            return (
                f"Understood. Since you've indicated that you do not wish to participate seriously in this {role} placement interview, "
                "we will terminate the evaluation here. In campus recruitment drives, unprofessional conduct leads to disqualification from placement opportunities.\n\n"
                "That concludes our interview. You can review your feedback scorecard now."
            )

        if is_timepass:
            return (
                f"I noticed you mentioned you are *'{msg_clean}'*.\n\n"
                f"A campus placement interview for a **{role}** position is a formal evaluation to assess your technical readiness, engineering mindset, and communication. "
                "Treating an interview as casual timepass would immediately disqualify a candidate in any actual hiring drive at top companies.\n\n"
                "If you would like to prepare constructively, let's reset: please tell me what degree and branch you are pursuing, "
                "what programming languages or technical tools you are comfortable with, and any project you've worked on. "
                "Or, if you prefer not to continue, let me know and we will conclude this session."
            )

        if is_ai_meta:
            return (
                f"I understand your frustration if my previous response felt rigid or scripted!\n\n"
                f"As your mock interviewer for the **{role}** position, my purpose is to simulate a realistic technical screening where your actual skills and problem-solving are tested.\n\n"
                "Let's move past any robotic pre-canned answers and have an authentic technical conversation. "
                "What programming languages (like Python, Java, C++, JavaScript) are you most comfortable with, or what is a project you've built recently? Let's focus on that."
            )

        if is_uncooperative:
            return (
                f"In an engineering placement interview, collaboration and clear communication are evaluated just as closely as coding syntax. "
                f"If you find this specific question difficult or prefer to skip to a different technical topic for **{role}**, just let me know respectfully.\n\n"
                "Would you like to tackle a different question, or should we conclude this session?"
            )

        # 3. Standard Intent Detection
        is_greeting = bool(re.search(r'\b(hi|hello|hey|good morning|good afternoon|good evening|greetings)\b', msg_lower))
        asked_how_are_you = bool(re.search(r'\b(how are you|how r u|how\'s it going|how are you doing|how do you do|hope you are well)\b', msg_lower))
        has_academic = bool(re.search(r'\b(btech|b\.tech|b\.e|be|bsc|bca|mca|mtech|engineering|computer science|information technology|data science|electronics|mechanical|student|semester|sem|cgpa|gpa|college|university|branch)\b', msg_lower))
        has_projects = bool(re.search(r'\b(project|built|developed|created|worked on|implemented|designed|github|pipeline|model|dashboard|analysis|dataset|system|tool|application|app|website)\b', msg_lower))
        is_idk = bool(re.search(r'\b(i do not know|do not know|i don\'t know|dont know|idk|no idea|not sure|can\'t remember|cannot recall|skip|pass|no clue|haven\'t studied|not aware)\b', msg_lower))
        is_clarification = bool(re.search(r'\b(what do you mean|could you repeat|can you repeat|pardon|please explain|what is the question|clarify)\b', msg_lower))
        is_too_brief = word_count < 8

        # Extract mentioned technical skills
        extracted_skills = [s for s in KNOWN_SKILLS if re.search(rf'\b{re.escape(s)}\b', msg_lower)]
        skills_summary = ", ".join(f"**{s.title()}**" for s in extracted_skills[:3]) if extracted_skills else ""

        # ─── ROUND 1: Introduction Round ─────────────────────────────────
        if candidate_count == 1:
            greeting_prefix = ""
            if asked_how_are_you:
                greeting_prefix = f"Hello{' ' + candidate_name if candidate_name else ''}! I'm doing well, thank you for asking. "
            elif is_greeting:
                greeting_prefix = f"Hello{' ' + candidate_name if candidate_name else ''}! Nice to meet you. "
            else:
                greeting_prefix = f"Welcome{' ' + candidate_name if candidate_name else ''}! "

            # Case A: Candidate only said "hi" or only stated their name without academic or projects
            if not has_academic and not has_projects:
                return (
                    f"{greeting_prefix}However, you haven't really shared your academic background or any projects yet. "
                    f"In a placement interview for a **{role}** role, your introduction is your first opportunity "
                    "to highlight your degree, technical strengths, and project experience.\n\n"
                    f"Could you please tell me:\n"
                    f"1. What degree and branch you are currently pursuing?\n"
                    f"2. What technical skills or programming tools you are most comfortable with?\n"
                    f"3. A brief summary of one project you've worked on that is relevant to {role}?"
                )

            # Case B: Candidate gave academic background but no project
            if has_academic and not has_projects:
                skills_mention = f"It's great to hear that you have experience with {skills_summary}. " if skills_summary else ""
                return (
                    f"{greeting_prefix}Thanks for sharing your academic background! {skills_mention}"
                    "To help me assess your practical experience, could you walk me through one specific "
                    "project you've built or worked on? What was the objective, what tools did you use, "
                    "and what was your personal contribution?"
                )

            # Case C: Candidate gave a full intro with projects / skills
            tech_questions = ROLE_TECHNICAL_QUESTIONS.get(role, ROLE_TECHNICAL_QUESTIONS["Software Engineer"])
            q1 = tech_questions[0]
            skills_mention = f"I'm pleased to hear about your hands-on work with {skills_summary}. " if skills_summary else ""
            return (
                f"{greeting_prefix}Thank you for the thorough introduction! {skills_mention}"
                f"Now let's dive into our technical assessment for the **{role}** position.\n\n"
                f"**Question 1:** {q1}"
            )

        # ─── ROUND 2: Introduction Follow-up / Transition to Technical ───
        if candidate_count == 2:
            tech_questions = ROLE_TECHNICAL_QUESTIONS.get(role, ROLE_TECHNICAL_QUESTIONS["Software Engineer"])
            q1 = tech_questions[0]

            if has_projects or extracted_skills or word_count >= 18:
                skills_mention = f"with {skills_summary}" if skills_summary else "on your project"
                return (
                    f"Thank you{' ' + candidate_name if candidate_name else ''}, that provides much better context! "
                    f"Your practical experience {skills_mention} is directly relevant to our team.\n\n"
                    f"Let's move into the technical evaluation for the **{role}** role.\n\n"
                    f"**Question 1:** {q1}"
                )
            elif is_idk:
                return (
                    f"That's completely fine{' ' + candidate_name if candidate_name else ''} -- as an entry-level candidate, "
                    "having fewer major projects is normal, and we value fundamental problem-solving above all.\n\n"
                    f"Let's jump straight into the technical fundamentals for the **{role}** role.\n\n"
                    f"**Question 1:** {q1}"
                )
            else:
                return (
                    f"I see you didn't highlight your technical projects or core languages yet. "
                    f"In a placement interview, providing concrete examples gives the panel the best signal of your capabilities.\n\n"
                    f"Let's proceed directly to the technical evaluation so you can demonstrate your core computer science knowledge.\n\n"
                    f"**Question 1:** {q1}"
                )

        # ─── ROUNDS 3–6: Technical Questions ─────────────────────────────
        tech_questions = ROLE_TECHNICAL_QUESTIONS.get(role, ROLE_TECHNICAL_QUESTIONS["Software Engineer"])
        current_q_idx = candidate_count - 3  # Q0 asked in round 2, answered in round 3

        if 3 <= candidate_count <= 6:
            feedback = ""
            if is_idk:
                # Use the question evaluation to give a targeted hint
                eval_result = _evaluate_answer_quality(msg_lower, word_count, role, current_q_idx)
                correct = eval_result["correct_brief"]
                topic = eval_result["topic"]
                if correct:
                    feedback = (
                        f"No worries at all -- {topic} is a topic that trips up a lot of candidates. "
                        f"Honesty is far better than guessing in an interview. "
                        f"Here's the key idea to take away: {correct}\n\n"
                    )
                else:
                    feedback = (
                        "That's completely fine -- not every concept comes naturally, and recognizing gaps "
                        "is the first step to filling them. Let's keep going.\n\n"
                    )
            elif is_clarification:
                eval_result = _evaluate_answer_quality(msg_lower, word_count, role, current_q_idx)
                feedback = (
                    f"Sure thing! To clarify -- this question is about {eval_result['what_asks']}. "
                    "I'm looking for your technical reasoning and practical decision-making, "
                    "not a textbook definition. Take your best shot.\n\n"
                )
            else:
                # ─── Intelligent per-question evaluation ───
                eval_result = _evaluate_answer_quality(msg_lower, word_count, role, current_q_idx)
                quality = eval_result["quality"]
                topic = eval_result["topic"]
                confusion_detail = eval_result["confusion_detail"]
                correct_brief = eval_result["correct_brief"]
                relevant_hits = eval_result["relevant_hits"]
                what_asks = eval_result["what_asks"]

                if quality == "irrelevant":
                    # Candidate gave a completely wrong-domain answer
                    feedback = (
                        f"I appreciate the response, but I need to flag something important: "
                        f"you mentioned \"{msg_clean[:60]}{'...' if len(msg_clean) > 60 else ''}\", "
                        f"which doesn't address the question. {confusion_detail}.\n\n"
                        f"This question was about {what_asks}. "
                    )
                    if correct_brief:
                        feedback += (
                            f"Here's a quick pointer so you can study this later: {correct_brief}\n\n"
                            "In a real placement interview, giving an irrelevant answer signals "
                            "you may not have understood the question -- it's always better to ask for "
                            "clarification or honestly say you're not sure.\n\n"
                        )

                elif quality == "confused":
                    # Mixed some off-topic terms but may have touched on something relevant
                    feedback = (
                        f"You touched on a couple of things there, but your answer seems to mix up concepts. "
                        f"{confusion_detail}. The question was specifically about {what_asks}.\n\n"
                    )
                    if correct_brief:
                        feedback += (
                            f"Here's the distinction that matters: {correct_brief}\n\n"
                        )

                elif quality == "shallow":
                    # Brief answer with no relevant terms at all
                    feedback = (
                        f"I can see you attempted a response, but it was quite surface-level "
                        f"and didn't really engage with {topic}. "
                        f"In placement interviews, interviewers are looking for specific technical depth -- "
                        f"time/space complexities, trade-offs, and concrete examples.\n\n"
                    )
                    if correct_brief:
                        feedback += (
                            f"For reference, a strong answer would cover: {correct_brief}\n\n"
                        )

                elif quality == "partial":
                    # Got some relevant terms but incomplete
                    hits_str = ", ".join(relevant_hits[:3])
                    feedback = (
                        f"You're on the right track -- you touched on {hits_str}, which shows "
                        f"some foundation in {topic}. However, a strong interview answer needs more depth: "
                        f"specific complexities, trade-offs, and when you'd choose one approach over another.\n\n"
                    )

                elif quality == "solid":
                    # Good answer with multiple relevant concepts
                    hits_str = " and ".join(relevant_hits[:4])
                    feedback = (
                        f"Excellent answer! You demonstrated solid understanding of {topic} by "
                        f"covering {hits_str}. That's exactly the kind of technical depth "
                        f"interviewers want to see.\n\n"
                    )

                else:
                    feedback = (
                        f"Thanks for your response on {topic}. "
                    )

            next_q_idx = candidate_count - 2
            if next_q_idx < len(tech_questions):
                next_q = tech_questions[next_q_idx]
                return f"{feedback}Let's move to our next technical topic:\n\n**Question {candidate_count - 1}:** {next_q}"
            else:
                return (
                    f"{feedback}That wraps up the technical portion of our interview.\n\n"
                    "Let's now switch gears to a behavioral scenario -- this is where I assess "
                    "your problem-solving under pressure and how you work in teams.\n\n"
                    "**Question 5 (Behavioral):** Can you tell me about a time when a project or code didn't work as planned "
                    "right before a deadline? What was the challenge, what specific actions did you take, and what was the outcome?"
                )

        # ─── ROUNDS 7–8: Behavioral Questions ────────────────────────────
        if candidate_count == 7:
            eval_feedback = ""
            if is_too_brief or is_idk:
                eval_feedback = (
                    "Thanks for sharing, though in behavioral rounds recruiters look for the STAR method "
                    "(Situation, Task, Action, Result) to understand your personal impact. "
                )
            else:
                eval_feedback = "That's a good reflection on your problem-solving and teamwork under pressure. "

            return (
                f"{eval_feedback}One final behavioral question before we wrap up:\n\n"
                "**Question 6:** Describe a situation where you received constructive criticism or negative feedback "
                "on your work or code from a professor, lead, or peer. How did you react, and what changes did you make as a result?"
            )

        if candidate_count >= 8:
            return (
                f"Thank you for sharing that perspective{' ' + candidate_name if candidate_name else ''}! "
                f"It gives me clear insight into your growth mindset and communication style.\n\n"
                "That concludes our interview! I appreciate your time and thoughtful responses throughout our discussion. "
                "You can now view your comprehensive performance scorecard and feedback report."
            )

        return "Thank you, that concludes our interview. I appreciated your time today."

    async def generate_final_report(self, db: AsyncSession, session_id: uuid.UUID) -> dict:
        """Generate a comprehensive rubric-based report."""
        result = await db.execute(
            select(MockInterviewSession).where(MockInterviewSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

        transcript = session.transcript or []
        candidate_msgs = [t["content"] for t in transcript if t.get("role") == "candidate"]
        total_words = session.word_count or sum(len(m.split()) for m in candidate_msgs)
        filler_count = session.filler_word_count or 0
        filler_rate = round((filler_count / max(total_words, 1)) * 100, 1)

        avg_words_per_response = total_words // max(len(candidate_msgs), 1)

        report = None
        if is_gemini_configured():
            try:
                transcript_text = "\n".join(
                    f"{t['role'].upper()}: {t['content']}" for t in transcript
                )
                system_prompt = (
                    "You are an expert interview coach and placement trainer. "
                    "Analyze interview transcripts and provide detailed, evidence-based scoring. "
                    "Be fair but honest. Respond only with valid JSON."
                )
                report_prompt = f"""Analyze this mock interview transcript for a {session.difficulty} {session.role_target} role:

{transcript_text}

Generate an assessment in valid JSON:
{{
    "technical_score": <1-10>,
    "communication_score": <1-10>,
    "confidence_score": <1-10>,
    "relevance_score": <1-10>,
    "verdict": "<Strong Hire | Hire | Borderline | No Hire>",
    "strengths": [
        {{"point": "<strength>", "evidence": "<quote from transcript>"}},
        {{"point": "<strength>", "evidence": "<quote from transcript>"}}
    ],
    "improvements": [
        {{"point": "<area>", "advice": "<specific actionable advice>"}},
        {{"point": "<area>", "advice": "<specific actionable advice>"}},
        {{"point": "<area>", "advice": "<specific actionable advice>"}}
    ],
    "overall_feedback": "<2-3 sentence overall summary>"
}}"""
                raw = await generate_json_content(system_prompt, report_prompt)
                clean = raw.strip()
                if clean.startswith("```json"):
                    clean = clean[7:]
                if clean.startswith("```"):
                    clean = clean[3:]
                if clean.endswith("```"):
                    clean = clean[:-3]
                report = json.loads(clean.strip())
            except Exception as e:
                logger.warning(f"Gemini report generation failed: {e}. Generating rubric report.")

        if not report:
            report = self._build_transcript_aware_report(
                session=session,
                candidate_msgs=candidate_msgs,
                avg_words=avg_words_per_response,
                filler_rate=filler_rate,
            )

        report["filler_word_count"] = filler_count
        report["filler_word_rate"] = filler_rate
        report["total_words"] = total_words
        report["duration_seconds"] = session.duration_seconds
        report["exchange_count"] = len(candidate_msgs)
        report["role_target"] = session.role_target
        report["company_style"] = session.company_style

        session.final_report = report
        session.performance_scores = {
            "communication": report.get("communication_score", 0),
            "technical": report.get("technical_score", 0),
            "confidence": report.get("confidence_score", 0),
            "relevance": report.get("relevance_score", 0),
        }

        await db.commit()
        return report

    def _build_transcript_aware_report(
        self,
        session: MockInterviewSession,
        candidate_msgs: list[str],
        avg_words: int,
        filler_rate: float,
    ) -> dict:
        """Constructs an evidence-backed scorecard matching the candidate's actual transcript."""
        role = session.role_target or "Software Engineer"
        all_candidate_text = " ".join(candidate_msgs).lower()

        timepass_keywords = [
            "time pass", "timepass", "chilling", "doing time pass", "wasting time", "time waste"
        ]
        uncooperative_phrases = ["why should i", "shut up", "leave it", "dont care", "whatever"]

        timepass_detected = any(kw in all_candidate_text for kw in timepass_keywords)
        uncooperative_detected = any(ph in all_candidate_text for ph in uncooperative_phrases)

        # Case 1: Unprofessional / timepass session
        if timepass_detected or uncooperative_detected:
            return {
                "technical_score": 2,
                "communication_score": 1,
                "confidence_score": 2,
                "relevance_score": 1,
                "verdict": "No Hire",
                "strengths": [
                    {
                        "point": "Session Attendance",
                        "evidence": "Candidate initiated the interview session.",
                    }
                ],
                "improvements": [
                    {
                        "point": "Professional Demeanor",
                        "advice": "Campus placement interviews require serious professionalism. Avoid casual remarks like 'doing time pass'.",
                    },
                    {
                        "point": "Technical Engagement",
                        "advice": "Actively attempt technical questions rather than dismissing the interview format.",
                    },
                    {
                        "point": "Communication Standards",
                        "advice": "Use formal, structured communication suitable for software engineering corporate recruitment.",
                    },
                ],
                "overall_feedback": (
                    "Candidate displayed unprofessional behavior ('doing time pass') and refused to engage meaningfully with the interview. "
                    "In actual campus placement drives, this results in immediate rejection and potential placement cell debarment."
                ),
            }

        # Case 2: Normal session scoring
        if avg_words < 12:
            comm_score = 4
            tech_score = 4
            conf_score = 4
            rel_score = 5
            verdict = "Borderline"
            feedback_summary = (
                "Responses were consistently very brief, providing limited signal for the recruiting team. "
                "To pass competitive campus placement rounds, aim to elaborate thoroughly on your technical reasoning and project experiences."
            )
        elif avg_words < 30:
            comm_score = 6
            tech_score = 6
            conf_score = 6
            rel_score = 7
            verdict = "Hire"
            feedback_summary = (
                "Decent foundation shown across the interview. You demonstrated familiarity with key concepts, "
                "but adding more architectural depth and quantifiable project results will significantly boost your interview score."
            )
        else:
            comm_score = 8
            tech_score = 8
            conf_score = 8
            rel_score = 8
            verdict = "Strong Hire"
            feedback_summary = (
                f"Strong, articulate performance for a {role} position! You structured your answers logically, "
                "provided concrete project examples, and demonstrated solid technical maturity."
            )

        if filler_rate > 5.0:
            conf_score = max(conf_score - 1, 3)

        return {
            "technical_score": tech_score,
            "communication_score": comm_score,
            "confidence_score": conf_score,
            "relevance_score": rel_score,
            "verdict": verdict,
            "strengths": [
                {
                    "point": "Professional Demeanor",
                    "evidence": candidate_msgs[0][:60] + "..." if candidate_msgs else "Maintained polite engagement.",
                },
                {
                    "point": f"Target Alignment for {role}",
                    "evidence": f"Engaged across {len(candidate_msgs)} interview rounds.",
                },
            ],
            "improvements": [
                {
                    "point": "Elaboration & Structure",
                    "advice": "Use the STAR method (Situation, Task, Action, Result) to give structured answers with specific metrics.",
                },
                {
                    "point": "Technical Depth",
                    "advice": f"Dive deeper into edge-cases and architectural trade-offs specific to {role}.",
                },
                {
                    "point": "Filler Word Reduction",
                    "advice": "Pause deliberately before speaking rather than using filler words like 'um' or 'like'.",
                },
            ],
            "overall_feedback": feedback_summary,
        }

    async def get_session(
        self, db: AsyncSession, session_id: uuid.UUID, student_id: uuid.UUID
    ) -> MockInterviewSession:
        result = await db.execute(
            select(MockInterviewSession).where(
                MockInterviewSession.id == session_id,
                MockInterviewSession.student_id == student_id,
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview session not found")
        return session

    async def list_sessions(
        self, db: AsyncSession, student_id: uuid.UUID, limit: int = 20
    ) -> list[MockInterviewSession]:
        result = await db.execute(
            select(MockInterviewSession)
            .where(MockInterviewSession.student_id == student_id)
            .order_by(MockInterviewSession.started_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_stats(self, db: AsyncSession, student_id: uuid.UUID) -> dict:
        result = await db.execute(
            select(MockInterviewSession)
            .where(
                MockInterviewSession.student_id == student_id,
                MockInterviewSession.status == "completed",
            )
            .order_by(MockInterviewSession.started_at.desc())
        )
        sessions = result.scalars().all()

        if not sessions:
            return {
                "total_sessions": 0,
                "avg_technical_score": 0,
                "avg_communication_score": 0,
                "avg_confidence_score": 0,
                "avg_relevance_score": 0,
                "improvement_trend": [],
            }

        tech_scores = []
        comm_scores = []
        conf_scores = []
        rel_scores = []
        trend = []

        for s in sessions:
            scores = s.performance_scores or {}
            tech = scores.get("technical", 0)
            comm = scores.get("communication", 0)
            conf = scores.get("confidence", 0)
            rel = scores.get("relevance", 0)
            tech_scores.append(tech)
            comm_scores.append(comm)
            conf_scores.append(conf)
            rel_scores.append(rel)
            trend.append({
                "session_id": str(s.id),
                "date": s.started_at.isoformat() if s.started_at else None,
                "technical": tech,
                "communication": comm,
                "confidence": conf,
                "relevance": rel,
                "verdict": (s.final_report or {}).get("verdict", "N/A"),
            })

        return {
            "total_sessions": len(sessions),
            "avg_technical_score": round(sum(tech_scores) / len(tech_scores), 1),
            "avg_communication_score": round(sum(comm_scores) / len(comm_scores), 1),
            "avg_confidence_score": round(sum(conf_scores) / len(conf_scores), 1),
            "avg_relevance_score": round(sum(rel_scores) / len(rel_scores), 1),
            "improvement_trend": trend,
        }


mock_interview_service = MockInterviewService()
