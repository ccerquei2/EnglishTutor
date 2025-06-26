// /src/pages/DashboardPage.tsx (Versão Final e Segura)

import { useState } from 'react';
import toast from 'react-hot-toast';
import { useAuth } from '@/contexts/AuthContext';
import apiClient from '@/lib/apiClient';
import type { Lesson } from '@/types/lesson';
import { LessonItemRenderer } from '@/components/LessonItemRenderer';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';

export function DashboardPage() {
  const { user, profile, signOut } = useAuth();
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [loadingLesson, setLoadingLesson] = useState(false);
  const [isCompleting, setIsCompleting] = useState(false);
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
      toast.error(err.response?.data?.detail || "Falha ao carregar a lição.");
    } finally {
      setLoadingLesson(false);
    }
  };

  const handleCompleteLesson = async () => {
    if (!lesson) return;
    setIsCompleting(true);
    try {
      await apiClient.post(`/lessons/${lesson.lesson_id}/complete`);
      toast.success("Lição concluída com sucesso! Pronto para a próxima.");
      setLesson(null);
    } catch (err: any) {
      console.error("Erro ao completar a lição:", err);
      toast.error("Não foi possível marcar a lição como concluída.");
    } finally {
      setIsCompleting(false);
    }
  };

  // Define um fallback seguro para a língua nativa
  const nativeLanguage = profile?.native_language_code || 'pt-BR';

  return (
    <div className="max-w-4xl mx-auto p-4 sm:p-6 lg:p-8">
      <header className="flex justify-between items-center pb-4 border-b">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <div className="flex items-center gap-4">
          {/* Adicionada verificação extra para user e user.email */}
          {user?.email && <span className="text-sm text-muted-foreground">{user.email}</span>}
          <Button variant="destructive" size="sm" onClick={signOut}> Sair </Button>
        </div>
      </header>

      <main className="mt-6">
        {!lesson && (
          <section>
            <h2 className="text-2xl font-semibold">Pronto para aprender?</h2>
            <p className="text-muted-foreground mt-1">Clique abaixo para gerar sua próxima lição personalizada.</p>
            <Button onClick={handleGetNewLesson} disabled={loadingLesson} className="mt-4">
              {loadingLesson ? 'Gerando sua lição...' : 'Gerar Nova Lição'}
            </Button>
          </section>
        )}

        {error && <p className="mt-4 text-red-600 bg-red-100 p-3 rounded-md">Erro: {error}</p>}

        {/* ### A VERIFICAÇÃO DE SEGURANÇA MAIS IMPORTANTE ESTÁ AQUI ### */}
        {/* Garantimos que 'lesson' e 'lesson.lesson_items' existam e sejam um array antes de mapear */}
        {lesson && Array.isArray(lesson.lesson_items) && (
          <Card className="mt-8">
            <CardHeader>
              <CardTitle className="text-2xl">{lesson.title}</CardTitle>
              <CardDescription>{lesson.objective}</CardDescription>
            </CardHeader>
            <CardContent>
              <h3 className="text-xl font-semibold mb-2">Itens da Lição:</h3>
              <div className="space-y-4">
                {lesson.lesson_items.map((item) => {
                  // Verificação extra dentro do map para garantir que o item é válido
                  if (!item || !item.id) {
                    console.error("Item da lição inválido encontrado:", item);
                    return null; // Pula a renderização deste item inválido
                  }
                  return (
                    <LessonItemRenderer
                      key={item.id}
                      item={item}
                      lessonId={lesson.lesson_id}
                      nativeLanguageCode={nativeLanguage}
                    />
                  );
                })}
              </div>
            </CardContent>
            <CardFooter className="flex justify-end pt-6">
              <Button onClick={handleCompleteLesson} disabled={isCompleting} variant="goo">
                {isCompleting ? "Finalizando..." : "Concluir Lição"}
              </Button>
            </CardFooter>
          </Card>
        )}
      </main>
    </div>
  );
}