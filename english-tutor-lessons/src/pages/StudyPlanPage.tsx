// /src/pages/StudyPlanPage.tsx

import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { getStudyPlanProgress, startStudyPlanLesson, StudyPlanProgress } from '@/services/tutorService';
import { ModuleCard } from '@/components/ui/ModuleCard';
import { Skeleton } from '@/components/ui/skeleton';
import type { Lesson } from '@/types/lesson';

interface StudyPlanPageProps {
  onStartLesson: (lesson: Lesson) => void;
}

export function StudyPlanPage({ onStartLesson }: StudyPlanPageProps) {
  const [studyPlan, setStudyPlan] = useState<StudyPlanProgress | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isStartingLesson, setIsStartingLesson] = useState(false);

  const fetchStudyPlan = async () => {
    if (!isStartingLesson) setIsLoading(true);
    try {
      const data = await getStudyPlanProgress();
      setStudyPlan(data);
    } catch (error) {
      console.error(error);
      toast.error("Não foi possível carregar seu plano de estudos.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStudyPlan();
  }, []);

  const handleStartLessonClick = async (moduleId: string) => {
    setIsStartingLesson(true);
    try {
      const lessonData = await startStudyPlanLesson(moduleId);
      onStartLesson(lessonData);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Não foi possível iniciar a lição.";
      // Mensagem amigável se a lição ainda não tiver conteúdo
      if (errorMessage.includes("Nenhuma lição disponível")) {
        toast.error("Este módulo ainda está em preparação. Volte em breve!");
      } else {
        toast.error(errorMessage);
      }
      setIsStartingLesson(false);
    }
  };

  if (isLoading) return <StudyPlanSkeleton />;
  if (!studyPlan || !studyPlan.modules || studyPlan.modules.length === 0) {
    return (
      <div className="text-center p-10 border rounded-lg bg-slate-50">
        <h3 className="text-xl font-semibold">Jornada em Preparação!</h3>
        <p className="text-muted-foreground mt-2">Nenhum plano de estudos está disponível para seu nível ainda.</p>
      </div>
    );
  }

  const { overall_progress, modules } = studyPlan;

  // LÓGICA DE DESBLOQUEIO REFINADA: O módulo ativo é o primeiro que não está 'completed'.
  const activeModuleIndex = modules.findIndex(m => m.status !== 'completed');

  return (
    <section className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold">Sua Jornada no Nível A1</h2>
        <p className="text-muted-foreground">Complete os módulos em sequência para avançar.</p>
        <div className="mt-4 space-y-2">
          <div className="flex justify-between font-medium">
            <span>Progresso Geral</span>
            <span>{overall_progress.percentage}%</span>
          </div>
          <div className="w-full bg-slate-200 rounded-full h-4">
            <div className="bg-green-600 h-4 rounded-full text-white flex items-center justify-center text-xs" style={{ width: `${overall_progress.percentage}%` }}>
              {overall_progress.percentage > 10 && `${overall_progress.percentage}%`}
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        {modules.map((module, index) => (
          <ModuleCard
            key={module.module_id}
            module={module}
            // O módulo está ativo se o seu índice for o primeiro não completado
            isActive={activeModuleIndex !== -1 && index === activeModuleIndex}
            onStartLesson={handleStartLessonClick}
            isLoading={isStartingLesson}
          />
        ))}
      </div>
    </section>
  );
}

const StudyPlanSkeleton = () => (
  <section className="space-y-8">
    <div>
      <Skeleton className="h-8 w-3/4 mb-2" />
      <Skeleton className="h-4 w-1/2" />
      <div className="mt-4 space-y-2">
        <Skeleton className="h-4 w-full" />
      </div>
    </div>
    <div className="space-y-4">
      <Skeleton className="h-32 w-full" />
      <Skeleton className="h-32 w-full" />
      <Skeleton className="h-32 w-full" />
    </div>
  </section>
);