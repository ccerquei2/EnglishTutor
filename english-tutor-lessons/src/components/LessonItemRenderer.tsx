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
import { RewriteSentenceExercise } from "./exercises/RewriteSentenceExercise";

// Importando todos os componentes de conteúdo/UI
import { GrammarRuleItem } from "./ui/GrammarRuleItem";
import { DialogueItem } from "./ui/DialogueItem";
import { VocabularyItem } from "./ui/VocabularyItem";
import { CulturalTipItem } from "./ui/CulturalTipItem";
import { CongratulationsMessageItem } from "./ui/CongratulationsMessageItem";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card"; // Para o RichTextReader

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

      // Para a jornada guiada, o lessonId é temporário. O backend usará o user_id.
      // O importante é registrar o unit_id e a resposta.
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

  // Componente interno para renderizar nosso formato de texto rico
  const RichTextReader = ({ item }: { item: LessonItem }) => {
    const content = item.content || {};
    const title = content.title || 'Texto para Leitura';
    const passage = content.reading_passage || {};
    const englishText = passage['en-US'] || 'No text available.';
    const translatedText = passage[nativeLanguageCode] || passage['en-US'] || 'No translation available.';

    return (
      <Card className="bg-sky-50 border-sky-200">
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent className="grid md:grid-cols-2 gap-x-6 gap-y-4">
          <div className="prose max-w-none text-base">
            <p>{englishText}</p>
          </div>
          <div className="prose max-w-none text-base text-muted-foreground border-l-2 pl-6 italic">
            <p>{translatedText}</p>
          </div>
        </CardContent>
      </Card>
    );
  };

  // --- LÓGICA DE ROTEAMENTO ---
  const itemType = item.type;

  // Agrupa 'exercise' e 'review_exercise' para simplificar o roteamento.
  if (itemType === "exercise" || itemType === "review_exercise") {
    const exerciseType = item.content?.exercise_type;

    switch (exerciseType) {
      case "choose_the_correct_option":
      case "multiple_choice":
      case "fill_in_the_blank_preposition":
      case "fill_in_the_blank_quantifier":
      case "fill_in_the_blank_article":
      case "choose_the_word":
        return <ChooseOptionExercise item={item} onAnswerSubmit={handleAnswer} />;

      case "fill_in_the_blank":
        return <FillInTheBlankExercise item={item} onAnswerSubmit={handleAnswer} />;

      case "match_pairs":
      case "match_question_answer":
        return <MatchExercise item={item} onAnswerSubmit={handleAnswer} />;

      case "read_and_answer":
          // A unidade 'read_and_answer' pode ter dois formatos:
          // 1. O novo, com 'reading_passage', que é apenas para leitura.
          // 2. O antigo, com 'text' e 'question', que é um exercício.
          if (item.content.reading_passage) {
            return <RichTextReader item={item} />;
          }
          // Se não tiver 'reading_passage', assume que é um exercício interativo.
          return <ReadAndAnswerExercise item={item} onAnswerSubmit={handleAnswer} />;

      case "reorder_words":
        return <ReorderWordsExercise item={item} onAnswerSubmit={handleAnswer} />;

      case "rewrite_sentence":
        return <RewriteSentenceExercise item={item} onAnswerSubmit={handleAnswer} />;

      default:
        return (
          <div className="p-4 rounded-md border bg-red-50 text-red-800">
            <p><strong>Erro de Renderização:</strong> Exercício do tipo <strong>{exerciseType || 'desconhecido'}</strong> não é suportado pelo frontend.</p>
          </div>
        );
    }
  }

  // --- Rotas para conteúdo estático ---
  switch (itemType) {
    case "grammar_rule":
      return <GrammarRuleItem item={item} />;

    case "dialogue":
      return <DialogueItem item={item} />;

    case "vocabulary":
      return <VocabularyItem item={item} nativeLanguageCode={nativeLanguageCode} />;

    case "cultural_tip":
      return <CulturalTipItem item={item} nativeLanguageCode={nativeLanguageCode} />;

    case "congratulations_message":
      return <CongratulationsMessageItem item={item} nativeLanguageCode={nativeLanguageCode} />;

    // Adiciona um caso para o tipo 'read_and_answer' que não é um exercício
    // Isso garante que nossos textos âncora sempre sejam renderizados.
    case "read_and_answer":
        return <RichTextReader item={item} />;

    // --- Fallback geral ---
    default:
      return (
        <div className="p-4 rounded-md border bg-amber-50 text-amber-800">
          <p>Item do tipo <strong>{itemType}</strong> não renderizado.</p>
        </div>
      );
  }
}