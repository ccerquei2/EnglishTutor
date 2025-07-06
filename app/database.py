# /app/database.py

from supabase.client import Client, PostgrestAPIResponse
from typing import List, Dict, Optional, Any
import json
import os
import uuid

# --- Instância Singleton do Cliente Supabase ---
_supabase_client: Optional[Client] = None


def get_db() -> Client:
    """
    Cria e retorna uma instância singleton do cliente Supabase.
    Isso evita criar múltiplas conexões.
    """
    global _supabase_client
    if _supabase_client is None:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("Supabase URL e Key devem ser definidos nas variáveis de ambiente.")
        _supabase_client = Client(url, key)
    return _supabase_client


# --- FUNÇÃO CRÍTICA CORRIGIDA (VERSÃO FINAL E CORRETA) ---
def save_performance_record(supabase: Client, user_id: str, lesson_id: str, unit_id: str, is_correct: bool,
                            response_data: dict):
    """
    Salva o desempenho do aluno. Lida com lições da Jornada (lesson_id não existe na tabela lessons)
    e com lições do Modo Prática (lesson_id existe na tabela lessons).
    """
    try:
        final_lesson_id_for_db = None

        # Etapa 1: Verifica se o lesson_id recebido é um UUID válido.
        try:
            uuid_obj = uuid.UUID(lesson_id, version=4)
            potential_lesson_id = str(uuid_obj)

            # Etapa 2: Verifica se este UUID válido REALMENTE existe na tabela 'lessons'.
            # Esta consulta é a chave. Se não encontrar nada, o erro de FK não ocorrerá.
            lesson_check_res = supabase.table("lessons").select("id").eq("id",
                                                                         potential_lesson_id).maybe_single().execute()

            if lesson_check_res and hasattr(lesson_check_res, 'data') and lesson_check_res.data:
                # O ID existe! É uma lição do Modo Prática.
                final_lesson_id_for_db = potential_lesson_id
                # Tenta atualizar o status da lição de prática
                supabase.table("lessons").update({"status": "in_progress"}).eq("id", final_lesson_id_for_db).eq(
                    "status", "not_started").execute()
            else:
                # É um UUID válido, mas não está na tabela 'lessons'. Logo, é da Jornada.
                # O valor para o banco será NULL.
                print(f"Salvando desempenho para a Jornada Guiada (ID temporário: {lesson_id}).")

        except (ValueError, AttributeError):
            # Não é nem mesmo um UUID. Definitivamente é da Jornada.
            print(f"Salvando desempenho para a Jornada Guiada (ID não-UUID: {lesson_id}).")

        # Etapa 3: Insere o registro de desempenho.
        performance_data = {
            "user_id": user_id,
            "lesson_id": final_lesson_id_for_db,  # Será None para a jornada, ou um ID válido para a prática.
            "unit_id": unit_id,
            "is_correct": is_correct,
            "response_data": response_data
        }
        supabase.table("student_performance").insert(performance_data).execute()
        return True
    except Exception as e:
        print(f"!!! ERRO ao salvar desempenho: {e} !!!")
        return False


# --- FUNÇÕES DA JORNADA GUIADA (STUDY PLAN) ---
def update_student_lesson_progress(supabase: Client, user_id: str, module_id: str) -> bool:
    try:
        response = supabase.rpc('increment_lesson_progress', {'p_user_id': user_id, 'p_module_id': module_id}).execute()
        return response.data
    except Exception as e:
        print(f"Erro no RPC increment_lesson_progress: {e}")
        return False


