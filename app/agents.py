# app/agents.py
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from supabase.client import Client
# Adicionamos a nova função de maestria
from .database import get_student_mastery_summary, get_learning_units_by_similarity, save_lesson, \
    get_learning_unit_by_id, save_performance_record
import random


# create_semantic_query_chain() permanece igual
def create_semantic_query_chain():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", """You are an expert curriculum designer. Your goal is to create a semantic query for a vector search. The query should describe the ideal lesson content based on the student's request, their weak topics (areas to review), and their strong topics (areas to avoid or use for context).

        The query must be a single, descriptive sentence.

        Example 1:
        Request: 'I want a new lesson.'
        Weak Topics: 'past simple, prepositions'
        Strong Topics: 'greetings, family'
        Output: A review lesson focusing on the Past Simple tense and prepositions of time and place, perhaps using examples about family to make it more engaging.

        Example 2:
        Request: 'I want to practice speaking.'
        Weak Topics: 'None'
        Strong Topics: 'food, present simple'
        Output: A new conversational lesson that introduces vocabulary for travel and directions, allowing the student to use their strong knowledge of the present simple in a new context.
        """),
        ("human",
         "Student Request: '{student_request}'. Student's Weakest Topics: '{weak_topics}'. Student's Strongest Topics: '{strong_topics}'.")
    ])

    output_parser = StrOutputParser()
    return prompt_template | llm | output_parser


# select_and_structure_lesson_items() permanece igual
def select_and_structure_lesson_items(units: list, count: int = 6) -> list:
    if not units:
        return []

    grammar = [u for u in units if u['type'] == 'grammar_rule']
    exercises = [u for u in units if u['type'] in ['exercise', 'review_exercise']]
    vocab = [u for u in units if u['type'] == 'vocabulary']
    dialogues = [u for u in units if u['type'] == 'dialogue']

    lesson_plan = []
    lesson_plan.extend(random.sample(grammar, min(len(grammar), 2)))
    needed = count - len(lesson_plan)
    lesson_plan.extend(random.sample(exercises, min(len(exercises), needed)))

    needed = count - len(lesson_plan)
    if needed > 0:
        other_units = vocab + dialogues
        lesson_plan.extend(random.sample(other_units, min(len(other_units), needed)))

    random.shuffle(lesson_plan)
    print(f"--- [AGENT] Plano final da lição: {[u.get('unit_code', 'N/A') for u in lesson_plan]} ---")
    return lesson_plan


# orchestrate_lesson_creation() é MODIFICADO para usar a nova função
def orchestrate_lesson_creation(supabase: Client, user_id: str, student_request: str, level: str = "A1"):
    # 1. Analisar maestria do aluno
    print("--- [ORCHESTRATOR] Analisando maestria do aluno (baseado em atividade)... ---")
    performance = get_student_mastery_summary(supabase=supabase, user_id=user_id)
    weak_topics_str = ", ".join(performance['weak_topics']) if performance['weak_topics'] else "None"
    strong_topics_str = ", ".join(performance['strong_topics']) if performance['strong_topics'] else "None"

    # 2. Construir o input para a IA
    final_prompt_input = {
        "student_request": student_request,
        "weak_topics": weak_topics_str,
        "strong_topics": strong_topics_str
    }

    # 3. Gerar a query semântica
    print(f"--- [ORCHESTRATOR] Gerando query semântica com input: {final_prompt_input} ---")
    query_chain = create_semantic_query_chain()
    semantic_query = query_chain.invoke(final_prompt_input)
    print(f"--- [ORCHESTRATOR] Query semântica gerada: '{semantic_query}' ---")

    # 4. Gerar embedding e buscar unidades
    embeddings = OpenAIEmbeddings()
    query_embedding = embeddings.embed_query(semantic_query)
    candidate_units = get_learning_units_by_similarity(supabase=supabase, embedding=query_embedding, level=level,
                                                       count=15)

    if not candidate_units:
        return None

    # 5. Selecionar e estruturar
    lesson_items = select_and_structure_lesson_items(candidate_units)
    if not lesson_items:
        return None

    # 6. Salvar
    lesson_title = "Sua Lição Personalizada de Hoje"
    lesson_objective = f"Uma lição focada em: {semantic_query}"

    lesson_id = save_lesson(supabase=supabase, user_id=user_id, title=lesson_title, objective=lesson_objective,
                            items=lesson_items)
    if not lesson_id:
        return None

    return {"lesson_id": lesson_id, "title": lesson_title, "objective": lesson_objective,
            "suggested_topics": semantic_query, "lesson_items": lesson_items}


# A função `process_student_answer` permanece a mesma
def process_student_answer(supabase: Client, user_id: str, lesson_id: str, unit_id: str, student_response: str):
    print(f"--- [PERFORMANCE AGENT] Processando resposta para a unidade {unit_id} ---")
    unit = get_learning_unit_by_id(supabase, unit_id)
    if not unit:
        return {"error": "Unidade de aprendizado não encontrada."}
    exercisable_types = ["exercise", "review_exercise"]
    if unit.get("type") not in exercisable_types:
        return {"error": "Unidade de aprendizado inválida ou não é um exercício."}
    correct_answer = unit.get("content", {}).get("correct_answer")
    if not correct_answer:
        return {"error": "Exercício não tem uma resposta correta definida."}
    is_correct = student_response.strip().lower() == correct_answer.strip().lower()
    feedback_obj = unit.get("content", {}).get("feedback", {})
    save_performance_record(supabase=supabase, user_id=user_id, lesson_id=lesson_id, unit_id=unit_id,
                            is_correct=is_correct, response_data={"answer": student_response})
    return {"is_correct": is_correct, "correct_answer": correct_answer, "feedback": feedback_obj}
