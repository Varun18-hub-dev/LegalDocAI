import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Scale, Lock, Mail, Loader2, AlertTriangle } from 'lucide-react';
import { apiService } from '../services/api';
import { useAuthStore } from '../store/useAuthStore';

export const Login: React.FC = () => {
  const navigate = useNavigate();
  const setAuth = useAuthStore((state) => state.setAuth);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const data = await apiService.login({ email, password });
      setAuth(data.access_token, data.user);
      
      // Redirect based on role
      const role = data.user.role;
      if (role === 'ADMIN') {
        navigate('/');
      } else if (role === 'LAWYER') {
        navigate('/');
      } else {
        navigate('/');
      }
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Authentication failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen w-screen justify-center items-center bg-brand-dark p-6 overflow-hidden relative">
      <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-tr from-accent-cyan/5 via-transparent to-accent-purple/5 pointer-events-none" />
      
      <div className="glass-card max-w-[420px] w-full border border-brand-border p-10 flex flex-col gap-6 z-10 shadow-glow-blue/15">
        {/* Brand Logo */}
        <div className="flex flex-col items-center gap-2 select-none">
          <div className="p-3 bg-accent-blue/10 border border-accent-blue/30 rounded-2xl text-accent-blue shadow-glow-blue/20">
            <Scale className="w-8 h-8" />
          </div>
          <h1 className="font-heading text-2xl font-extrabold tracking-tight bg-gradient-to-r from-accent-cyan to-accent-purple bg-clip-text text-transparent mt-2">
            LegalDocAI Portal
          </h1>
          <p className="text-xs text-gray-500 font-medium">SaaS Multi-User Intelligence Engine</p>
        </div>

        {error && (
          <div className="text-xs text-rose-400 font-semibold border border-rose-500/20 bg-rose-500/5 rounded-xl p-3 flex items-center gap-2 select-none">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleLogin} className="flex flex-col gap-4">
          {/* Email input */}
          <div className="flex flex-col gap-1.5">
            <label className="text-[10px] font-bold uppercase tracking-wider text-gray-500">Email Address</label>
            <div className="flex items-center bg-brand-secondary border border-brand-border rounded-xl px-4 py-3 gap-3 focus-within:border-accent-blue/40 transition-all duration-300">
              <Mail className="w-4 h-4 text-gray-500" />
              <input 
                type="email" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@firm.com" 
                className="bg-transparent border-none outline-none text-sm text-white flex-1 font-sans"
                required
                disabled={loading}
              />
            </div>
          </div>

          {/* Password input */}
          <div className="flex flex-col gap-1.5">
            <label className="text-[10px] font-bold uppercase tracking-wider text-gray-500">Password</label>
            <div className="flex items-center bg-brand-secondary border border-brand-border rounded-xl px-4 py-3 gap-3 focus-within:border-accent-blue/40 transition-all duration-300">
              <Lock className="w-4 h-4 text-gray-500" />
              <input 
                type="password" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••" 
                className="bg-transparent border-none outline-none text-sm text-white flex-1 font-sans"
                required
                disabled={loading}
              />
            </div>
          </div>

          {/* Submit */}
          <button 
            type="submit" 
            disabled={loading || !email.trim() || !password.trim()}
            className="btn-gradient w-full py-3 rounded-xl flex items-center justify-center gap-2 font-heading text-sm font-semibold tracking-wider uppercase mt-4 select-none disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Authenticating...</span>
              </>
            ) : (
              <span>Sign In</span>
            )}
          </button>
        </form>

        <div className="text-center text-xs text-gray-500 select-none">
          Don't have an account?{' '}
          <Link to="/register" className="text-accent-blue hover:underline font-semibold">
            Create Account
          </Link>
        </div>
      </div>
    </div>
  );
};
