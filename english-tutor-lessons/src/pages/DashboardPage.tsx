// /src/pages/DashboardPage.tsx

import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { TutorMessages } from '@/components/TutorMessages';
import { StudyPlanPage } from './StudyPlanPage';
import { LessonView } from '@/components/LessonView';
import type { Lesson } from '@/types/lesson';

export function DashboardPage() {
  const { user, signOut, profile } = useAuth();
  const [activeLesson, setActiveLesson] = useState<Lesson | null>(null);

  // NOVO: Estado para forçar a atualização da StudyPlanPage
  const [studyPlanKey, setStudyPlanKey] = useState(Date.now());

  const handleCompleteLesson = () => {
    setActiveLesson(null);
    // ATUALIZAÇÃO: Muda a 'key' da StudyPlanPage, forçando o React a recriar
    // o componente e, consequentemente, a executar seu useEffect novamente.
    setStudyPlanKey(Date.now());
  };

  return (
    <div className="max-w-4xl mx-auto p-4 sm:p-6 lg:p-8">
      <header className="flex justify-between items-center pb-4 border-b">
        <h1 className="text-3xl font-bold">EnglishTutor</h1>
        <div className="flex items-center gap-4">
          {user?.email && <span className="text-sm text-muted-foreground">{user.email}</span>}
          <Button variant="outline" size="sm" onClick={signOut}> Sair </Button>
        </div>
      </header>

      <main className="mt-6">
        <TutorMessages />

        {activeLesson ? (
          <LessonView
            lesson={activeLesson}
            onComplete={handleCompleteLesson}
            nativeLanguageCode={profile?.native_language_code || 'pt-BR'}
          />
        ) : (
          <StudyPlanPage
            key={studyPlanKey} // <-- A MÁGICA ACONTECE AQUI
            onStartLesson={setActiveLesson}
          />
        )}
      </main>
    </div>
  );
}