import React, { useState, useRef, useEffect } from 'react';
import { Search, Compass, AlertCircle, Bookmark, Loader2, RefreshCw } from 'lucide-react';
import { apiService } from '../../services/api';

interface SearchMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: any[];
}

export const UserDashboard: React.FC = () => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<SearchMessage[]>([]);
  const [activeMessageId, setActiveMessageId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const suggestedQueries = [
    "consequences of breach of contract compensation",
    "fundamental rights under article 19 of constitution",
    "theft provisions under Bharatiya Nyaya Sanhita 2023",
    "relevance of evidence in BSA section 27"
  ];

  // Auto-scroll to bottom of conversation
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSearch = async (questionText: string) => {
    if (!questionText.trim() || loading) return;
    setLoading(true);
    setError(null);
    
    const userMsgId = `user-${Date.now()}`;
    const updatedMessages: SearchMessage[] = [
      ...messages,
      { id: userMsgId, role: 'user', content: questionText }
    ];
    setMessages(updatedMessages);
    setQuery(''); // Clear search input
    
    try {
      const data = await apiService.queryGlobalKB(questionText);
      const assistantMsgId = `assistant-${Date.now()}`;
      
      const finalMessages: SearchMessage[] = [
        ...updatedMessages,
        { 
          id: assistantMsgId, 
          role: 'assistant', 
          content: data.answer, 
          citations: data.citations 
        }
      ];
      setMessages(finalMessages);
      setActiveMessageId(assistantMsgId);
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.message || err.message || 'Search request failed.');
    } finally {
      setLoading(false);
    }
  };

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSearch(query);
  };

  const handleReset = () => {
    setQuery('');
    setMessages([]);
    setActiveMessageId(null);
    setError(null);
  };

  const hasResult = messages.length > 0;
  const activeMessage = messages.find(m => m.id === activeMessageId);
  const activeCitations = activeMessage?.citations || [];

  return (
    <div className="flex flex-col h-full flex-1 w-full overflow-hidden relative select-none">
      
      {/* Top Banner / Header (Shrinks after search is active) */}
      <div className={`p-6 w-full border-b border-brand-border/40 bg-brand-secondary/30 flex items-center justify-between gap-4 transition-all duration-500 ease-in-out ${
        hasResult ? 'py-4' : 'py-12 flex-col text-center'
      }`}>
        <div className={hasResult ? 'flex flex-col gap-0.5' : 'flex flex-col gap-2 items-center'}>
          <h1 className={`font-heading font-extrabold tracking-tight bg-gradient-to-r from-accent-blue to-accent-cyan bg-clip-text text-transparent transition-all duration-500 ${
            hasResult ? 'text-lg' : 'text-4xl'
          }`}>
            Indian Legal Intelligence Engine
          </h1>
          {!hasResult && (
            <p className="text-sm text-gray-400 max-w-2xl mt-2 leading-relaxed">
              Query statutory articles, central penal codes (BNS, BNSS, BSA), and landmark case judgments with natural language reasoning.
            </p>
          )}
        </div>

        {hasResult && (
          <button 
            onClick={handleReset}
            className="flex items-center gap-2 px-4 py-2 text-xs font-bold text-gray-400 hover:text-white border border-brand-border hover:border-accent-blue/30 rounded-xl bg-brand-secondary/60 hover:bg-brand-tertiary transition-all uppercase tracking-wider"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>New Search</span>
          </button>
        )}
      </div>

      {/* Answer Workspace Area (Fills the screen height) */}
      <div className="flex-1 overflow-hidden relative flex flex-col">
        
        {loading && messages.length === 0 && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-brand-dark/50 gap-3 z-20">
            <Loader2 className="w-8 h-8 animate-spin text-accent-blue" />
            <span className="text-xs font-semibold text-gray-300">Retrieving statutory references...</span>
          </div>
        )}

        {error && (
          <div className="p-6">
            <div className="max-w-md mx-auto p-4 border border-rose-500/20 bg-rose-500/5 text-rose-400 text-xs font-semibold rounded-xl text-center flex items-center justify-center gap-2">
              <AlertCircle className="w-4 h-4" />
              <span>{error}</span>
            </div>
          </div>
        )}

        {!hasResult && (
          <div className="flex-1 flex flex-col items-center justify-center p-8">
            <div className="search-container max-w-3xl w-full flex flex-col gap-6">
              <form onSubmit={onSubmit} className="search-input-wrapper w-full bg-brand-secondary/80 flex items-center border border-brand-border rounded-xl px-5 py-4 gap-4 focus-within:border-accent-blue/40 transition-all duration-300">
                <Search className="w-5 h-5 text-accent-blue flex-shrink-0" />
                <input 
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search statutes, rules, or articles (e.g. 'indemnity in breach of contract')"
                  className="bg-transparent border-none outline-none text-sm text-white flex-1 font-sans"
                  disabled={loading}
                />
                <button 
                  type="submit" 
                  disabled={loading || !query.trim()} 
                  className="bg-accent-blue hover:bg-accent-blue/80 text-white font-heading text-xs font-semibold px-5 py-2.5 rounded-lg transition-all uppercase tracking-wider disabled:opacity-40"
                >
                  {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Search'}
                </button>
              </form>

              {/* Suggestion Chips */}
              <div className="flex flex-wrap gap-2 justify-center max-w-2xl mx-auto">
                {suggestedQueries.map((q, idx) => (
                  <button
                    key={idx}
                    onClick={() => { setQuery(q); handleSearch(q); }}
                    className="text-[10px] font-bold px-3.5 py-2 rounded-xl bg-brand-secondary border border-brand-border text-gray-400 hover:text-white hover:border-accent-blue/30 hover:bg-brand-tertiary transition-all"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Desktop Split View / Mobile Stack View for Chat threads */}
        {hasResult && (
          <div className="flex-1 flex flex-col md:flex-row overflow-hidden w-full h-full">
            
            {/* Left 70% Column: Conversation & Follow-up Input */}
            <div className="flex-1 md:w-[70%] flex flex-col h-full border-r border-brand-border/40 overflow-hidden bg-brand-dark/20">
              
              {/* Scrollable Conversation messages */}
              <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-6">
                {messages.map((msg) => (
                  msg.role === 'user' ? (
                    <div key={msg.id} className="flex justify-end">
                      <div className="bg-accent-blue/15 border border-accent-blue/30 rounded-2xl px-5 py-3 max-w-[80%] text-left text-[14px] text-gray-200">
                        {msg.content}
                      </div>
                    </div>
                  ) : (
                    <div 
                      key={msg.id}
                      onClick={() => setActiveMessageId(msg.id)}
                      className={`flex gap-4 p-5 rounded-2xl border transition-all cursor-pointer text-left ${
                        activeMessageId === msg.id 
                          ? 'bg-brand-secondary/60 border-accent-blue/40 shadow-glow-cyan' 
                          : 'bg-brand-secondary/25 border-brand-border/40 hover:border-accent-blue/20'
                      }`}
                    >
                      <div className="message-avatar w-9 h-9 rounded-xl bg-accent-blue/10 text-accent-blue border border-accent-blue/20 flex items-center justify-center text-xs font-bold font-mono select-none flex-shrink-0">
                        AI
                      </div>
                      <div className="flex-1 flex flex-col gap-2">
                        <h4 className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">AI Analysis Memo</h4>
                        <div className="text-[14px] leading-[1.7] text-gray-200 whitespace-pre-wrap font-sans select-text">
                          {msg.content}
                        </div>
                        {msg.citations && msg.citations.length > 0 && (
                          <div className="message-citations flex flex-wrap gap-2 mt-3 select-none items-center">
                            <span className="text-[9px] font-bold text-gray-500 uppercase">Citations:</span>
                            {msg.citations.map((c: any, cIdx: number) => (
                              <span key={cIdx} className="text-[9px] font-semibold px-2 py-0.5 bg-brand-tertiary border border-brand-border rounded text-accent-cyan">
                                {c.coordinate || c.act_name || 'Source'}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  )
                ))}
                
                {loading && (
                  <div className="flex gap-4 p-5 rounded-2xl bg-brand-secondary/20 border border-brand-border/30 text-left">
                    <Loader2 className="w-5 h-5 animate-spin text-accent-blue flex-shrink-0" />
                    <span className="text-xs text-gray-400 font-semibold animate-pulse">Consulting legal statutes & rules...</span>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>

              {/* Follow-up input bar */}
              <div className="p-4 border-t border-brand-border/40 bg-brand-dark/40">
                <form onSubmit={onSubmit} className="search-input-wrapper max-w-4xl w-full mx-auto bg-brand-secondary/80 flex items-center border border-brand-border rounded-xl px-4 py-3 gap-3 focus-within:border-accent-blue/40 transition-all duration-300">
                  <Search className="w-5 h-5 text-accent-blue flex-shrink-0" />
                  <input 
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Ask a follow-up query (e.g. 'explain compensation requirements')"
                    className="bg-transparent border-none outline-none text-sm text-white flex-1 font-sans"
                    disabled={loading}
                  />
                  <button 
                    type="submit" 
                    disabled={loading || !query.trim()} 
                    className="bg-accent-blue hover:bg-accent-blue/80 text-white font-heading text-xs font-semibold px-4 py-2 rounded-lg transition-all uppercase tracking-wider disabled:opacity-40"
                  >
                    Ask
                  </button>
                </form>
              </div>
            </div>

            {/* Right 30% Column: Citations & Sources for activeMessage */}
            <div className="md:w-[30%] overflow-y-auto p-6 bg-brand-secondary/10 h-full flex flex-col">
              <h4 className="text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-4">Retrieved Sources</h4>
              
              {activeCitations && activeCitations.length > 0 ? (
                <div className="flex flex-col gap-4">
                  {activeCitations.map((c: any, idx: number) => (
                    <div key={idx} className="p-4 bg-brand-secondary/40 border border-brand-border rounded-xl flex flex-col gap-3 hover:border-accent-blue/20 transition-all select-text">
                      <div className="flex items-center gap-2">
                        <Bookmark className="w-3.5 h-3.5 text-accent-blue" />
                        <span className="text-[9px] font-bold text-accent-blue uppercase tracking-wider truncate max-w-[180px]">
                          {c.act_name || 'Penal Code'}
                        </span>
                      </div>
                      
                      <div>
                        {c.coordinate && (
                          <h5 className="text-xs font-bold text-gray-200">{c.coordinate}</h5>
                        )}
                        {c.title && (
                          <p className="text-[9px] text-gray-400 mt-0.5">{c.title}</p>
                        )}
                        <p className="text-xs text-gray-300 mt-2 italic leading-normal bg-brand-dark/20 p-2 border border-brand-border/30 rounded">
                          "{c.snippet}"
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-gray-500 italic">Select an AI analysis response to view cited sources.</p>
              )}
            </div>

          </div>
        )}
      </div>
    </div>
  );
};
