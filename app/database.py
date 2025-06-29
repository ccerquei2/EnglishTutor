# /app/database.py

from supabase.client import Client, PostgrestAPIResponse
from typing import List, Dict
import random
import json

# --- FUNÇÕES PARA HISTÓRICO DE CONVERSA ---
# ... (código existente sem alterações) ...

def save_conversation_turn(supabase: Client, user_id: str, role: str, content: str) -> bool:
    try:
        supabase.table("conversation_history").insert({ "user_id": user_id, "role": role, "content": content }).execute()
        return True
    except Exception as e:
        print(f"!!! ERRO no Supabase ao salvar turno da conversa: {e} !!!")
        return False

def get_conversation_history(supabase: Client, user_id: str, limit: int = 10) -> List[Dict]:
    try:
        response = supabase.table("conversation_history").select("role, content").eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute()
        return list(reversed(response.data)) or []
    except Exception as e:
        print(f"!!! ERRO no Supabase ao buscar histórico da conversa: {e} !!!")
        return []

# --- FUNÇÕES PARA MENSAGENS DO TUTOR (PROATIVAS) ---
# ... (código existente sem alterações) ...

def save_tutor_message(supabase: Client, user_id: str, message: str) -> bool:
    try:
        supabase.table("tutor_messages").insert({ "user_id": user_id, "message_content": message }).execute()
        return True
    except Exception as e:
        print(f"!!! ERRO no Supabase ao salvar mensagem do tutor: {e} !!!")
        return False

def get_unread_tutor_messages(supabase: Client, user_id: str) -> List[dict]:
    try:
        response = supabase.table("tutor_messages").select("*").eq("user_id", user_id).eq("status", "unread").order("created_at", desc=True).execute()
        return response.data or []
    except Exception as e:
        print(f"!!! ERRO no Supabase ao buscar mensagens do tutor: {e} !!!")
        return []

def mark_tutor_message_as_read(supabase: Client, message_id: int) -> bool:
    try:
        supabase.table("tutor_messages").update({"status": "read"}).eq("id", message_id).execute()
        return True
    except Exception as e:
        print(f"!!! ERRO no Supabase ao marcar mensagem como lida: {e} !!!")
        return False

# --- FUNÇÕES DE DADOS DE APRENDIZADO ---
# ... (código existente sem alterações, exceto a nova função abaixo) ...
def get_learning_units_by_topic(supabase: Client, topic: str, level: str, count: int = 15) -> list:
    try:
        json_filter_value = json.dumps([topic])
        response = (supabase.table("learning_units").select("*").eq("metadata->>level", level).contains("metadata->topic", json_filter_value).limit(count).execute())
        return response.data or []
    except Exception as e:
        print(f"!!! ERRO ao buscar unidades por tópico: {e} !!!")
        return []

# ### NOVA FUNÇÃO PARA MARCAR UNIDADES COMO VISTAS ###
def mark_lesson_units_as_seen(supabase: Client, user_id: str, lesson_id: str):
    """
    Busca todas as unidades de uma lição e cria um registro de desempenho para cada uma,
    marcando-as efetivamente como 'vistas' para o filtro de repetição.
    """
    print(f"--- [DATABASE] Marcando unidades da lição {lesson_id} como vistas... ---")
    try:
        # 1. Encontra todos os unit_ids para a lição
        items_response = supabase.table("lesson_items").select("unit_id").eq("lesson_id", lesson_id).execute()
        if not items_response.data:
            print("--- [DATABASE] Nenhuma unidade encontrada para esta lição.")
            return

        # 2. Prepara os registros para inserção em lote
        performance_records = [
            {
                "user_id": user_id,
                "lesson_id": lesson_id,
                "unit_id": item['unit_id'],
                "is_correct": True,  # Assumimos 'True' para simplificar, pois a lição foi completada
                "response_data": {"note": "Marked as seen upon lesson completion."}
            }
            for item in items_response.data
        ]

        # 3. Insere todos os registros de uma vez
        if performance_records:
            supabase.table("student_performance").insert(performance_records).execute()
            print(f"--- [DATABASE] {len(performance_records)} unidades marcadas como vistas.")

    except Exception as e:
        print(f"!!! ERRO ao marcar unidades da lição como vistas: {e} !!!")

