# /app/schemas.py

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal

# --- Modelos de Dados de Conteúdo ---
# Estes modelos representam as estruturas de dados que vêm do banco de dados
# e são usados para compor as respostas da API.

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

# --- Modelos para a API de Interação ---
# Estes modelos definem os contratos de entrada e saída do nosso endpoint principal.

class UserIntent(BaseModel):
    """
    Representa a intenção do usuário, seja um clique de botão ou uma mensagem de chat.
    """
    type: Literal['button_click', 'chat_message']
    action_id: str | None = Field(None, description="Para 'button_click', action_id é obrigatório. Ex: 'generate_new_lesson'")
    text: str | None = Field(None, description="Para 'chat_message', text é obrigatório.")
    metadata: Dict[str, Any] | None = Field(None, description="Carrega contexto extra, como o ID da lição a ser completada.")

class AIResponse(BaseModel):
    """
    Representa a resposta estruturada do Tutor de IA para o frontend.
    """
    response_type: Literal[
        'new_lesson',
        'active_lesson_returned',
        'tutor_feedback',
        'error'
    ]
    message_to_user: str
    content: Lesson | None = Field(None, description="A 'carga útil' principal, como os dados de uma nova lição.")

# --- Modelos para Endpoints Legados e Novos ---
# Mantemos os modelos antigos para garantir que os endpoints existentes não quebrem
# durante a transição, e adicionamos novos para as novas funcionalidades.

class AnswerPayload(BaseModel):
    lesson_id: str
    unit_id: str
    student_response: str

class AnswerResponse(BaseModel):
    is_correct: bool
    correct_answer: str
    feedback: Dict[str, str]

class TutorMessage(BaseModel):
    """
    Representa uma única mensagem do tutor a ser exibida no frontend.
    """
    id: int
    message_content: str
    status: str
    created_at: str