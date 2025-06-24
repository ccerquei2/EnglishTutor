// /src/components/exercises/MatchExercise.tsx

import { useState, useEffect, useMemo } from 'react';
import type { LessonItem } from '@/types/lesson';
import { Card, CardContent } from '@/components/ui/card';
import { cn } from "@/lib/utils";
import { shuffle } from 'lodash'; // Usaremos a função shuffle da biblioteca lodash

// Definindo o tipo para os pares de pergunta e resposta
type Pair = { question: string; answer: string };

interface ExerciseProps {
  item: LessonItem;
  onAnswerSubmit: (isCorrect: boolean, studentResponse: string) => void;
}

export function MatchExercise({ item, onAnswerSubmit }: ExerciseProps) {
  const { question, pairs }: { question: string, pairs: Pair[] } = item.content;

  // useMemo garante que as respostas sejam embaralhadas apenas uma vez
  const shuffledAnswers = useMemo(() => shuffle(pairs.map(p => p.answer)), [pairs]);

  const [selectedQuestion, setSelectedQuestion] = useState<string | null>(null);
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [matchedPairs, setMatchedPairs] = useState<Pair[]>([]);
  const [incorrectAttempt, setIncorrectAttempt] = useState<[string, string] | null>(null);

  const allMatched = matchedPairs.length === pairs.length;

  // Efeito para verificar se um par foi formado
  useEffect(() => {
    if (selectedQuestion && selectedAnswer) {
      const correctPair = pairs.find(p => p.question === selectedQuestion);

      if (correctPair && correctPair.answer === selectedAnswer) {
        // Se o par estiver correto
        setMatchedPairs([...matchedPairs, correctPair]);
        setSelectedQuestion(null);
        setSelectedAnswer(null);
      } else {
        // Se o par estiver incorreto, mostra um feedback visual e reseta
        setIncorrectAttempt([selectedQuestion, selectedAnswer]);
        setTimeout(() => {
          setSelectedQuestion(null);
          setSelectedAnswer(null);
          setIncorrectAttempt(null);
        }, 800); // Reseta após 0.8 segundos
      }
    }
  }, [selectedQuestion, selectedAnswer, pairs, matchedPairs]);

  // Efeito para submeter a resposta quando tudo for combinado
  useEffect(() => {
    if (allMatched) {
      // A resposta submetida pode ser um simples JSON dos pares
      onAnswerSubmit(true, JSON.stringify(pairs));
    }
  }, [allMatched, onAnswerSubmit, pairs]);

  // Funções para obter a classe de estilo dinamicamente
  const getQuestionClass = (q: string) => {
    if (matchedPairs.some(p => p.question === q)) return 'bg-green-200 border-green-400';
    if (selectedQuestion === q) return 'bg-blue-200 border-blue-400';
    if (incorrectAttempt && incorrectAttempt[0] === q) return 'bg-red-200 border-red-400';
    return 'bg-slate-100 hover:bg-slate-200';
  };

  const getAnswerClass = (a: string) => {
    if (matchedPairs.some(p => p.answer === a)) return 'bg-green-200 border-green-400';
    if (selectedAnswer === a) return 'bg-blue-200 border-blue-400';
    if (incorrectAttempt && incorrectAttempt[1] === a) return 'bg-red-200 border-red-400';
    return 'bg-slate-100 hover:bg-slate-200';
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
          {/* Coluna de Perguntas */}
          <div className="space-y-2">
            {pairs.map(p => (
              <button
                key={p.question}
                onClick={() => !matchedPairs.some(mp => mp.question === p.question) && setSelectedQuestion(p.question)}
                disabled={allMatched || !!selectedQuestion}
                className={cn("w-full p-3 text-left rounded-md border-2 transition-colors", getQuestionClass(p.question))}
              >
                {p.question}
              </button>
            ))}
          </div>

          {/* Coluna de Respostas (Embaralhada) */}
          <div className="space-y-2">
            {shuffledAnswers.map(answer => (
              <button
                key={answer}
                onClick={() => !matchedPairs.some(mp => mp.answer === answer) && setSelectedAnswer(answer)}
                disabled={allMatched || !!selectedAnswer}
                className={cn("w-full p-3 text-left rounded-md border-2 transition-colors", getAnswerClass(answer))}
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