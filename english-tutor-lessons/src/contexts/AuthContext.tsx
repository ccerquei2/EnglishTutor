// src/contexts/AuthContext.tsx

import { useState, useEffect, createContext, useContext, ReactNode } from 'react';
import { supabase } from '../lib/supabaseClient';
import type { Session, User } from '@supabase/supabase-js';

// Definimos o formato dos dados que nosso contexto irá fornecer
interface AuthContextType {
  session: Session | null;
  user: User | null;
  loading: boolean;
  signOut: () => Promise<void>;
}

// Criamos o contexto com um valor inicial de 'undefined'
// O '!' é um 'non-null assertion' - dizemos ao TypeScript que vamos prover um valor antes de usá-lo.
const AuthContext = createContext<AuthContextType>(null!);

// Criamos o componente Provedor
export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Pega a sessão inicial
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setUser(session?.user ?? null);
      setLoading(false);
    });

    // Ouve por mudanças na autenticação
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (_event, session) => {
        setSession(session);
        setUser(session?.user ?? null);
        setLoading(false); // Garante que o loading para após a primeira verificação
      }
    );

    // Limpa o listener
    return () => {
      subscription.unsubscribe();
    };
  }, []);

  // Função de logout
  const signOut = async () => {
    await supabase.auth.signOut();
  };

  // O valor que será compartilhado com todos os componentes filhos
  const value = {
    session,
    user,
    loading,
    signOut,
  };

  // Enquanto estiver carregando, não renderiza nada para evitar "flickering"
  // A aplicação só renderiza quando sabemos se o usuário está logado ou não.
  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
}

// Hook customizado para facilitar o uso do nosso contexto
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth deve ser usado dentro de um AuthProvider');
  }
  return context;
}