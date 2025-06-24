// /src/components/exercises/ReadAndAnswerExercise.tsx

import { useState } from 'react';
import type { LessonItem } from '@/types/lesson';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { cn } from "@/lib/utils";

interface ExerciseProps {
  item: LessonItem;
  onAnswerSubmit: (isCorrect: boolean, studentResponse: string) => void;
}

export function ReadAndAnswerExercise({ item, onAnswerSubmit }: ExerciseProps) {
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [isCorrect, setIsCorrect] = useState(false);

  const { text, question, options, correct_answer, feedback } = item.content;
  const feedbackText = feedback['pt-BR'] || feedback['en-US'];

  const handleOptionSelect = (option: string) => {
    if (isSubmitted) return;
    setSelectedOption(option);
  };

  const handleSubmit = () => {
    if (!selectedOption) return;
    const correct = selectedOption === correct_answer;
    setIsCorrect(correct);
    setIsSubmitted(true);
    onAnswerSubmit(correct, selectedOption);
  };

  const feedbackClass = isCorrect ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800';

  return (
    <Card className="border-slate-200">
      <CardContent className="p-6">
        {/* Bloco de texto para leitura, agora com melhor estilo */}
        <div className="mb-4 p-4 bg-slate-50 rounded-lg border">
          <p className="text-slate-800 italic">{text}</p>
        </div>

        <p className="text-lg font-semibold mb-4">{question}</p>

        <div className="space-y-2">
          {options.map((option: string, index: number) => (
            <Button
              key={index}
              onClick={() => handleOptionSelect(option)}
              disabled={isSubmitted}
              variant={selectedOption === option ? "default" : "secondary"}
              className={cn(
                "w-full justify-start h-auto text-left py-3",
                isSubmitted && correct_answer === option && "bg-green-500 hover:bg-green-600",
                isSubmitted && selectedOption === option && correct_answer !== option && "bg-red-500 hover:bg-red-600"
              )}
            >
              {option}
            </Button>
          ))}
        </div>

        <Button
          onClick={handleSubmit}
          disabled={isSubmitted || !selectedOption}
          className="mt-4"
        >
          Verificar Resposta
        </Button>

        {isSubmitted && (
          <div className={cn("mt-4 p-3 rounded-md text-sm", feedbackClass)}>
            <p className="font-bold">{isCorrect ? 'Correto!' : 'Incorreto.'}</p>
            <p>{feedbackText}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}