import React, { useCallback, useState } from 'react';
import { Upload, FileText, CheckCircle2, AlertCircle } from 'lucide-react';
import { useDocumentStore } from '../store/useDocumentStore';
import { apiService } from '../services/api';

export const UploadZone: React.FC = () => {
  const [dragActive, setDragActive] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [currentFile, setCurrentFile] = useState<string | null>(null);
  
  const { isUploading, uploadProgress, setUploading, setUploadProgress, fetchDocuments } = useDocumentStore();

  const handleUpload = async (file: File) => {
    if (file.type !== 'application/pdf') {
      alert('Only PDF files are allowed.');
      return;
    }
    
    setUploading(true);
    setUploadProgress(0);
    setUploadStatus('uploading');
    setCurrentFile(file.name);
    
    try {
      await apiService.uploadDocument(file, (progressEvent) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        setUploadProgress(percentCompleted);
      });
      setUploadStatus('success');
      setUploading(false);
      // Refresh documents list
      await fetchDocuments();
      setTimeout(() => {
        setUploadStatus('idle');
        setCurrentFile(null);
      }, 3000);
    } catch (error) {
      console.error(error);
      setUploadStatus('error');
      setUploading(false);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleUpload(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleUpload(e.target.files[0]);
    }
  };

  return (
    <div className="w-full">
      <div 
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        className={`relative flex flex-col items-center justify-center p-8 border-2 border-dashed rounded-xl transition-all duration-300 ${
          dragActive 
            ? 'border-accent-purple bg-purple-500/5 shadow-glow-purple' 
            : 'border-brand-border hover:border-accent-blue bg-white/1'
        }`}
      >
        <input 
          type="file" 
          id="file-upload" 
          multiple={false} 
          accept="application/pdf"
          onChange={handleChange}
          className="hidden"
          disabled={isUploading}
        />
        
        {uploadStatus === 'idle' && (
          <label htmlFor="file-upload" className="flex flex-col items-center cursor-pointer gap-4">
            <div className="p-4 bg-brand-tertiary rounded-full text-gray-400 hover:text-accent-blue transition-all duration-300">
              <Upload className="w-8 h-8" />
            </div>
            <div className="text-center">
              <p className="font-semibold text-gray-200 text-sm">Drag and drop your PDF here</p>
              <p className="text-xs text-gray-400 mt-1">or click to browse files</p>
            </div>
          </label>
        )}

        {uploadStatus === 'uploading' && (
          <div className="flex flex-col items-center w-full gap-4">
            <div className="p-4 bg-brand-tertiary rounded-full text-accent-blue animate-pulse-subtle">
              <FileText className="w-8 h-8" />
            </div>
            <div className="w-full text-center max-w-[280px]">
              <p className="font-semibold text-gray-200 text-sm truncate">{currentFile}</p>
              <p className="text-xs text-gray-400 mt-1">Uploading and indexing document...</p>
              <div className="w-full mt-4 h-1.5 bg-brand-tertiary rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-accent-blue to-accent-purple transition-all duration-300 ease-out"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
              <p className="text-xs font-mono text-gray-400 mt-2">{uploadProgress}%</p>
            </div>
          </div>
        )}

        {uploadStatus === 'success' && (
          <div className="flex flex-col items-center w-full gap-3 text-center">
            <div className="p-4 bg-emerald-500/10 rounded-full text-emerald-500">
              <CheckCircle2 className="w-8 h-8" />
            </div>
            <div>
              <p className="font-semibold text-emerald-400 text-sm">Upload Successful!</p>
              <p className="text-xs text-gray-400 mt-1">Your document has been processed.</p>
            </div>
          </div>
        )}

        {uploadStatus === 'error' && (
          <div className="flex flex-col items-center w-full gap-3 text-center">
            <div className="p-4 bg-rose-500/10 rounded-full text-rose-500">
              <AlertCircle className="w-8 h-8" />
            </div>
            <div>
              <p className="font-semibold text-rose-400 text-sm">Upload Failed</p>
              <p className="text-xs text-gray-400 mt-1">Something went wrong during indexing.</p>
              <button 
                onClick={() => setUploadStatus('idle')}
                className="mt-3 px-4 py-1.5 bg-brand-tertiary hover:bg-brand-secondary border border-brand-border text-xs rounded-lg transition-all"
              >
                Try Again
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
