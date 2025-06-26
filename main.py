# /main.py

from dotenv import load_dotenv
load_dotenv()

import os
from fastapi import FastAPI, HTTPException, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from supabase.client import Client, create_client
from pydantic import BaseModel
from typing import List, Dict, Any

from app.agents import orchestrate_lesson_creation, process_student_answer
from app.dependencies import get_current_user
# Importa as novas funções do database
from app.database import get_active_lesson, update_lesson_status

# --- CONFIGURAÇÃO DA APLICAÇÃO FASTAPI ---
# CORREÇÃO APLICADA AQUI: Removido o '...' extra
app = FastAPI(
    title="EnglishTutor AI API",
    description="API para criar lições e processar o desempenho dos alunos.",
    version="0.3.0"
)

# Configuração do CORS (Cross-Origin Resource Sharing)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIGURAÇÃO DO CLIENTE SUPABASE ---
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
if not supabase_url or not supabase_key:
    raise ValueError("SUPABASE_URL ou SUPABASE_SERVICE_KEY não encontradas. Verifique seu arquivo .env")
supabase: Client = create_client(supabase_url, supabase_key)

# --- MODELOS DE DADOS (PYDANTIC) ---
class LearningUnit(BaseModel):
    id: str
    unit_code: str
    type: str
    content: Dict[str, Any]
    metadata: Dict[str, Any]

class LessonResponse(BaseModel):
    lesson_id: str
    title: str
    objective: str
    suggested_topics: str
    lesson_items: List[LearningUnit]

class AnswerPayload(BaseModel):
    lesson_id: str
    unit_id: str
    student_response: str

class AnswerResponse(BaseModel):
    is_correct: bool
    correct_answer: str
    feedback: Dict[str, str]

# --- ENDPOINTS DA API (ROTAS) ---
@app.get("/")
def read_root():
    return {"message": "Bem-vindo à API do EnglishTutor! Conectado ao Supabase."}

@app.post("/api/v1/lessons/new", response_model=LessonResponse)
def get_or_create_lesson(
    user_id: str = Depends(get_current_user),
    student_request: str = Body("I want to have a general practice lesson.", embed=True)
):
    """
    Obtém a lição ativa do usuário ou cria uma nova se nenhuma estiver ativa.
    """
    active_lesson = get_active_lesson(supabase=supabase, user_id=user_id)
    if active_lesson:
        print(f"--- [MAIN] Retornando lição ativa existente para o usuário {user_id}. ---")
        return active_lesson

    print(f"--- [MAIN] Nenhuma lição ativa encontrada. Criando uma nova para o usuário {user_id}. ---")
    new_lesson = orchestrate_lesson_creation(
        supabase=supabase,
        user_id=user_id,
        student_request=student_request
    )
    if not new_lesson:
        raise HTTPException(
            status_code=500,
            detail="Ocorreu um erro interno e não foi possível criar a lição."
        )
    return new_lesson

@app.post("/api/v1/lessons/{lesson_id}/complete", status_code=204)
def complete_lesson_endpoint(lesson_id: str, user_id: str = Depends(get_current_user)):
    """Marca uma lição específica como 'completed'."""
    # Validação futura: verificar se o lesson_id pertence ao user_id
    success = update_lesson_status(supabase=supabase, lesson_id=lesson_id, new_status="completed")
    if not success:
        raise HTTPException(status_code=500, detail="Não foi possível atualizar o status da lição.")
    return

@app.post("/api/v1/lessons/answer", response_model=AnswerResponse)
def submit_answer(payload: AnswerPayload, user_id: str = Depends(get_current_user)):
    """Recebe e registra a resposta de um aluno para um exercício."""
    result = process_student_answer(
        supabase=supabase,
        user_id=user_id,
        lesson_id=payload.lesson_id,
        unit_id=payload.unit_id,
        student_response=payload.student_response
    )
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result