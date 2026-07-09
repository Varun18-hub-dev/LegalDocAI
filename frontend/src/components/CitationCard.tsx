import React, { useState } from 'react';
import { ChevronDown, ChevronUp, FileText } from 'lucide-react';
import { CitationSchema } from '../types';
import { useChatStore } from '../store/useChatStore';

interface CitationCardProps {
  node: CitationSchema;
  index: number;
  isUserDoc?: boolean;
}

export const CitationCard: React.FC<CitationCardProps> = ({ node, index, isUserDoc = false }) => {
  const [expanded, setExpanded] = useState(false);
  const setPdfPageJump = useChatStore((state) => state.setPdfPageJump);

  // Determine Source / Act Name
  const sourceName = node.act_name || node.case_name || node.filename || node.document_id;
  
  // Construct Location Label
  const locationLabel = [
    node.coordinate,
    node.segment,
    node.title
  ].filter(Boolean).join(' > ');

  const handleCardClick = () => {
    if ((isUserDoc || node.type === 'user_document') && node.page !== undefined && node.page !== null) {
      // Jump to page in PDF viewer
      setPdfPageJump(node.page);
    } else {
      setExpanded(!expanded);
    }
  };

  return (
    <div className="border border-brand-border rounded-xl bg-brand-secondary/40 hover:bg-brand-secondary/70 hover:border-accent-blue/30 transition-all duration-300 overflow-hidden">
      <div 
        onClick={handleCardClick}
        className="p-4 flex gap-4 items-start cursor-pointer select-none"
      >
        <span className="flex-shrink-0 w-6 h-6 rounded bg-accent-blue/10 text-accent-blue border border-accent-blue/20 flex items-center justify-center text-xs font-bold font-mono">
          {index}
        </span>
        
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-accent-blue font-heading truncate max-w-[200px]" title={sourceName || ''}>
              {sourceName}
            </span>
            
            {node.confidence_score !== undefined && (
              <span className="text-[10px] font-bold px-2 py-0.5 border rounded-full font-sans text-emerald-400 bg-emerald-500/10 border-emerald-500/20">
                Match ({Math.round(node.confidence_score * 100)}%)
              </span>
            )}
          </div>
          
          <h4 className="text-sm font-semibold text-gray-200 mt-1 truncate">
            {node.type === 'user_document' || isUserDoc 
              ? `Page ${node.page || 1}` 
              : locationLabel || 'Statute Section'}
          </h4>
          
          <p className="text-xs text-gray-400 mt-1.5 line-clamp-2 leading-relaxed">
            {node.snippet}
          </p>
        </div>

        <button className="text-gray-500 hover:text-gray-300 p-1">
          {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
      </div>

      {expanded && (
        <div className="px-4 pb-4 pt-1 border-t border-brand-border bg-brand-dark/20 text-xs text-gray-300 leading-relaxed flex flex-col gap-3">
          <div className="whitespace-pre-wrap font-sans text-gray-200">
            {node.snippet}
          </div>
        </div>
      )}
    </div>
  );
};
