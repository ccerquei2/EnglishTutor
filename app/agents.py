# /app/agents.py

from supabase.client import Client
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel, Field
from typing import Literal, List, Optional, Dict, Any, Tuple
import random
import json

from .schemas import UserIntent, AIResponse, Lesson
from .database import (
    get_active_lesson, update_lesson_status, get_student_mastery_summary,
    get_recently_seen_units, get_learning_units_by_similarity, save_lesson,
    get_learning_unit_by_id, save_performance_record, save_tutor_message,
    save_conversation_turn, get_conversation_history, get_learning_units_by_topic,
    mark_lesson_units_as_seen, get_units_by_dependency, get_all_topics_for_level
)

# --- CONSTANTES DE CONFIGURAÇÃO ---
MINIMUM_UNITS_FOR_LESSON = 4
RECENTLY_SEEN_DAYS = 14
WEAKNESS_FOCUS_PROBABILITY = 0.7

class TopicRouter(BaseModel):
    tool_name: Literal["plan_new_lesson", "general_conversation"]
    topic_tag: str = Field(default="general-practice", description="O tópico normalizado em inglês ou 'general-practice'.")

def _create_topic_router_chain():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    parser = JsonOutputParser(pydantic_object=TopicRouter)
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", f"Você é um assistente de IA que analisa a mensagem de um usuário e a roteia para a ferramenta correta, extraindo uma tag de tópico normalizada. Responda APENAS com um objeto JSON formatado de acordo com o seguinte esquema: {{format_instructions}}. Regras para 'topic_tag': - A tag deve ser em inglês, minúscula e com espaços (ex: 'simple present'). NÃO use hífens. - Se nenhum tópico for encontrado, use 'general-practice'."),
        MessagesPlaceholder(variable_name="history"),
        ("human", "Mensagem do usuário: {user_message}")
    ])
    prompt_with_instructions = prompt_template.partial(format_instructions=parser.get_format_instructions())
    return prompt_with_instructions | llm | parser

def _create_conversational_chain():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are 'Alex', a friendly English tutor. Respond to the user in Brazilian Portuguese, considering the conversation history. Your main goal is the student's pedagogical progress. Be encouraging and brief."),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{user_message}")
    ])
    return prompt | llm | StrOutputParser()

def _create_semantic_query_chain() -> ChatPromptTemplate:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "You are an English Curriculum Designer. Based on the requested focus, create a SINGLE descriptive sentence for a semantic search. Focus of the lesson: {lesson_focus}. Student's weak topics (for context, not necessarily for focus): {weak_topics}. Student's strong topics (to be avoided if possible): {strong_topics}. OUTPUT: ONLY the sentence for the semantic search."),
        ("human", "Generate the semantic query.")
    ])
    return prompt_template | llm | StrOutputParser()

def _build_and_save_lesson(supabase: Client, user_id: str, title: str, objective: str, items: List[Dict[str, Any]]) -> Optional[Dict]:
    if not items: return None
    lesson_id = save_lesson(supabase, user_id, title, objective, items)
    if not lesson_id: return None
    return {"lesson_id": lesson_id, "title": title, "objective": objective, "lesson_items": items}

def _get_next_focus_topic(performance: dict, all_level_topics: list) -> Tuple[str, str]:
    weak_topics = performance.get('weak_topics', [])
    strong_topics = performance.get('strong_topics', [])
    practiced_topics = set(weak_topics + strong_topics)
    unpracticed_topics = [t for t in all_level_topics if t not in practiced_topics]
    if weak_topics and random.random() < WEAKNESS_FOCUS_PROBABILITY:
        focus = random.choice(weak_topics)
        print(f"--- [FOCUS DECISION] Estratégia: Foco em Ponto Fraco. Tópico: '{focus}'")
        return focus, "weakness_focus"
    if unpracticed_topics:
        focus = random.choice(unpracticed_topics)
        print(f"--- [FOCUS DECISION] Estratégia: Descoberta. Tópico novo: '{focus}'")
        return focus, "discovery"
    if weak_topics:
        focus = random.choice(weak_topics)
        print(f"--- [FOCUS DECISION] Estratégia: Fallback para Ponto Fraco. Tópico: '{focus}'")
        return focus, "weakness_focus"
    print("--- [FOCUS DECISION] Estratégia: Revisão Geral.")
    return "general review of all topics", "general_review"

