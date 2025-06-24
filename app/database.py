# app/database.py

from supabase.client import Client, PostgrestAPIResponse
import random


# --- FUNÇÕES DE LEITURA (MODIFICADA) ---

def get_student_mastery_summary(supabase: Client, user_id: str) -> dict:
    """
    Busca um resumo de maestria do aluno, identificando pontos fortes e fracos
    com base nas últimas interações, não em datas.
    """
    print(f"--- [DATABASE] Buscando resumo de maestria para o user_id: {user_id} ---")
    weak_topics = []
    strong_topics = []
    try:
        # Usamos a nova VIEW 'student_topic_mastery'
        response = supabase.table("student_topic_mastery").select("*").eq("user_id", user_id).execute()

        if response.data:
            for row in response.data:
                # Lógica para definir o que é um ponto fraco ou forte
                # Fraco se errou mais do que acertou nas últimas 5 tentativas
                if row['errors_in_last_5'] > row['successes_in_last_5']:
                    weak_topics.append(row['topic'])
                # Forte se as últimas 3 tentativas foram todas corretas
                elif row['successful_streak_in_last_3'] == 3:
                    strong_topics.append(row['topic'])

        print(f"--- [DATABASE] Pontos fracos (baseado em atividade): {weak_topics} ---")
        print(f"--- [DATABASE] Pontos fortes (baseado em atividade): {strong_topics} ---")

        return {"weak_topics": weak_topics, "strong_topics": strong_topics}

    except Exception as e:
        print(f"!!! ERRO no Supabase ao buscar maestria (verifique a VIEW 'student_topic_mastery'): {e} !!!")
        return {"weak_topics": [], "strong_topics": []}


# ... (o resto do arquivo `database.py` permanece o mesmo, então vou omitir para brevidade) ...
# ... get_learning_units_by_similarity, get_learning_unit_by_id, save_lesson, save_performance_record ...
# Você não precisa mudar as outras funções.

def get_learning_units_by_similarity(supabase: Client, embedding: list, level: str, count: int = 15) -> list:
    print(f"--- [DATABASE] Buscando os {count} resultados mais similares para o nível {level}... ---")
    try:
        response = supabase.rpc('match_learning_units',
                                {'query_embedding': embedding, 'match_count': count, 'p_level': level}).execute()
        if not response.data:
            print("--- [DATABASE] Nenhuma unidade encontrada. O banco pode estar vazio.")
            return []
        return response.data
    except Exception as e:
        print(f"!!! ERRO no Supabase ao chamar RPC: {e} !!!")
        return []


def get_learning_unit_by_id(supabase: Client, unit_id: str) -> dict | None:
    print(f"--- [DATABASE] Buscando unidade com ID: {unit_id} ---")
    try:
        response: PostgrestAPIResponse = supabase.table("learning_units").select("*").eq("id",
                                                                                         unit_id).single().execute()
        return response.data
    except Exception as e:
        print(f"!!! ERRO no Supabase ao buscar unidade por ID: {e} !!!")
        return None


def save_lesson(supabase: Client, user_id: str, title: str, objective: str, items: list) -> str | None:
    print(f"--- [DATABASE] Salvando lição para user_id: {user_id} ---")
    try:
        lesson_data = {"user_id": user_id, "title": title, "objective": objective, "status": "not_started"}
        lesson_response: PostgrestAPIResponse = supabase.table("lessons").insert(lesson_data).execute()

        if not lesson_response.data:
            raise Exception("Falha ao criar o registro da lição.")

        new_lesson_id = lesson_response.data[0]['id']
        print(f"--- [DATABASE] Lição criada com ID: {new_lesson_id} ---")

        lesson_items_to_insert = []
        for index, item in enumerate(items):
            lesson_items_to_insert.append({"lesson_id": new_lesson_id, "unit_id": item['id'], "item_order": index + 1})

        if lesson_items_to_insert:
            supabase.table("lesson_items").insert(lesson_items_to_insert).execute()

        print(f"--- [DATABASE] {len(lesson_items_to_insert)} itens da lição salvos. ---")
        return new_lesson_id
    except Exception as e:
        print(f"!!! ERRO no Supabase ao salvar a lição: {e} !!!")
        return None


def save_performance_record(supabase: Client, user_id: str, lesson_id: str, unit_id: str, is_correct: bool,
                            response_data: dict):
    print(f"--- [DATABASE] Salvando desempenho para user_id: {user_id}, unit_id: {unit_id} ---")
    try:
        performance_data = {
            "user_id": user_id,
            "lesson_id": lesson_id,
            "unit_id": unit_id,
            "is_correct": is_correct,
            "response_data": response_data
        }
        supabase.table("student_performance").insert(performance_data).execute()
        print("--- [DATABASE] Desempenho salvo com sucesso. ---")
        return True
    except Exception as e:
        print(f"!!! ERRO no Supabase ao salvar desempenho: {e} !!!")
        return False