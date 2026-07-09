import React, { useEffect, useState } from 'react';
import { apiService } from '../../services/api';
import { Database, FileText, RefreshCw, Clock } from 'lucide-react';

export const AdminDocuments: React.FC = () => {
  const [documents, setDocuments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      const data = await apiService.getAdminDocuments();
      setDocuments(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-5xl mx-auto flex flex-col gap-8 select-none">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white font-heading">Uploaded Documents Oversight</h2>
        <p className="text-xs text-gray-400 mt-1">Inspecting global system document volumes, upload statuses, and file ownership details.</p>
      </div>

      <div className="glass-card p-6 border border-brand-border bg-brand-secondary/40">
        {loading ? (
          <div className="py-12 flex justify-center">
            <RefreshCw className="w-6 h-6 animate-spin text-accent-purple" />
          </div>
        ) : documents.length === 0 ? (
          <div className="py-12 text-center text-gray-500 italic text-xs">
            No legal documents uploaded globally.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-brand-border pb-3 text-[10px] font-bold text-gray-500 uppercase tracking-wider">
                  <th className="py-3 px-2">File Name</th>
                  <th className="py-3 px-2">Owner Name</th>
                  <th className="py-3 px-2">Visibility</th>
                  <th className="py-3 px-2">Uploaded At</th>
                  <th className="py-3 px-2 text-right">Status</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((d) => (
                  <tr key={d.id} className="border-b border-brand-border/40 hover:bg-brand-dark/20 text-xs text-gray-300 transition-all">
                    <td className="py-4 px-2 font-semibold text-gray-200 truncate max-w-[200px]" title={d.filename}>
                      <div className="flex items-center gap-2">
                        <FileText className="w-4 h-4 text-accent-purple" />
                        <span>{d.filename}</span>
                      </div>
                    </td>
                    <td className="py-4 px-2">{d.owner_name || 'N/A'}</td>
                    <td className="py-4 px-2">
                      <span className="text-[10px] font-bold tracking-wider px-2 py-0.5 border border-brand-border rounded-full bg-brand-tertiary text-gray-400 uppercase">
                        {d.visibility}
                      </span>
                    </td>
                    <td className="py-4 px-2 flex items-center gap-1.5 mt-1 text-[11px] text-gray-400">
                      <Clock className="w-3.5 h-3.5" />
                      <span>{new Date(d.uploaded_at).toLocaleDateString()}</span>
                    </td>
                    <td className="py-4 px-2 text-right">
                      <span className={`px-2 py-0.5 border rounded text-[10px] font-bold ${
                        d.status === 'processed' 
                          ? 'border-emerald-500/20 bg-emerald-500/5 text-emerald-400' 
                          : d.status === 'failed' 
                          ? 'border-rose-500/20 bg-rose-500/5 text-rose-400'
                          : 'border-amber-500/20 bg-amber-500/5 text-amber-400 animate-pulse'
                      }`}>
                        {d.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
