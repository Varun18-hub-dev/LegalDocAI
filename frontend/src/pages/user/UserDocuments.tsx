import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { UploadZone } from '../../components/UploadZone';
import { useDocumentStore } from '../../store/useDocumentStore';
import { FileText, Trash2, Clock, CheckCircle, RefreshCw, AlertCircle, FilePlus, ChevronRight } from 'lucide-react';
import { apiService } from '../../services/api';

export const UserDocuments: React.FC = () => {
  const navigate = useNavigate();
  const { documents, fetchDocuments, deleteDocument } = useDocumentStore();
  const [selectedSummaryDoc, setSelectedSummaryDoc] = useState<string | null>(null);
  const [summaryText, setSummaryText] = useState<string | null>(null);
  const [loadingSummary, setLoadingSummary] = useState(false);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const handleGenerateSummary = async (docId: string) => {
    setSelectedSummaryDoc(docId);
    setLoadingSummary(true);
    setSummaryText(null);
    try {
      const data = await apiService.getDocumentSummary(docId);
      setSummaryText(data.summary);
    } catch (err: any) {
      setSummaryText('Failed to generate summary.');
    } finally {
      setLoadingSummary(false);
    }
  };

  const handleDelete = async (docId: string) => {
    if (confirm('Are you sure you want to permanently delete this contract and all its search indexes?')) {
      try {
        await deleteDocument(docId);
      } catch (err) {
        alert('Failed to delete document.');
      }
    }
  };

  return (
    <div className="p-8 max-w-5xl mx-auto flex flex-col gap-8 select-none">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white font-heading">My Legal Documents</h2>
        <p className="text-xs text-gray-400 mt-1">Upload and organize your private legal agreements, contracts, or filings.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left 2 Cols: List */}
        <div className="lg:col-span-2 flex flex-col gap-4">
          <div className="glass-card p-6 border border-brand-border flex flex-col gap-4 h-full bg-brand-secondary/40">
            <h3 className="text-sm font-semibold text-gray-200">Indexed Files</h3>

            {documents.length === 0 ? (
              <div className="flex-1 flex flex-col items-center justify-center py-12 text-gray-500 italic text-xs gap-3">
                <FilePlus className="w-8 h-8 opacity-40" />
                <span>No legal documents uploaded yet.</span>
              </div>
            ) : (
              <div className="flex flex-col gap-3">
                {documents.map((doc) => (
                  <div key={doc.id} className="p-4 bg-brand-tertiary/20 hover:bg-brand-tertiary/40 border border-brand-border rounded-xl flex items-center justify-between gap-4 transition-all">
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="p-2 bg-accent-blue/10 border border-accent-blue/20 rounded-lg text-accent-blue flex-shrink-0">
                        <FileText className="w-5 h-5" />
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-semibold text-gray-200 truncate" title={doc.filename}>{doc.filename}</p>
                        <div className="flex items-center gap-2 mt-1 text-[10px] text-gray-400">
                          <Clock className="w-3 h-3" />
                          <span>{new Date(doc.uploaded_at).toLocaleDateString()}</span>
                          <span>•</span>
                          {doc.status === 'processed' && (
                            <span className="text-emerald-400 font-semibold flex items-center gap-1">
                              <CheckCircle className="w-3 h-3" /> Ready
                            </span>
                          )}
                          {(doc.status === 'uploading' || doc.status === 'processing') && (
                            <span className="text-amber-400 font-semibold flex items-center gap-1 animate-pulse">
                              <RefreshCw className="w-3 h-3 animate-spin" /> Processing
                            </span>
                          )}
                          {doc.status === 'failed' && (
                            <span className="text-rose-400 font-semibold flex items-center gap-1">
                              <AlertCircle className="w-3 h-3" /> Failed
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 flex-shrink-0">
                      {doc.status === 'processed' && (
                        <>
                          <button 
                            onClick={() => handleGenerateSummary(doc.id)}
                            className="px-3 py-1.5 bg-brand-tertiary hover:bg-brand-secondary border border-brand-border text-xs rounded-lg text-gray-300 hover:text-white transition-all font-semibold"
                          >
                            Summarize
                          </button>
                          <button 
                            onClick={() => navigate(`/user/chat/${doc.id}`)}
                            className="p-1.5 bg-accent-blue hover:bg-accent-blue/80 text-white rounded-lg transition-all"
                            title="Chat with document"
                          >
                            <ChevronRight className="w-4 h-4" />
                          </button>
                        </>
                      )}
                      <button 
                        onClick={() => handleDelete(doc.id)}
                        className="p-2 text-gray-500 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-all"
                        title="Delete Document"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right 1 Col: Upload Portal */}
        <div className="flex flex-col gap-6">
          <div className="glass-card p-6 border border-brand-border flex flex-col gap-4 bg-brand-secondary/40">
            <h3 className="text-sm font-semibold text-gray-200">Upload Workspace</h3>
            <p className="text-xs text-gray-400 leading-relaxed">
              Drop any PDF legal document here. Once uploaded, the engine indexes the document clauses for natural language questioning.
            </p>
            <UploadZone />
          </div>

          {/* Summarizer Sidebar Info */}
          {selectedSummaryDoc && (
            <div className="glass-card p-6 border border-brand-border flex flex-col gap-3 animate-fade-in bg-brand-secondary/40">
              <div className="flex justify-between items-center">
                <h4 className="text-xs font-bold uppercase tracking-wider text-gray-400">Executive Summary</h4>
                <button onClick={() => setSelectedSummaryDoc(null)} className="text-xs text-gray-500 hover:text-gray-300">Close</button>
              </div>

              {loadingSummary ? (
                <div className="py-6 flex flex-col items-center justify-center gap-2 text-gray-400">
                  <RefreshCw className="w-6 h-6 animate-spin text-accent-blue" />
                  <span className="text-xs">Summarizing contract clauses...</span>
                </div>
              ) : (
                <div className="text-xs leading-relaxed text-gray-300 whitespace-pre-wrap max-h-[300px] overflow-y-auto pr-1">
                  {summaryText}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
