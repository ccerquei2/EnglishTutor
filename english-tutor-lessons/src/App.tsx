// /src/App.tsx

import { Routes, Route } from 'react-router-dom';
import { LoginPage } from './pages/LoginPage';
import { ProtectedRoute } from './components/ProtectedRoute';
import { DashboardPage } from './pages/DashboardPage';
import { Toaster } from 'react-hot-toast'; // 1. Importe o Toaster

function App() {
  return (
    <> {/* 2. Use um fragmento para envolver a aplicação e o Toaster */}
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          }
        />
      </Routes>
      {/* 3. Adicione o componente Toaster aqui. Ele ficará invisível até ser chamado. */}
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
        }}
      />
    </>
  );
}

export default App;