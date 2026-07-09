import React from 'react';
import { useAuthStore } from '../../store/useAuthStore';
import { useNavigate } from 'react-router-dom';
import { Settings, LogOut, User, Mail } from 'lucide-react';

export const UserSettings: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  const handleSignOut = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="p-8 max-w-2xl mx-auto flex flex-col gap-8 select-none">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white font-heading">Settings</h2>
        <p className="text-xs text-gray-400 mt-1">Manage your account profile details and workspace options.</p>
      </div>

      <div className="glass-card p-6 border border-brand-border flex flex-col gap-6 bg-brand-secondary/40">
        <h3 className="text-sm font-semibold text-gray-200">Account Profile</h3>

        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-4 p-4 bg-brand-dark/30 border border-brand-border rounded-xl">
            <User className="w-5 h-5 text-gray-400" />
            <div>
              <p className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">Display Name</p>
              <p className="text-sm font-semibold text-gray-200 mt-0.5">{user?.name}</p>
            </div>
          </div>

          <div className="flex items-center gap-4 p-4 bg-brand-dark/30 border border-brand-border rounded-xl">
            <Mail className="w-5 h-5 text-gray-400" />
            <div>
              <p className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">Email Address</p>
              <p className="text-sm font-semibold text-gray-200 mt-0.5">{user?.email}</p>
            </div>
          </div>

          <div className="flex items-center gap-4 p-4 bg-brand-dark/30 border border-brand-border rounded-xl">
            <Settings className="w-5 h-5 text-gray-400" />
            <div>
              <p className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">Access Profile Role</p>
              <p className="text-sm font-semibold text-accent-blue mt-0.5 uppercase">{user?.role}</p>
            </div>
          </div>
        </div>

        <button 
          onClick={handleSignOut}
          className="mt-4 py-3 rounded-xl border border-rose-500/20 bg-rose-500/5 hover:bg-rose-500/10 text-rose-400 flex items-center justify-center gap-2 font-heading text-sm font-semibold tracking-wider uppercase transition-all"
        >
          <LogOut className="w-4 h-4" />
          <span>Sign Out</span>
        </button>
      </div>
    </div>
  );
};
