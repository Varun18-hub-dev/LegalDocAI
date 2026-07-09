import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { Unauthorized } from './pages/Unauthorized';
import { ProtectedRoute } from './components/ProtectedRoute';
import { useAuthStore } from './store/useAuthStore';

// Layouts
import { UserLayout } from './layouts/UserLayout';
import { AdminLayout } from './layouts/AdminLayout';

// User Pages
import { UserDashboard } from './pages/user/UserDashboard';
import { UserDocuments } from './pages/user/UserDocuments';
import { UserChat } from './pages/user/UserChat';
import { UserCompare } from './pages/user/UserCompare';
import { UserSettings } from './pages/user/UserSettings';

// Admin Pages
import { AdminDashboard } from './pages/admin/AdminDashboard';
import { AdminUsers } from './pages/admin/AdminUsers';
import { AdminDocuments } from './pages/admin/AdminDocuments';
import { AdminKnowledgeBase } from './pages/admin/AdminKnowledgeBase';
import { AdminLogs } from './pages/admin/AdminLogs';

// Initialize React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

const RoleRedirect: React.FC = () => {
  const { user } = useAuthStore();
  if (!user) return <Navigate to="/login" replace />;
  if (user.role === 'ADMIN') return <Navigate to="/admin/dashboard" replace />;
  return <Navigate to="/user/dashboard" replace />;
};

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Routes>
          {/* Auth Routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/unauthorized" element={<Unauthorized />} />

          {/* Root Redirect to specific role dashboard */}
          <Route 
            path="/" 
            element={
              <ProtectedRoute>
                <RoleRedirect />
              </ProtectedRoute>
            } 
          />

          {/* User Workspace Routes */}
          <Route 
            path="/user" 
            element={
              <ProtectedRoute allowedRoles={['USER']}>
                <UserLayout />
              </ProtectedRoute>
            }
          >
            <Route path="dashboard" element={<UserDashboard />} />
            <Route path="documents" element={<UserDocuments />} />
            <Route path="chat/:docId" element={<UserChat />} />
            <Route path="compare" element={<UserCompare />} />
            <Route path="settings" element={<UserSettings />} />
          </Route>

          {/* Admin Workspace Routes */}
          <Route 
            path="/admin" 
            element={
              <ProtectedRoute allowedRoles={['ADMIN']}>
                <AdminLayout />
              </ProtectedRoute>
            }
          >
            <Route path="dashboard" element={<AdminDashboard />} />
            <Route path="users" element={<AdminUsers />} />
            <Route path="documents" element={<AdminDocuments />} />
            <Route path="kb" element={<AdminKnowledgeBase />} />
            <Route path="logs" element={<AdminLogs />} />
            <Route path="settings" element={<UserSettings />} />
          </Route>

          {/* Catch all redirecting back to home role redirect */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