def get_lesson_for_module(supabase: Client, user_id: str, module_id: str) -> Optional[Dict[str, Any]]:
    try:
        progress_res = supabase.table("student_progress").select("current_lesson_order").eq("user_id", user_id).eq(
            "module_id", module_id).maybe_single().execute()
        lesson_order = 1
        if progress_res and hasattr(progress_res, 'data') and progress_res.data:
            lesson_order = progress_res.data.get('current_lesson_order', 1)
        else:
            print(
                f"Nenhum progresso encontrado para o usuário {user_id} no módulo {module_id}. Iniciando e criando registro para lesson_order 1.")
            supabase.table("student_progress").insert(
                {"user_id": user_id, "module_id": module_id, "current_lesson_order": 1,
                 "status": "in_progress"}).execute()
        items_res = (
            supabase.table("module_items").select("*, learning_units(*)").eq("module_id", module_id).eq("lesson_order",
                                                                                                        lesson_order).order(
                "item_order", desc=False).execute())
        if not items_res.data:
            print(f"Nenhum item de lição encontrado para o módulo {module_id}, lição {lesson_order}.")
            return None
        lesson_items = [item['learning_units'] for item in items_res.data if item.get('learning_units')]
        lesson_title = items_res.data[0].get('lesson_title', f'Módulo de Estudo - Lição {lesson_order}')
        temp_lesson_id = str(uuid.uuid4())
        return {"lesson_id": temp_lesson_id, "title": lesson_title,
                "objective": f"Jornada de Aprendizagem - Lição {lesson_order}", "lesson_items": lesson_items,
                "module_id": module_id}
    except Exception as e:
        print(f"Erro ao buscar lição para o módulo: {e}")
        return None


def get_student_progress_summary(supabase: Client, user_id: str, level: str) -> Optional[Dict[str, Any]]:
    """
    Consulta e monta a visão completa da jornada de aprendizado de um aluno.
    VERSÃO FINAL: Retorna o status real do banco, sem adivinhar.
    """
    try:
        modules_res = supabase.table("modules").select("*").eq("level", level).eq("is_published", True).order(
            "module_order").execute()
        if not modules_res.data: return None
        all_modules = modules_res.data

        module_ids = [m['id'] for m in all_modules]
        progress_res = supabase.table("student_progress").select("*").eq("user_id", user_id).in_("module_id",
                                                                                                 module_ids).execute()
        student_progress_map = {p['module_id']: p for p in progress_res.data}

        items_res = supabase.table("module_items").select("module_id, lesson_order").execute()
        lessons_per_module = {}
        if items_res.data:
            for item in items_res.data:
                mod_id, lesson_order = item.get('module_id'), item.get('lesson_order')
                if mod_id and lesson_order:
                    if mod_id not in lessons_per_module: lessons_per_module[mod_id] = set()
                    lessons_per_module[mod_id].add(lesson_order)

        modules_summary = []
        for module in all_modules:
            module_id = module['id']
            progress = student_progress_map.get(module_id)

            # LÓGICA REFINADA: O status é o que está no banco, ou 'locked' por padrão.
            status = progress['status'] if progress else "locked"

            total_lessons = len(lessons_per_module.get(module_id, set()))
            completed_lessons = (progress['current_lesson_order'] - 1) if progress and progress.get(
                'current_lesson_order') else 0

            modules_summary.append({
                "module_id": module_id, "module_order": module['module_order'],
                "title": module['title'], "description": module['description'],
                "status": status, "progress": {"total_lessons": total_lessons, "completed_lessons": completed_lessons}
            })

        completed_modules_count = len([m for m in modules_summary if m['status'] == 'completed'])
        total_modules_count = len(all_modules)

        return {
            "overall_progress": {"completed_modules": completed_modules_count, "total_modules": total_modules_count,
                                 "percentage": int((
                                                               completed_modules_count / total_modules_count) * 100) if total_modules_count > 0 else 0},
            "modules": modules_summary
        }
    except Exception as e:
        print(f"Erro ao montar o resumo do progresso do aluno: {e}")
        return None


