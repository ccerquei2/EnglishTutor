# /app/study_plan.py

from fastapi import APIRouter, Depends, HTTPException, Body
from supabase.client import Client
from typing import Dict, Any, Optional

from .dependencies import get_current_user
from .database import get_db, get_student_progress_summary, get_lesson_for_module, update_student_lesson_progress
from .schemas import Lesson

router = APIRouter(
    prefix="/api/v1/study-plan",
    tags=["Study Plan"],
)

@router.get("/progress", response_model=Dict[str, Any])
def get_user_study_plan_progress(user_id: str = Depends(get_current_user), supabase: Client = Depends(get_db)):
    try:
        progress_summary = get_student_progress_summary(supabase, user_id, level="A1")
        if not progress_summary:
            return {"overall_progress": {"completed_modules": 0, "total_modules": 0, "percentage": 0}, "modules": []}
        return progress_summary
    except Exception as e:
        print(f"!!! ERRO CRÍTICO ao buscar progresso do plano de estudos: {e} !!!")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/start-lesson", response_model=Lesson)
def start_next_study_plan_lesson(module_id: str = Body(..., embed=True), user_id: str = Depends(get_current_user), supabase: Client = Depends(get_db)):
    try:
        lesson_data = get_lesson_for_module(supabase, user_id, module_id)
        if not lesson_data:
            raise HTTPException(status_code=404, detail="Nenhuma lição disponível ou o módulo já foi concluído.")
        return lesson_data
    except Exception as e:
        print(f"!!! ERRO ao iniciar a lição do plano de estudos: {e} !!!")
        raise HTTPException(status_code=500, detail=str(e))

# --- NOVO ENDPOINT PARA COMPLETAR UMA LIÇÃO ---
@router.post("/complete-lesson", status_code=204)
def complete_study_plan_lesson(module_id: str = Body(..., embed=True), user_id: str = Depends(get_current_user), supabase: Client = Depends(get_db)):
    """
    Atualiza o progresso do aluno, incrementando a 'current_lesson_order'.
    """
    try:
        success = update_student_lesson_progress(supabase, user_id, module_id)
        if not success:
            raise HTTPException(status_code=404, detail="Progresso do aluno não encontrado ou já está no máximo.")
        # Retorna 204 No Content em caso de sucesso
        return
    except Exception as e:
        print(f"!!! ERRO ao completar lição do plano de estudos: {e} !!!")
        raise HTTPException(status_code=500, detail=str(e))