import React, { useState, useEffect } from 'react';
import { useDocumentStore } from '../../store/useDocumentStore';
import { apiService } from '../../services/api';
import { GitCompare, Loader2, AlertCircle, RefreshCw } from 'lucide-react';

export const UserCompare: React.FC = () => {
  const { documents, fetchDocuments } = useDocumentStore();
  const [docId1, setDocId1] = useState('');
  const [docId2, setDocId2] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const handleCompare = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!docId1 || !docId2) return;
    if (docId1 === docId2) {
      setError('Please choose two different agreements to compare.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await apiService.compareDocuments(docId1, docId2);
      setResult(data);
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to compare the chosen documents.');
    } finally {
      setLoading(false);
    }
  };

  const processedDocs = documents.filter(d => d.status === 'processed');

  return (
    <div className="p-8 max-w-5xl mx-auto flex flex-col gap-8 select-none">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white font-heading">Compare Agreements</h2>
        <p className="text-xs text-gray-400 mt-1">Select two of your uploaded contracts to align and review clause changes side-by-side.</p>
      </div>

      {/* Select Box */}
      <form onSubmit={handleCompare} className="glass-card p-6 border border-brand-border bg-brand-secondary/40 flex flex-col gap-6">
        <div className="flex flex-col md:flex-row items-center gap-4">
          <div className="flex-1 w-full flex flex-col gap-2">
            <label className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Document A</label>
            <select 
              value={docId1} 
              onChange={(e) => setDocId1(e.target.value)}
              className="bg-brand-dark border border-brand-border text-xs text-gray-300 rounded-xl px-4 py-3 outline-none cursor-pointer focus:text-white w-full"
              required
            >
              <option value="">-- Choose Contract A --</option>
              {processedDocs.map(d => (
                <option key={d.id} value={d.id}>{d.filename}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center justify-center text-gray-500 mt-6 flex-shrink-0">
            <GitCompare className="w-5 h-5" />
          </div>

          <div className="flex-1 w-full flex flex-col gap-2">
            <label className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Document B</label>
            <select 
              value={docId2} 
              onChange={(e) => setDocId2(e.target.value)}
              className="bg-brand-dark border border-brand-border text-xs text-gray-300 rounded-xl px-4 py-3 outline-none cursor-pointer focus:text-white w-full"
              required
            >
              <option value="">-- Choose Contract B --</option>
              {processedDocs.map(d => (
                <option key={d.id} value={d.id}>{d.filename}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex justify-end mt-2">
          <button 
            type="submit" 
            disabled={loading || !docId1 || !docId2}
            className="btn-gradient w-full md:w-auto px-8 py-3.5 rounded-xl flex items-center justify-center gap-2 font-heading text-sm font-semibold tracking-wider uppercase disabled:opacity-40 disabled:cursor-not-allowed select-none flex-shrink-0"
          >
            {loading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Analyzing...</span>
              </>
            ) : (
              <>
                <GitCompare className="w-4 h-4" />
                <span>Compare Agreements</span>
              </>
            )}
          </button>
        </div>
      </form>

      {/* Comparison Results */}
      <div className="flex-1">
        {loading && (
          <div className="py-20 flex flex-col items-center justify-center gap-3 text-gray-400">
            <Loader2 className="w-8 h-8 animate-spin text-accent-blue" />
            <span className="text-sm font-medium">Running contract alignment engine...</span>
          </div>
        )}

        {error && (
          <div className="p-4 text-xs text-rose-400 font-semibold border border-rose-500/20 bg-rose-500/5 rounded-xl text-center flex items-center justify-center gap-2">
            <AlertCircle className="w-4 h-4" />
            <span>{error}</span>
          </div>
        )}

        {!loading && !error && !result && (
          <div className="py-20 text-center text-gray-500 italic text-xs flex flex-col items-center gap-2">
            <GitCompare className="w-8 h-8 opacity-30" />
            <span>Choose two contracts above and click Compare to evaluate clause variations.</span>
          </div>
        )}

        {!loading && !error && result && (
          <div className="glass-card p-6 border border-brand-border flex flex-col gap-4 animate-fade-in text-left bg-brand-secondary/40">
            <h3 className="text-sm font-semibold text-gray-200 uppercase tracking-wider">Clause Variations Analysis</h3>
            <div className="bg-brand-tertiary/20 p-5 rounded-xl border border-brand-border/60">
              <p className="text-sm leading-[1.7] text-gray-300 whitespace-pre-wrap font-sans">
                {result.comparison_summary}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
