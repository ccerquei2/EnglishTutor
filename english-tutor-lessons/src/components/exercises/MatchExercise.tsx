// /src/components/exercises/MatchExercise.tsx

import { useState, useEffect, useMemo } from 'react';
import type { LessonItem } from '@/types/lesson';
import { Card, CardContent } from '@/components/ui/card';
import { cn } from "@/lib/utils";
import { shuffle } from 'lodash';

type Pair = { question: string; answer: string };

interface ExerciseProps {
  item: LessonItem;
  onAnswerSubmit: (isCorrect: boolean, studentResponse: string) => void;
}

export function MatchExercise({ item, onAnswerSubmit }: ExerciseProps) {
  const { question, pairs }: { question: string, pairs: Pair[] } = item.content;
  const shuffledAnswers = useMemo(() => shuffle(pairs.map(p => p.answer)), [pairs]);

  const [selectedQuestion, setSelectedQuestion] = useState<string | null>(null);
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [matchedPairs, setMatchedPairs] = useState<Pair[]>([]);
  const [incorrectAttempt, setIncorrectAttempt] = useState<[string, string] | null>(null);

  const allMatched = matchedPairs.length === pairs.length;

  const handleQuestionClick = (q: string) => {
    if (incorrectAttempt || isButtonDisabled(q, 'question')) return;
    setSelectedQuestion(prev => (prev === q ? null : q));
  };

  const handleAnswerClick = (a: string) => {
    if (incorrectAttempt || isButtonDisabled(a, 'answer')) return;
    setSelectedAnswer(prev => (prev === a ? null : a));
  };

  useEffect(() => {
    if (selectedQuestion && selectedAnswer) {
      const correctPair = pairs.find(p => p.question === selectedQuestion);

      if (correctPair?.answer === selectedAnswer) {
        setMatchedPairs(prev => [...prev, correctPair]);
        setSelectedQuestion(null);
        setSelectedAnswer(null);
      } else {
        setIncorrectAttempt([selectedQuestion, selectedAnswer]);
        setTimeout(() => {
          setSelectedQuestion(null);
          setSelectedAnswer(null);
          setIncorrectAttempt(null);
        }, 800);
      }
    }
  }, [selectedQuestion, selectedAnswer, pairs]);

  useEffect(() => {
    if (allMatched) {
      // A submissão automática legada continua desativada.
      console.log("MatchExercise concluído. O progresso será salvo ao finalizar a lição.");
      // onAnswerSubmit(true, JSON.stringify(pairs));
    }
  }, [allMatched]); // Removidas dependências desnecessárias

  const getButtonClass = (text: string, type: 'question' | 'answer') => {
    const isMatched = matchedPairs.some(p => p[type] === text);
    if (isMatched) return 'bg-green-200 border-green-400 text-green-900 opacity-70 cursor-not-allowed';

    const isIncorrect = incorrectAttempt && (incorrectAttempt[0] === text || incorrectAttempt[1] === text);
    if (isIncorrect) return 'bg-red-200 border-red-400 text-red-900 animate-shake';

    const isSelected = type === 'question' ? selectedQuestion === text : selectedAnswer === text;
    if (isSelected) return 'bg-blue-200 border-blue-400 ring-2 ring-blue-500';

    return 'bg-slate-100 hover:bg-slate-200 border-slate-300';
  };

  const isButtonDisabled = (text: string, type: 'question' | 'answer') => {
    return allMatched || matchedPairs.some(p => p[type] === text);
  };

  return (
    <Card className="border-slate-200">
      <CardContent className="p-6">
        <p className="text-lg font-semibold mb-4">{question}</p>

        {allMatched && (
          <div className="p-3 rounded-md bg-green-100 text-green-800 font-bold text-center">
            Excelente! Todos os pares combinados!
          </div>
        )}

        <div className="grid grid-cols-2 gap-4 mt-4">
          <div className="space-y-2">
            {pairs.map(p => (
              <button
                key={p.question}
                onClick={() => handleQuestionClick(p.question)}
                disabled={isButtonDisabled(p.question, 'question')}
                className={cn("w-full p-3 text-left rounded-md border-2 transition-all duration-200", getButtonClass(p.question, 'question'))}
              >
                {p.question}
              </button>
            ))}
          </div>
          <div className="space-y-2">
            {shuffledAnswers.map(answer => (
              <button
                key={answer}
                onClick={() => handleAnswerClick(answer)}
                disabled={isButtonDisabled(answer, 'answer')}
                className={cn("w-full p-3 text-left rounded-md border-2 transition-all duration-200", getButtonClass(answer, 'answer'))}
              >
                {answer}
              </button>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}