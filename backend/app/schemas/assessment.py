import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class AssessmentStartRequest(BaseModel):
    topic: str
    difficulty: str


class AssessmentQuestionResponse(BaseModel):
    id: uuid.UUID
    question_text: str
    options: list[str]

    model_config = {"from_attributes": True}


class AssessmentSessionResponse(BaseModel):
    id: uuid.UUID
    topic: str
    difficulty: str
    status: str
    started_at: datetime
    questions: list[AssessmentQuestionResponse]

    model_config = {"from_attributes": True}


class AssessmentAnswerItem(BaseModel):
    question_id: uuid.UUID
    selected_option: str


class AssessmentSubmitRequest(BaseModel):
    answers: list[AssessmentAnswerItem]


class AssessmentResultQuestion(BaseModel):
    id: uuid.UUID
    question_text: str
    options: list[str]
    selected_option: Optional[str]
    correct_answer: str
    is_correct: bool
    explanation: Optional[str]

    model_config = {"from_attributes": True}


class AssessmentResultResponse(BaseModel):
    id: uuid.UUID
    topic: str
    difficulty: str
    score: float
    total_questions: int
    correct: int
    incorrect: int
    percentage: float
    questions: list[AssessmentResultQuestion]
    completed_at: datetime

    model_config = {"from_attributes": True}


class AssessmentHistoryItemResponse(BaseModel):
    id: uuid.UUID
    topic: str
    difficulty: str
    score: Optional[float] = None
    percentage: Optional[float] = None
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
