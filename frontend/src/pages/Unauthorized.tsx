import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldAlert, ArrowLeft } from 'lucide-react';

export const Unauthorized: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="flex h-screen w-screen justify-center items-center bg-brand-dark p-6 overflow-hidden relative">
      <div className="glass-card max-w-[440px] w-full border border-brand-border p-10 flex flex-col gap-6 items-center text-center z-10 shadow-glow-purple/15">
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-2xl text-rose-500 shadow-glow-purple/20">
          <ShieldAlert className="w-12 h-12" />
        </div>
        
        <div>
          <h1 className="font-heading text-2xl font-extrabold text-rose-400">Access Denied</h1>
          <p className="text-sm text-gray-400 mt-2 leading-relaxed">
            You do not have the required permissions or role configurations to access this workspace panel. 
            Please contact your system administrator if you believe this is an error.
          </p>
        </div>

        <button 
          onClick={() => navigate('/')}
          className="btn-gradient w-full py-3 rounded-xl flex items-center justify-center gap-2 font-heading text-sm font-semibold tracking-wider uppercase mt-2"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Go to Dashboard</span>
        </button>
      </div>
    </div>
  );
};
