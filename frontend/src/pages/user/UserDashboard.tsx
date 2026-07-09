import React, { useState } from 'react';
import { Search, Compass, BookOpen, AlertCircle, Bookmark, Loader2 } from 'lucide-react';
import { apiService } from '../../services/api';
import { SearchResponse } from '../../types';

export const UserDashboard: React.FC = () => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const suggestedQueries = [
    "consequences of breach of contract compensation",
    "fundamental rights under article 19 of constitution",
    "theft provisions under Bharatiya Nyaya Sanhita 2023",
    "relevance of evidence in BSA section 27"
  ];

  const handleSearch = async (questionText: string) => {
    if (!questionText.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await apiService.queryGlobalKB(questionText);
      setResult(data);
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

  const hasResult = result !== null;

  return (
    <div className="flex flex-col h-[calc(100vh-60px)] w-full overflow-hidden relative select-none">
      
      {/* Top Banner / Header (Shrinks after search is active) */}
      <div className={`p-8 w-full border-b border-brand-border/40 bg-brand-secondary/30 flex flex-col gap-2 transition-all duration-500 ease-in-out ${
        hasResult ? 'py-4' : 'py-12 items-center text-center'
      }`}>
        <h1 className={`font-heading font-extrabold tracking-tight bg-gradient-to-r from-accent-blue to-accent-cyan bg-clip-text text-transparent transition-all duration-500 ${
          hasResult ? 'text-xl' : 'text-4xl'
        }`}>
          Indian Legal Intelligence Engine
        </h1>
        {!hasResult && (
          <p className="text-sm text-gray-400 max-w-2xl mt-2 leading-relaxed">
            Query statutory articles, central penal codes (BNS, BNSS, BSA), and landmark case judgments with natural language reasoning.
          </p>
        )}
      </div>

      {/* Query Bar (Position changes after query) */}
      <div className={`p-6 w-full border-b border-brand-border/40 bg-brand-dark/40 z-10 transition-all duration-500 flex flex-col items-center justify-center`}>
        <form onSubmit={onSubmit} className="search-input-wrapper max-w-4xl w-full bg-brand-secondary/80 flex items-center border border-brand-border rounded-xl px-4 py-3 gap-3 focus-within:border-accent-blue/40 transition-all duration-300">
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
            className="bg-accent-blue hover:bg-accent-blue/80 text-white font-heading text-xs font-semibold px-4 py-2 rounded-lg transition-all uppercase tracking-wider disabled:opacity-40"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Search'}
          </button>
        </form>

        {/* Suggestion Chips - Hidden after query */}
        {!hasResult && !loading && (
          <div className="flex flex-wrap gap-2 justify-center mt-4 max-w-2xl">
            {suggestedQueries.map((q, idx) => (
              <button
                key={idx}
                onClick={() => { setQuery(q); handleSearch(q); }}
                className="text-[10px] font-bold px-3 py-1.5 rounded-lg bg-brand-secondary border border-brand-border text-gray-400 hover:text-white hover:border-accent-blue/30 hover:bg-brand-tertiary transition-all"
              >
                {q}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Answer Workspace Area (Fills the screen height) */}
      <div className="flex-1 overflow-hidden relative flex flex-col">
        
        {loading && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-brand-dark/50 gap-3 z-20">
            <Loader2 className="w-8 h-8 animate-spin text-accent-blue" />
            <span className="text-xs font-semibold text-gray-300">Retrieving statutory references...</span>
          </div>
        )}

        {error && (
          <div className="p-8 flex justify-center items-center h-full">
            <div className="max-w-md w-full p-4 border border-rose-500/20 bg-rose-500/5 text-rose-400 text-xs font-semibold rounded-xl text-center flex items-center justify-center gap-2">
              <AlertCircle className="w-4 h-4" />
              <span>{error}</span>
            </div>
          </div>
        )}

        {!loading && !error && !hasResult && (
          <div className="flex-1 flex flex-col items-center justify-center text-gray-500 italic text-xs gap-2 py-12">
            <Compass className="w-10 h-10 opacity-30 text-accent-blue mb-2" />
            <span>Enter your legal query above to begin semantic research.</span>
          </div>
        )}

        {/* Desktop Split View / Mobile Stack View */}
        {!loading && !error && hasResult && result && (
          <div className="flex-1 flex flex-col md:flex-row overflow-hidden w-full max-w-7xl mx-auto h-full">
            
            {/* Left 70% Column: AI Reading Panel */}
            <div className="flex-1 md:w-[70%] overflow-y-auto p-8 border-r border-brand-border/40 h-full flex flex-col">
              <div className="max-w-[950px] mx-auto w-full pr-4 pb-12">
                <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-4">AI Analysis Memo</h3>
                <div className="text-[17px] leading-[1.7] text-gray-200 whitespace-pre-wrap font-sans select-text">
                  {result.answer}
                </div>
              </div>
            </div>

            {/* Right 30% Column: Citations & Sources */}
            <div className="md:w-[30%] overflow-y-auto p-8 bg-brand-secondary/10 h-full flex flex-col">
              <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-4">Retrieved Sources</h4>
              
              {result.citations && result.citations.length > 0 ? (
                <div className="flex flex-col gap-4">
                  {result.citations.map((c: any, idx: number) => (
                    <div key={idx} className="p-4 bg-brand-secondary/40 border border-brand-border rounded-xl flex flex-col gap-3 hover:border-accent-blue/20 transition-all select-text">
                      <div className="flex items-center gap-2">
                        <Bookmark className="w-3.5 h-3.5 text-accent-blue" />
                        <span className="text-[10px] font-bold text-accent-blue uppercase tracking-wider truncate max-w-[180px]">
                          {c.act_name || 'Penal Code'}
                        </span>
                      </div>
                      
                      <div>
                        {c.coordinate && (
                          <h5 className="text-xs font-bold text-gray-200">{c.coordinate}</h5>
                        )}
                        {c.title && (
                          <p className="text-[10px] text-gray-400 mt-0.5">{c.title}</p>
                        )}
                        <p className="text-xs text-gray-300 mt-2 italic leading-normal bg-brand-dark/20 p-2 border border-brand-border/30 rounded">
                          "{c.snippet}"
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-gray-500 italic">No direct sources cited.</p>
              )}
            </div>

          </div>
        )}
      </div>
    </div>
  );
};
