import React, { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Scale, FileText, Search, GitCompare, LogOut, MessageSquare, Settings, Menu, X } from 'lucide-react';
import { useAuthStore } from '../store/useAuthStore';

export const UserLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuthStore();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleSignOut = () => {
    logout();
    navigate('/login');
  };

  const handleNavigate = (path: string) => {
    navigate(path);
    setSidebarOpen(false); // Close sidebar on mobile navigation click
  };

  return (
    <div className="app-container flex flex-col md:flex-row h-screen w-screen overflow-hidden bg-brand-dark">
      {/* Mobile Top Header */}
      <header className="md:hidden flex items-center justify-between px-6 py-4 bg-brand-secondary border-b border-brand-border/60 flex-shrink-0 select-none">
        <div className="flex items-center gap-2">
          <Scale className="w-5 h-5 text-accent-blue" />
          <span className="font-heading text-lg font-bold bg-gradient-to-r from-accent-cyan via-accent-blue to-accent-purple bg-clip-text text-transparent">
            LegalDoc USER
          </span>
        </div>
        <button 
          onClick={() => setSidebarOpen(true)}
          className="p-2 rounded-lg bg-brand-tertiary border border-brand-border text-gray-300 hover:text-white"
        >
          <Menu className="w-5 h-5" />
        </button>
      </header>

      {/* Sidebar Overlay (mobile only) */}
      {sidebarOpen && (
        <div 
          className="md:hidden fixed inset-0 bg-brand-dark/70 backdrop-blur-sm z-40 transition-all duration-300"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar Panel */}
      <aside 
        className={`sidebar fixed inset-y-0 left-0 z-50 md:static md:translate-x-0 transition-transform duration-300 flex flex-col justify-between h-full bg-brand-secondary border-r border-brand-border/60 flex-shrink-0 shadow-2xl ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex flex-col flex-1 overflow-hidden">
          {/* Header */}
          <div className="sidebar-header flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <Scale className="w-6 h-6 text-accent-blue" />
              <span className="sidebar-logo">LegalDoc USER</span>
            </div>
            <button 
              onClick={() => setSidebarOpen(false)}
              className="md:hidden p-1.5 rounded-lg bg-brand-tertiary border border-brand-border text-gray-400 hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Navigation Menu */}
          <div className="sidebar-menu overflow-y-auto">
            <div className="sidebar-section-title">Navigation</div>
            
            <button 
              onClick={() => handleNavigate('/user/dashboard')}
              className={`menu-item ${location.pathname === '/user/dashboard' ? 'active-blue' : ''}`}
            >
              <Search className="w-4 h-4" />
              <span>Global KB Search</span>
            </button>

            <button 
              onClick={() => handleNavigate('/user/documents')}
              className={`menu-item ${location.pathname === '/user/documents' ? 'active-blue' : ''}`}
            >
              <FileText className="w-4 h-4" />
              <span>My Documents</span>
            </button>

            <button 
              onClick={() => handleNavigate('/user/chat')}
              className={`menu-item ${location.pathname.startsWith('/user/chat') ? 'active-blue' : ''}`}
            >
              <MessageSquare className="w-4 h-4" />
              <span>Ask Legal Assistant</span>
            </button>

            <button 
              onClick={() => handleNavigate('/user/compare')}
              className={`menu-item ${location.pathname === '/user/compare' ? 'active-blue' : ''}`}
            >
              <GitCompare className="w-4 h-4" />
              <span>Compare Agreements</span>
            </button>

            <button 
              onClick={() => handleNavigate('/user/settings')}
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
      <main className="main-content flex-1 h-full overflow-hidden flex flex-col">
        <Outlet />
      </main>
    </div>
  );
};