def _find_semantic_lesson(supabase: Client, user_id: str, level: str, performance: Dict, seen_units_ids: set, all_level_topics: list, exclude_strong_topics: bool, exclude_seen_units: bool) -> Optional[Tuple[List[Dict[str, Any]], str]]:
    focus_topic, focus_type = _get_next_focus_topic(performance, all_level_topics)
    strong_topics = performance.get('strong_topics', []) if exclude_strong_topics else []
    query_chain = _create_semantic_query_chain()
    semantic_query = query_chain.invoke({"lesson_focus": focus_topic, "weak_topics": ", ".join(performance.get('weak_topics', []) or ["Nenhum"]), "strong_topics": ", ".join(strong_topics or ["Nenhum"])})
    print(f"--- [PLANNER] Query Semântica gerada: '{semantic_query}' ---")
    embeddings = OpenAIEmbeddings()
    query_embedding = embeddings.embed_query(semantic_query)
    candidate_units = get_learning_units_by_similarity(supabase, query_embedding, level, count=50)
    if exclude_strong_topics:
        candidate_units = [u for u in candidate_units if not set(u.get('metadata', {}).get('topic', [])).intersection(set(strong_topics))]
    if exclude_seen_units:
        candidate_units = [u for u in candidate_units if u.get('id') not in seen_units_ids]
    if len(candidate_units) >= MINIMUM_UNITS_FOR_LESSON:
        k = min(len(candidate_units), 6)
        return random.sample(candidate_units, k), semantic_query
    return None, None

def tool_plan_new_lesson(supabase: Client, user_id: str, topic_tag: str, level: str = "A1") -> Optional[Dict]:
    print(f"\n--- [DYNAMIC FUNNEL PLANNER V5.0] --- Tópico: '{topic_tag}' ---")
    performance = get_student_mastery_summary(supabase, user_id)
    seen_units_ids = get_recently_seen_units(supabase, user_id, days_ago=RECENTLY_SEEN_DAYS)
    if topic_tag != 'general-practice':
        print(f"--- [PLANNER] Tentativa 1 (Específica): Buscando Âncora para '{topic_tag}'...")
        anchor_types = ["read_and_answer", "dialogue"]
        anchors = get_learning_units_by_topic(supabase, topic_tag, level, anchor_types, count=10)
        valid_anchors = [u for u in anchors if u.get('id') not in seen_units_ids]
        if valid_anchors:
            anchor = random.choice(valid_anchors)
            dependencies = get_units_by_dependency(supabase, anchor['id'], level)
            lesson_items = [anchor] + dependencies
            if len(lesson_items) >= MINIMUM_UNITS_FOR_LESSON:
                title = anchor.get('content', {}).get('title', f"Lição sobre {topic_tag.title()}")
                objective = f"Praticar '{topic_tag.title()}' com base em um texto de exemplo."
                print(f"--- [PLANNER] SUCESSO! Lição contextual encontrada com {len(lesson_items)} itens.")
                return _build_and_save_lesson(supabase, user_id, title, objective, lesson_items)
        print(f"--- [PLANNER] Tentativa 2 (Específica): Buscando exercícios para '{topic_tag}'...")
        exercise_types = ["exercise", "grammar_rule", "review_exercise"]
        exercises = get_learning_units_by_topic(supabase, topic_tag, level, exercise_types, count=20)
        valid_exercises = [u for u in exercises if u.get('id') not in seen_units_ids]
        if len(valid_exercises) >= MINIMUM_UNITS_FOR_LESSON:
            k = min(len(valid_exercises), 5)
            lesson_items = random.sample(valid_exercises, k)
            title = f"Exercícios de {topic_tag.title()}"
            objective = f"Uma série de exercícios para reforçar seu conhecimento sobre {topic_tag}."
            print(f"--- [PLANNER] SUCESSO! Lição de exercícios focados encontrada com {len(lesson_items)} itens.")
            return _build_and_save_lesson(supabase, user_id, title, objective, lesson_items)

    print("--- [PLANNER] Iniciando funil de lição geral...")
    all_level_topics = get_all_topics_for_level(supabase, level)
    print("--- [PLANNER] Tentativa 1 (Geral): Busca Dinâmica Ideal (filtros: strong_topics, seen_units)...")
    lesson_items, objective = _find_semantic_lesson(supabase, user_id, level, performance, seen_units_ids, all_level_topics, exclude_strong_topics=True, exclude_seen_units=True)
    if lesson_items:
        print(f"--- [PLANNER] SUCESSO! Lição de revisão ideal encontrada com {len(lesson_items)} itens.")
        return _build_and_save_lesson(supabase, user_id, "Sua Lição de Revisão Inteligente", objective, lesson_items)
    print("--- [PLANNER] Tentativa 2 (Geral): Busca Dinâmica Confiável (filtro: seen_units)...")
    lesson_items, objective = _find_semantic_lesson(supabase, user_id, level, performance, seen_units_ids, all_level_topics, exclude_strong_topics=False, exclude_seen_units=True)
    if lesson_items:
        print(f"--- [PLANNER] SUCESSO! Lição de revisão confiável encontrada com {len(lesson_items)} itens.")
        return _build_and_save_lesson(supabase, user_id, "Sua Lição de Revisão", objective, lesson_items)
    print("--- [PLANNER] Tentativa 3 (Geral): Busca Dinâmica 'Não Falha' (sem filtros)...")
    lesson_items, objective = _find_semantic_lesson(supabase, user_id, level, performance, seen_units_ids, all_level_topics, exclude_strong_topics=False, exclude_seen_units=False)
    if lesson_items:
        print(f"--- [PLANNER] SUCESSO! Lição 'Não Falha' encontrada com {len(lesson_items)} itens.")
        return _build_and_save_lesson(supabase, user_id, "Sua Nova Lição", objective, lesson_items)
    print("--- [PLANNER] FALHA CRÍTICA: Não foi possível montar nenhuma lição.")
    return None

