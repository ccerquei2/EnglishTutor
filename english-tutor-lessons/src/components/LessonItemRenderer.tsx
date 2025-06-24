// /src/components/LessonItemRenderer.tsx

import type { LessonItem } from "@/types/lesson";
import apiClient from "@/lib/apiClient";
import { ChooseOptionExercise } from "./exercises/ChooseOptionExercise";
import { ReadAndAnswerExercise } from "./exercises/ReadAndAnswerExercise";
import { ReorderWordsExercise } from "./exercises/ReorderWordsExercise";
import { FillInTheBlankExercise } from "./exercises/FillInTheBlankExercise";
// 1. Importe o novo componente
import { MatchExercise } from "./exercises/MatchExercise";

interface RendererProps {
  item: LessonItem;
  lessonId: string;
}

export function LessonItemRenderer({ item, lessonId }: RendererProps) {

  const handleAnswer = async (isCorrect: boolean, studentResponse: string) => {
    console.log(`Enviando resposta: lesson_id=${lessonId}, unit_id=${item.id}, response=${studentResponse}`);
    try {
      const payload = {
        lesson_id: lessonId,
        unit_id: item.id,
        student_response: studentResponse,
      };
      await apiClient.post('/lessons/answer', payload);
      console.log("Resposta salva com sucesso!");
    } catch (error) {
      console.error("Erro ao salvar a resposta no backend:", error);
    }
  };

  switch (item.type) {
    case 'exercise':
    case 'review_exercise':
      if (item.content.exercise_type === 'choose_the_correct_option') {
        return <ChooseOptionExercise item={item} onAnswerSubmit={handleAnswer} />;
      }
      if (item.content.exercise_type === 'read_and_answer') {
        return <ReadAndAnswerExercise item={item} onAnswerSubmit={handleAnswer} />;
      }
      if (item.content.exercise_type === 'reorder_words') {
        return <ReorderWordsExercise item={item} onAnswerSubmit={handleAnswer} />;
      }
      if (item.content.exercise_type === 'fill_in_the_blank') {
        return <FillInTheBlankExercise item={item} onAnswerSubmit={handleAnswer} />;
      }
      // 2. Adicione a nova condição para 'match_question_answer'
      if (item.content.exercise_type === 'match_question_answer') {
        return <MatchExercise item={item} onAnswerSubmit={handleAnswer} />;
      }

      // Fallback para exercícios que ainda possam aparecer
      return (
        <div className="p-4 my-4 border rounded-lg bg-yellow-100">
          <p>Exercício do tipo <strong>{item.content.exercise_type}</strong> ainda não implementado.</p>
          <pre className="text-sm bg-gray-200 p-2 mt-2 rounded">
            {JSON.stringify(item.content, null, 2)}
          </pre>
        </div>
      );

    default:
      return (
        <div className="p-4 my-4 border rounded-lg bg-gray-100">
          <p>Item do tipo <strong>{item.type}</strong>.</p>
          <pre className="text-sm bg-white p-2 mt-2 rounded">
            {JSON.stringify(item.content, null, 2)}
          </pre>
        </div>
      );
  }
}