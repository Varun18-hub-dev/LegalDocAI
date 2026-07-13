import React, { useEffect, useRef, useState } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { Send, FileText, Sparkles, MessageSquare, Loader2, ArrowLeft } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

import { useDocumentStore } from '../../store/useDocumentStore';
import { useChatStore } from '../../store/useChatStore';
import { apiService } from '../../services/api';
import { PDFViewer } from '../../components/PDFViewer';

export const UserChat: React.FC = () => {
  const { docId } = useParams<{ docId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const queryParams = new URLSearchParams(location.search);
  const tabParam = queryParams.get('tab');

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const lastResponseRef = useRef<HTMLDivElement>(null);

  const [inputQuestion, setInputQuestion] = useState('');
  const [summaryData, setSummaryData] = useState<string | null>(null);
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [prevQuerying, setPrevQuerying] = useState(false);

  const { documents, fetchDocuments } = useDocumentStore();
  const { 
    messages, 
    isQuerying, 
    activeTab, 
    setActiveTab, 
    sendMessage, 
    clearHistory
  } = useChatStore();

  const currentDoc = documents.find((d) => d.id === docId);

  // Load documents on init
  useEffect(() => {
    if (!currentDoc) {
      fetchDocuments();
    }
  }, [docId, currentDoc, fetchDocuments]);

  // Initialize active tab based on query param
  useEffect(() => {
    if (tabParam === 'summary') {
      setActiveTab('summary');
    } else {
      setActiveTab('chat');
    }
  }, [tabParam, setActiveTab]);

  // Smart scroll logic: scroll to top of new response when query finishes
  useEffect(() => {
    if (prevQuerying && !isQuerying && lastResponseRef.current) {
      lastResponseRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } else if (isQuerying) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
    setPrevQuerying(isQuerying);
  }, [messages, isQuerying, prevQuerying]);

  // Fetch document summary if summary tab is opened and not already loaded
  useEffect(() => {
    const getSummary = async () => {
      if (activeTab === 'summary' && docId && !summaryData) {
        setLoadingSummary(true);
        try {
          const res = await apiService.getDocumentSummary(docId);
          setSummaryData(res.summary);
        } catch (err) {
          console.error(err);
          setSummaryData('Failed to generate document summary.');
        } finally {
          setLoadingSummary(false);
        }
      }
    };
    getSummary();
  }, [activeTab, docId, summaryData]);

  // Reset summary state when docId changes
  useEffect(() => {
    setSummaryData(null);
  }, [docId]);

  if (!docId) {
    const processedDocs = documents.filter(d => d.status === 'processed');
    return (
      <div className="p-8 max-w-5xl mx-auto flex flex-col gap-8 select-none h-full overflow-y-auto">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white font-heading">Document Q&A Sessions</h2>
          <p className="text-xs text-gray-400 mt-1">Select an indexed contract or agreement from your workspace to start a private clause Q&A session.</p>
        </div>

        <div className="glass-card p-6 border border-brand-border bg-brand-secondary/40 flex flex-col gap-4">
          <h3 className="text-sm font-semibold text-gray-200">Active Workspaces</h3>
          {processedDocs.length === 0 ? (
            <div className="py-12 text-center text-gray-500 italic text-xs flex flex-col items-center gap-3">
              <FileText className="w-8 h-8 opacity-30 text-gray-600" />
              <span>No processed agreements available. Upload a PDF in My Documents to start a Q&A session.</span>
            </div>
          ) : (
            <div className="flex flex-col gap-3">
              {processedDocs.map(doc => (
                <div key={doc.id} className="p-4 bg-brand-tertiary/20 hover:bg-brand-tertiary/40 border border-brand-border rounded-xl flex items-center justify-between gap-4 transition-all">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="p-2 bg-accent-blue/10 border border-accent-blue/20 rounded-lg text-accent-blue flex-shrink-0">
                      <FileText className="w-5 h-5" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-gray-200 truncate">{doc.filename}</p>
                      <p className="text-[10px] text-gray-400 mt-0.5">Uploaded on {new Date(doc.uploaded_at).toLocaleDateString()}</p>
                    </div>
                  </div>
                  <button 
                    onClick={() => navigate(`/user/chat/${doc.id}`)}
                    className="px-4 py-2 bg-accent-blue hover:bg-accent-blue/80 text-white text-xs font-semibold rounded-lg transition-all"
                  >
                    Open Chat
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputQuestion.trim() || isQuerying) return;
    const q = inputQuestion;
    setInputQuestion('');
    try {
      await sendMessage(docId, q);
    } catch (err) {
      alert('Failed to get answer from server.');
    }
  };

  const handleClearChat = async () => {
    if (confirm('Clear chat logs for this document session?')) {
      await clearHistory();
    }
  };

  const suggestedQuestions = [
    "What are the key obligations of the parties?",
    "What is the termination clause and notice period?",
    "Are there any indemnification or liability caps?",
    "What is the dispute resolution mechanism and governing law?"
  ];

  return (
    <div className="flex flex-col md:flex-row h-full flex-1 w-full overflow-hidden select-none">
      
      {/* Left Column: PDF Viewer */}
      <div className="w-full md:w-[50%] h-[40vh] md:h-full border-b md:border-b-0 md:border-r border-brand-border/60">
        <PDFViewer docId={docId} />
      </div>

      {/* Right Column: Chat Q&A & Document summary tab */}
      <div className="w-full md:w-[50%] h-[60vh] md:h-full flex flex-col bg-brand-dark overflow-hidden">
        {/* Document Header & Tab Selector */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-brand-border/60 bg-brand-secondary/90 flex-shrink-0">
          <div className="flex items-center gap-3 min-w-0">
            <button 
              onClick={() => navigate('/user/documents')}
              className="p-1 rounded text-gray-400 hover:text-white transition-all flex-shrink-0"
              title="Go back to Documents"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
            <div className="overflow-hidden min-w-0">
              <h2 className="text-xs font-bold text-gray-200 truncate max-w-[180px]" title={currentDoc?.filename}>
                {currentDoc?.filename || 'Document Workspace'}
              </h2>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex gap-1 bg-brand-tertiary/60 p-0.5 rounded-lg border border-brand-border/40 flex-shrink-0">
            <button
              onClick={() => setActiveTab('chat')}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-semibold transition-all ${
                activeTab === 'chat' 
                  ? 'bg-brand-secondary text-accent-blue shadow-sm' 
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              <MessageSquare className="w-3.5 h-3.5" />
              <span>Q&A Chat</span>
            </button>
            
            <button
              onClick={() => setActiveTab('summary')}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-semibold transition-all ${
                activeTab === 'summary' 
                  ? 'bg-brand-secondary text-accent-cyan shadow-sm' 
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Summary</span>
            </button>
          </div>
        </div>

        {/* Tab Content slots */}
        <div className="flex-1 overflow-hidden relative flex flex-col">
          {activeTab === 'chat' && (
            <div className="flex-grow flex flex-col h-full overflow-hidden">
              {/* Message log */}
              <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-6">
                {messages.length === 0 ? (
                  <div className="flex-grow flex flex-col items-center justify-center text-center p-8 gap-4 max-w-sm mx-auto select-none opacity-50 h-full">
                    <FileText className="w-10 h-10 text-gray-600" />
                    <div>
                      <p className="font-semibold text-gray-300 text-xs uppercase tracking-wider">Ask about your contract</p>
                      <p className="text-[11px] text-gray-500 mt-1 leading-relaxed">
                        Input details or query terms. The engine parses the clause contexts and highlights relevant pages.
                      </p>
                    </div>
                  </div>
                ) : (
                  messages.map((msg, idx) => {
                    const isLast = idx === messages.length - 1;
                    return (
                      <div key={idx} className="flex flex-col gap-4" ref={isLast ? lastResponseRef : null}>
                        {/* User Question Bubble */}
                        <div className="flex justify-end animate-fade-in">
                          <div className="max-w-[85%] rounded-2xl p-4 text-sm leading-[1.7] bg-accent-blue text-white rounded-br-none">
                            <p className="whitespace-pre-wrap font-sans">{msg.question}</p>
                          </div>
                        </div>

                      {/* Assistant Answer Bubble */}
                      {msg.answer && (
                        <div className="flex justify-start animate-fade-in">
                          <div className="max-w-[85%] rounded-2xl p-4 text-sm leading-[1.7] bg-brand-secondary border border-brand-border text-gray-200 rounded-bl-none">
                            <p className="whitespace-pre-wrap font-sans">{msg.answer}</p>
                            
                            {/* Render Citations */}
                            {msg.sources && msg.sources.length > 0 && (
                              <div className="mt-4 pt-3 border-t border-brand-border/40 select-none">
                                <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider mr-2">Cited Pages:</span>
                                <div className="flex flex-wrap gap-1.5 mt-1.5">
                                  {Array.from(new Set(msg.sources.map((s) => s.page))).map((page, pIdx) => (
                                    <button 
                                      key={pIdx}
                                      onClick={() => useChatStore.getState().setPdfPageJump(page)}
                                      className="text-[10px] font-mono px-2 py-0.5 border border-accent-blue/20 bg-accent-blue/10 hover:bg-accent-blue/20 text-accent-blue rounded"
                                    >
                                      Page {page}
                                    </button>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                      </div>
                    );
                  })
                )}

                {isQuerying && (
                  <div className="flex justify-start animate-pulse">
                    <div className="bg-brand-secondary border border-brand-border rounded-2xl rounded-bl-none p-4 flex items-center gap-2">
                      <Loader2 className="w-4 h-4 animate-spin text-accent-blue" />
                      <span className="text-xs text-gray-400">Assistant is evaluating clause contexts...</span>
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>

              {/* Chat Input & Suggestions panel */}
              <div className="p-4 border-t border-brand-border/60 bg-brand-secondary/80 flex flex-col gap-3">
                {/* Suggestions - only show initially */}
                {messages.length === 0 && (
                  <div className="flex flex-wrap gap-2 mb-2">
                    {suggestedQuestions.map((q, idx) => (
                      <button
                        key={idx}
                        onClick={() => { setInputQuestion(q); }}
                        className="text-[10px] font-bold px-3 py-1.5 rounded-lg bg-brand-tertiary border border-brand-border text-gray-400 hover:text-white hover:border-accent-blue/30 transition-all text-left"
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                )}

                <form onSubmit={handleSend} className="flex items-center gap-3">
                  <input 
                    type="text"
                    value={inputQuestion}
                    onChange={(e) => setInputQuestion(e.target.value)}
                    placeholder="Ask about this agreement..."
                    className="flex-1 bg-brand-dark border border-brand-border rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-accent-blue/40 font-sans"
                    disabled={isQuerying}
                  />
                  <button 
                    type="submit" 
                    disabled={isQuerying || !inputQuestion.trim()} 
                    className="p-3 bg-accent-blue hover:bg-accent-blue/80 disabled:opacity-40 rounded-xl text-white transition-all"
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </form>

                {messages.length > 0 && (
                  <div className="flex justify-between items-center text-[10px] text-gray-500 mt-1">
                    <span>Press Enter to send</span>
                    <button onClick={handleClearChat} className="hover:text-rose-400 font-semibold transition-all">Clear Chat Session</button>
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'summary' && (
            <div className="flex-grow overflow-y-auto p-8 text-left h-full">
              {loadingSummary && (
                <div className="flex flex-col items-center gap-3 py-20 text-gray-400">
                  <Loader2 className="w-8 h-8 animate-spin text-accent-cyan" />
                  <span className="text-xs font-semibold">Summarizing contract clauses...</span>
                </div>
              )}
              
              {!loadingSummary && summaryData && (
                <div className="glass-card bg-brand-secondary/40 p-6 rounded-xl border border-brand-border flex flex-col gap-4">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-accent-cyan">
                    Executive summary
                  </h3>
                  <div className="text-sm text-gray-300 leading-[1.7] font-sans summary-content">
                    <ReactMarkdown>{summaryData}</ReactMarkdown>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
