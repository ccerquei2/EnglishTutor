// /src/components/exercises/RewriteSentenceExercise.tsx

import { useState } from 'react';
import type { LessonItem } from '@/types/lesson';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input'; // Usaremos um Input
import { cn } from "@/lib/utils";

interface ExerciseProps {
  item: LessonItem;
  onAnswerSubmit: (isCorrect: boolean, studentResponse: string) => void;
}

export function RewriteSentenceExercise({ item, onAnswerSubmit }: ExerciseProps) {
  const [studentAnswer, setStudentAnswer] = useState('');
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [isCorrect, setIsCorrect] = useState(false);

  const { question, correct_answer, feedback } = item.content;
  const feedbackText = feedback?.['pt-BR'] || feedback?.['en-US'] || 'Bom trabalho!';

  const handleSubmit = () => {
    if (!studentAnswer.trim()) return;

    // Normaliza as respostas para uma comparação mais robusta
    // Remove espaços extras e pontuação final.
    const normalizedStudentAnswer = studentAnswer.trim().replace(/[.!?]$/, '').toLowerCase();
    const normalizedCorrectAnswer = correct_answer.trim().replace(/[.!?]$/, '').toLowerCase();

    const correct = normalizedStudentAnswer === normalizedCorrectAnswer;
    setIsCorrect(correct);
    setIsSubmitted(true);
    onAnswerSubmit(correct, studentAnswer);
  };

  const feedbackClass = isCorrect ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800';

  return (
    <Card className="border-slate-200">
      <CardContent className="p-6">
        <p className="text-lg font-semibold mb-4">{question}</p>

        <Input
          type="text"
          value={studentAnswer}
          onChange={(e) => setStudentAnswer(e.target.value)}
          placeholder="Reescreva a frase aqui..."
          disabled={isSubmitted}
          className="text-base"
        />

        <Button
          onClick={handleSubmit}
          disabled={isSubmitted || !studentAnswer.trim()}
          className="mt-4"
        >
          Verificar Resposta
        </Button>

        {isSubmitted && (
          <div className={cn("mt-4 p-3 rounded-md text-sm", feedbackClass)}>
            <p className="font-bold">{isCorrect ? 'Correto!' : 'Incorreto.'}</p>
            {!isCorrect && <p>A resposta correta é: <strong>{correct_answer}</strong></p>}
            <p>{feedbackText}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}