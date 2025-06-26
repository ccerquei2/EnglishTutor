# /app/agents.py

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from supabase.client import Client
# MODIFICAÇÃO: Importa a nova função
from .database import get_student_mastery_summary, get_learning_units_by_similarity, save_lesson, \
    get_learning_unit_by_id, save_performance_record, get_recently_seen_units
import random


def create_semantic_query_chain():
    """ ... (código existente, sem alterações) ... """
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", """You are an elite English Curriculum Designer. Your task is to create a SINGLE, descriptive sentence for a semantic lesson search. Follow these STRICT rules:
        1.  **PRIMARY FOCUS:** The description MUST focus on these WEAK TOPICS: {weak_topics}. This is your main goal.
        2.  **EXCLUSION (CRITICAL):** The description MUST NOT, under any circumstances, mention or allude to these already mastered STRONG TOPICS: {strong_topics}. Your top priority is to prevent repeating content the student already knows. If weak topics are also listed as strong topics, prioritize them for review.
        3.  **STUDENT REQUEST:** If possible, incorporate the student's request ('{student_request}') without violating rules 1 and 2.
        4.  **OUTPUT FORMAT:** Your entire output must be ONLY the descriptive sentence. No preambles, no explanations. Just the query.
        """),
        ("human", "Generate the semantic query based on the rules.")
    ])
    output_parser = StrOutputParser()
    return prompt_template | llm | output_parser


def select_and_structure_lesson_items(units: list, count: int = 6) -> list:
    """ ... (código existente, sem alterações) ... """
    if not units: return []
    # ... (lógica de seleção aleatória) ...
    return random.sample(units, min(len(units), count))


# MODIFICAÇÃO PRINCIPAL: Adicionado o filtro de unidades recentes
def orchestrate_lesson_creation(supabase: Client, user_id: str, student_request: str, level: str = "A1"):
    # 1. Analisar maestria
    performance = get_student_mastery_summary(supabase=supabase, user_id=user_id)

    # --- NOVO: Buscar unidades vistas recentemente ---
    seen_units_ids = get_recently_seen_units(supabase=supabase, user_id=user_id, days_ago=7)

    # 2. Gerar query semântica (código existente)
    # ... (código de geração de query) ...
    weak_topics_str = ", ".join(performance['weak_topics']) if performance['weak_topics'] else "None"
    strong_topics_str = ", ".join(performance['strong_topics']) if performance['strong_topics'] else "None"
    final_prompt_input = {"student_request": student_request, "weak_topics": weak_topics_str,
                          "strong_topics": strong_topics_str}
    query_chain = create_semantic_query_chain()
    semantic_query = query_chain.invoke(final_prompt_input)
    print(f"--- [ORCHESTRATOR] Query semântica gerada: '{semantic_query}' ---")

    # 3. Buscar unidades por similaridade (código existente)
    embeddings = OpenAIEmbeddings()
    query_embedding = embeddings.embed_query(semantic_query)
    # Aumentamos a contagem para 30 para ter uma piscina maior para filtrar
    candidate_units = get_learning_units_by_similarity(supabase=supabase, embedding=query_embedding, level=level,
                                                       count=30)
    if not candidate_units: return None

    # 4. APLICAR FILTROS EM CASCATA
    # Filtro 1: Tópicos fortes (já existente)
    strong_topics_set = set(performance['strong_topics'])
    print(f"--- [ORCHESTRATOR] Filtro 1: Removendo tópicos fortes: {strong_topics_set} ---")
    units_after_topic_filter = []
    for unit in candidate_units:
        unit_topics = set(unit.get('metadata', {}).get('topic', []))
        if not unit_topics.intersection(strong_topics_set):
            units_after_topic_filter.append(unit)
    print(f"--- [ORCHESTRATOR] Unidades após filtro de tópico: {len(units_after_topic_filter)} ---")

    # --- Filtro 2: Unidades vistas recentemente (NOVO) ---
    print(f"--- [ORCHESTRATOR] Filtro 2: Removendo {len(seen_units_ids)} unidades vistas recentemente ---")
    final_candidates = []
    for unit in units_after_topic_filter:
        if unit['id'] not in seen_units_ids:
            final_candidates.append(unit)
        else:
            print(f"--- [ORCHESTRATOR] Unidade '{unit.get('unit_code')}' removida por ter sido vista recentemente.")

    print(f"--- [ORCHESTRATOR] Unidades finais para seleção: {len(final_candidates)} ---")

    # 5. Estruturar e salvar (código existente)
    lesson_items = select_and_structure_lesson_items(final_candidates)
    if not lesson_items:
        print("--- [ORCHESTRATOR] Não foi possível estruturar a lição. Poucas unidades restantes após filtros.")
        return None

    # ... (código para salvar a lição) ...
    lesson_title = "Sua Lição Personalizada de Hoje"
    lesson_objective = f"Uma lição focada em: {semantic_query}"
    lesson_id = save_lesson(supabase=supabase, user_id=user_id, title=lesson_title, objective=lesson_objective,
                            items=lesson_items)
    if not lesson_id: return None

    return {"lesson_id": lesson_id, "title": lesson_title, "objective": lesson_objective,
            "suggested_topics": semantic_query, "lesson_items": lesson_items}


def process_student_answer(supabase: Client, user_id: str, lesson_id: str, unit_id: str, student_response: str):
    """ ... (código existente, sem alterações) ... """
    # ...
    return {"is_correct": is_correct, "correct_answer": correct_answer, "feedback": feedback_obj}