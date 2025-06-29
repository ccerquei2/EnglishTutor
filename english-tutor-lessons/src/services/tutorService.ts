// /src/services/tutorService.ts

// CORREÇÃO: O caminho foi ajustado para apontar para o diretório 'lib' usando o alias '@'.
import { supabase } from '@/lib/supabaseClient';

// --- TIPOS DE DADOS ---

export interface AIResponse {
  response_type: 'new_lesson' | 'active_lesson_returned' | 'tutor_feedback' | 'error';
  message_to_user: string;
  content?: any; // Pode ser uma lição ou nulo
}

export interface UserIntent {
  type: 'button_click' | 'chat_message';
  action_id?: string;
  text?: string;
  metadata?: Record<string, any>;
}

// NOVO TIPO para mensagens de chat
export interface ChatMessage {
  role: 'user' | 'ai';
  content: string;
}

// --- FUNÇÕES DE API ---

/**
 * Ponto de entrada unificado para interagir com o tutor de IA.
 */
export async function interactWithTutor(intent: UserIntent): Promise<AIResponse> {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) throw new Error("Usuário não autenticado");

  const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/tutor/interact`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${session.access_token}`
    },
    body: JSON.stringify(intent),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Erro desconhecido na API' }));
    return {
      response_type: 'error',
      message_to_user: errorData.detail || 'Ocorreu um erro no servidor.',
    };
  }
  return response.json();
}

/**
 * Busca o histórico de conversas do usuário.
 */
export async function getConversationHistory(): Promise<ChatMessage[]> {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) return [];

  const { data, error } = await supabase
    .from('conversation_history')
    .select('role, content')
    .order('created_at', { ascending: true });

  if (error) {
    console.error('Erro ao buscar histórico da conversa:', error);
    return [];
  }

  // O tipo já deve bater com ChatMessage[], mas garantimos com um 'as'
  return (data as ChatMessage[]) || [];
}