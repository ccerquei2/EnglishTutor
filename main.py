# /main.py

from dotenv import load_dotenv

load_dotenv()

import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from supabase.client import Client, create_client
from typing import List

# Importações de negócio e esquemas
from app.agents import tutor_orchestrator, original_process_student_answer
from app.dependencies import get_current_user
from app.schemas import UserIntent, AIResponse, AnswerPayload, AnswerResponse, TutorMessage

# --- CONFIGURAÇÃO DA APLICAÇÃO ---
app = FastAPI(
    title="EnglishTutor AI API v2.0",
    description="API com Tutor Híbrido e Proativo.",
    version="2.0.0"
)
origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"],
                   allow_headers=["*"])

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
if not supabase_url or not supabase_key:
    raise ValueError("SUPABASE_URL ou SUPABASE_SERVICE_KEY não encontradas.")
supabase: Client = create_client(supabase_url, supabase_key)


# --- ENDPOINTS DA API (v2.0) ---

@app.get("/")
def read_root():
    return {"message": "Bem-vindo à API do EnglishTutor v2.0 (Híbrida)!"}


@app.post("/api/v1/tutor/interact", response_model=AIResponse)
def interact_with_tutor(intent: UserIntent, user_id: str = Depends(get_current_user)):
    """Endpoint único para todas as interações diretas com o Tutor de IA."""
    try:
        return tutor_orchestrator(supabase=supabase, user_id=user_id, intent=intent)
    except Exception as e:
        # Restaurado para o log de erro limpo original
        print(f"!!! ERRO CRÍTICO no orquestrador: {e} !!!")
        raise HTTPException(status_code=500, detail="Ocorreu um erro interno no tutor.")


@app.get("/api/v1/tutor/messages", response_model=List[TutorMessage])
def fetch_tutor_messages(user_id: str = Depends(get_current_user)):
    """Busca mensagens não lidas do tutor para o usuário."""
    from app.database import get_unread_tutor_messages
    messages = get_unread_tutor_messages(supabase=supabase, user_id=user_id)
    return [TutorMessage(id=m['id'], message_content=m['message_content'], status=m['status'],
                         created_at=str(m['created_at'])) for m in messages]


@app.post("/api/v1/tutor/messages/{message_id}/read", status_code=204)
def mark_message_read(message_id: int, user_id: str = Depends(get_current_user)):
    """Marca uma mensagem do tutor como lida."""
    from app.database import mark_tutor_message_as_read
    mark_tutor_message_as_read(supabase=supabase, message_id=message_id)
    return


# --- ENDPOINTS LEGADOS (Para não quebrar o frontend atual) ---

@app.post("/api/v1/lessons/new", deprecated=True, include_in_schema=False)
def get_or_create_lesson(user_id: str = Depends(get_current_user)):
    """Endpoint legado para gerar lição. Será substituído por /interact."""
    intent = UserIntent(type='button_click', action_id='generate_new_lesson')
    response = tutor_orchestrator(supabase=supabase, user_id=user_id, intent=intent)

    if response.response_type in ['new_lesson', 'active_lesson_returned']:
        return response.content.dict()

    raise HTTPException(status_code=500, detail=response.message_to_user)


@app.post("/api/v1/lessons/{lesson_id}/complete", deprecated=True, include_in_schema=False, status_code=204)
def complete_lesson_endpoint(lesson_id: str, user_id: str = Depends(get_current_user)):
    """Endpoint legado para completar lição. Será substituído por /interact."""
    intent = UserIntent(type='button_click', action_id='complete_current_lesson', metadata={'lesson_id': lesson_id})
    tutor_orchestrator(supabase=supabase, user_id=user_id, intent=intent)
    return


@app.post("/api/v1/lessons/answer", response_model=AnswerResponse, deprecated=True, include_in_schema=False)
def submit_answer(payload: AnswerPayload, user_id: str = Depends(get_current_user)):
    """Endpoint legado para submeter resposta."""
    result = original_process_student_answer(supabase, user_id, payload.lesson_id, payload.unit_id,
                                             payload.student_response)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result