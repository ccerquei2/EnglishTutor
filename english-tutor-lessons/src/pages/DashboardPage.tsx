// /src/pages/DashboardPage.tsx

import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { useAuth } from '@/contexts/AuthContext';
import type { Lesson } from '@/types/lesson';
import { LessonItemRenderer } from '@/components/LessonItemRenderer';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { interactWithTutor, UserIntent, getConversationHistory, ChatMessage } from '@/services/tutorService';
import { TutorMessages } from '@/components/TutorMessages';
import { TutorChat } from '@/components/TutorChat';

export function DashboardPage() {
  const { user, profile, signOut } = useAuth();
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  // NOVO: Estado para armazenar o histórico de mensagens da conversa
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);

  // Efeito para carregar o histórico do chat ao iniciar a página
  useEffect(() => {
    const fetchHistory = async () => {
      const history = await getConversationHistory();
      setChatMessages(history);
    };
    fetchHistory();
  }, []);

  const handleInteraction = async (intent: UserIntent) => {
    setIsLoading(true);

    if (intent.type === 'button_click' && intent.action_id === 'generate_new_lesson') {
      setLesson(null);
    }
    // Se for uma mensagem de chat, adiciona a mensagem do usuário à UI imediatamente
    if (intent.type === 'chat_message') {
      const userMessage: ChatMessage = { role: 'user', content: intent.text ?? '' };
      setChatMessages(prev => [...prev, userMessage]);
    }

    const response = await interactWithTutor(intent);

    // Adiciona a resposta da IA à UI
    if (intent.type === 'chat_message') {
        const aiMessage: ChatMessage = { role: 'ai', content: response.message_to_user };
        setChatMessages(prev => [...prev, aiMessage]);
    }

    switch(response.response_type) {
      case 'new_lesson':
      case 'active_lesson_returned':
        setLesson(response.content ?? null);
        // Mostra toast para ações que geram lições
        toast.success(response.message_to_user);
        break;
      case 'tutor_feedback':
        if (intent.action_id === 'complete_current_lesson') {
           setLesson(null);
           toast.success(response.message_to_user); // Toast apenas ao completar lição
        }
        break;
      case 'error':
        toast.error(response.message_to_user);
        break;
    }

    setIsLoading(false);
  };

  const nativeLanguage = profile?.native_language_code || 'pt-BR';

  return (
    <div className="max-w-4xl mx-auto p-4 sm:p-6 lg:p-8">
      <header className="flex justify-between items-center pb-4 border-b">
        <h1 className="text-3xl font-bold">EnglishTutor</h1>
        <div className="flex items-center gap-4">
          {user?.email && <span className="text-sm text-muted-foreground">{user.email}</span>}
          <Button variant="destructive" size="sm" onClick={signOut}> Sair </Button>
        </div>
      </header>

      <main className="mt-6">
        <TutorMessages />

        {!lesson && (
          <div className="grid md:grid-cols-2 gap-8 items-start">
            <section className="flex flex-col gap-4">
              <h2 className="text-2xl font-semibold">Pronto para aprender?</h2>
              <p className="text-muted-foreground mt-1">Gere uma lição personalizada ou converse com seu tutor abaixo.</p>
              <Button
                onClick={() => handleInteraction({ type: 'button_click', action_id: 'generate_new_lesson' })}
                disabled={isLoading}
                className="mt-4 w-fit"
              >
                {isLoading ? 'Aguarde...' : 'Gerar Nova Lição'}
              </Button>
            </section>

            <section>
                <TutorChat
                  messages={chatMessages}
                  onSendMessage={handleInteraction}
                  isLoading={isLoading}
                />
            </section>
          </div>
        )}

        {lesson && Array.isArray(lesson.lesson_items) && (
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
                    nativeLanguageCode={nativeLanguage}
                  />
                ))}
              </div>
            </CardContent>
            <CardFooter className="flex justify-end pt-6">
              <Button
                onClick={() => handleInteraction({
                  type: 'button_click',
                  action_id: 'complete_current_lesson',
                  metadata: { lesson_id: lesson.lesson_id }
                })}
                disabled={isLoading}
              >
                {isLoading ? 'Finalizando...' : 'Concluir Lição'}
              </Button>
            </CardFooter>
          </Card>
        )}
      </main>
    </div>
  );
}