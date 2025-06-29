// /src/components/LessonItemRenderer.tsx

import type { LessonItem } from "@/types/lesson";
import toast from "react-hot-toast";
import { supabase } from "@/lib/supabaseClient";

// Importando todos os componentes de exercício
import { ChooseOptionExercise } from "./exercises/ChooseOptionExercise";
import { FillInTheBlankExercise } from "./exercises/FillInTheBlankExercise";
import { MatchExercise } from "./exercises/MatchExercise";
import { ReadAndAnswerExercise } from "./exercises/ReadAndAnswerExercise";
import { ReorderWordsExercise } from "./exercises/ReorderWordsExercise";

// Importando todos os componentes de conteúdo/UI
import { GrammarRuleItem } from "./ui/GrammarRuleItem";
import { DialogueItem } from "./ui/DialogueItem";
import { VocabularyItem } from "./ui/VocabularyItem";
import { CulturalTipItem } from "./ui/CulturalTipItem";

interface LessonItemRendererProps {
  item: LessonItem;
  lessonId: string;
  nativeLanguageCode: string;
}

export function LessonItemRenderer({ item, lessonId, nativeLanguageCode }: LessonItemRendererProps) {

  const handleAnswer = async (isCorrect: boolean, studentResponse: string) => {
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) throw new Error("Usuário não autenticado para salvar resposta.");

      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/lessons/answer`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify({
          lesson_id: lessonId,
          unit_id: item.id,
          student_response: studentResponse,
        }),
      });

      if (!response.ok) {
        throw new Error(`O servidor respondeu com o status ${response.status}`);
      }

    } catch (error) {
      console.error("Erro ao salvar a resposta no backend: ", error);
      toast.error("Houve um problema ao salvar seu progresso.");
    }
  };

  switch (item.type) {
    case "exercise": {
      const exerciseType = item.content?.exercise_type;

      switch (exerciseType) {
        case "choose_the_correct_option":
        case "multiple_choice":
          return <ChooseOptionExercise item={item} onAnswerSubmit={handleAnswer} />;

        case "fill_in_the_blank":
          return <FillInTheBlankExercise item={item} onAnswerSubmit={handleAnswer} />;

        // ### CORREÇÃO APLICADA AQUI ###
        // Adicionamos o novo tipo de exercício 'match_question_answer' para usar o mesmo
        // componente do 'match_pairs'.
        case "match_pairs":
        case "match_question_answer":
          return <MatchExercise item={item} onAnswerSubmit={handleAnswer} />;

        case "read_and_answer":
            return <ReadAndAnswerExercise item={item} onAnswerSubmit={handleAnswer} />;

        case "reorder_words":
          return <ReorderWordsExercise item={item} onAnswerSubmit={handleAnswer} />;

        default:
          return (
            <div className="p-4 rounded-md border bg-red-50 text-red-800">
              <p>
                <strong>Erro de Renderização:</strong> Exercício do tipo <strong>{exerciseType || 'desconhecido'}</strong> não é suportado pelo frontend.
              </p>
            </div>
          );
      }
    }

    // --- Rotas para conteúdo estático ---
    case "grammar_rule":
      return <GrammarRuleItem item={item} />;

    case "dialogue":
      return <DialogueItem item={item} />;

    case "vocabulary":
      return <VocabularyItem item={item} nativeLanguageCode={nativeLanguageCode} />;

    case "cultural_tip":
      return <CulturalTipItem item={item} nativeLanguageCode={nativeLanguageCode} />;

    // --- Fallback geral ---
    default:
      return (
        <div className="p-4 rounded-md border bg-amber-50 text-amber-800">
          <p>
            Item do tipo <strong>{item.type}</strong> não renderizado.
          </p>
        </div>
      );
  }
}