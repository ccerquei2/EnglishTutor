// /src/services/tutorService.ts

import { supabase } from '@/lib/supabaseClient';
import type { Lesson } from '@/types/lesson';

// --- TIPOS DE DADOS ---

export interface AIResponse {
  response_type: 'new_lesson' | 'active_lesson_returned' | 'tutor_feedback' | 'error';
  message_to_user: string;
  content?: Lesson;
}

export interface UserIntent {
  type: 'button_click' | 'chat_message';
  action_id?: string;
  text?: string;
  metadata?: Record<string, any>;
}

export interface ChatMessage {
  role: 'user' | 'ai';
  content: string;
}

export interface ModuleProgress {
  module_id: string;
  module_order: number;
  title: string;
  description: string;
  status: 'locked' | 'in_progress' | 'completed';
  progress: {
    total_lessons: number;
    completed_lessons: number;
  };
}

export interface StudyPlanProgress {
  overall_progress: {
    completed_modules: number;
    total_modules: number;
    percentage: number;
  };
  modules: ModuleProgress[];
}


// --- FUNÇÕES DE API ---

/**
 * Busca e retorna o conteúdo da próxima lição disponível para o aluno em um módulo.
 */
export async function startStudyPlanLesson(moduleId: string): Promise<Lesson> {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) throw new Error("Usuário não autenticado para iniciar a lição.");

  const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/study-plan/start-lesson`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${session.access_token}`
    },
    body: JSON.stringify({ module_id: moduleId }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Falha ao iniciar a lição.' }));
    throw new Error(errorData.detail);
  }
  return response.json();
}


/**
 * Informa ao backend que o aluno completou a lição atual de um módulo.
 */
export async function completeStudyPlanLesson(moduleId: string): Promise<void> {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) throw new Error("Usuário não autenticado para completar a lição.");

  const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/study-plan/complete-lesson`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${session.access_token}`
    },
    body: JSON.stringify({ module_id: moduleId }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Falha ao completar a lição.' }));
    throw new Error(errorData.detail);
  }
  // Não precisa retornar nada em caso de sucesso (status 204)
}

/**
 * Busca o estado completo da jornada de aprendizado do usuário.
 */
export async function getStudyPlanProgress(): Promise<StudyPlanProgress> {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) throw new Error("Usuário não autenticado para buscar o plano de estudos.");

  const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/study-plan/progress`, {
    method: 'GET',
    headers: { 'Authorization': `Bearer ${session.access_token}` },
  });

  if (!response.ok) throw new Error('Falha ao buscar o progresso do plano de estudos.');
  return response.json();
}

/**
 * Ponto de entrada unificado para interagir com o tutor de IA (Modo Prática).
 */
export async function interactWithTutor(intent: UserIntent): Promise<AIResponse> {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) throw new Error("Usuário não autenticado");

  const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/tutor/interact`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${session.access_token}` },
    body: JSON.stringify(intent),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Erro desconhecido na API' }));
    return { response_type: 'error', message_to_user: errorData.detail || 'Ocorreu um erro no servidor.' };
  }
  return response.json();
}

/**
 * Busca o histórico de conversas do usuário.
 */
export async function getConversationHistory(): Promise<ChatMessage[]> {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) return [];

  const { data, error } = await supabase.from('conversation_history').select('role, content').order('created_at', { ascending: true });

  if (error) {
    console.error('Erro ao buscar histórico da conversa:', error);
    return [];
  }
  return (data as ChatMessage[]) || [];
}