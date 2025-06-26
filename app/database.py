# /app/database.py

from supabase.client import Client, PostgrestAPIResponse
import random


# --- NOVA FUNÇÃO ---
def get_recently_seen_units(supabase: Client, user_id: str, days_ago: int = 7) -> set:
    """
    Busca os IDs das unidades que um usuário viu recentemente usando a função RPC.
    Retorna um conjunto (set) para buscas rápidas.
    """
    print(f"--- [DATABASE] Buscando unidades vistas nos últimos {days_ago} dias para o user_id: {user_id} ---")
    try:
        response = supabase.rpc('get_recently_seen_unit_ids',
                                {'p_user_id': user_id, 'p_days_ago': days_ago}).execute()

        if not response.data:
            return set()

        # Extrai os IDs e os retorna como um conjunto
        seen_ids = {item['unit_id'] for item in response.data}
        print(f"--- [DATABASE] Encontrados {len(seen_ids)} IDs de unidades vistas recentemente. ---")
        return seen_ids
    except Exception as e:
        print(f"!!! ERRO no Supabase ao chamar RPC 'get_recently_seen_unit_ids': {e} !!!")
        return set()


# --- FUNÇÕES EXISTENTES ---
# ... (todo o resto do arquivo, como get_active_lesson, get_student_mastery_summary, etc. permanece igual) ...

def get_active_lesson(supabase: Client, user_id: str) -> dict | None:
    # ... (sem alterações)
    print(f"--- [DATABASE] Verificando lição ativa para user_id: {user_id} ---")
    try:
        response = supabase.table("lessons").select("*").eq("user_id", user_id).in_("status", ["not_started",
                                                                                               "in_progress"]).maybe_single().execute()
        if not response.data:
            print("--- [DATABASE] Nenhuma lição ativa encontrada. ---")
            return None
        lesson = response.data
        print(f"--- [DATABASE] Lição ativa encontrada com ID: {lesson['id']} e status: {lesson['status']} ---")
        items_response = supabase.table("lesson_items").select("*, learning_units(*)").eq("lesson_id",
                                                                                          lesson['id']).order(
            "item_order", desc=False).execute()
        lesson_items = [item['learning_units'] for item in items_response.data if
                        'learning_units' in item and item['learning_units']]
        return {
            "lesson_id": lesson['id'],
            "title": lesson['title'],
            "objective": lesson['objective'],
            "suggested_topics": lesson.get('objective', ''),
            "lesson_items": lesson_items
        }
    except Exception as e:
        print(f"!!! ERRO no Supabase ao buscar lição ativa: {e} !!!")
        return None


def update_lesson_status(supabase: Client, lesson_id: str, new_status: str) -> bool:
    # ... (sem alterações)
    print(f"--- [DATABASE] Atualizando status da lição {lesson_id} para '{new_status}' ---")
    try:
        supabase.table("lessons").update({"status": new_status}).eq("id", lesson_id).execute()
        print(f"--- [DATABASE] Status da lição {lesson_id} atualizado com sucesso. ---")
        return True
    except Exception as e:
        print(f"!!! ERRO no Supabase ao atualizar status da lição: {e} !!!")
        return False


def get_student_mastery_summary(supabase: Client, user_id: str) -> dict:
    # ... (sem alterações)
    print(f"--- [DATABASE] Buscando resumo de maestria para o user_id: {user_id} ---")
    try:
        response = supabase.table("student_topic_mastery").select("*").eq("user_id", user_id).execute()
        weak_topics, strong_topics = [], []
        if response.data:
            for row in response.data:
                if row['errors_in_last_5'] > row['successes_in_last_5']:
                    weak_topics.append(row['topic'])
                elif row['successful_streak_in_last_3'] == 3:
                    strong_topics.append(row['topic'])
        print(f"--- [DATABASE] Pontos fracos: {weak_topics} ---")
        print(f"--- [DATABASE] Pontos fortes: {strong_topics} ---")
        return {"weak_topics": weak_topics, "strong_topics": strong_topics}
    except Exception as e:
        print(f"!!! ERRO ao buscar maestria: {e} !!!")
        return {"weak_topics": [], "strong_topics": []}


def get_learning_units_by_similarity(supabase: Client, embedding: list, level: str, count: int = 15) -> list:
    # ... (sem alterações)
    print(f"--- [DATABASE] Buscando os {count} resultados mais similares para o nível {level}... ---")
    try:
        response = supabase.rpc('match_learning_units',
                                {'query_embedding': embedding, 'match_count': count, 'p_level': level}).execute()
        return response.data or []
    except Exception as e:
        print(f"!!! ERRO no RPC: {e} !!!")
        return []


def get_learning_unit_by_id(supabase: Client, unit_id: str) -> dict | None:
    # ... (sem alterações)
    print(f"--- [DATABASE] Buscando unidade com ID: {unit_id} ---")
    try:
        response: PostgrestAPIResponse = supabase.table("learning_units").select("*").eq("id",
                                                                                         unit_id).single().execute()
        return response.data
    except Exception as e:
        print(f"!!! ERRO ao buscar unidade por ID: {e} !!!")
        return None


def save_lesson(supabase: Client, user_id: str, title: str, objective: str, items: list) -> str | None:
    # ... (sem alterações)
    print(f"--- [DATABASE] Salvando lição para user_id: {user_id} ---")
    try:
        lesson_data = {"user_id": user_id, "title": title, "objective": objective, "status": "not_started"}
        lesson_response: PostgrestAPIResponse = supabase.table("lessons").insert(lesson_data).execute()
        new_lesson_id = lesson_response.data[0]['id']
        lesson_items_to_insert = [{"lesson_id": new_lesson_id, "unit_id": item['id'], "item_order": i + 1} for i, item
                                  in enumerate(items)]
        if lesson_items_to_insert:
            supabase.table("lesson_items").insert(lesson_items_to_insert).execute()
        return new_lesson_id
    except Exception as e:
        print(f"!!! ERRO ao salvar a lição: {e} !!!")
        return None


def save_performance_record(supabase: Client, user_id: str, lesson_id: str, unit_id: str, is_correct: bool,
                            response_data: dict):
    # ... (sem alterações)
    print(f"--- [DATABASE] Salvando desempenho para user_id: {user_id}, unit_id: {unit_id} ---")
    try:
        supabase.table("lessons").update({"status": "in_progress"}).eq("id", lesson_id).eq("status",
                                                                                           "not_started").execute()
        performance_data = {"user_id": user_id, "lesson_id": lesson_id, "unit_id": unit_id, "is_correct": is_correct,
                            "response_data": response_data}
        supabase.table("student_performance").insert(performance_data).execute()
        return True
    except Exception as e:
        print(f"!!! ERRO ao salvar desempenho: {e} !!!")
        return False