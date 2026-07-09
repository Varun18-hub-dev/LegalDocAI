import React, { useEffect, useRef, useState } from 'react';
import * as pdfjsLib from 'pdfjs-dist';
import { ZoomIn, ZoomOut, ChevronLeft, ChevronRight, Loader2 } from 'lucide-react';
import { useChatStore } from '../store/useChatStore';

// Configure PDFJS Worker
pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url
).toString();

interface PDFViewerProps {
  docId: string;
}

export const PDFViewer: React.FC<PDFViewerProps> = ({ docId }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [pdf, setPdf] = useState<any>(null);
  const [pageNum, setPageNum] = useState<number>(1);
  const [numPages, setNumPages] = useState<number>(0);
  const [scale, setScale] = useState<number>(1.2);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const { pdfPageJump, setPdfPageJump } = useChatStore();

  // Load PDF document when docId changes
  useEffect(() => {
    const loadPDF = async () => {
      setLoading(true);
      setError(null);
      setPdf(null);
      setPageNum(1);
      
      const apiBase = import.meta.env.VITE_API_BASE_URL || '/api/v1';
      const pdfUrl = `${apiBase}/documents/${docId}/pdf`;
      const token = localStorage.getItem('auth_token');
      
      try {
        const loadingTask = pdfjsLib.getDocument({
          url: pdfUrl,
          withCredentials: false,
          httpHeaders: token ? { 'Authorization': `Bearer ${token}` } : {}
        });
        const pdfDoc = await loadingTask.promise;
        setPdf(pdfDoc);
        setNumPages(pdfDoc.numPages);
      } catch (err: any) {
        console.error('Error loading PDF:', err);
        setError('Failed to load PDF document.');
      } finally {
        setLoading(false);
      }
    };

    if (docId) {
      loadPDF();
    }
  }, [docId]);

  // Listen to jumps triggered by chat citations
  useEffect(() => {
    if (pdfPageJump !== null && pdfPageJump > 0 && pdfPageJump <= numPages) {
      setPageNum(pdfPageJump);
      setPdfPageJump(null); // Clear jump signal after navigating
    }
  }, [pdfPageJump, numPages, setPdfPageJump]);

  // Render the current page on the canvas
  useEffect(() => {
    const renderPage = async () => {
      if (!pdf || !canvasRef.current) return;

      const canvas = canvasRef.current;
      const context = canvas.getContext('2d');
      if (!context) return;

      try {
        const page = await pdf.getPage(pageNum);
        const viewport = page.getViewport({ scale });
        
        // Match canvas size to PDF viewport
        canvas.height = viewport.height;
        canvas.width = viewport.width;

        const renderContext = {
          canvasContext: context,
          viewport: viewport
        };
        
        await page.render(renderContext).promise;
      } catch (err) {
        console.error('Error rendering page:', err);
      }
    };

    renderPage();
  }, [pdf, pageNum, scale]);

  const handlePrevPage = () => {
    if (pageNum > 1) {
      setPageNum(pageNum - 1);
    }
  };

  const handleNextPage = () => {
    if (pageNum < numPages) {
      setPageNum(pageNum + 1);
    }
  };

  const handleZoomIn = () => {
    setScale((prevScale) => Math.min(prevScale + 0.2, 2.4));
  };

  const handleZoomOut = () => {
    setScale((prevScale) => Math.max(prevScale - 0.2, 0.6));
  };

  return (
    <div className="flex flex-col h-full bg-brand-dark border-l border-brand-border">
      {/* PDF Controls Header */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-brand-border bg-brand-secondary/90 backdrop-blur-sm z-10">
        <div className="flex items-center gap-2">
          <button 
            onClick={handlePrevPage}
            disabled={pageNum <= 1 || loading}
            className="p-1.5 rounded-lg bg-brand-tertiary border border-brand-border text-gray-300 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed hover:bg-brand-secondary transition-all"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span className="text-xs font-mono text-gray-300 px-2 select-none">
            Page {pageNum} / {numPages || '--'}
          </span>
          <button 
            onClick={handleNextPage}
            disabled={pageNum >= numPages || loading}
            className="p-1.5 rounded-lg bg-brand-tertiary border border-brand-border text-gray-300 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed hover:bg-brand-secondary transition-all"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        <div className="flex items-center gap-2">
          <button 
            onClick={handleZoomOut}
            disabled={loading}
            className="p-1.5 rounded-lg bg-brand-tertiary border border-brand-border text-gray-300 hover:text-white hover:bg-brand-secondary transition-all"
            title="Zoom Out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <span className="text-xs font-mono text-gray-300 px-1 select-none">
            {Math.round(scale * 100)}%
          </span>
          <button 
            onClick={handleZoomIn}
            disabled={loading}
            className="p-1.5 rounded-lg bg-brand-tertiary border border-brand-border text-gray-300 hover:text-white hover:bg-brand-secondary transition-all"
            title="Zoom In"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Canvas PDF Display Area */}
      <div className="flex-1 overflow-auto p-6 flex justify-center items-start bg-brand-dark/50">
        {loading && (
          <div className="flex flex-col items-center gap-3 py-20 text-gray-400">
            <Loader2 className="w-8 h-8 animate-spin text-accent-purple" />
            <span className="text-sm font-medium">Loading document...</span>
          </div>
        )}
        
        {error && (
          <div className="text-center py-20 text-rose-400 font-medium text-sm">
            {error}
          </div>
        )}

        {!loading && !error && pdf && (
          <div className="shadow-2xl border border-brand-border rounded-lg overflow-hidden bg-white">
            <canvas ref={canvasRef} />
          </div>
        )}
      </div>
    </div>
  );
};