def tutor_orchestrator(supabase: Client, user_id: str, intent: UserIntent) -> AIResponse:
    if intent.type == 'button_click':
        action = intent.action_id
        if action == 'generate_new_lesson':
            active_lesson_data = get_active_lesson(supabase, user_id)
            if active_lesson_data:
                return AIResponse(response_type='active_lesson_returned', message_to_user="Você já tem uma lição em andamento.", content=Lesson(**active_lesson_data))
            new_lesson_data = tool_plan_new_lesson(supabase, user_id=user_id, topic_tag='general-practice')
            if not new_lesson_data:
                return AIResponse(response_type='error', message_to_user="Desculpe, não consegui criar uma nova lição agora. Tente novamente em alguns instantes.")
            return AIResponse(response_type='new_lesson', message_to_user="Aqui está sua nova lição personalizada!", content=Lesson(**new_lesson_data))
        elif action == 'complete_current_lesson':
            lesson_id = intent.metadata.get('lesson_id') if intent.metadata else None
            if not lesson_id: return AIResponse(response_type='error', message_to_user="Não foi possível identificar qual lição completar.")
            update_lesson_status(supabase, lesson_id, "completed")
            mark_lesson_units_as_seen(supabase, user_id, lesson_id)
            return AIResponse(response_type='tutor_feedback', message_to_user="Ótimo trabalho ao completar a lição!")
    elif intent.type == 'chat_message' and intent.text:
        save_conversation_turn(supabase, user_id, 'user', intent.text)
        history_raw = get_conversation_history(supabase, user_id)
        history_langchain = [HumanMessage(content=h['content']) if h['role'] == 'user' else AIMessage(content=h['content']) for h in history_raw]
        router_chain = _create_topic_router_chain()
        router_result = router_chain.invoke({"user_message": intent.text, "history": history_langchain})
        if router_result['tool_name'] == "plan_new_lesson":
            active_lesson_data = get_active_lesson(supabase, user_id)
            if active_lesson_data:
                response = AIResponse(response_type='active_lesson_returned', message_to_user="Boa ideia! Mas primeiro, vamos terminar a lição que já está em andamento.", content=Lesson(**active_lesson_data))
            else:
                topic_tag = router_result['topic_tag']
                new_lesson_data = tool_plan_new_lesson(supabase, user_id=user_id, topic_tag=topic_tag)
                if not new_lesson_data:
                    message = f"Ótimo pedido! No momento, não consegui montar uma lição sobre '{topic_tag.title()}'. Que tal praticarmos outro tópico ou uma revisão geral?"
                    response = AIResponse(response_type='tutor_feedback', message_to_user=message)
                else:
                    response = AIResponse(response_type='new_lesson', message_to_user=f"Ótimo! Preparei uma lição especial para você sobre {topic_tag.title()}.", content=Lesson(**new_lesson_data))
            save_conversation_turn(supabase, user_id, 'ai', response.message_to_user)
            return response
        elif router_result['tool_name'] == "general_conversation":
            conv_chain = _create_conversational_chain()
            response_text = conv_chain.invoke({"user_message": intent.text, "history": history_langchain})
            response = AIResponse(response_type='tutor_feedback', message_to_user=response_text)
            save_conversation_turn(supabase, user_id, 'ai', response.message_to_user)
            return response
    return AIResponse(response_type='error', message_to_user="Não entendi sua solicitação.")

def original_process_student_answer(supabase: Client, user_id: str, lesson_id: str, unit_id: str, student_response: str):
    print(f"--- [ANSWER PROCESSOR] Processando resposta para a unidade: {unit_id} ---")
    unit = get_learning_unit_by_id(supabase, unit_id)
    if not unit:
        return {"error": f"Unidade de aprendizado '{unit_id}' não encontrada."}
    content = unit.get("content", {})
    correct_answer = content.get("correct_answer")
    if correct_answer is None:
        save_performance_record(supabase, user_id, lesson_id, unit_id, True, {"answer": student_response, "note": "Assumed correct from client."})
        return {"is_correct": True, "correct_answer": student_response, "feedback": content.get("feedback", {})}
    is_correct = student_response.strip().lower() == str(correct_answer).strip().lower()
    feedback_obj = content.get("feedback", {})
    save_performance_record(supabase, user_id, lesson_id, unit_id, is_correct, {"answer": student_response})
    return {"is_correct": is_correct, "correct_answer": correct_answer, "feedback": feedback_obj}