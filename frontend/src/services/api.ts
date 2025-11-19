import axios from 'axios';

// Base URL from env
const API_BASE_URL = import.meta.env.VITE_API_URL;

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

// Add auth token to headers
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("auth_token");
  if (token && token !== "null" && token !== "undefined") {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token expiry
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.log("AXIOS ERROR:", error);

    if (!error.response) return Promise.reject(error);

    if (
      error.response.status === 401 &&
      error.response.data?.detail === "Token has expired"
    ) {
      localStorage.removeItem("auth_token");
      window.location.href = "/login";
    }

    return Promise.reject(error);
  }
);

// --- Types ---
export interface SignupData { name: string; email: string; password: string; }
export interface LoginData { email: string; password: string; }
export interface ChatRequest { model_name: string; prompt: string; }
export interface ChatResponse { response: string; }

// --- Auth API ---
export const authAPI = {
  signup: (data: SignupData) => api.post('/auth/register', data).then(res => res.data),
  login: (data: LoginData) => api.post('/auth/login', data).then(res => res.data),
};

// --- Chat API ---
export const chatAPI = {
  sendMessage: (data: ChatRequest) => api.post('/ai/chat', data).then(res => res.data),
  getPlatforms: () => api.get('/ai/platforms').then(res => res.data.platforms),
  getChatHistory: (model_name: string) => 
    api.get('/ai/chat-history', { params: { model_name } }).then(res => res.data.chat),
  connectWS: (token: string) => {
    const wsUrl = API_BASE_URL.replace(/^http/, 'ws') + `/ai/ws/chat?token=${token}`;
    return new WebSocket(wsUrl);
  }
};

export default api;
