// /src/components/LessonView.tsx

import { useState } from 'react';
import { LessonItemRenderer } from './LessonItemRenderer';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import type { Lesson } from '@/types/lesson';
import toast from 'react-hot-toast';
import { completeStudyPlanLesson } from '@/services/tutorService';

interface LessonViewProps {
  lesson: Lesson;
  onComplete: () => void;
  nativeLanguageCode: string;
}

export function LessonView({ lesson, onComplete, nativeLanguageCode }: LessonViewProps) {
  const [isLoading, setIsLoading] = useState(false);

  const handleCompleteClick = async () => {
    // CORREÇÃO: Verifica se o module_id existe antes de prosseguir.
    if (!lesson.module_id) {
      toast.error("Erro: ID do módulo não encontrado. Não foi possível salvar o progresso.");
      return;
    }

    setIsLoading(true);
    try {
      // Agora usamos o ID correto que veio da API
      await completeStudyPlanLesson(lesson.module_id);
      toast.success("Lição concluída! Progresso salvo.");
      onComplete();
    } catch (error) {
      console.error("Erro ao completar a lição:", error);
      const errorMessage = error instanceof Error ? error.message : "Houve um problema ao salvar seu progresso.";
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="mt-8">
      <CardHeader>
        <CardTitle className="text-2xl">{lesson.title}</CardTitle>
        <CardDescription>{lesson.objective}</CardDescription>
      </CardHeader>
      <CardContent>
        <h3 className="text-xl font-semibold mb-2">Itens da Lição:</h3>
        <div className="space-y-4">
          {lesson.lesson_items.map((item) => (
            <LessonItemRenderer
              key={item.id}
              item={item}
              lessonId={lesson.lesson_id}
              nativeLanguageCode={nativeLanguageCode}
            />
          ))}
        </div>
      </CardContent>
      <CardFooter className="flex justify-end pt-6">
        <Button onClick={handleCompleteClick} disabled={isLoading}>
          {isLoading ? 'Finalizando...' : 'Concluir Lição'}
        </Button>
      </CardFooter>
    </Card>
  );
}