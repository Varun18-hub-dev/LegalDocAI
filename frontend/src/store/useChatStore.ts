import { create } from 'zustand';
import { ChatMessage, SearchResponse, CitationSchema } from '../types';
import { apiService } from '../services/api';

interface ChatState {
  sessionId: string;
  activeTab: 'chat' | 'summary' | 'compare';
  messages: ChatMessage[];
  isQuerying: boolean;
  globalQueryResults: SearchResponse | null;
  selectedCitations: CitationSchema[];
  pdfPageJump: number | null;
  error: string | null;

  setSessionId: (id: string) => void;
  setActiveTab: (tab: 'chat' | 'summary' | 'compare') => void;
  setGlobalQueryResults: (results: SearchResponse | null) => void;
  setSelectedCitations: (citations: CitationSchema[]) => void;
  setPdfPageJump: (page: number | null) => void;
  fetchHistory: () => Promise<void>;
  sendMessage: (docId: string, question: string) => Promise<void>;
  clearHistory: () => Promise<void>;
}

// Helper to generate simple unique session ID
const generateSessionId = () => 'sess_' + Math.random().toString(36).substring(2, 11);

export const useChatStore = create<ChatState>((set, get) => ({
  sessionId: generateSessionId(),
  activeTab: 'chat',
  messages: [],
  isQuerying: false,
  globalQueryResults: null,
  selectedCitations: [],
  pdfPageJump: null,
  error: null,

  setSessionId: (sessionId) => set({ sessionId }),
  setActiveTab: (activeTab) => set({ activeTab }),
  setGlobalQueryResults: (globalQueryResults) => set({ globalQueryResults }),
  setSelectedCitations: (selectedCitations) => set({ selectedCitations }),
  setPdfPageJump: (pdfPageJump) => set({ pdfPageJump }),

  fetchHistory: async () => {
    const { sessionId } = get();
    set({ isQuerying: true, error: null });
    try {
      const res = await apiService.getChatHistory(sessionId);
      set({ messages: res.history, isQuerying: false });
    } catch (err: any) {
      set({ error: err.message || 'Failed to fetch chat history', isQuerying: false });
    }
  },

  sendMessage: async (docId, question) => {
    const { sessionId, messages } = get();
    set({ isQuerying: true, error: null });
    
    // Add user message optimistically
    const tempUserMsg: ChatMessage = {
      session_id: sessionId,
      question,
      answer: '',
      sources: [],
      created_at: new Date().toISOString(),
    };
    
    set({ messages: [...messages, tempUserMsg] });
    
    try {
      const response = await apiService.queryDocument(docId, question, sessionId);
      
      // Map citations into sources format expected by ChatMessage
      const sourcesMapped = response.citations.map((c) => ({
        page: c.page || 1,
        text: c.snippet,
        score: c.confidence_score,
      }));
      
      // Update last message with the response
      const updatedMessages = [...get().messages];
      const lastIndex = updatedMessages.length - 1;
      
      updatedMessages[lastIndex] = {
        session_id: sessionId,
        question,
        answer: response.answer,
        sources: sourcesMapped,
        created_at: new Date().toISOString(),
      };
      
      set({ 
        messages: updatedMessages, 
        isQuerying: false,
        selectedCitations: response.citations
      });
    } catch (err: any) {
      // Rollback or show error
      set({ error: err.message || 'Failed to send query', isQuerying: false });
      // Remove optimistic message
      set({ messages: get().messages.filter(m => m !== tempUserMsg) });
      throw err;
    }
  },

  clearHistory: async () => {
    const { sessionId } = get();
    try {
      await apiService.clearChatHistory(sessionId);
      set({ messages: [] });
    } catch (err: any) {
      set({ error: err.message || 'Failed to clear chat history' });
    }
  },
}));
