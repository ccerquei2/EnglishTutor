// // src/components/ProtectedRoute.tsx
//
// import { Navigate } from 'react-router-dom';
// import { useAuth } from '../contexts/AuthContext'; // 1. Importe nosso hook customizado
//
// export function ProtectedRoute({ children }: { children: JSX.Element }) {
//   // 2. Use o hook para obter as informações de autenticação
//   const { user, loading } = useAuth();
//
//   // 3. Enquanto o contexto está carregando a informação, mostramos uma mensagem
//   if (loading) {
//     return <div>Verificando autenticação...</div>;
//   }
//
//   // 4. Se não houver usuário após o carregamento, redirecionamos para o login
//   if (!user) {
//     return <Navigate to="/login" replace />;
//   }
//
//   // 5. Se houver usuário, renderizamos a página protegida
//   return children;
// }


// /src/components/ProtectedRoute.tsx

import { Navigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';

export function ProtectedRoute({ children }: { children: JSX.Element }) {
  // Pegamos user e loading do nosso contexto central
  const { user, loading } = useAuth();

  // Se o contexto ainda está na sua carga inicial, não fazemos nada.
  // O AuthProvider já está mostrando uma tela de carregamento ou null.
  // Isso evita uma renderização dupla de "carregando".
  if (loading) {
    return null; // Deixa o AuthProvider controlar o estado de loading
  }

  // Após o carregamento, se NÃO houver usuário, redireciona para o login.
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // Se passou por tudo, o usuário está autenticado. Renderiza a página.
  return children;
}