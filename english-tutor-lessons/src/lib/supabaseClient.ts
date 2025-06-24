// src/lib/supabaseClient.ts
import { createClient } from '@supabase/supabase-js'

// Busca as variáveis de ambiente que configuramos no arquivo .env
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

// Uma verificação de segurança para garantir que as variáveis foram carregadas
if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error("Erro: VITE_SUPABASE_URL ou VITE_SUPABASE_ANON_KEY não encontradas no arquivo .env");
}

// Cria e exporta a instância do cliente Supabase
export const supabase = createClient(supabaseUrl, supabaseAnonKey)