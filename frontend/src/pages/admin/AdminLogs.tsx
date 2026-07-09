import React, { useEffect, useState } from 'react';
import { apiService } from '../../services/api';
import { Sliders, RefreshCw, Terminal, Clock, ShieldCheck } from 'lucide-react';

export const AdminLogs: React.FC = () => {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLogs();
  }, []);

  const fetchLogs = async () => {
    try {
      const data = await apiService.getAdminLogs();
      setLogs(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-5xl mx-auto flex flex-col gap-8 select-none">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white font-heading">Operations Audit Logs</h2>
        <p className="text-xs text-gray-400 mt-1">Review live security audit records, login events, and pipeline error reports.</p>
      </div>

      <div className="glass-card p-6 border border-brand-border bg-brand-secondary/40">
        <div className="flex items-center gap-2 mb-4 border-b border-brand-border/60 pb-3">
          <Terminal className="w-4 h-4 text-accent-purple" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-gray-400">System Logs Stream</h3>
        </div>

        {loading ? (
          <div className="py-12 flex justify-center">
            <RefreshCw className="w-6 h-6 animate-spin text-accent-purple" />
          </div>
        ) : logs.length === 0 ? (
          <div className="py-12 text-center text-gray-500 italic text-xs">
            No system logs captured yet.
          </div>
        ) : (
          <div className="flex flex-col gap-3 font-mono text-[11px] leading-relaxed">
            {logs.map((log, idx) => (
              <div key={idx} className="p-3 bg-brand-dark/40 border border-brand-border/50 rounded-lg flex flex-col md:flex-row md:items-center justify-between gap-2">
                <div className="flex items-start md:items-center gap-3">
                  <span className="text-[10px] text-gray-500 flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5" />
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </span>
                  <div>
                    <span className="font-semibold text-accent-purple">[{log.event}]</span>
                    <span className="text-gray-300 ml-2">{log.detail}</span>
                  </div>
                </div>
                <span className={`self-start md:self-auto px-1.5 py-0.5 border rounded text-[9px] font-bold ${
                  log.status === 'SUCCESS'
                    ? 'border-emerald-500/20 bg-emerald-500/5 text-emerald-400'
                    : 'border-rose-500/20 bg-rose-500/5 text-rose-400'
                }`}>
                  {log.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
