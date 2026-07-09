import { create } from 'zustand';
import { UserDocument } from '../types';
import { apiService } from '../services/api';

interface DocumentState {
  documents: UserDocument[];
  activeDocId: string | null;
  isUploading: boolean;
  uploadProgress: number;
  isLoading: boolean;
  error: string | null;
  
  setDocuments: (docs: UserDocument[]) => void;
  setActiveDocId: (id: string | null) => void;
  setUploading: (uploading: boolean) => void;
  setUploadProgress: (progress: number) => void;
  fetchDocuments: () => Promise<void>;
  deleteDocument: (docId: string) => Promise<void>;
}

export const useDocumentStore = create<DocumentState>((set, get) => ({
  documents: [],
  activeDocId: null,
  isUploading: false,
  uploadProgress: 0,
  isLoading: false,
  error: null,

  setDocuments: (documents) => set({ documents }),
  setActiveDocId: (activeDocId) => set({ activeDocId }),
  setUploading: (isUploading) => set({ isUploading }),
  setUploadProgress: (uploadProgress) => set({ uploadProgress }),

  fetchDocuments: async () => {
    set({ isLoading: true, error: null });
    try {
      const docs = await apiService.listDocuments();
      set({ documents: docs, isLoading: false });
    } catch (err: any) {
      set({ error: err.message || 'Failed to fetch documents', isLoading: false });
    }
  },

  deleteDocument: async (docId) => {
    try {
      await apiService.deleteDocument(docId);
      // Remove from state
      const updatedDocs = get().documents.filter((d) => d.id !== docId);
      set({ documents: updatedDocs });
      
      // Clear activeDocId if we just deleted the active document
      if (get().activeDocId === docId) {
        set({ activeDocId: null });
      }
    } catch (err: any) {
      set({ error: err.message || 'Failed to delete document' });
      throw err;
    }
  },
}));