def get_recently_seen_units(supabase: Client, user_id: str, days_ago: int = 7) -> set:
    try:
        # O RPC usa a tabela student_performance, que agora será preenchida.
        response = supabase.rpc('get_recently_seen_unit_ids', {'p_user_id': user_id, 'p_days_ago': days_ago}).execute()
        if not response.data:
            return set()
        return {item['unit_id'] for item in response.data}
    except Exception as e:
        print(f"!!! ERRO no RPC 'get_recently_seen_unit_ids': {e} !!!")
        return set()

# ... (restante do código do database.py) ...
def get_active_lesson(supabase: Client, user_id: str) -> dict | None:
    try:
        response = supabase.table("lessons").select("*").eq("user_id", user_id).in_("status", ["not_started", "in_progress"]).maybe_single().execute()
        if not response or not hasattr(response, 'data') or not response.data:
            return None
        lesson = response.data
        items_response = supabase.table("lesson_items").select("*, learning_units(*)").eq("lesson_id", lesson['id']).order("item_order", desc=False).execute()
        lesson_items = [item['learning_units'] for item in items_response.data if 'learning_units' in item and item['learning_units']]
        return {"lesson_id": lesson['id'], "title": lesson['title'], "objective": lesson['objective'], "lesson_items": lesson_items}
    except Exception as e:
        print(f"!!! ERRO no Supabase ao buscar lição ativa: {e} !!!")
        return None

def update_lesson_status(supabase: Client, lesson_id: str, new_status: str) -> bool:
    try:
        supabase.table("lessons").update({"status": new_status}).eq("id", lesson_id).execute()
        return True
    except Exception as e:
        print(f"!!! ERRO no Supabase ao atualizar status da lição: {e} !!!")
        return False

# ... (outras funções do database.py permanecem iguais)
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
        print(f"!!! ERRO ao buscar maestria: {e} !!!")
        return {"weak_topics": [], "strong_topics": []}

def get_learning_units_by_similarity(supabase: Client, embedding: list, level: str, count: int = 15) -> list:
    try:
        response = supabase.rpc('match_learning_units', {'query_embedding': embedding, 'match_count': count, 'p_level': level}).execute()
        return response.data or []
    except Exception as e:
        print(f"!!! ERRO no RPC 'match_learning_units': {e} !!!")
        return []

def get_learning_unit_by_id(supabase: Client, unit_id: str) -> dict | None:
    try:
        response: PostgrestAPIResponse = supabase.table("learning_units").select("*").eq("id", unit_id).single().execute()
        return response.data
    except Exception as e:
        print(f"!!! ERRO ao buscar unidade por ID: {e} !!!")
        return None

def save_lesson(supabase: Client, user_id: str, title: str, objective: str, items: list) -> str | None:
    try:
        lesson_data = {"user_id": user_id, "title": title, "objective": objective, "status": "not_started"}
        lesson_response: PostgrestAPIResponse = supabase.table("lessons").insert(lesson_data).execute()
        new_lesson_id = lesson_response.data[0]['id']
        lesson_items_to_insert = [{"lesson_id": new_lesson_id, "unit_id": item['id'], "item_order": i + 1} for i, item in enumerate(items)]
        if lesson_items_to_insert:
            supabase.table("lesson_items").insert(lesson_items_to_insert).execute()
        return new_lesson_id
    except Exception as e:
        print(f"!!! ERRO ao salvar a lição: {e} !!!")
        return None

def save_performance_record(supabase: Client, user_id: str, lesson_id: str, unit_id: str, is_correct: bool, response_data: dict):
    try:
        supabase.table("lessons").update({"status": "in_progress"}).eq("id", lesson_id).eq("status", "not_started").execute()
        performance_data = {"user_id": user_id, "lesson_id": lesson_id, "unit_id": unit_id, "is_correct": is_correct, "response_data": response_data}
        supabase.table("student_performance").insert(performance_data).execute()
        return True
    except Exception as e:
        print(f"!!! ERRO ao salvar desempenho: {e} !!!")
        return False