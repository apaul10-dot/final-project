"""
Pydantic schemas for API requests/responses
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class MistakeAnalysis(BaseModel):
    question_number: int
    mistake_description: str
    why_wrong: str
    how_to_fix: str
    weak_area: str
    user_answer: Optional[str] = None
    correct_answer: Optional[str] = None


class PracticeQuestion(BaseModel):
    id: Optional[str] = None
    question_text: str
    difficulty: str
    topic: str
    correct_answer: str
    solution_steps: List[str]


class TestSubmission(BaseModel):
    test_id: str
    images: List[str]
    extracted_content: dict

