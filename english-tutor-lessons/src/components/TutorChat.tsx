// /src/components/TutorChat.tsx

import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { UserIntent, ChatMessage } from '@/services/tutorService';
import { Send, User, Bot } from 'lucide-react';
import { cn } from '@/lib/utils';

interface TutorChatProps {
  messages: ChatMessage[];
  onSendMessage: (intent: UserIntent) => void;
  isLoading: boolean;
}

export function TutorChat({ messages, onSendMessage, isLoading }: TutorChatProps) {
  const [text, setText] = useState('');
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  // Efeito para rolar para a última mensagem
  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [messages]);

  const handleFormSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!text.trim() || isLoading) return;

    const intent: UserIntent = { type: 'chat_message', text: text.trim() };
    onSendMessage(intent);
    setText('');
  };

  return (
    <Card className="flex flex-col h-[500px]">
      <CardHeader>
        <CardTitle>Converse com seu Tutor</CardTitle>
      </CardHeader>

      <CardContent className="flex-grow overflow-y-auto p-4 space-y-4" ref={scrollAreaRef}>
        {messages.map((msg, index) => (
          <div key={index} className={cn("flex items-start gap-3", msg.role === 'user' ? 'justify-end' : 'justify-start')}>
            {/* Ícone do Tutor (AI) */}
            {msg.role === 'ai' && <div className="bg-primary text-primary-foreground rounded-full p-2"><Bot size={20} /></div>}

            {/* Balão da Mensagem */}
            <div
              className={cn(
                "max-w-xs md:max-w-md p-3 rounded-lg",
                msg.role === 'user' ? 'bg-secondary text-secondary-foreground rounded-br-none' : 'bg-muted rounded-bl-none'
              )}
            >
              <p className="text-sm">{msg.content}</p>
            </div>

            {/* Ícone do Usuário */}
            {msg.role === 'user' && <div className="bg-slate-300 text-slate-800 rounded-full p-2"><User size={20} /></div>}
          </div>
        ))}
        {isLoading && messages[messages.length-1]?.role === 'user' && (
             <div className="flex items-start gap-3 justify-start">
                <div className="bg-primary text-primary-foreground rounded-full p-2"><Bot size={20} /></div>
                <div className="max-w-xs md:max-w-md p-3 rounded-lg bg-muted rounded-bl-none">
                    <p className="text-sm italic">Digitando...</p>
                </div>
            </div>
        )}
      </CardContent>

      <form onSubmit={handleFormSubmit}>
        <CardFooter className="flex items-center gap-2 border-t pt-4">
          <Input
            id="chat-input"
            type="text"
            placeholder="Digite sua mensagem..."
            value={text}
            onChange={(e) => setText(e.target.value)}
            disabled={isLoading}
            autoComplete="off"
          />
          <Button type="submit" size="icon" disabled={isLoading || !text.trim()} aria-label="Enviar mensagem">
            <Send className="h-4 w-4" />
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
}