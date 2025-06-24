// /src/components/exercises/ReorderWordsExercise.tsx

import { useState } from 'react';
import type { LessonItem } from '@/types/lesson';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { cn } from "@/lib/utils";
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core';
import {
  SortableContext,
  sortableKeyboardCoordinates,
  rectSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

// Componente interno para uma única palavra arrastável
function SortableWord({ id, word }: { id: string, word: string }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
  } = useSortable({ id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners}>
      <div className="bg-slate-200 text-slate-800 px-4 py-2 rounded-md cursor-grab active:cursor-grabbing">
        {word}
      </div>
    </div>
  );
}

interface ExerciseProps {
  item: LessonItem;
  onAnswerSubmit: (isCorrect: boolean, studentResponse: string) => void;
}

export function ReorderWordsExercise({ item, onAnswerSubmit }: ExerciseProps) {
  // Damos a cada palavra um ID único para o dnd-kit
  const initialWords = item.content.words.map((word: string, index: number) => ({ id: `word-${index}`, text: word }));

  const [availableWords, setAvailableWords] = useState(initialWords);
  const [sentenceWords, setSentenceWords] = useState<{id: string, text: string}[]>([]);

  const [isSubmitted, setIsSubmitted] = useState(false);
  const [isCorrect, setIsCorrect] = useState(false);

  const { question, correct_answer, feedback } = item.content;
  const feedbackText = feedback['pt-BR'] || feedback['en-US'];

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      // Lógica para mover entre as listas (não implementada neste exemplo simples)
      // Para este exercício, o clique é uma abordagem mais simples.
    }
  }

  // Usaremos clique em vez de drag-and-drop complexo para simplificar
  const moveWordToSentence = (wordToMove: {id: string, text: string}) => {
    if(isSubmitted) return;
    setSentenceWords([...sentenceWords, wordToMove]);
    setAvailableWords(availableWords.filter(w => w.id !== wordToMove.id));
  };

  const moveWordToBank = (wordToMove: {id: string, text: string}) => {
    if(isSubmitted) return;
    setAvailableWords([...availableWords, wordToMove]);
    setSentenceWords(sentenceWords.filter(w => w.id !== wordToMove.id));
  };

  const handleSubmit = () => {
    const studentResponse = sentenceWords.map(w => w.text).join(' ');
    if (!studentResponse) return;

    const correct = studentResponse === correct_answer;
    setIsCorrect(correct);
    setIsSubmitted(true);
    onAnswerSubmit(correct, studentResponse);
  };

  const feedbackClass = isCorrect ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800';

  return (
    <Card className="border-slate-200">
      <CardContent className="p-6">
        <p className="text-lg font-semibold mb-4">{question}</p>

        {/* Área da Resposta (onde as palavras são colocadas) */}
        <div className="w-full min-h-[60px] bg-slate-100 p-3 rounded-md border-2 border-dashed flex flex-wrap gap-2 items-center">
          {sentenceWords.map(word => (
            <button key={word.id} onClick={() => moveWordToBank(word)} disabled={isSubmitted}
              className="bg-blue-500 text-white px-4 py-2 rounded-md"
            >
              {word.text}
            </button>
          ))}
        </div>

        {/* Banco de Palavras Disponíveis */}
        <div className="w-full mt-4 flex flex-wrap gap-2 items-center">
          {availableWords.map(word => (
            <button key={word.id} onClick={() => moveWordToSentence(word)} disabled={isSubmitted}
              className="bg-slate-200 text-slate-800 px-4 py-2 rounded-md"
            >
              {word.text}
            </button>
          ))}
        </div>

        <Button
          onClick={handleSubmit}
          disabled={isSubmitted || sentenceWords.length === 0}
          className="mt-6"
        >
          Verificar Frase
        </Button>

        {isSubmitted && (
          <div className={cn("mt-4 p-3 rounded-md text-sm", feedbackClass)}>
            <p className="font-bold">{isCorrect ? 'Correto!' : 'Incorreto.'}</p>
            <p>{feedbackText}</p>
            {!isCorrect && <p>A resposta correta é: "{correct_answer}"</p>}
          </div>
        )}
      </CardContent>
    </Card>
  );
}