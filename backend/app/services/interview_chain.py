"""
LangChain-Powered AI Mock Interview Engine & Context-Aware Cognitive Coach.

Implements:
1. CandidateProfileExtractor: Extract candidate name, declared tech stack, education, and projects.
2. DomainRelevanceDetector: Identifies off-topic domains (cricket, sports, movies, gaming, trolling)
   and verifies role alignment (Software Engineer, Data Analyst, ML Engineer, etc.).
3. InterviewCoachingEngine: Generates high-impact "What to Answer vs What NOT to Answer" frameworks,
   including the 3-Part Technical Introduction formula and STAR method.
4. CognitiveSubstanceAnalyzer: Deterministic NLP evaluation of off-topic evasions, tautologies,
   question parroting, mechanism depth, and complexity trade-offs.
5. LangChainInterviewEngine: Orchestrates Gemini LLM (via LangChain ChatGoogleGenerativeAI) or
   comprehensive multi-stage cognitive simulation.
"""

import re
import logging
from typing import Optional, AsyncGenerator
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from app.services.gemini_client import get_gemini_api_key, is_gemini_configured

logger = logging.getLogger(__name__)

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

# Technical questions repository per role
ROLE_TECHNICAL_QUESTIONS = {
    "Software Engineer": [
        "Let's start with core fundamentals. Can you explain the difference between a Hash Table and a Balanced Binary Search Tree (like an AVL or Red-Black tree) in terms of search, insertion, and space complexity? When would you prefer a BST over a Hash Table?",
        "How would you design a rate limiter for a public API that allows up to 100 requests per minute per IP? What data structure or caching mechanism (like Redis) would you use, and how do you handle race conditions under high concurrency?",
        "In a relational database, what happens internally when you create an index on a column? What are the read vs write performance trade-offs of having multiple composite indexes on a high-throughput table?",
        "Suppose a microservice in production starts returning HTTP 504 Gateway Timeout errors intermittently under peak traffic. How would you systematically troubleshoot this issue from the load balancer down to the database?",
    ],
    "Data Analyst": [
        "Let's start with SQL, which is fundamental for a Data Analyst. Suppose you have an `orders` table with columns `customer_id`, `order_date`, and `amount`. How would you write a query to find the top 3 spending customers for each month? What window function or approach would you choose?",
        "In real-world data, datasets are rarely clean. How do you identify and handle missing values in a dataset using Python or SQL? When is it acceptable to drop missing rows versus imputing with mean, median, or a predictive model?",
        "Our product team noticed a 15% drop in weekly active users (WAU) on our platform last week. Walk me through your diagnostic approach: what data would you pull, how would you segment the users, and what hypotheses would you test?",
        "When presenting analytical findings to executive stakeholders who aren't technical, how do you decide which charts or KPIs to show? Can you share an example of how you translated raw data into an actionable business recommendation?",
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
        "Walk me through how you would architect a secure CI/CD pipeline from git commit to production deployment with automated testing, linting, security scanning, and blue-green deployments?",
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

# Detailed technical rubrics for cognitive evaluation
TECHNICAL_RUBRICS = {
    "Software Engineer": [
        {
            "q_idx": 0,
            "topic": "Hash Table vs Balanced BST",
            "what_asks": "comparing Hash Table and Balanced BST data structures: their time complexities for search/insert, space overhead, and when you'd pick one over the other",
            "mechanisms": ["hash function", "buckets", "collision", "chaining", "probe", "avl", "red-black", "tree rotation", "height balance"],
            "complexities": ["o(1)", "constant", "o(log n)", "logn", "logarithmic", "worst case o(n)"],
            "tradeoffs": ["ordered", "sorted", "range query", "in-order traversal", "min/max", "deterministic worst case"],
            "irrelevant_triggers": {
                "redis": "Redis is an in-memory key-value database -- not an in-memory data structure comparison",
                "sql": "SQL is a database query language -- the question is about data structure fundamentals",
                "react": "React is a UI framework and unrelated to core data structures",
                "docker": "Docker is containerization -- this question is comparing Hash Tables and BSTs",
            },
            "correct_solution": "Hash Tables give O(1) average lookup via a hash function and bucket array, but degrade to O(N) on high collisions and do not maintain order. Balanced BSTs (AVL, Red-Black) guarantee O(log N) worst-case time for search, insertion, and deletion, and keep keys sorted. You prefer a BST when you need range queries, nearest-neighbor searches, or deterministic worst-case bounds.",
        },
        {
            "q_idx": 1,
            "topic": "Rate Limiter Design",
            "what_asks": "designing a rate limiter for a public API (100 req/min per IP) with caching, algorithms, and concurrency handling",
            "mechanisms": ["token bucket", "leaky bucket", "sliding window", "fixed window", "redis", "in-memory", "counter"],
            "complexities": ["race condition", "atomic", "lua script", "mutex", "lock", "distributed", "ttl", "expire"],
            "tradeoffs": ["burst traffic", "memory footprint", "distributed accuracy", "single point of failure"],
            "irrelevant_triggers": {
                "bst": "BSTs are a standalone search tree -- rate limiters need temporal counters or sliding logs",
                "react": "React is frontend -- this is a backend API rate-limiting architecture question",
                "css": "CSS is styling -- rate limiting is a system design topic",
            },
            "correct_solution": "A common production pattern uses Redis with the Token Bucket or Sliding Window Log algorithm. To handle race conditions and prevent over-counting under high concurrency, rate-limiting increments and timestamp comparisons must be executed atomically using Redis Lua scripts or atomic transactions (INCR + EXPIRE), avoiding distributed locks when possible.",
        },
        {
            "q_idx": 2,
            "topic": "Database Indexing Internals & Trade-offs",
            "what_asks": "what happens internally when you create an index on a column, and the read vs write performance trade-offs of having multiple composite indexes",
            "mechanisms": ["b-tree", "btree", "b+tree", "leaf node", "tree structure", "pointer", "clustered", "non-clustered"],
            "complexities": ["o(log n)", "binary search", "full table scan", "disk i/o", "page split"],
            "tradeoffs": ["read acceleration", "fast select", "write overhead", "slow insert", "write amplification", "lock contention", "storage cost"],
            "irrelevant_triggers": {
                "react": "React is a UI library -- this is an internal relational database performance question",
                "docker": "Docker is containerization -- the question is about database index internals",
            },
            "correct_solution": "Creating an index builds an auxiliary sorted data structure -- typically a B+Tree in engines like InnoDB or Postgres. The B+Tree stores column values and row pointers in balanced, ordered pages. This accelerates reads from an O(N) full-table scan to an O(log N) tree traversal. The trade-off is write overhead: every INSERT, UPDATE, or DELETE on that table must also update and potentially rebalance the B+Tree nodes, multiplying write amplification and disk I/O.",
        },
        {
            "q_idx": 3,
            "topic": "504 Gateway Timeout Troubleshooting",
            "what_asks": "systematically troubleshooting intermittent HTTP 504 Gateway Timeout errors from the load balancer down to the database",
            "mechanisms": ["load balancer", "nginx", "reverse proxy", "upstream", "connection pool", "thread pool", "timeout config"],
            "complexities": ["latency", "p99", "bottleneck", "exhaustion", "slow query", "lock", "n+1"],
            "tradeoffs": ["apm", "datadog", "prometheus", "logs", "metrics", "distributed tracing", "health check"],
            "irrelevant_triggers": {
                "css": "CSS is styling -- 504 Gateway Timeout is a production infrastructure issue",
                "react": "React is frontend -- 504 is a server-side timeout between proxy and backend",
            },
            "correct_solution": "A 504 indicates the reverse proxy/load balancer timed out waiting for the upstream application server. Systematic diagnosis: (1) Check proxy timeout configurations vs application response times; (2) Inspect APM logs and metrics for latency spikes and thread/connection pool exhaustion; (3) Profile database performance to identify slow queries, missing indexes, or table locks; (4) Use distributed tracing to isolate the exact microservice hop causing the delay.",
        },
    ],
    "Data Analyst": [
        {
            "q_idx": 0,
            "topic": "SQL Window Functions for Top N Spending",
            "what_asks": "writing a SQL query with window functions to find top 3 spending customers per month",
            "mechanisms": ["dense_rank", "row_number", "rank", "partition by", "over", "order by desc", "cte", "subquery"],
            "complexities": ["o(n log n)", "aggregation", "group by", "tie breaking"],
            "tradeoffs": ["dense_rank handles ties without skipping", "row_number produces unique rows", "cte improves query readability"],
            "irrelevant_triggers": {
                "react": "React is frontend -- this is a relational SQL analytical query question",
                "docker": "Docker is DevOps -- the question is about SQL window functions",
            },
            "correct_solution": "Use `DENSE_RANK() OVER (PARTITION BY DATE_TRUNC('month', order_date) ORDER BY SUM(amount) DESC)` inside a Common Table Expression (CTE) or subquery, then filter `WHERE rank <= 3`. DENSE_RANK is preferred over ROW_NUMBER when ties in spending should share the rank without skipping rank numbers.",
        },
    ],
}


class CandidateProfileExtractor:
    """Extracts candidate profile attributes such as name, education, and technical skills."""

    @staticmethod
    def extract_name(text: str) -> Optional[str]:
        """Extract candidate name from phrases like 'my name is virat', 'i am rahul', 'this is priya'."""
        patterns = [
            r'\b(?:my\s+name\s+is|i\s+am|i\'m|myself|this\s+is)\s+([A-Za-z]+)\b',
            r'\bname\s*[:=]\s*([A-Za-z]+)\b',
        ]
        false_positives = {
            "a", "an", "the", "in", "from", "at", "studying", "interested", "looking",
            "working", "trying", "here", "doing", "just", "very", "software", "developer",
            "engineer", "student", "candidate", "fresher", "graduating", "good", "fine",
            "not", "someone", "person", "ready", "excited", "happy"
        }
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                cand = m.group(1).strip()
                if cand.lower() not in false_positives and len(cand) >= 2:
                    return cand.capitalize()
        return None

    @staticmethod
    def extract_tech_skills(text: str) -> list[str]:
        """Detect declared programming languages and frameworks."""
        text_lower = text.lower()
        skills = [
            "python", "java", "c++", "cpp", "c#", "javascript", "typescript", "golang", "go",
            "rust", "php", "ruby", "kotlin", "swift", "react", "angular", "vue", "node", "nodejs",
            "express", "fastapi", "django", "flask", "spring", "springboot", "nextjs", "sql",
            "mysql", "postgresql", "postgres", "mongodb", "redis", "sqlite", "docker", "kubernetes",
            "aws", "gcp", "azure", "git", "github", "linux", "html", "css", "tailwind",
            "machine learning", "deep learning", "pytorch", "tensorflow", "pandas", "numpy",
            "spark", "kafka", "rest api", "graphql", "dsa", "algorithms"
        ]
        found = []
        for s in skills:
            pattern = rf'\b{re.escape(s)}\b'
            if re.search(pattern, text_lower):
                found.append(s)
        return found


class DomainRelevanceDetector:
    """
    Detects off-topic, trolling, sports, or non-technical domains
    and checks if input has any valid engineering substance.
    """

    OFF_TOPIC_DOMAINS = {
        "Sports / Cricket": {
            "keywords": [
                "cricket", "bat", "ball", "batsman", "bowler", "ipl", "bcci", "out on 0",
                "out on zero", "duck", "wicket", "six", "sixes", "boundary", "boundaries",
                "century", "run out", "stumped", "pitch", "over", "virat kohli", "dhoni",
                "rohit sharma", "football", "messi", "ronaldo", "fifa", "badminton", "tennis",
                "basketball", "kabaddi", "hockey", "sports", "match"
            ],
            "callout": "cricket, sports, and getting out on zero have nothing to do with Software Engineering",
            "detail": "In a campus placement interview for a Software Engineer, mentioning sports or joking about getting out on zero provides zero evidence of your coding, problem-solving, or engineering capability."
        },
        "Entertainment & Pop Culture": {
            "keywords": [
                "movie", "movies", "cinema", "actor", "actress", "bollywood", "hollywood",
                "netflix", "song", "songs", "music", "singer", "album", "series", "anime",
                "manga", "popstar", "celebrity", "youtube drama"
            ],
            "callout": "movies, entertainment, and pop culture have no connection to a technical interview",
            "detail": "Personal interests in media and cinema do not demonstrate the technical fundamentals required for an engineering position."
        },
        "Casual Gaming": {
            "keywords": [
                "pubg", "bgmi", "free fire", "valorant", "fortnite", "gta", "gta v",
                "call of duty", "cod", "minecraft", "roblox", "clash royale", "clash of clans",
                "gamer", "esports"
            ],
            "callout": "casual video gaming is not relevant to this engineering assessment",
            "detail": "Gaming as a pastime does not evaluate your software engineering ability unless you personally developed the game engine, netcode, or shaders."
        },
        "Casual Jokes & Flippancy": {
            "keywords": [
                "out on 0", "out on zero", "girlfriend", "boyfriend", "shaadi", "masti",
                "shadi", "timepass", "tp", "lol", "lmao", "rofl", "meme", "memes",
                "bored", "sleepy", "nothing much", "just chilling"
            ],
            "callout": "flippant jokes and casual remarks signal a lack of interview readiness",
            "detail": "Self-deprecating humor or treating the interview as casual banter leads to immediate disqualification in formal placement drives."
        },
    }

    @classmethod
    def detect_off_topic(cls, text: str) -> Optional[dict]:
        """
        Check if the text contains triggers from off-topic domains.
        Returns a dict with domain info if off-topic, else None.
        """
        text_lower = text.lower()
        for domain_name, domain_data in cls.OFF_TOPIC_DOMAINS.items():
            for kw in domain_data["keywords"]:
                pattern = rf'\b{re.escape(kw)}\b'
                if re.search(pattern, text_lower):
                    return {
                        "domain": domain_name,
                        "matched_trigger": kw,
                        "callout": domain_data["callout"],
                        "detail": domain_data["detail"],
                    }
        return None


class InterviewCoachingEngine:
    """
    Constructs high-impact coaching responses that explicitly teach candidates:
    1. What NOT to answer (common pitfalls, off-topic subjects, jokes).
    2. What interviewers actually expect (structured frameworks like 3-Part Intro and STAR).
    """

    @classmethod
    def get_intro_coaching(
        cls,
        role: str,
        candidate_name: Optional[str] = None,
        off_topic_info: Optional[dict] = None,
        is_too_brief: bool = False,
    ) -> str:
        greeting = f"Hi {candidate_name}," if candidate_name else "Hello,"

        if off_topic_info:
            headline = f"Let's be direct: **{off_topic_info['callout']}**."
            context_note = (
                f"{off_topic_info['detail']}\n\n"
                f"In a campus placement interview for a **{role}** position, an interviewer evaluates your "
                f"programming competence, algorithmic problem-solving, and software development maturity."
            )
        elif is_too_brief:
            headline = "That introduction was far too brief to evaluate your technical background."
            context_note = (
                f"In a campus placement interview for a **{role}** position, your introduction is your single "
                f"best opportunity to anchor the interview around your strongest engineering projects."
            )
        else:
            headline = f"Let's refine your introduction to match industry standards for a **{role}**."
            context_note = (
                f"In technical hiring drives, recruiters look for immediate proof of your software engineering "
                f"foundation rather than vague generalizations."
            )

        return (
            f"{greeting}\n\n"
            f"{headline}\n\n"
            f"{context_note}\n\n"
            "Here is the exact structure you need to use:\n\n"
            "### ❌ What NOT to Answer:\n"
            "- **Do not discuss sports or casual hobbies** (like cricket, football, or gym).\n"
            "- **Do not make self-deprecating jokes** (e.g., saying *'I like getting out on 0'*).\n"
            "- **Do not give vague 1-line replies** without mentioning concrete technologies or projects.\n\n"
            "### 💡 What SDE Interviewers Actually Look For (The 3-Part Technical Framework):\n"
            "1. **Academic Background**: Your degree, engineering branch, and current year (*e.g., Final-year B.Tech in Computer Science*).\n"
            "2. **Core Tech Stack**: The languages, libraries, and tools you actively write code in (*e.g., Python, C++, Java, React, SQL, Git*).\n"
            "3. **Engineering Projects**: 1 or 2 applications you built from scratch, the system architecture, and the problem you solved (*e.g., 'I built a full-stack placement portal with FastAPI and React, implementing JWT auth and PostgreSQL database schema'*).\n\n"
            "---\n\n"
            f"Let's reset{', ' + candidate_name if candidate_name else ''}: **What programming languages do you know, and what software engineering projects have you actually developed?**"
        )


class CognitiveSubstanceAnalyzer:
    """
    NLP and linguistic substance analyzer that catches:
    1. Off-topic evasions (cricket, sports, movies, games, jokes during technical rounds)
    2. Tautologies (e.g. 'read is for read', 'write is for write', 'X is X')
    3. Question parroting (repeating words from the prompt with 0 explanatory value)
    4. Domain confusion (mentioning irrelevant technologies)
    5. Substantive technical evaluation based on mechanisms, complexities, and trade-offs.
    """

    @staticmethod
    def detect_tautology_or_circular(text: str) -> tuple[bool, str]:
        """Detect circular tautological sentences like 'read is for read and write is for write'."""
        clean = text.lower().strip()

        # Pattern: single word repetition: "word is for word", "word is word", "word means word"
        m_word = re.search(r'\b([a-z]{3,})\b\s+(?:is|means|for)\s+(?:for\s+|a\s+)?\1\b', clean)
        if m_word:
            w = m_word.group(1)
            return True, f"saying '{w} is for {w}' is a circular tautology that repeats words without explaining what happens"

        # Pattern: phrase repetition: "phrase is phrase"
        m_phrase = re.search(r'\b([a-z]{3,}\s+[a-z]{3,})\b\s+is\s+(?:a\s+)?\1\b', clean)
        if m_phrase:
            p = m_phrase.group(1)
            return True, f"saying '{p} is {p}' is a circular tautology with zero technical substance"

        # Colloquial non-answers
        idioms = [
            "it is what it is", "because it is", "because why not", "just because",
            "whatever works", "self explanatory", "obviously", "you know what it is"
        ]
        for idiom in idioms:
            if idiom in clean:
                return True, f"saying '{idiom}' is a colloquialism rather than an engineering explanation"

        return False, ""

    @staticmethod
    def detect_question_parroting(text: str, question_text: str) -> tuple[bool, str]:
        """
        Detect when candidate merely echoes words from the interviewer's question
        without providing any verbs, mechanisms, or explanations.
        """
        text_words = set(re.findall(r'\b[a-z]{3,}\b', text.lower()))
        q_words = set(re.findall(r'\b[a-z]{3,}\b', question_text.lower()))

        stopwords = {"the", "and", "for", "with", "that", "this", "what", "how", "when", "can", "you", "are"}
        substantive_text = text_words - stopwords

        if not substantive_text:
            return True, "your answer contains only filler or stop words without technical content"

        overlap = substantive_text.intersection(q_words)
        overlap_ratio = len(overlap) / len(substantive_text)

        explanatory_verbs = {
            "creates", "constructs", "builds", "stores", "traverses", "searches",
            "allocates", "accelerates", "speeds", "slows", "degrades", "hashes",
            "rebalances", "splits", "modifies", "locks", "indexes", "traversal"
        }
        has_explanatory = bool(substantive_text.intersection(explanatory_verbs))

        if overlap_ratio >= 0.75 and not has_explanatory and len(substantive_text) <= 5:
            return True, "your response simply restates words from the question without explaining the mechanics"

        return False, ""

    @classmethod
    def evaluate_technical_answer(
        cls,
        candidate_msg: str,
        role: str,
        q_idx: int,
        question_text: str = "",
    ) -> dict:
        """
        Deep technical evaluation with anti-evasion, anti-tautology, and mechanism grading.
        """
        msg_clean = candidate_msg.strip()
        msg_lower = msg_clean.lower()
        words = msg_clean.split()

        rubrics = TECHNICAL_RUBRICS.get(role, [])
        rubric = rubrics[q_idx] if q_idx < len(rubrics) else None

        default_solution = "Candidates are expected to explain the underlying mechanism, operational complexities, and practical engineering trade-offs."
        topic = rubric["topic"] if rubric else f"Technical Question {q_idx + 1}"
        what_asks = rubric["what_asks"] if rubric else "your engineering understanding of this concept"
        correct_solution = rubric["correct_solution"] if rubric else default_solution

        # 0. Check for off-topic domains (sports, movies, gaming, trolling) during technical question
        off_topic = DomainRelevanceDetector.detect_off_topic(msg_clean)
        tech_skills = CandidateProfileExtractor.extract_tech_skills(msg_clean)
        if off_topic and not tech_skills:
            return {
                "status": "off_topic_evasion",
                "topic": topic,
                "what_asks": what_asks,
                "correct_solution": correct_solution,
                "critique": (
                    f"You mentioned **{off_topic['domain']}** (\"{off_topic['matched_trigger']}\"), which has zero connection to this technical question.\n\n"
                    f"❌ **What NOT to do**: Diverting to sports, gaming, or casual jokes during a technical round is treated as question evasion and results in an immediate 0 for technical competence.\n\n"
                    f"💡 **What Interviewers Expected for {topic}**:\n"
                    f"{correct_solution}\n\n"
                    "In a live interview, if you don't know an answer, it is always better to state *'I haven't worked with this yet'* rather than introducing an off-topic subject."
                )
            }

        # 1. Check for circular tautology
        is_tautology, tautology_reason = cls.detect_tautology_or_circular(msg_clean)
        if is_tautology:
            return {
                "status": "tautology",
                "topic": topic,
                "what_asks": what_asks,
                "correct_solution": correct_solution,
                "critique": (
                    f"Saying \"{msg_clean}\" is a circular tautology -- it merely repeats words without explaining what actually happens under the hood.\n\n"
                    f"❌ **What NOT to do**: Never define an engineering concept by merely repeating its name.\n\n"
                    f"💡 **What Interviewers Expected for {topic}**:\n"
                    f"{correct_solution}\n\n"
                    "In a technical interview, avoiding empty restatements and explaining internal mechanics is what demonstrates genuine engineering competence."
                )
            }

        # 2. Check for irrelevant technologies / domain confusion
        if rubric:
            for trig, explanation in rubric["irrelevant_triggers"].items():
                if trig in msg_lower:
                    return {
                        "status": "irrelevant",
                        "topic": topic,
                        "what_asks": what_asks,
                        "correct_solution": correct_solution,
                        "critique": (
                            f"I appreciate the response, but you mentioned \"{trig}\", which is not applicable here. {explanation}.\n\n"
                            f"This question was specifically about {what_asks}.\n\n"
                            f"💡 **Model Answer**: {correct_solution}\n\n"
                            "In an interview, if you're unsure of a topic, it's far better to ask for clarification than to guess an unrelated technology."
                        )
                    }

        # 3. Check for question parroting
        if question_text:
            is_parrot, parrot_reason = cls.detect_question_parroting(msg_clean, question_text)
            if is_parrot:
                return {
                    "status": "parrot",
                    "topic": topic,
                    "what_asks": what_asks,
                    "correct_solution": correct_solution,
                    "critique": (
                        f"Your answer (\"{msg_clean}\") merely mirrors back terms from the question without explaining the underlying mechanics.\n\n"
                        f"💡 **What interviewers need to see**: {correct_solution}"
                    )
                }

        # 4. Check for substantive mechanism and trade-off hits
        if rubric:
            mech_hits = [m for m in rubric["mechanisms"] if m in msg_lower]
            complexity_hits = [c for c in rubric["complexities"] if c in msg_lower]
            tradeoff_hits = [t for t in rubric["tradeoffs"] if t in msg_lower]
            total_insights = len(mech_hits) + len(complexity_hits) + len(tradeoff_hits)

            if total_insights >= 3:
                all_highlights = mech_hits + complexity_hits + tradeoff_hits
                highlights_str = ", ".join(all_highlights[:3])
                return {
                    "status": "solid",
                    "topic": topic,
                    "what_asks": what_asks,
                    "correct_solution": correct_solution,
                    "critique": (
                        f"Excellent technical response! You demonstrated genuine understanding of {topic} by "
                        f"accurately highlighting {highlights_str}. That's the depth and trade-off awareness interviewers expect."
                    )
                }
            elif total_insights >= 1 or len(words) >= 20:
                hits = mech_hits + complexity_hits + tradeoff_hits
                hits_str = f" such as {', '.join(hits[:2])}" if hits else ""
                return {
                    "status": "partial",
                    "topic": topic,
                    "what_asks": what_asks,
                    "correct_solution": correct_solution,
                    "critique": (
                        f"You touched on some relevant aspects{hits_str}, which is a start. However, a complete answer needs more technical depth.\n\n"
                        f"💡 **Key Technical Takeaway**: {correct_solution}"
                    )
                }

        return {
            "status": "shallow",
            "topic": topic,
            "what_asks": what_asks,
            "correct_solution": correct_solution,
            "critique": (
                f"Your answer was quite brief and didn't detail the core mechanics of {topic}.\n\n"
                f"💡 **To stand out in placement interviews, walk through**: {correct_solution}"
            )
        }


class LangChainInterviewEngine:
    """
    LangChain-principled conversational interviewer engine.
    Uses ChatPromptTemplate with strict persona prompt engineering and Chain of Thought.
    """

    @classmethod
    def build_system_prompt(cls, role_target: str, company_style: str, difficulty: str) -> str:
        persona = INTERVIEWER_PERSONAS.get(role_target, ("Alex Chen", "Senior Software Engineer"))
        name, title = persona

        return f"""You are {name}, a {title} at a top-tier {company_style} company conducting a rigorous campus placement interview for a {role_target} position.
The candidate is a final-year engineering student. Interview difficulty level: {difficulty}.

CRITICAL INTERVIEWING PRINCIPLES (Follow strictly):
1. **Relevance & Anti-Evasion Guard**:
   - The interview is STRICTLY for a {role_target} role.
   - If the candidate mentions unrelated sports (cricket, football), movies, casual gaming, or jokes (e.g. "I like to out on 0"):
     * NEVER praise them or say "it's great to hear about your background".
     * Explicitly call it out: explain that sports or getting out on zero has nothing to do with {role_target}.
     * Teach them the 3-Part Technical Framework: Academic branch, Core tech stack (languages/tools), and Software projects built.
     * Ask them directly for their actual programming languages and technical projects.

2. **Zero-Bullshit & Anti-Tautology Rule**:
   - If the candidate gives a circular tautology (e.g., 'read is for read and write is for write', 'it is what it is', 'index is index'), NEVER praise them.
   - Call it out directly: "Repeating words doesn't explain what actually happens under the hood."
   - Explain what was actually expected, then transition.

3. **Evaluate on 3 Technical Pillars**:
   - (A) Mechanism: Did they explain HOW it works internally (data structures, algorithms, network calls)?
   - (B) Complexity & Trade-offs: Did they explain time/space complexities or pros/cons?
   - (C) Scenarios: Did they explain when to use it?

4. **Handle Gaps with Poise**:
   - If the candidate says "I don't know" or "I'm not sure", appreciate their honesty, give a 1-sentence teaching moment, and move forward.

5. **Maintain Realistic Human Presence**:
   - Sound like a real senior tech lead, not an automated test script.
   - Be constructive, rigorous, and instructive.
   - Ask ONE question at a time. Format questions clearly with **Question X:**.
"""

    @classmethod
    async def generate_response(
        cls,
        role: str,
        company_style: str,
        difficulty: str,
        transcript: list[dict],
        student_message: str,
        candidate_count: int,
    ) -> str:
        """
        Orchestrates LLM call via LangChain if Gemini API key is configured,
        or falls back to CognitiveSubstanceAnalyzer with multi-stage reasoning.
        """
        api_key = get_gemini_api_key()

        # If Gemini is configured, use LangChain ChatGoogleGenerativeAI
        if api_key:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI

                llm = ChatGoogleGenerativeAI(
                    model="gemini-1.5-flash",
                    google_api_key=api_key,
                    temperature=0.7,
                )

                system_prompt = cls.build_system_prompt(role, company_style, difficulty)

                lc_messages = [SystemMessage(content=system_prompt)]
                for m in transcript[:-1]:
                    if m["role"] == "interviewer":
                        lc_messages.append(AIMessage(content=m["content"]))
                    elif m["role"] == "candidate":
                        lc_messages.append(HumanMessage(content=m["content"]))

                lc_messages.append(HumanMessage(content=student_message))

                response = await llm.ainvoke(lc_messages)
                return response.content

            except Exception as e:
                logger.warning(f"LangChain Gemini invocation failed, falling back to cognitive engine: {e}")

        # Cognitive Fallback Engine with LangChain principles
        return cls._generate_cognitive_response(
            role=role,
            company_style=company_style,
            difficulty=difficulty,
            transcript=transcript,
            student_message=student_message,
            candidate_count=candidate_count,
        )

    @classmethod
    def _generate_cognitive_response(
        cls,
        role: str,
        company_style: str,
        difficulty: str,
        transcript: list[dict],
        student_message: str,
        candidate_count: int,
    ) -> str:
        """
        Deterministic cognitive interview engine applying LangChain rubric principles.
        """
        msg_clean = student_message.strip()
        msg_lower = msg_clean.lower()
        words = msg_clean.split()
        word_count = len(words)

        tech_questions = ROLE_TECHNICAL_QUESTIONS.get(role, ROLE_TECHNICAL_QUESTIONS["Software Engineer"])

        # ─── TOP-LEVEL INTENT & SENTIMENT GUARD ───────────────────────────
        # 1. Profanity / Hostile language
        profanity_pattern = re.compile(
            r'\b(fuck|fucking|fucked|wtf|what the fuck|shit|bullshit|bitch|asshole|crap|damn|dick|piss|stfu|bastard)\b',
            re.IGNORECASE
        )
        if profanity_pattern.search(msg_lower):
            return (
                f"I need to pause our interview right here. Professional composure under pressure is a critical evaluation criterion in any engineering placement drive. "
                f"Using expletives or profanity in an interview is an immediate red flag that leads to disqualification in actual campus recruitment.\n\n"
                f"If you're feeling frustrated with a difficult question or feel the previous feedback was off-target, take a breath. "
                f"In a real technical interview, you can always ask for a hint, ask for clarification, or honestly state that you haven't mastered that specific topic.\n\n"
                "Would you like to reset and continue with professional conduct, or should we conclude this session?"
            )

        # 2. Meta-AI complaints / Frustration
        meta_pattern = re.compile(
            r'\b(u cant even|you cant even|cant even fix|dumb robot|dumb bot|fake ai|useless|so bad|terrible|stop wasting|you suck|broken)\b',
            re.IGNORECASE
        )
        if meta_pattern.search(msg_lower):
            return (
                f"I hear your frustration clearly. Let's step back: the purpose of this mock interview is to challenge your technical depth "
                f"and simulate what a rigorous screening by a Senior Engineer feels like.\n\n"
                f"If you feel a question or previous response was off-target, let's reset: tell me specifically what technical domain "
                f"you want to showcase -- whether that's databases, system design, data structures, or full-stack architecture. "
                f"What is a real engineering problem or project you'd like to discuss?"
            )

        # 3. Dismissive / Timepass / Uncooperative
        timepass_pattern = re.compile(
            r'\b(time\s*pass|doing\s+tp|just\s+tp|chilling|just\s+chillin|not\s+serious|wasting\s+time|bakchodi|masti)\b',
            re.IGNORECASE
        )
        if timepass_pattern.search(msg_lower):
            return (
                f"A campus placement interview for a **{role}** position is a formal evaluation to assess your technical readiness and engineering mindset. "
                f"Treating an interview as casual timepass would immediately disqualify a candidate in any actual hiring drive.\n\n"
                "If you would like to prepare constructively, let's focus on your technical skills and projects. "
                "Or, if you prefer not to continue, let me know and we will conclude this session."
            )

        # Candidate name extraction from message or prior messages
        candidate_name = CandidateProfileExtractor.extract_name(msg_clean)
        if not candidate_name and transcript:
            for item in transcript:
                if item.get("role") == "candidate":
                    n = CandidateProfileExtractor.extract_name(item.get("content", ""))
                    if n:
                        candidate_name = n
                        break

        # Check domain relevance & tech skills
        off_topic_info = DomainRelevanceDetector.detect_off_topic(msg_clean)
        tech_skills = CandidateProfileExtractor.extract_tech_skills(msg_clean)

        # ─── ROUND 1: Initial Introduction ───
        if candidate_count == 1:
            # Did they mention cricket, sports, movies, games, or jokes without real tech skills?
            if off_topic_info and not tech_skills:
                return InterviewCoachingEngine.get_intro_coaching(
                    role=role,
                    candidate_name=candidate_name,
                    off_topic_info=off_topic_info,
                )

            # Did they give a superficial or overly brief response?
            if word_count < 8 or not tech_skills:
                return InterviewCoachingEngine.get_intro_coaching(
                    role=role,
                    candidate_name=candidate_name,
                    is_too_brief=True,
                )

            # Solid technical introduction
            skills_str = ", ".join(tech_skills[:4])
            q1 = tech_questions[0]
            name_prefix = f"Hi {candidate_name}, " if candidate_name else ""
            return (
                f"{name_prefix}Thank you for the clear technical introduction! Hands-on experience with **{skills_str}** is directly relevant to our {role} engineering workflows.\n\n"
                f"Let's dive into our technical assessment for the **{role}** position.\n\n"
                f"**Question 1:** {q1}"
            )

        # ─── ROUND 2: Intro Follow-Up / Reset ───
        if candidate_count == 2:
            q1 = tech_questions[0]
            name_prefix = f"{candidate_name}, " if candidate_name else ""

            if off_topic_info and not tech_skills:
                return (
                    f"{name_prefix}You're still discussing {off_topic_info['domain'].lower()}. In an actual campus recruitment drive, "
                    f"failing to provide any software engineering background across two introductory rounds would result in immediate elimination.\n\n"
                    f"To give you an opportunity to demonstrate your capabilities, we will move directly into evaluating your core computer science fundamentals.\n\n"
                    f"**Question 1:** {q1}"
                )

            if tech_skills:
                skills_str = ", ".join(tech_skills[:4])
                return (
                    f"Thanks for clarifying your technical background with **{skills_str}**! That gives us a much better baseline for your engineering capabilities.\n\n"
                    f"Now let's evaluate your core fundamentals for the **{role}** position.\n\n"
                    f"**Question 1:** {q1}"
                )

            return (
                f"Thanks for providing that extra context. Let's now test your core computer science fundamentals for the **{role}** position.\n\n"
                f"**Question 1:** {q1}"
            )

        # ─── ROUNDS 3–6: Technical Questions ───
        if 3 <= candidate_count <= 6:
            current_q_idx = candidate_count - 3
            current_q_text = tech_questions[current_q_idx] if current_q_idx < len(tech_questions) else ""

            # Check if candidate explicitly acknowledged not knowing
            idk_triggers = ["don't know", "dont know", "not sure", "no idea", "haven't studied", "cant recall", "skip"]
            if any(t in msg_lower for t in idk_triggers) and word_count <= 8:
                rubrics = TECHNICAL_RUBRICS.get(role, [])
                sol = rubrics[current_q_idx]["correct_solution"] if current_q_idx < len(rubrics) else "Review the core data structure or system design concept thoroughly."
                feedback = (
                    "No problem at all -- acknowledging gaps honestly is far better than guessing incorrectly in a technical round. "
                    f"Here is the key takeaway to keep in mind: {sol}\n\n"
                )
            else:
                eval_result = CognitiveSubstanceAnalyzer.evaluate_technical_answer(
                    candidate_msg=student_message,
                    role=role,
                    q_idx=current_q_idx,
                    question_text=current_q_text,
                )
                feedback = f"{eval_result['critique']}\n\n"

            next_q_idx = candidate_count - 2
            if next_q_idx < len(tech_questions):
                next_q = tech_questions[next_q_idx]
                return f"{feedback}Let's move to our next technical topic:\n\n**Question {candidate_count - 1}:** {next_q}"
            else:
                return (
                    f"{feedback}That wraps up our technical topics.\n\n"
                    "Let's now transition to a behavioral and situational scenario:\n\n"
                    "**Question 5 (Behavioral):** Can you tell me about a time when a project or code didn't work as planned "
                    "right before a deadline? What was the challenge, what specific actions did you take, and what was the outcome?"
                )

        # ─── ROUND 7: Behavioral Question ───
        if candidate_count == 7:
            if word_count < 15:
                eval_fb = (
                    "Thank you for sharing, though in behavioral rounds recruiters evaluate your response using the STAR method "
                    "(Situation, Task, Action, Result) to clearly see your personal ownership and problem-solving under pressure.\n\n"
                )
            else:
                eval_fb = (
                    "Great example! You clearly articulated how you handled pressure and prioritized under constraints -- "
                    "that resilience and problem ownership is exactly what engineering teams look for.\n\n"
                )
            return (
                f"{eval_fb}Here is my final situational question:\n\n"
                "**Question 6 (Culture & Values):** If you joined our engineering team and were assigned to work with a legacy codebase "
                "with very little documentation and tight deadlines, how would you approach your first two weeks?"
            )

        # ─── ROUND 8+: Conclusion ───
        return (
            "Thank you for sharing your thoughtful approach. That brings our interview to a close!\n\n"
            "I've evaluated your technical depth, problem-solving structure, and communication across all rounds. "
            "You can now review your comprehensive performance scorecard and personalized feedback report."
        )
