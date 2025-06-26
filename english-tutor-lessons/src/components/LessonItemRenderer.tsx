// /src/components/LessonItemRenderer.tsx (Versão Final Restaurada)

import type { LessonItem } from "@/types/lesson";
import apiClient from "@/lib/apiClient";
import { ChooseOptionExercise } from "./exercises/ChooseOptionExercise";
import { ReadAndAnswerExercise } from "./exercises/ReadAndAnswerExercise";
import { ReorderWordsExercise } from "./exercises/ReorderWordsExercise";
import { FillInTheBlankExercise } from "./exercises/FillInTheBlankExercise";
import { MatchExercise } from "./exercises/MatchExercise";
import { VocabularyItem } from "./VocabularyItem";
import { CulturalTipItem } from "./CulturalTipItem";

interface RendererProps {
  item: LessonItem;
  lessonId: string;
  nativeLanguageCode: string;
}

export function LessonItemRenderer({ item, lessonId, nativeLanguageCode }: RendererProps) {

  const handleAnswer = async (isCorrect: boolean, studentResponse: string) => {
    try {
      const payload = {
        lesson_id: lessonId,
        unit_id: item.id,
        student_response: studentResponse,
      };
      await apiClient.post('/lessons/answer', payload);
    } catch (error) {
      console.error("Erro ao salvar a resposta no backend:", error);
    }
  };

  switch (item.type) {
    case 'exercise':
    case 'review_exercise':
      // Restauramos todos os 'if' para cada tipo de exercício
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
      if (item.content.exercise_type === 'match_question_answer') {
        return <MatchExercise item={item} onAnswerSubmit={handleAnswer} />;
      }
      if (item.content.exercise_type === 'fill_in_the_blank_pronoun') {
        return <ChooseOptionExercise item={item} onAnswerSubmit={handleAnswer} />;
      }

      // Fallback para tipos de exercício que ainda não conhecemos
      return (
        <div className="p-4 my-4 border rounded-lg bg-yellow-100">
          <p>Exercício do tipo <strong>{item.content.exercise_type || 'desconhecido'}</strong> ainda não implementado.</p>
          <pre className="text-sm bg-gray-200 p-2 mt-2 rounded">
            {JSON.stringify(item.content, null, 2)}
          </pre>
        </div>
      );

    case 'vocabulary':
      // Restauramos a chamada ao componente de vocabulário
      return <VocabularyItem item={item} nativeLanguageCode={nativeLanguageCode} />;

    case 'cultural_tip':
      // Restauramos a chamada ao componente de dica cultural
      return <CulturalTipItem item={item} nativeLanguageCode={nativeLanguageCode} />;

    default:
      // Fallback para tipos de item que não conhecemos
      return (
        <div className="p-4 my-4 border rounded-lg bg-gray-100">
          <p>Item do tipo <strong>{item.type}</strong> não renderizado.</p>
        </div>
      );
  }
}