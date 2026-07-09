import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Scale, Lock, Mail, User, ShieldCheck, Loader2, AlertTriangle } from 'lucide-react';
import { apiService } from '../services/api';

export const Register: React.FC = () => {
  const navigate = useNavigate();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('USER');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !email.trim() || !password.trim()) return;

    setLoading(true);
    setError(null);

    try {
      await apiService.register({ name, email, password, role });
      setSuccess(true);
      setTimeout(() => {
        navigate('/login');
      }, 2000);
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Registration failed. Email address may already be in use.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen w-screen justify-center items-center bg-brand-dark p-6 overflow-hidden relative">
      <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-tr from-accent-cyan/5 via-transparent to-accent-purple/5 pointer-events-none" />
      
      <div className="glass-card max-w-[420px] w-full border border-brand-border p-10 flex flex-col gap-6 z-10 shadow-glow-purple/15">
        {/* Brand Logo */}
        <div className="flex flex-col items-center gap-2 select-none">
          <div className="p-3 bg-accent-purple/10 border border-accent-purple/30 rounded-2xl text-accent-purple shadow-glow-purple/20">
            <Scale className="w-8 h-8" />
          </div>
          <h1 className="font-heading text-2xl font-extrabold tracking-tight bg-gradient-to-r from-accent-cyan to-accent-purple bg-clip-text text-transparent mt-2">
            Create Account
          </h1>
          <p className="text-xs text-gray-500 font-medium">SaaS Multi-User Intelligence Engine</p>
        </div>

        {error && (
          <div className="text-xs text-rose-400 font-semibold border border-rose-500/20 bg-rose-500/5 rounded-xl p-3 flex items-center gap-2 select-none">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="text-xs text-emerald-400 font-semibold border border-emerald-500/20 bg-emerald-500/5 rounded-xl p-3 text-center select-none animate-pulse-subtle">
            Account created successfully! Redirecting to login...
          </div>
        )}

        {!success && (
          <form onSubmit={handleRegister} className="flex flex-col gap-4">
            {/* Name Input */}
            <div className="flex flex-col gap-1.5">
              <label className="text-[10px] font-bold uppercase tracking-wider text-gray-500">Full Name</label>
              <div className="flex items-center bg-brand-secondary border border-brand-border rounded-xl px-4 py-3 gap-3 focus-within:border-accent-purple/40 transition-all duration-300">
                <User className="w-4 h-4 text-gray-500" />
                <input 
                  type="text" 
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Attorney John Doe" 
                  className="bg-transparent border-none outline-none text-sm text-white flex-1 font-sans"
                  required
                  disabled={loading}
                />
              </div>
            </div>

            {/* Email Input */}
            <div className="flex flex-col gap-1.5">
              <label className="text-[10px] font-bold uppercase tracking-wider text-gray-500">Email Address</label>
              <div className="flex items-center bg-brand-secondary border border-brand-border rounded-xl px-4 py-3 gap-3 focus-within:border-accent-purple/40 transition-all duration-300">
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

            {/* Password Input */}
            <div className="flex flex-col gap-1.5">
              <label className="text-[10px] font-bold uppercase tracking-wider text-gray-500">Password</label>
              <div className="flex items-center bg-brand-secondary border border-brand-border rounded-xl px-4 py-3 gap-3 focus-within:border-accent-purple/40 transition-all duration-300">
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

            {/* Role Selector dropdown */}
            <div className="flex flex-col gap-1.5">
              <label className="text-[10px] font-bold uppercase tracking-wider text-gray-500">Workspace Access Profile</label>
              <div className="flex items-center bg-brand-secondary border border-brand-border rounded-xl px-4 py-3 gap-3 focus-within:border-accent-purple/40 transition-all duration-300">
                <ShieldCheck className="w-4 h-4 text-gray-500" />
                <select 
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="bg-transparent border-none outline-none text-sm text-gray-300 flex-grow font-sans cursor-pointer focus:text-white"
                  required
                  disabled={loading}
                >
                  <option value="USER" className="bg-brand-secondary text-gray-200">USER (Client Matter / Research Account)</option>
                  <option value="ADMIN" className="bg-brand-secondary text-gray-200">ADMIN (System Administrator)</option>
                </select>
              </div>
            </div>

            {/* Submit */}
            <button 
              type="submit" 
              disabled={loading || !name.trim() || !email.trim() || !password.trim()}
              className="btn-gradient w-full py-3 rounded-xl flex items-center justify-center gap-2 font-heading text-sm font-semibold tracking-wider uppercase mt-4 select-none disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Registering...</span>
                </>
              ) : (
                <span>Register</span>
              )}
            </button>
          </form>
        )}

        <div className="text-center text-xs text-gray-500 select-none">
          Already have an account?{' '}
          <Link to="/login" className="text-accent-purple hover:underline font-semibold">
            Sign In
          </Link>
        </div>
      </div>
    </div>
  );
};
