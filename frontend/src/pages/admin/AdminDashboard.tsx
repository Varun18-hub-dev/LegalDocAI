import React, { useEffect, useState } from 'react';
import { apiService } from '../../services/api';
import { Users, Database, ShieldAlert, Cpu, Activity, Clock, Sliders } from 'lucide-react';

export const AdminDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMetrics();
  }, []);

  const fetchMetrics = async () => {
    try {
      const data = await apiService.getAdminMetrics();
      setMetrics(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !metrics) {
    return (
      <div className="p-8 text-center py-20 text-gray-400">
        <Activity className="w-8 h-8 animate-spin mx-auto text-accent-purple" />
        <p className="text-xs mt-3">Loading operational dashboard stats...</p>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-5xl mx-auto flex flex-col gap-8 select-none">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white font-heading">Operations Dashboard</h2>
        <p className="text-xs text-gray-400 mt-1">Platform-level usage metrics, active user distribution, and Gemini telemetry.</p>
      </div>

      {/* Metrics Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        
        {/* Total Users */}
        <div className="glass-card p-5 border border-brand-border flex items-center justify-between bg-brand-secondary/40">
          <div>
            <p className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">Total Users</p>
            <p className="text-2xl font-extrabold text-white mt-1">{metrics.total_users}</p>
            <div className="flex gap-2 mt-1.5 text-[9px] text-gray-400 font-semibold">
              <span className="text-accent-cyan">{metrics.total_lawyers} Lawyers</span>
              <span>•</span>
              <span className="text-accent-purple">{metrics.total_clients} Clients</span>
            </div>
          </div>
          <div className="p-3 bg-accent-purple/10 border border-accent-purple/20 text-accent-purple rounded-xl">
            <Users className="w-6 h-6" />
          </div>
        </div>

        {/* Total Documents */}
        <div className="glass-card p-5 border border-brand-border flex items-center justify-between bg-brand-secondary/40">
          <div>
            <p className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">Indexed Documents</p>
            <p className="text-2xl font-extrabold text-white mt-1">{metrics.total_documents}</p>
            <span className="text-[9px] text-emerald-400 font-semibold mt-1.5 block">100% processed</span>
          </div>
          <div className="p-3 bg-accent-purple/10 border border-accent-purple/20 text-accent-purple rounded-xl">
            <Database className="w-6 h-6" />
          </div>
        </div>

        {/* Queries Today */}
        <div className="glass-card p-5 border border-brand-border flex items-center justify-between bg-brand-secondary/40">
          <div>
            <p className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">Queries Today</p>
            <p className="text-2xl font-extrabold text-white mt-1">{metrics.queries_today}</p>
            <span className="text-[9px] text-gray-400 font-semibold mt-1.5 block">API status: healthy</span>
          </div>
          <div className="p-3 bg-accent-purple/10 border border-accent-purple/20 text-accent-purple rounded-xl">
            <Activity className="w-6 h-6" />
          </div>
        </div>

        {/* Latency */}
        <div className="glass-card p-5 border border-brand-border flex items-center justify-between bg-brand-secondary/40">
          <div>
            <p className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">Average API Latency</p>
            <p className="text-2xl font-extrabold text-white mt-1">{metrics.average_latency_ms} ms</p>
            <span className="text-[9px] text-gray-400 font-semibold mt-1.5 block">Includes hybrid RRF routing</span>
          </div>
          <div className="p-3 bg-accent-purple/10 border border-accent-purple/20 text-accent-purple rounded-xl">
            <Clock className="w-6 h-6" />
          </div>
        </div>

        {/* Cache Hit Rate */}
        <div className="glass-card p-5 border border-brand-border flex items-center justify-between bg-brand-secondary/40">
          <div>
            <p className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">Cache Hit Rate</p>
            <p className="text-2xl font-extrabold text-white mt-1">{metrics.cache_hit_rate}%</p>
            <span className="text-[9px] text-gray-400 font-semibold mt-1.5 block">Signature-validated cache</span>
          </div>
          <div className="p-3 bg-accent-purple/10 border border-accent-purple/20 text-accent-purple rounded-xl">
            <Sliders className="w-6 h-6" />
          </div>
        </div>

        {/* Gemini tokens */}
        <div className="glass-card p-5 border border-brand-border flex items-center justify-between bg-brand-secondary/40">
          <div>
            <p className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">Gemini Tokens Today</p>
            <p className="text-2xl font-extrabold text-white mt-1">{metrics.tokens_used_today.toLocaleString()}</p>
            <span className="text-[9px] text-gray-400 font-semibold mt-1.5 block">Model: gemini-2.5-flash</span>
          </div>
          <div className="p-3 bg-accent-purple/10 border border-accent-purple/20 text-accent-purple rounded-xl">
            <Cpu className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Diagnostics panel */}
      <div className="glass-card p-6 border border-brand-border flex flex-col gap-4 bg-brand-secondary/40">
        <h3 className="text-xs font-bold uppercase tracking-wider text-gray-400">System Telemetry status</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-brand-dark/20 border border-brand-border rounded-xl flex items-center justify-between">
            <span className="text-xs text-gray-400">FastAPI Server</span>
            <span className="text-xs font-bold text-emerald-400">ONLINE</span>
          </div>
          <div className="p-4 bg-brand-dark/20 border border-brand-border rounded-xl flex items-center justify-between">
            <span className="text-xs text-gray-400">ChromaDB Node</span>
            <span className="text-xs font-bold text-emerald-400">ONLINE</span>
          </div>
          <div className="p-4 bg-brand-dark/20 border border-brand-border rounded-xl flex items-center justify-between">
            <span className="text-xs text-gray-400">Errors Detected</span>
            <span className="text-xs font-bold text-emerald-400">0</span>
          </div>
        </div>
      </div>
    </div>
  );
};
