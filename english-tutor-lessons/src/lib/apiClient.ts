// src/lib/apiClient.ts

import axios from 'axios';
import { supabase } from './supabaseClient';

// Crie uma instância do Axios com a URL base da sua API FastAPI.
// Lembre-se de que seu backend Python precisa estar rodando para que isso funcione.
// Durante o desenvolvimento, esta será provavelmente 'http://127.0.0.1:8000'.
const apiClient = axios.create({
  baseURL: 'http://127.0.0.1:8000/api/v1', // ATENÇÃO: Verifique se a porta está correta
});

// Axios Interceptor: Este é um "middleware" para todas as requisições.
// Antes de cada requisição sair do frontend, este código será executado.
apiClient.interceptors.request.use(
  async (config) => {
    // Pega a sessão atual do Supabase
    const { data: { session } } = await supabase.auth.getSession();

    // Se existir uma sessão (usuário logado), adicionamos o token JWT ao cabeçalho
    if (session) {
      config.headers.Authorization = `Bearer ${session.access_token}`;
    }

    return config;
  },
  (error) => {
    // Se houver um erro na configuração da requisição, ele é rejeitado
    return Promise.reject(error);
  }
);

export default apiClient;