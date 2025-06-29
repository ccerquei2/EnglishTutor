# /app/agents.py

from supabase.client import Client
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel, Field
from typing import Literal
import random
import json

from .schemas import UserIntent, AIResponse, Lesson
from .database import (
    get_active_lesson, update_lesson_status, get_student_mastery_summary,
    get_recently_seen_units, get_learning_units_by_similarity, save_lesson,
    get_learning_unit_by_id, save_performance_record, save_tutor_message,
    save_conversation_turn, get_conversation_history, get_learning_units_by_topic,
    mark_lesson_units_as_seen
)


# --- MODELOS E CADEIAS DE IA AUXILIARES ---

class TopicRouter(BaseModel):
    tool_name: Literal["plan_new_lesson", "general_conversation"]
    topic_tag: str = "general-practice"


def _create_topic_router_chain():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    parser = JsonOutputParser(pydantic_object=TopicRouter)

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", f"""Você é um assistente de IA que analisa a mensagem de um usuário e a roteia para a ferramenta correta, extraindo uma tag de tópico normalizada.
        Responda APENAS com um objeto JSON formatado de acordo com o seguinte esquema: {{format_instructions}}
        Regras para 'topic_tag':
        - A tag deve ser em inglês, minúscula e com espaços (ex: 'simple present'). NÃO use hífens.
        - Se nenhum tópico for encontrado, use 'general-practice'.
        Exemplos:
        - "Quero praticar Simple Present" -> tool_name: 'plan_new_lesson', topic_tag: 'simple present'
        - "Olá, tudo bem?" -> tool_name: 'general_conversation', topic_tag: 'general-practice'
        """),
        MessagesPlaceholder(variable_name="history"),
        ("human", "Mensagem do usuário: {user_message}")
    ])

    prompt_with_instructions = prompt_template.partial(format_instructions=parser.get_format_instructions())
    return prompt_with_instructions | llm | parser


def _create_conversational_chain():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are 'Alex', a friendly English tutor. Respond to the user in Brazilian Portuguese, considering the conversation history. Your main goal is the student's pedagogical progress. Be encouraging and brief."),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{user_message}")
    ])
    return prompt | llm | StrOutputParser()


def _create_semantic_query_chain() -> ChatPromptTemplate:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", """You are an English Curriculum Designer. Create a SINGLE descriptive sentence for a semantic search. Rules:
        1.  **TOP PRIORITY**: The query must be about the student's request: '{student_request}'.
        2.  **SECONDARY GOAL**: If the request is generic, THEN focus on weak topics: {weak_topics}.
        3.  **ABSOLUTE EXCLUSION**: NEVER mention mastered strong topics: {strong_topics}.
        4.  **OUTPUT**: ONLY the sentence."""),
        ("human", "Generate the semantic query.")
    ])
    return prompt_template | llm | StrOutputParser()


def _select_and_structure_lesson_items(units: list, count: int = 6) -> list:
    if not units: return []
    # Garante que não estamos tentando amostrar mais itens do que os disponíveis
    k = min(len(units), count)
    return random.sample(units, k)


# --- FERRAMENTA DE PLANEJAMENTO DE LIÇÃO (LÓGICA HÍBRIDA) ---

def tool_plan_new_lesson(supabase: Client, user_id: str, topic_tag: str, level: str = "A1") -> dict | None:
    print("\n\n--- [HYBRID LESSON PLANNER V2] ---")

    performance = get_student_mastery_summary(supabase, user_id)
    strong_topics_set = set(performance.get('strong_topics', []))

    # Busca inicial de candidatos
    candidate_units = []
    lesson_objective = ""
    is_specific_request = topic_tag != 'general-practice'

    if is_specific_request:
        print(f"--- [PLANNER] Estratégia 1 (Específica): Buscando por keyword (tag) '{topic_tag}'... ---")
        candidate_units = get_learning_units_by_topic(supabase, topic_tag, level, count=30)
        lesson_objective = f"Uma lição focada em: {topic_tag.replace('-', ' ').title()}"
    else:
        print(f"--- [PLANNER] Estratégia 2 (Genérica): Usando Busca Semântica... ---")
        query_chain = _create_semantic_query_chain()
        semantic_query = query_chain.invoke({
            "student_request": "a general practice lesson",
            "weak_topics": ", ".join(performance.get('weak_topics', []) or ["Nenhum"]),
            "strong_topics": ", ".join(strong_topics_set or ["Nenhum"])
        })
        print(f"--- [PLANNER] Query Semântica gerada: '{semantic_query}' ---")
        embeddings = OpenAIEmbeddings()
        query_embedding = embeddings.embed_query(semantic_query)
        candidate_units = get_learning_units_by_similarity(supabase, query_embedding, level, count=50)
        lesson_objective = semantic_query

    if not candidate_units:
        print(f"--- [PLANNER] FALHA INICIAL: Nenhum candidato encontrado na busca primária. ---")
        return None

    print(f"--- [PLANNER] Encontradas {len(candidate_units)} unidades candidatas antes da filtragem. ---")

    # ### CORREÇÃO: LÓGICA DE MÚLTIPLAS TENTATIVAS ###
    final_candidates = []

    # Tentativa 1: Filtro completo (tópicos fortes + vistos recentemente)
    print("--- [PLANNER] Tentativa 1: Aplicando todos os filtros (tópicos fortes + vistos recentemente)...")
    seen_units_ids = get_recently_seen_units(supabase, user_id, days_ago=7)
    units_after_strong_filter = [u for u in candidate_units if
                                 not set(u.get('metadata', {}).get('topic', [])).intersection(strong_topics_set)]
    final_candidates = [u for u in units_after_strong_filter if u.get('id') not in seen_units_ids]
    print(f"--- [PLANNER] Tentativa 1 resultou em {len(final_candidates)} unidades.")

    # Tentativa 2: Relaxar o filtro de 'vistos recentemente' se a primeira tentativa falhar
    MINIMUM_UNITS_REQUIRED = 4
    if len(final_candidates) < MINIMUM_UNITS_REQUIRED:
        print(f"--- [PLANNER] Poucas unidades. Tentativa 2: Relaxando o filtro de 'vistos recentemente'...")
        final_candidates = units_after_strong_filter  # Reverte para a lista antes do filtro de 'vistos'
        print(f"--- [PLANNER] Tentativa 2 resultou em {len(final_candidates)} unidades.")

    lesson_items = _select_and_structure_lesson_items(final_candidates)
    if not lesson_items:
        print("--- [PLANNER] FALHA FINAL: Não foi possível montar a lição mesmo após relaxar os filtros. ---")
        return None

    lesson_title = "Sua Lição Personalizada"
    lesson_id = save_lesson(supabase, user_id, lesson_title, lesson_objective, lesson_items)
    if not lesson_id: return None

    return {"lesson_id": lesson_id, "title": lesson_title, "objective": lesson_objective, "lesson_items": lesson_items}


def tool_generate_proactive_feedback(supabase: Client, user_id: str):
    performance = get_student_mastery_summary(supabase, user_id)
    if not performance.get('weak_topics') and not performance.get('strong_topics'):
        return
    # Resto da função
    pass


# --- O CÉREBRO: TUTOR ORQUESTRADOR ---
def tutor_orchestrator(supabase: Client, user_id: str, intent: UserIntent) -> AIResponse:
    if intent.type == 'button_click':
        action = intent.action_id
        if action == 'generate_new_lesson':
            active_lesson_data = get_active_lesson(supabase, user_id)
            if active_lesson_data:
                return AIResponse(response_type='active_lesson_returned',
                                  message_to_user="Você já tem uma lição em andamento.",
                                  content=Lesson(**active_lesson_data))
            new_lesson_data = tool_plan_new_lesson(supabase, user_id=user_id, topic_tag='general-practice')
            if not new_lesson_data:
                return AIResponse(response_type='error',
                                  message_to_user="Desculpe, não consegui criar uma nova lição agora.")
            return AIResponse(response_type='new_lesson', message_to_user="Aqui está sua nova lição personalizada!",
                              content=Lesson(**new_lesson_data))

        elif action == 'complete_current_lesson':
            lesson_id = intent.metadata.get('lesson_id') if intent.metadata else None
            if not lesson_id:
                return AIResponse(response_type='error',
                                  message_to_user="Não foi possível identificar qual lição completar.")
            update_lesson_status(supabase, lesson_id, "completed")
            mark_lesson_units_as_seen(supabase, user_id, lesson_id)
            tool_generate_proactive_feedback(supabase, user_id)
            return AIResponse(response_type='tutor_feedback', message_to_user="Ótimo trabalho ao completar a lição!")

    elif intent.type == 'chat_message' and intent.text:
        save_conversation_turn(supabase, user_id, 'user', intent.text)
        history_raw = get_conversation_history(supabase, user_id)
        history_langchain = [
            HumanMessage(content=h['content']) if h['role'] == 'user' else AIMessage(content=h['content']) for h in
            history_raw]

        router_chain = _create_topic_router_chain()
        router_result = router_chain.invoke({"user_message": intent.text, "history": history_langchain})

        if router_result['tool_name'] == "plan_new_lesson":
            active_lesson_data = get_active_lesson(supabase, user_id)
            if active_lesson_data:
                response = AIResponse(response_type='active_lesson_returned',
                                      message_to_user="Boa ideia! Mas primeiro, vamos terminar a lição que já está em andamento.",
                                      content=Lesson(**active_lesson_data))
            else:
                topic_tag = router_result['topic_tag']
                new_lesson_data = tool_plan_new_lesson(supabase, user_id=user_id, topic_tag=topic_tag)

                if not new_lesson_data:
                    if topic_tag != 'general-practice':
                        message = f"Ótimo pedido! No momento, não encontrei exercícios sobre '{topic_tag}' para o seu nível (A1). Que tal praticarmos outro tópico?"
                    else:
                        message = "Puxa, parece que não consegui montar uma lição de revisão geral agora. Tente novamente em alguns instantes."
                    response = AIResponse(response_type='tutor_feedback', message_to_user=message)
                else:
                    response = AIResponse(
                        response_type='new_lesson',
                        message_to_user="Ótimo! Preparei uma lição especial para você sobre esse tópico.",
                        content=Lesson(**new_lesson_data)
                    )
            save_conversation_turn(supabase, user_id, 'ai', response.message_to_user)
            return response

        elif router_result['tool_name'] == "general_conversation":
            conv_chain = _create_conversational_chain()
            response_text = conv_chain.invoke({"user_message": intent.text, "history": history_langchain})
            response = AIResponse(response_type='tutor_feedback', message_to_user=response_text)
            save_conversation_turn(supabase, user_id, 'ai', response.message_to_user)
            return response

    return AIResponse(response_type='error', message_to_user="Não entendi sua solicitação.")


def original_process_student_answer(supabase: Client, user_id: str, lesson_id: str, unit_id: str,
                                    student_response: str):
    print(f"--- [LEGACY ANSWER] Processando resposta para a unidade: {unit_id} ---")
    unit = get_learning_unit_by_id(supabase, unit_id)
    if not unit:
        print(f"!!! ERRO CRÍTICO: Unidade de aprendizado com ID '{unit_id}' NÃO ENCONTRADA no banco de dados. !!!")
        return {"error": f"Unidade de aprendizado '{unit_id}' não encontrada."}
    correct_answer = unit.get("content", {}).get("correct_answer")
    if not correct_answer:
        return {"error": "Exercício sem resposta correta definida."}
    is_correct = student_response.strip().lower() == str(correct_answer).strip().lower()
    feedback_obj = unit.get("content", {}).get("feedback", {})
    save_performance_record(supabase, user_id, lesson_id, unit_id, is_correct, {"answer": student_response})
    return {"is_correct": is_correct, "correct_answer": correct_answer, "feedback": feedback_obj}