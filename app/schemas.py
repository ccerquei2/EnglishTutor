# /app/schemas.py

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal, Optional

# --- Modelos de Dados de Conteúdo ---

class LearningUnit(BaseModel):
    id: str
    unit_code: str | None = None
    type: str
    content: Dict[str, Any]
    metadata: Dict[str, Any]

class Lesson(BaseModel):
    lesson_id: str
    title: str
    objective: str
    lesson_items: List[LearningUnit]
    module_id: Optional[str] = None # <-- NOVO CAMPO OPCIONAL

# --- Modelos para a API de Interação ---

class UserIntent(BaseModel):
    type: Literal['button_click', 'chat_message']
    action_id: str | None = Field(None)
    text: str | None = Field(None)
    metadata: Dict[str, Any] | None = Field(None)

class AIResponse(BaseModel):
    response_type: Literal['new_lesson', 'active_lesson_returned', 'tutor_feedback', 'error']
    message_to_user: str
    content: Optional[Lesson] = None

# --- Modelos para Endpoints Diversos ---

class AnswerPayload(BaseModel):
    lesson_id: str
    unit_id: str
    student_response: str

class AnswerResponse(BaseModel):
    is_correct: bool
    correct_answer: str
    feedback: Dict[str, str]

class TutorMessage(BaseModel):
    id: int
    user_id: str # Mantido como string para simplicidade na serialização
    message_content: str
    status: str
    created_at: str

    class Config:
        from_attributes = True