// /src/components/exercises/ChooseOptionExercise.tsx

import { useState } from 'react';
import type { LessonItem } from '@/types/lesson';
// 1. Importe o Button e o Card
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { cn } from "@/lib/utils"; // Importa a função utilitária para classes condicionais

interface ExerciseProps {
  item: LessonItem;
  onAnswerSubmit: (isCorrect: boolean, studentResponse: string) => void;
}

export function ChooseOptionExercise({ item, onAnswerSubmit }: ExerciseProps) {
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [isCorrect, setIsCorrect] = useState(false);

  const { question, options, correct_answer, feedback } = item.content;
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

  // Lógica para a cor do feedback
  const feedbackClass = isCorrect ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800';

  return (
    // 2. Envolvemos o exercício em um <Card> com uma borda sutil
    <Card className="border-slate-200">
      <CardContent className="p-6">
        <p className="text-lg font-semibold mb-4">{question}</p>
        <div className="space-y-2">
          {options.map((option: string, index: number) => (
            // 3. Usamos o componente <Button> para as opções
            <Button
              key={index}
              onClick={() => handleOptionSelect(option)}
              disabled={isSubmitted}
              // Usamos a prop 'variant' para controlar o estilo do botão
              variant={selectedOption === option ? "default" : "secondary"}
              // Usamos 'cn' para adicionar classes condicionais de forma limpa
              className={cn(
                "w-full justify-start h-auto text-left py-3", // Estilo base
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