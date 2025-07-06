# /main.py

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from typing import List

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Importa os roteadores e funções dos outros arquivos
from app.agents import tutor_orchestrator, original_process_student_answer
from app.schemas import UserIntent, AIResponse, AnswerPayload, AnswerResponse, TutorMessage
from app.dependencies import get_current_user
from app.database import get_db, get_unread_tutor_messages
from app.study_plan import router as study_plan_router

app = FastAPI(
    title="EnglishTutor API",
    description="API para a plataforma de aprendizado de inglês EnglishTutor.",
    version="1.0.0"
)

# Configuração do CORS para permitir que o frontend se comunique com a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Em produção, restrinja para o domínio do seu frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclui os endpoints do Plano de Estudos e outros
app.include_router(study_plan_router)

# --- ENDPOINTS PRINCIPAIS ---

@app.post("/api/v1/tutor/interact", response_model=AIResponse)
def interact_with_tutor(intent: UserIntent, user_id: str = Depends(get_current_user)):
    """ Endpoint unificado para interação com o tutor de IA (Modo Prática). """
    supabase = get_db()
    return tutor_orchestrator(supabase, user_id, intent)

@app.post("/api/v1/lessons/answer", response_model=AnswerResponse)
def process_answer(payload: AnswerPayload, user_id: str = Depends(get_current_user)):
    """ Processa a resposta de um aluno a um exercício e salva o desempenho. """
    supabase = get_db()
    result = original_process_student_answer(
        supabase=supabase, user_id=user_id, lesson_id=payload.lesson_id,
        unit_id=payload.unit_id, student_response=payload.student_response
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

# --- NOVO ENDPOINT QUE ESTAVA FALTANDO ---
@app.get("/api/v1/tutor/messages", response_model=List[TutorMessage])
def get_tutor_messages(user_id: str = Depends(get_current_user)):
    """ Busca as mensagens não lidas do tutor para o usuário logado. """
    supabase = get_db()
    messages = get_unread_tutor_messages(supabase, user_id)
    return messages


@app.get("/")
def read_root():
    return {"message": "Welcome to EnglishTutor API v1"}