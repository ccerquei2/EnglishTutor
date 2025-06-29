// /src/components/TutorMessages.tsx

import { useEffect, useState } from 'react';
import apiClient from '@/lib/apiClient';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Mail } from 'lucide-react';
import toast from 'react-hot-toast';

interface TutorMessage {
  id: number;
  message_content: string;
}

export function TutorMessages() {
  const [messages, setMessages] = useState<TutorMessage[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchMessages = async () => {
    try {
      const response = await apiClient.get<TutorMessage[]>('/tutor/messages');
      setMessages(response.data);
    } catch (error) {
      console.error("Erro ao buscar mensagens do tutor:", error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchMessages();
  }, []);

  const handleMarkAsRead = async (messageId: number) => {
    // Remove a mensagem da UI imediatamente para uma experiência mais fluida
    setMessages(messages.filter(msg => msg.id !== messageId));

    try {
      // Informa ao backend que a mensagem foi lida
      await apiClient.post(`/tutor/messages/${messageId}/read`);
    } catch (error) {
      toast.error("Não foi possível marcar a mensagem como lida.");
      // Se der erro, busca as mensagens novamente para sincronizar o estado
      fetchMessages();
    }
  };

  if (isLoading || messages.length === 0) {
    return null; // Não renderiza nada se estiver carregando ou se não houver mensagens
  }

  return (
    <section className="mb-8">
      <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-blue-900">
            <Mail className="h-5 w-5" />
            Uma Mensagem do seu Tutor
          </CardTitle>
        </CardHeader>
        <CardContent>
          {messages.map(msg => (
            <div key={msg.id} className="mb-4">
              <p className="text-slate-700">{msg.message_content}</p>
              <Button
                variant="ghost"
                size="sm"
                className="mt-2 text-blue-700 hover:bg-blue-100"
                onClick={() => handleMarkAsRead(msg.id)}
              >
                Entendido!
              </Button>
            </div>
          ))}
        </CardContent>
      </Card>
    </section>
  );
}