// src/components/ProtectedRoute.tsx

import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext'; // 1. Importe nosso hook customizado

export function ProtectedRoute({ children }: { children: JSX.Element }) {
  // 2. Use o hook para obter as informações de autenticação
  const { user, loading } = useAuth();

  // 3. Enquanto o contexto está carregando a informação, mostramos uma mensagem
  if (loading) {
    return <div>Verificando autenticação...</div>;
  }

  // 4. Se não houver usuário após o carregamento, redirecionamos para o login
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // 5. Se houver usuário, renderizamos a página protegida
  return children;
}