# --- FUNÇÕES DO MODO PRÁTICA (TUTOR INTERACT) ---
def get_active_lesson(supabase: Client, user_id: str) -> Optional[Dict]:
    try:
        lesson_response = supabase.table("lessons").select("*").eq("user_id", user_id).in_("status", ["not_started",
                                                                                                      "in_progress"]).maybe_single().execute()
        if not lesson_response or not lesson_response.data: return None
        lesson = lesson_response.data
        lesson_id = lesson.get('id')
        if not lesson_id: return None
        items_response = supabase.table("lesson_items").select("*, learning_units(*)").eq("lesson_id", lesson_id).order(
            "item_order", desc=False).execute()
        lesson_items = [item['learning_units'] for item in items_response.data if
                        'learning_units' in item and item['learning_units']] if items_response.data else []
        return {"lesson_id": lesson_id, "title": lesson.get('title'), "objective": lesson.get('objective'),
                "lesson_items": lesson_items}
    except Exception as e:
        print(f"!!! ERRO no Supabase ao buscar lição ativa: {e} !!!"); return None


def save_lesson(supabase: Client, user_id: str, title: str, objective: str, items: list) -> Optional[str]:
    try:
        lesson_data = {"user_id": user_id, "title": title, "objective": objective, "status": "not_started"}
        lesson_response: PostgrestAPIResponse = supabase.table("lessons").insert(lesson_data).execute()
        new_lesson_id = lesson_response.data[0]['id']
        lesson_items_to_insert = [{"lesson_id": new_lesson_id, "unit_id": item['id'], "item_order": i + 1} for i, item
                                  in enumerate(items)]
        if lesson_items_to_insert: supabase.table("lesson_items").insert(lesson_items_to_insert).execute()
        return new_lesson_id
    except Exception as e:
        print(f"!!! ERRO ao salvar a lição: {e} !!!"); return None


def update_lesson_status(supabase: Client, lesson_id: str, new_status: str) -> bool:
    try:
        supabase.table("lessons").update({"status": new_status}).eq("id", lesson_id).execute()
        return True
    except Exception as e:
        print(f"!!! ERRO no Supabase ao atualizar status da lição: {e} !!!"); return False


def mark_lesson_units_as_seen(supabase: Client, user_id: str, lesson_id: str):
    try:
        items_response = supabase.table("lesson_items").select("unit_id").eq("lesson_id", lesson_id).execute()
        if not items_response.data: return
        performance_records = [
            {"user_id": user_id, "lesson_id": lesson_id, "unit_id": item['unit_id'], "is_correct": True,
             "response_data": {"note": "Marked as seen upon lesson completion."}} for item in items_response.data]
        if performance_records: supabase.table("student_performance").insert(performance_records).execute()
    except Exception as e:
        print(f"!!! ERRO ao marcar unidades da lição como vistas: {e} !!!")


# --- FUNÇÕES GERAIS DE ACESSO A DADOS ---
def save_conversation_turn(supabase: Client, user_id: str, role: str, content: str) -> bool:
    try:
        supabase.table("conversation_history").insert({"user_id": user_id, "role": role, "content": content}).execute()
        return True
    except Exception as e:
        print(f"!!! ERRO no Supabase ao salvar turno da conversa: {e} !!!"); return False


def get_conversation_history(supabase: Client, user_id: str, limit: int = 10) -> List[Dict]:
    try:
        response = supabase.table("conversation_history").select("role, content").eq("user_id", user_id).order(
            "created_at", desc=True).limit(limit).execute()
        return list(reversed(response.data)) or []
    except Exception as e:
        print(f"!!! ERRO no Supabase ao buscar histórico da conversa: {e} !!!"); return []


def save_tutor_message(supabase: Client, user_id: str, message: str) -> bool:
    try:
        supabase.table("tutor_messages").insert({"user_id": user_id, "message_content": message}).execute()
        return True
    except Exception as e:
        print(f"!!! ERRO no Supabase ao salvar mensagem do tutor: {e} !!!"); return False


def get_unread_tutor_messages(supabase: Client, user_id: str) -> List[dict]:
    try:
        response = supabase.table("tutor_messages").select("*").eq("user_id", user_id).eq("status", "unread").order(
            "created_at", desc=True).execute()
        return response.data or []
    except Exception as e:
        print(f"!!! ERRO no Supabase ao buscar mensagens do tutor: {e} !!!"); return []


