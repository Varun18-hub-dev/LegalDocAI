import React from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Scale, Users, Database, LogOut, Shield, Activity, Settings } from 'lucide-react';
import { useAuthStore } from '../store/useAuthStore';

export const AdminLayout: React.FC = () => {
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
            <Scale className="w-6 h-6 text-accent-purple" />
            <span className="sidebar-logo">Admin Console</span>
          </div>

          {/* Navigation Menu */}
          <div className="sidebar-menu overflow-y-auto">
            <div className="sidebar-section-title">Operations Control</div>
            
            <button 
              onClick={() => navigate('/admin/dashboard')}
              className={`menu-item ${location.pathname === '/admin/dashboard' ? 'active-blue' : ''}`}
            >
              <Activity className="w-4 h-4" />
              <span>Metrics & Stats</span>
            </button>

            <button 
              onClick={() => navigate('/admin/users')}
              className={`menu-item ${location.pathname === '/admin/users' ? 'active-blue' : ''}`}
            >
              <Users className="w-4 h-4" />
              <span>Accounts Directory</span>
            </button>

            <button 
              onClick={() => navigate('/admin/documents')}
              className={`menu-item ${location.pathname === '/admin/documents' ? 'active-blue' : ''}`}
            >
              <Database className="w-4 h-4" />
              <span>Uploaded Documents</span>
            </button>

            <button 
              onClick={() => navigate('/admin/kb')}
              className={`menu-item ${location.pathname === '/admin/kb' ? 'active-blue' : ''}`}
            >
              <Shield className="w-4 h-4" />
              <span>Knowledge Base</span>
            </button>

            <button 
              onClick={() => navigate('/admin/logs')}
              className={`menu-item ${location.pathname === '/admin/logs' ? 'active-blue' : ''}`}
            >
              <Settings className="w-4 h-4" />
              <span>Audit Logs</span>
            </button>
          </div>
        </div>

        {/* Bottom Profile Card */}
        <div className="p-6 border-t border-brand-border/40 bg-brand-dark/20 flex flex-col gap-4 select-none">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2 min-w-0">
              <div className="w-8 h-8 rounded-full bg-accent-purple/10 border border-accent-purple/30 flex items-center justify-center text-accent-purple font-bold text-xs flex-shrink-0">
                {user?.name.substring(0, 2).toUpperCase()}
              </div>
              <div className="overflow-hidden">
                <p className="text-xs font-semibold text-gray-200 truncate">{user?.name}</p>
                <span className="text-[9px] font-bold tracking-wider px-1.5 py-0.5 border border-brand-border rounded-full bg-brand-tertiary text-accent-purple uppercase">
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
