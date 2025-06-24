// /src/components/exercises/FillInTheBlankExercise.tsx

import { useState } from 'react';
import type { LessonItem } from '@/types/lesson';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input'; // Vamos usar o componente Input do Shadcn
import { cn } from "@/lib/utils";

interface ExerciseProps {
  item: LessonItem;
  onAnswerSubmit: (isCorrect: boolean, studentResponse: string) => void;
}

export function FillInTheBlankExercise({ item, onAnswerSubmit }: ExerciseProps) {
  const [studentInput, setStudentInput] = useState('');
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [isCorrect, setIsCorrect] = useState(false);

  const { question, correct_answer, feedback } = item.content;
  const feedbackText = feedback['pt-BR'] || feedback['en-US'];

  // Divide a questão em duas partes onde a lacuna '___' está
  const parts = question.split('___');
  const firstPart = parts[0];
  const secondPart = parts[1] || ''; // Garante que a segunda parte exista

  const handleSubmit = () => {
    if (!studentInput.trim()) return;

    // Compara a resposta ignorando maiúsculas/minúsculas e espaços extras
    const correct = studentInput.trim().toLowerCase() === correct_answer.toLowerCase();
    setIsCorrect(correct);
    setIsSubmitted(true);
    onAnswerSubmit(correct, studentInput.trim());
  };

  const feedbackClass = isCorrect ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800';

  return (
    <Card className="border-slate-200">
      <CardContent className="p-6">
        <div className="flex flex-wrap items-center gap-2 text-lg font-semibold mb-4">
          <span>{firstPart}</span>
          <Input
            type="text"
            value={studentInput}
            onChange={(e) => setStudentInput(e.target.value)}
            disabled={isSubmitted}
            className="w-32 text-center"
            placeholder="..."
          />
          <span>{secondPart}</span>
        </div>

        <Button
          onClick={handleSubmit}
          disabled={isSubmitted || !studentInput.trim()}
          className="mt-4"
        >
          Verificar Resposta
        </Button>

        {isSubmitted && (
          <div className={cn("mt-4 p-3 rounded-md text-sm", feedbackClass)}>
            <p className="font-bold">{isCorrect ? 'Correto!' : 'Incorreto.'}</p>
            <p>{feedbackText}</p>
            {!isCorrect && <p>A resposta correta é: "<strong>{correct_answer}</strong>"</p>}
          </div>
        )}
      </CardContent>
    </Card>
  );
}