def mark_tutor_message_as_read(supabase: Client, message_id: int) -> bool:
    try:
        supabase.table("tutor_messages").update({"status": "read"}).eq("id", message_id).execute()
        return True
    except Exception as e:
        print(f"!!! ERRO no Supabase ao marcar mensagem como lida: {e} !!!"); return False


def get_all_topics_for_level(supabase: Client, level: str) -> List[str]:
    try:
        response = supabase.table("learning_units").select("metadata->topic").eq("metadata->>level", level).execute()
        if not response.data: return []
        all_topics = set()
        for item in response.data:
            topics = item.get('topic')
            if isinstance(topics, list):
                for topic in topics: all_topics.add(topic)
        return list(all_topics)
    except Exception as e:
        print(f"!!! ERRO ao buscar todos os tópicos para o nível: {e} !!!"); return []


def get_learning_units_by_topic(supabase: Client, topic: str, level: str, unit_types: List[str],
                                count: int = 15) -> list:
    try:
        json_filter_value = json.dumps([topic])
        query = supabase.table("learning_units").select("*").eq("metadata->>level", level).contains("metadata->topic",
                                                                                                    json_filter_value).in_(
            "type", unit_types).limit(count)
        response = query.execute()
        return response.data or []
    except Exception as e:
        print(f"!!! ERRO ao buscar unidades por tópico e tipo: {e} !!!"); return []


def get_units_by_dependency(supabase: Client, dependency_id: str, level: str) -> list:
    try:
        dependency_json = json.dumps([dependency_id])
        response = supabase.table("learning_units").select("*").eq("metadata->>level", level).contains(
            "metadata->dependencies", dependency_json).execute()
        return response.data or []
    except Exception as e:
        print(f"!!! ERRO ao buscar unidades por dependência: {e} !!!"); return []


def get_recently_seen_units(supabase: Client, user_id: str, days_ago: int = 7) -> set:
    try:
        response = supabase.rpc('get_recently_seen_unit_ids', {'p_user_id': user_id, 'p_days_ago': days_ago}).execute()
        return {item['unit_id'] for item in response.data} if response.data else set()
    except Exception as e:
        print(f"!!! ERRO no RPC 'get_recently_seen_unit_ids': {e} !!!"); return []


def get_learning_units_by_similarity(supabase: Client, embedding: list, level: str, count: int = 15) -> list:
    try:
        response = supabase.rpc('match_learning_units',
                                {'query_embedding': embedding, 'match_count': count, 'p_level': level}).execute()
        return response.data or []
    except Exception as e:
        print(f"!!! ERRO no RPC 'match_learning_units': {e} !!!"); return []


def get_student_mastery_summary(supabase: Client, user_id: str) -> dict:
    weak_topics, strong_topics = [], []
    try:
        response = supabase.table("student_topic_mastery").select("*").eq("user_id", user_id).execute()
        if response.data:
            for row in response.data:
                if row.get('errors_in_last_5', 0) > row.get('successes_in_last_5', 0):
                    weak_topics.append(row['topic'])
                elif row.get('successful_streak_in_last_3', 0) >= 3:
                    strong_topics.append(row['topic'])
        return {"weak_topics": weak_topics, "strong_topics": strong_topics}
    except Exception as e:
        print(f"!!! ERRO ao buscar maestria: {e} !!!"); return {"weak_topics": [], "strong_topics": []}


def get_learning_unit_by_id(supabase: Client, unit_id: str) -> Optional[Dict]:
    try:
        response: PostgrestAPIResponse = supabase.table("learning_units").select("*").eq("id",
                                                                                         unit_id).single().execute()
        return response.data
    except Exception as e:
        print(f"!!! ERRO ao buscar unidade por ID: {e} !!!"); return None
