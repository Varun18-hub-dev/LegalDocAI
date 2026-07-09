import React, { useEffect, useState } from 'react';
import { apiService } from '../../services/api';
import { HealthResponse } from '../../types';
import { Shield, RefreshCw, Cpu, Database, CheckSquare, HardDrive } from 'lucide-react';

export const AdminKnowledgeBase: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHealth();
  }, []);

  const fetchHealth = async () => {
    try {
      const data = await apiService.getHealth();
      setHealth(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-5xl mx-auto flex flex-col gap-8 select-none">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white font-heading">Statutes Knowledge Base</h2>
        <p className="text-xs text-gray-400 mt-1">Inspecting ChromaDB vector indices, SQLite relational mappings, and tokenizers.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Left Card: Database Health meters */}
        <div className="glass-card p-6 border border-brand-border bg-brand-secondary/40 flex flex-col gap-6">
          <h3 className="text-xs font-bold uppercase tracking-wider text-gray-400">Database node states</h3>

          {loading ? (
            <div className="py-12 flex justify-center">
              <RefreshCw className="w-6 h-6 animate-spin text-accent-purple" />
            </div>
          ) : health ? (
            <div className="flex flex-col gap-4">
              
              <div className="p-4 bg-brand-dark/25 border border-brand-border rounded-xl flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Database className="w-5 h-5 text-accent-purple" />
                  <div>
                    <h4 className="text-xs font-semibold text-gray-200">SQLite Database</h4>
                    <p className="text-[10px] text-gray-400 mt-0.5">Primary relational store</p>
                  </div>
                </div>
                <span className="text-[10px] font-bold px-2 py-0.5 border border-emerald-500/20 bg-emerald-500/5 text-emerald-400 uppercase rounded">
                  {health.sqlite}
                </span>
              </div>

              <div className="p-4 bg-brand-dark/25 border border-brand-border rounded-xl flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <HardDrive className="w-5 h-5 text-accent-purple" />
                  <div>
                    <h4 className="text-xs font-semibold text-gray-200">ChromaDB Vector Store</h4>
                    <p className="text-[10px] text-gray-400 mt-0.5">Document embedding index</p>
                  </div>
                </div>
                <span className="text-[10px] font-bold px-2 py-0.5 border border-emerald-500/20 bg-emerald-500/5 text-emerald-400 uppercase rounded">
                  {health.chromadb}
                </span>
              </div>

              <div className="p-4 bg-brand-dark/25 border border-brand-border rounded-xl flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Cpu className="w-5 h-5 text-accent-purple" />
                  <div>
                    <h4 className="text-xs font-semibold text-gray-200">Gemini LLM Gateway</h4>
                    <p className="text-[10px] text-gray-400 mt-0.5">Generative reasoning agent</p>
                  </div>
                </div>
                <span className="text-[10px] font-bold px-2 py-0.5 border border-emerald-500/20 bg-emerald-500/5 text-emerald-400 uppercase rounded">
                  {health.gemini}
                </span>
              </div>

            </div>
          ) : (
            <div className="text-center py-6 text-rose-400 text-xs font-semibold">
              Failed to load health metrics.
            </div>
          )}
        </div>

        {/* Right Card: Schema version parameters */}
        <div className="glass-card p-6 border border-brand-border bg-brand-secondary/40 flex flex-col gap-6">
          <h3 className="text-xs font-bold uppercase tracking-wider text-gray-400">Knowledge Base properties</h3>

          {loading ? (
            <div className="py-12 flex justify-center">
              <RefreshCw className="w-6 h-6 animate-spin text-accent-purple" />
            </div>
          ) : health ? (
            <div className="flex flex-col gap-4">
              <div className="p-4 bg-brand-dark/25 border border-brand-border rounded-xl">
                <p className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">Statutory Volumes Count</p>
                <p className="text-sm font-semibold text-gray-200 mt-1">{health.knowledge_base}</p>
              </div>

              <div className="p-4 bg-brand-dark/25 border border-brand-border rounded-xl">
                <p className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">Embedding Model Specification</p>
                <p className="text-xs font-mono text-gray-300 mt-1">{health.embedding_model}</p>
              </div>

              <div className="p-4 bg-brand-dark/25 border border-brand-border rounded-xl flex justify-between items-center">
                <div>
                  <p className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">API Version Code</p>
                  <p className="text-xs font-mono text-gray-300 mt-0.5">{health.api_version}</p>
                </div>
                <span className="text-[10px] font-bold px-2.5 py-1 border border-accent-purple/20 bg-accent-purple/5 text-accent-purple rounded-xl uppercase">
                  Stable
                </span>
              </div>
            </div>
          ) : (
            <div className="text-center py-6 text-rose-400 text-xs font-semibold">
              Failed to load properties.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
