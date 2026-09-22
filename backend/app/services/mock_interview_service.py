"""
Mock Interview Service V2 — Multi-round AI interview with structured lifecycle,
filler-word detection, adaptive follow-ups, and rubric-based final reports.
"""

import re
import uuid
import json
import logging
from datetime import datetime, timezone
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status

from app.models.interview_session import MockInterviewSession
from app.services.gemini_client import stream_chat, generate_json_content, is_gemini_configured

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


def _build_system_prompt(role_target: str, company_style: str, difficulty: str) -> str:
    persona = INTERVIEWER_PERSONAS.get(role_target, ("Alex Chen", "Senior Engineer"))
    name, title = persona

    return f"""You are {name}, a {title} at a {company_style} company conducting a campus placement interview
for a {role_target} position. The candidate is a final-year engineering student.
The interview difficulty level is: {difficulty}.

Rules:
1. Stay strictly in character as an interviewer — never break character.
2. Ask one question at a time. Wait for the candidate's response before asking the next.
3. Ask follow-up questions based on the candidate's answers (adaptive).
4. Start with a warm professional greeting and introduce yourself briefly.
5. After the introduction round (2–3 questions about themselves and background), transition to technical questions.
6. After technical questions (3–4 questions), do behavioral/HR round (2 questions).
7. When you have enough signal (8+ total exchanges), say exactly: "Thank you, that concludes our interview."
8. Do NOT give feedback during the interview — save all feedback for the end.
9. Be professional, encouraging but not overly praising.
10. Adjust question difficulty based on the candidate's responses — if they answer well, ask harder questions.

Start with a warm professional greeting and introduce yourself."""


def _count_fillers(text: str) -> int:
    """Count filler words in candidate's text."""
    return len(FILLER_PATTERN.findall(text))


def _count_words(text: str) -> int:
    """Count total words in text."""
    return len(text.split())


