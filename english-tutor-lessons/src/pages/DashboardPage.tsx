// /src/pages/DashboardPage.tsx

import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext'; // Usando o novo alias
import apiClient from '@/lib/apiClient';          // Usando o novo alias
import type { Lesson } from '@/types/lesson';
import { LessonItemRenderer } from '@/components/LessonItemRenderer';

// 1. Importe os novos componentes de UI
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';

export function DashboardPage() {
  const { user, signOut } = useAuth();
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [loadingLesson, setLoadingLesson] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGetNewLesson = async () => {
    setLoadingLesson(true);
    setError(null);
    setLesson(null);

    try {
      const response = await apiClient.post<Lesson>('/lessons/new');
      setLesson(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Não foi possível carregar a lição.");
    } finally {
      setLoadingLesson(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-4 sm:p-6 lg:p-8">
      <header className="flex justify-between items-center pb-4 border-b">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <div className="flex items-center gap-4">
          {user && <span className="text-sm text-muted-foreground">{user.email}</span>}
          {/* 2. Substituímos o <button> pelo <Button> do Shadcn */}
          <Button variant="destructive" size="sm" onClick={signOut}>
            Sair
          </Button>
        </div>
      </header>

      <main className="mt-6">
        <section>
          <h2 className="text-2xl font-semibold">Sua Próxima Lição</h2>
          {/* 3. Substituímos o <button> pelo <Button> do Shadcn */}
          <Button onClick={handleGetNewLesson} disabled={loadingLesson} className="mt-2">
            {loadingLesson ? 'Gerando sua lição...' : 'Gerar Nova Lição'}
          </Button>
        </section>

        {error && (
            // Futuramente, podemos usar o componente <Alert> do Shadcn aqui
            <p className="mt-4 text-red-600 bg-red-100 p-3 rounded-md">Erro: {error}</p>
        )}

        {lesson && (
          // 4. Envolvemos a lição em um <Card> para um visual mais limpo
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
                  />
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  );
}