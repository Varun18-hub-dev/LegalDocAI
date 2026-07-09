import React from 'react';
import { UserDocument } from '../types';
import { FileText, Calendar, Layers, CheckCircle } from 'lucide-react';

interface ComparisonTableProps {
  doc1: UserDocument | null;
  doc2: UserDocument | null;
}

export const ComparisonTable: React.FC<ComparisonTableProps> = ({ doc1, doc2 }) => {
  if (!doc1 || !doc2) return null;

  return (
    <div className="w-full border border-brand-border rounded-xl bg-brand-secondary/30 overflow-hidden shadow-lg">
      <div className="grid grid-cols-3 border-b border-brand-border bg-brand-secondary/80 font-heading font-semibold text-xs uppercase tracking-wider text-gray-400 p-3 select-none text-center">
        <div>Property</div>
        <div>Document 1</div>
        <div>Document 2</div>
      </div>
      
      <div className="flex flex-col text-sm">
        {/* Name */}
        <div className="grid grid-cols-3 border-b border-brand-border p-3 text-center items-center">
          <div className="text-gray-400 font-medium flex items-center justify-center gap-2">
            <FileText className="w-4 h-4 text-accent-blue" /> Filename
          </div>
          <div className="text-gray-200 truncate font-semibold px-2">{doc1.filename}</div>
          <div className="text-gray-200 truncate font-semibold px-2">{doc2.filename}</div>
        </div>

        {/* Upload Date */}
        <div className="grid grid-cols-3 border-b border-brand-border p-3 text-center items-center">
          <div className="text-gray-400 font-medium flex items-center justify-center gap-2">
            <Calendar className="w-4 h-4 text-accent-blue" /> Uploaded At
          </div>
          <div className="text-gray-300 font-mono text-xs">
            {new Date(doc1.uploaded_at).toLocaleDateString()}
          </div>
          <div className="text-gray-300 font-mono text-xs">
            {new Date(doc2.uploaded_at).toLocaleDateString()}
          </div>
        </div>

        {/* Pages */}
        <div className="grid grid-cols-3 border-b border-brand-border p-3 text-center items-center">
          <div className="text-gray-400 font-medium flex items-center justify-center gap-2">
            <Layers className="w-4 h-4 text-accent-blue" /> Total Pages
          </div>
          <div className="text-gray-200 font-semibold">{doc1.total_pages || '--'}</div>
          <div className="text-gray-200 font-semibold">{doc2.total_pages || '--'}</div>
        </div>

        {/* Chunks */}
        <div className="grid grid-cols-3 border-b border-brand-border p-3 text-center items-center">
          <div className="text-gray-400 font-medium flex items-center justify-center gap-2">
            <Layers className="w-4 h-4 text-accent-blue" /> Text Chunks
          </div>
          <div className="text-gray-200 font-semibold">{doc1.total_chunks || '--'}</div>
          <div className="text-gray-200 font-semibold">{doc2.total_chunks || '--'}</div>
        </div>

        {/* Status */}
        <div className="grid grid-cols-3 p-3 text-center items-center">
          <div className="text-gray-400 font-medium flex items-center justify-center gap-2">
            <CheckCircle className="w-4 h-4 text-accent-blue" /> Process Status
          </div>
          <div>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 uppercase">
              {doc1.status}
            </span>
          </div>
          <div>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 uppercase">
              {doc2.status}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
