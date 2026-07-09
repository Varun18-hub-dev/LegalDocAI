import React from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Scale, FileText, Search, GitCompare, LogOut, MessageSquare, Settings } from 'lucide-react';
import { useAuthStore } from '../store/useAuthStore';

export const UserLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuthStore();

  const handleSignOut = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="app-container">
      {/* Sidebar Panel */}
      <aside className="sidebar flex flex-col justify-between h-full bg-brand-secondary border-r border-brand-border/60">
        <div className="flex flex-col flex-1 overflow-hidden">
          {/* Header */}
          <div className="sidebar-header flex items-center gap-2">
            <Scale className="w-6 h-6 text-accent-blue" />
            <span className="sidebar-logo">LegalDoc USER</span>
          </div>

          {/* Navigation Menu */}
          <div className="sidebar-menu overflow-y-auto">
            <div className="sidebar-section-title">Navigation</div>
            
            <button 
              onClick={() => navigate('/user/dashboard')}
              className={`menu-item ${location.pathname === '/user/dashboard' ? 'active-blue' : ''}`}
            >
              <Search className="w-4 h-4" />
              <span>Global KB Search</span>
            </button>

            <button 
              onClick={() => navigate('/user/documents')}
              className={`menu-item ${location.pathname === '/user/documents' ? 'active-blue' : ''}`}
            >
              <FileText className="w-4 h-4" />
              <span>My Documents</span>
            </button>

            <button 
              onClick={() => navigate('/user/chat')}
              className={`menu-item ${location.pathname === '/user/chat' ? 'active-blue' : ''}`}
            >
              <MessageSquare className="w-4 h-4" />
              <span>Ask Legal Assistant</span>
            </button>

            <button 
              onClick={() => navigate('/user/compare')}
              className={`menu-item ${location.pathname === '/user/compare' ? 'active-blue' : ''}`}
            >
              <GitCompare className="w-4 h-4" />
              <span>Compare Agreements</span>
            </button>

            <button 
              onClick={() => navigate('/user/settings')}
              className={`menu-item ${location.pathname === '/user/settings' ? 'active-blue' : ''}`}
            >
              <Settings className="w-4 h-4" />
              <span>Settings</span>
            </button>
          </div>
        </div>

        {/* Bottom Profile Card */}
        <div className="p-6 border-t border-brand-border/40 bg-brand-dark/20 flex flex-col gap-4 select-none">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2 min-w-0">
              <div className="w-8 h-8 rounded-full bg-accent-blue/10 border border-accent-blue/30 flex items-center justify-center text-accent-blue font-bold text-xs flex-shrink-0">
                {user?.name.substring(0, 2).toUpperCase()}
              </div>
              <div className="overflow-hidden">
                <p className="text-xs font-semibold text-gray-200 truncate">{user?.name}</p>
                <span className="text-[9px] font-bold tracking-wider px-1.5 py-0.5 border border-brand-border rounded-full bg-brand-tertiary text-accent-blue uppercase">
                  {user?.role}
                </span>
              </div>
            </div>
            
            <button 
              onClick={handleSignOut}
              className="p-2 rounded-lg text-gray-500 hover:text-rose-400 hover:bg-rose-500/10 transition-all"
              title="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
};
