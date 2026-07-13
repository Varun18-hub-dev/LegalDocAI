import axios from 'axios';
import { 
  HealthResponse, 
  UserDocument, 
  SearchResponse, 
  ChatHistoryResponse, 
  ComparisonResponse 
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

import { useAuthStore } from '../store/useAuthStore';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Automatically inject JWT Bearer token into requests
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

// Handle 401 Unauthorized errors globally by logging out and redirecting to login
apiClient.interceptors.response.use((response) => {
  return response;
}, (error) => {
  if (error.response && error.response.status === 401) {
    // Clear credentials in auth store
    useAuthStore.getState().logout();
    
    // Redirect to login page if we are not already on login or register pages
    const currentPath = window.location.pathname;
    if (currentPath !== '/login' && currentPath !== '/register') {
      window.location.href = '/login';
    }
  }
  return Promise.reject(error);
});

export const apiService = {
  /**
   * Check backend API health
   */
  async getHealth(): Promise<HealthResponse> {
    const { data } = await apiClient.get<HealthResponse>('/health');
    return data;
  },

  /**
   * List all user uploaded documents
   */
  async listDocuments(): Promise<UserDocument[]> {
    const { data } = await apiClient.get<any[]>('/documents');
    return data.map((d: any) => ({
      ...d,
      id: d.document_id || d.id
    }));
  },

  /**
   * Upload a new PDF document
   */
  async uploadDocument(file: File, onUploadProgress?: (progressEvent: any) => void): Promise<{ document_id: string; filename: string; status: string; message: string }> {
    const formData = new FormData();
    formData.append('file', file);
    
    const { data } = await apiClient.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress,
    });
    return data;
  },

  /**
   * Get document processing status
   */
  async getDocumentStatus(docId: string): Promise<UserDocument> {
    const { data } = await apiClient.get<any>(`/documents/${docId}/status`);
    return {
      ...data,
      id: data.document_id || data.id
    };
  },

  /**
   * Query a custom document (RAG Q&A)
   */
  async queryDocument(docId: string, question: string, sessionId?: string): Promise<SearchResponse> {
    const { data } = await apiClient.post<SearchResponse>(`/documents/${docId}/query`, {
      question,
      session_id: sessionId,
    });
    return data;
  },

  /**
   * Get summary of custom document
   */
  async getDocumentSummary(docId: string): Promise<{ document_id: string; summary: string; metadata: any }> {
    const { data } = await apiClient.get<{ document_id: string; summary: string; metadata: any }>(`/documents/${docId}/summary`);
    return data;
  },

  /**
   * Compare two documents
   */
  async compareDocuments(docId1: string, docId2: string): Promise<ComparisonResponse & { metadata: any }> {
    const { data } = await apiClient.post<ComparisonResponse & { metadata: any }>('/documents/compare', {
      doc_id_1: docId1,
      doc_id_2: docId2,
    });
    return data;
  },

  /**
   * Query the global legal knowledge base (RAG)
   */
  async queryGlobalKB(question: string, sessionId?: string): Promise<SearchResponse> {
    const { data } = await apiClient.post<SearchResponse>('/kb/query', {
      question,
      session_id: sessionId,
    });
    return data;
  },

  /**
   * Get chat history for a session
   */
  async getChatHistory(sessionId: string): Promise<ChatHistoryResponse> {
    const { data } = await apiClient.get<ChatHistoryResponse>(`/chat/${sessionId}`);
    return data;
  },

  /**
   * Clear chat history for a session
   */
  async clearChatHistory(sessionId: string): Promise<{ status: string; message: string }> {
    const { data } = await apiClient.delete(`/chat/${sessionId}`);
    return data;
  },

  /**
   * List all user chat sessions (global + custom docs)
   */
  async listChatSessions(): Promise<any[]> {
    const { data } = await apiClient.get<any[]>('/chat/sessions');
    return data;
  },

  /**
   * Delete a chat session
   */
  async deleteChatSession(sessionId: string): Promise<{ status: string; message: string }> {
    const { data } = await apiClient.delete(`/chat/sessions/${sessionId}`);
    return data;
  },

  /**
   * Delete a custom document
   */
  async deleteDocument(docId: string): Promise<{ status: string; message: string }> {
    const { data } = await apiClient.delete(`/documents/${docId}`);
    return data;
  },

  /**
   * Login credentials and fetch JWT
   */
  async login(payload: any): Promise<any> {
    const { data } = await apiClient.post('/auth/login', payload);
    return data;
  },

  /**
   * Register a new user
   */
  async register(payload: any): Promise<any> {
    const { data } = await apiClient.post('/auth/register', payload);
    return data;
  },

  /**
   * Get currently authenticated user details
   */
  async getMe(): Promise<any> {
    const { data } = await apiClient.get('/auth/me');
    return data;
  },

  // ------------------------------------------------------------
  // Lawyer Workspaces APIs
  // ------------------------------------------------------------
  async createCase(payload: any): Promise<any> {
    const { data } = await apiClient.post('/lawyer/cases', payload);
    return data;
  },

  async listCases(): Promise<any[]> {
    const { data } = await apiClient.get<any[]>('/lawyer/cases');
    return data;
  },

  async getCaseDetails(caseId: string): Promise<any> {
    const { data } = await apiClient.get<any>(`/lawyer/cases/${caseId}`);
    return data;
  },

  async linkDocumentToCase(caseId: string, documentId: string): Promise<any> {
    const { data } = await apiClient.post(`/lawyer/cases/${caseId}/documents`, { document_id: documentId });
    return data;
  },

  // ------------------------------------------------------------
  // Admin Operations APIs
  // ------------------------------------------------------------
  async getAdminMetrics(): Promise<any> {
    const { data } = await apiClient.get('/admin/metrics');
    return data;
  },

  async getAdminUsers(): Promise<any[]> {
    const { data } = await apiClient.get<any[]>('/admin/users');
    return data;
  },

  async updateUserStatus(userId: string, status: string): Promise<any> {
    const { data } = await apiClient.patch(`/admin/users/${userId}/status`, { status });
    return data;
  },

  async updateUserRole(userId: string, role: string): Promise<any> {
    const { data } = await apiClient.patch(`/admin/users/${userId}/role`, { role });
    return data;
  },

  async getAdminDocuments(): Promise<any[]> {
    const { data } = await apiClient.get<any[]>('/admin/documents');
    return data;
  },

  async getAdminLogs(): Promise<any[]> {
    const { data } = await apiClient.get<any[]>('/admin/logs');
    return data;
  },
};
