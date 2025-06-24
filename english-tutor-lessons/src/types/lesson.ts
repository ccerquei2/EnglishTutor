// src/types/lesson.ts

// Define a estrutura de um único item dentro da lição
export interface LessonItem {
  id: string; // uuid da learning_unit
  unit_code: string;
  type: string;
  content: any; // Usamos 'any' por enquanto para flexibilidade
  metadata: any;
}

// Define a estrutura da lição completa que recebemos da API
export interface Lesson {
  id: string; // uuid da lição
  title: string;
  objective: string;
  lesson_items: LessonItem[];
}