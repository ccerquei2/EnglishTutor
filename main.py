# /EnglishTutor/main.py

# --- Bloco de Configuração Inicial ---
# É crucial que load_dotenv() seja chamado no topo, antes de qualquer
# importação de outros módulos da sua aplicação que dependam de variáveis de ambiente.
from dotenv import load_dotenv

load_dotenv()
# --- Fim do Bloco de Configuração Inicial ---

import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from supabase.client import Client, create_client
from pydantic import BaseModel
from typing import List, Dict, Any

# Agora que as variáveis de ambiente foram carregadas, estas importações funcionarão
from app.agents import orchestrate_lesson_creation, process_student_answer
from app.dependencies import get_current_user

# --- CONFIGURAÇÃO DA APLICAÇÃO FASTAPI ---
app = FastAPI(
    title="EnglishTutor AI API",
    description="API para criar lições e processar o desempenho dos alunos.",
    version="0.3.0"
)

# Configuração do CORS (Cross-Origin Resource Sharing)
# Permite que o frontend (rodando em outra porta) se comunique com este backend
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos os métodos (POST, GET, etc)
    allow_headers=["*"],  # Permite todos os cabeçalhos (incluindo Authorization)
)

# --- CONFIGURAÇÃO DO CLIENTE SUPABASE ---
supabase_url = os.getenv("SUPABASE_URL")
# No backend, sempre usamos a chave de SERVIÇO, que é secreta e tem privilégios de admin.
supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

if not supabase_url or not supabase_key:
    raise ValueError("SUPABASE_URL ou SUPABASE_SERVICE_KEY não encontradas. Verifique seu arquivo .env")

# Cria a instância do cliente Supabase que será usada nas rotas
supabase: Client = create_client(supabase_url, supabase_key)


# --- MODELOS DE DADOS (PYDANTIC) ---
# Define a estrutura dos dados que a API espera receber e envia

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
    """Endpoint raiz para verificar se a API está online."""
    return {"message": "Bem-vindo à API do EnglishTutor! Conectado ao Supabase."}


@app.post("/api/v1/lessons/new", response_model=LessonResponse)
def create_lesson_real(user_id: str = Depends(get_current_user)):
    """
    Cria e salva uma nova lição personalizada para o usuário autenticado.
    O ID do usuário é extraído automaticamente do token JWT enviado pelo frontend.
    """
    # No futuro, o 'student_request' pode vir do corpo da requisição do frontend.
    student_request = "I want to have a general practice lesson."

    result = orchestrate_lesson_creation(
        supabase=supabase,
        user_id=user_id,
        student_request=student_request
    )

    if not result:
        raise HTTPException(
            status_code=500,
            detail="Ocorreu um erro interno e não foi possível criar a lição."
        )

    return result


@app.post("/api/v1/lessons/answer", response_model=AnswerResponse)
def submit_answer(payload: AnswerPayload, user_id: str = Depends(get_current_user)):
    """
    Recebe, verifica e registra a resposta de um aluno para um exercício.
    O ID do usuário é extraído automaticamente do token JWT.
    """
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