def _detect_interview_end(response: str) -> bool:
    """Check if Gemini has signalled the interview is over."""
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
        """Create a new session and stream the opening greeting."""
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

        # Generate opening greeting
        system_prompt = _build_system_prompt(role_target, company_style, difficulty)
        greeting = ""

        if is_gemini_configured():
            try:
                chunks = []
                async for chunk in stream_chat(system_prompt, [], "Start the interview."):
                    chunks.append(chunk)
                greeting = "".join(chunks)
            except Exception as e:
                logger.error(f"Gemini error during interview start: {e}")
                persona = INTERVIEWER_PERSONAS.get(role_target, ("Alex Chen", "Senior Engineer"))
                greeting = (
                    f"Hello! I'm {persona[0]}, {persona[1]} here at our company. "
                    f"Thank you for joining us today for this {role_target} interview. "
                    "Let's start — could you please introduce yourself and tell me about "
                    "your academic background and any projects you've worked on?"
                )
        else:
            persona = INTERVIEWER_PERSONAS.get(role_target, ("Alex Chen", "Senior Engineer"))
            greeting = (
                f"Hello! I'm {persona[0]}, {persona[1]} here at our company. "
                f"Thank you for joining us today for this {role_target} interview. "
                "Let's start — could you please introduce yourself and tell me about "
                "your academic background and any projects you've worked on?"
            )

        # Save greeting to transcript
        now = datetime.now(timezone.utc).isoformat()
        transcript = list(session.transcript or [])
        transcript.append({
            "role": "interviewer",
            "content": greeting,
            "timestamp": now,
            "analysis": None,
        })
        session.transcript = transcript
        session.questions_asked = list(session.questions_asked or []) + ["Introduction/Greeting"]
        await db.commit()

        persona = INTERVIEWER_PERSONAS.get(role_target, ("Alex Chen", "Senior Engineer"))

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
        """Process candidate's message, call Gemini, return interviewer response."""
        # 1. Fetch and validate session
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

        # 2. Analyze candidate message
        fillers_in_msg = _count_fillers(student_message)
        words_in_msg = _count_words(student_message)

        now = datetime.now(timezone.utc).isoformat()
        transcript = list(session.transcript or [])

        # 3. Append candidate message to transcript
        transcript.append({
            "role": "candidate",
            "content": student_message,
            "timestamp": now,
            "analysis": {
                "filler_count": fillers_in_msg,
                "word_count": words_in_msg,
            },
        })

        # 4. Update cumulative stats
        session.filler_word_count = (session.filler_word_count or 0) + fillers_in_msg
        session.word_count = (session.word_count or 0) + words_in_msg

        # 5. Build conversation history for Gemini
        history = []
        for entry in transcript:
            role = "model" if entry["role"] == "interviewer" else "user"
            history.append({"role": role, "content": entry["content"]})

        # 6. Determine round progression
        candidate_count = sum(1 for t in transcript if t["role"] == "candidate")

        if candidate_count <= 2:
            current_phase = "intro"
        elif candidate_count <= 6:
            current_phase = "technical"
        else:
            current_phase = "behavioral"

        session.status = current_phase
        session.current_round = candidate_count

        # 7. Call Gemini for interviewer response
        system_prompt = _build_system_prompt(session.role_target, session.company_style, session.difficulty)
        interviewer_response = ""

        if is_gemini_configured():
            try:
                chunks = []
                # Use history (all messages except last user msg) + user message
                hist_for_gemini = history[:-1]  # exclude the latest user message we appended
                async for chunk in stream_chat(system_prompt, hist_for_gemini, student_message):
                    chunks.append(chunk)
                interviewer_response = "".join(chunks)
            except Exception as e:
                logger.error(f"Gemini error during interview: {e}")
                interviewer_response = self._fallback_response(current_phase, candidate_count)
        else:
            interviewer_response = self._fallback_response(current_phase, candidate_count)

        # 8. Detect interview end
        interview_ended = _detect_interview_end(interviewer_response)

        # 9. Append interviewer response to transcript
        now_resp = datetime.now(timezone.utc).isoformat()
        transcript.append({
            "role": "interviewer",
            "content": interviewer_response,
            "timestamp": now_resp,
            "analysis": None,
        })

        session.transcript = transcript
        session.questions_asked = list(session.questions_asked or []) + [f"Round {candidate_count}"]

        # 10. If ended, finalize
        report = None
        if interview_ended:
            session.status = "completed"
            session.completed_at = utcnow()
            # Calculate duration
            if session.started_at:
                delta = datetime.now(timezone.utc).replace(tzinfo=None) - session.started_at
                session.duration_seconds = int(delta.total_seconds())
            await db.commit()
            # Generate final report
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

    async def generate_final_report(self, db: AsyncSession, session_id: uuid.UUID) -> dict:
        """Generate a comprehensive rubric-based report using Gemini."""
        result = await db.execute(
            select(MockInterviewSession).where(MockInterviewSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

        transcript = session.transcript or []

        # Build transcript text for Gemini
        transcript_text = "\n".join(
            f"{'Interviewer' if t['role'] == 'interviewer' else 'Candidate'}: {t['content']}"
            for t in transcript
        )

        total_words = session.word_count or 1
        filler_count = session.filler_word_count or 0
        filler_rate = round((filler_count / total_words) * 100, 1) if total_words > 0 else 0

        report_prompt = f"""Review this mock interview transcript and score the candidate.

INTERVIEW TRANSCRIPT:
{transcript_text}

CANDIDATE STATS:
- Total words spoken: {total_words}
- Filler words used: {filler_count} (rate: {filler_rate}%)
- Interview role: {session.role_target}
- Company style: {session.company_style}
- Difficulty: {session.difficulty}

Score the candidate on these dimensions (0-10 each):
1. Technical Knowledge: Did they answer technical questions correctly and with depth?
2. Communication Clarity: Were answers structured? Did they use STAR method for behavioral?
3. Confidence: Tone, response length, self-doubt indicators?
4. Relevance: Did they answer what was asked without going off-topic?

Provide:
- Specific quotes from their answers as evidence for each score.
- Top 2 strengths with specific examples.
- Top 3 areas for improvement with actionable advice.
- A final verdict: "Strong Hire" / "Hire" / "Borderline" / "No Hire"

Respond ONLY with valid JSON (no markdown wrapping) in this exact format:
{{
    "technical_score": <int 0-10>,
    "communication_score": <int 0-10>,
    "confidence_score": <int 0-10>,
    "relevance_score": <int 0-10>,
    "verdict": "<string>",
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

        system_prompt = (
            "You are an expert interview coach and placement trainer. "
            "Analyze interview transcripts and provide detailed, evidence-based scoring. "
            "Be fair but honest. Respond only with valid JSON."
        )

        report = None
        if is_gemini_configured():
            try:
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
                logger.error(f"Failed to generate/parse interview report: {e}")
                report = self._fallback_report()
        else:
            report = self._fallback_report()

        # Enrich report with computed analytics
        report["filler_word_count"] = filler_count
        report["filler_word_rate"] = filler_rate
        report["total_words"] = total_words
        report["duration_seconds"] = session.duration_seconds
        report["exchange_count"] = sum(1 for t in transcript if t["role"] == "candidate")
        report["role_target"] = session.role_target
        report["company_style"] = session.company_style

        # Store in session
        session.final_report = report
        session.performance_scores = {
            "communication": report.get("communication_score", 0),
            "technical": report.get("technical_score", 0),
            "confidence": report.get("confidence_score", 0),
            "relevance": report.get("relevance_score", 0),
        }

        await db.commit()
        return report

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
        """Aggregate statistics across all completed sessions."""
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

    def _fallback_response(self, phase: str, round_num: int) -> str:
        """Fallback responses when Gemini is unavailable."""
        if phase == "intro":
            return "That's a great introduction. Can you tell me more about a challenging project you've worked on?"
        elif phase == "technical":
            questions = [
                "Can you explain the difference between an array and a linked list, and when you'd choose one over the other?",
                "How would you design a URL shortening service like bit.ly? Walk me through your approach.",
                "What's the time complexity of a binary search, and when would you not use it?",
                "Can you explain what a REST API is and how it differs from GraphQL?",
            ]
            idx = (round_num - 3) % len(questions)
            return f"Good answer. Let me ask you this: {questions[idx]}"
        else:
            return (
                "That's interesting. One last question: Tell me about a time when you had to work "
                "with a difficult team member. How did you handle it?\n\n"
                "Thank you, that concludes our interview. I appreciated your time today."
            )

    def _fallback_report(self) -> dict:
        """Fallback report when Gemini is unavailable."""
        return {
            "technical_score": 7,
            "communication_score": 7,
            "confidence_score": 6,
            "relevance_score": 7,
            "verdict": "Hire",
            "strengths": [
                {"point": "Clear communication", "evidence": "Candidate structured answers logically."},
                {"point": "Good foundational knowledge", "evidence": "Demonstrated understanding of core concepts."},
            ],
            "improvements": [
                {"point": "Technical depth", "advice": "Practice system design questions to demonstrate architectural thinking."},
                {"point": "Specific examples", "advice": "Use more concrete project examples with metrics and outcomes."},
                {"point": "Confidence in delivery", "advice": "Practice speaking about achievements without hedging language."},
            ],
            "overall_feedback": "Solid performance overall. The candidate shows good fundamentals and communication skills. With more practice on technical depth and specificity, they would be a stronger candidate.",
        }


mock_interview_service = MockInterviewService()
