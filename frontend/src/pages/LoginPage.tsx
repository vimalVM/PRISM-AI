import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock, User, ArrowRight, ShieldCheck, AlertCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState<string>('engineer');
  const [password, setPassword] = useState<string>('Engineer123!');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(username, password);
      navigate('/');
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Check credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-screen bg-surface flex items-center justify-center p-4 relative overflow-hidden select-none">
      {/* Background Ambient Glows */}
      <div className="pointer-events-none absolute -top-40 -left-40 w-[500px] h-[500px] bg-primary-container/10 rounded-full blur-3xl" />
      <div className="pointer-events-none absolute -bottom-40 -right-40 w-[500px] h-[500px] bg-secondary-container/15 rounded-full blur-3xl" />

      {/* Login Card */}
      <div className="relative z-10 w-full max-w-md bg-surface-container-lowest rounded-2xl p-8 border border-outline-variant/30 shadow-2xl space-y-6">
        {/* Top Branding */}
        <div className="text-center space-y-2">
          <div className="w-12 h-12 mx-auto rounded-xl bg-surface-container border border-outline-variant/30 p-2 flex items-center justify-center shadow-md">
            <img src="/emblem.svg" alt="PRISM-AI Sovereign Emblem" className="w-8 h-8 object-contain" />
          </div>
          <h1 className="font-headline text-2xl font-bold tracking-tight text-on-surface">
            PRISM-AI Enclave
          </h1>
          <p className="font-mono text-xs text-on-surface-variant">
            Sovereign Industrial AI Workbench · Air-Gapped Session
          </p>
        </div>

        {error && (
          <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 font-mono text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1">
            <label className="font-mono text-[10px] uppercase text-outline font-semibold">
              Operator Username
            </label>
            <div className="relative">
              <User className="w-4 h-4 text-on-surface-variant absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="e.g. engineer, reviewer, admin"
                className="w-full bg-surface-container text-on-surface font-mono text-xs pl-9 pr-3 py-2.5 rounded-lg border border-outline-variant/30 focus:outline-none focus:border-primary-container"
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="font-mono text-[10px] uppercase text-outline font-semibold">
              Security Credential
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-on-surface-variant absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full bg-surface-container text-on-surface font-mono text-xs pl-9 pr-3 py-2.5 rounded-lg border border-outline-variant/30 focus:outline-none focus:border-primary-container"
              />
            </div>
          </div>

          {/* Quick Demo Credentials Pill Bar */}
          <div className="pt-1">
            <span className="font-mono text-[10px] text-outline block mb-1">Quick Select Demo Account:</span>
            <div className="flex flex-wrap gap-1 font-mono text-[10px]">
              <button
                type="button"
                onClick={() => { setUsername('engineer'); setPassword('Engineer123!'); }}
                className="px-2 py-0.5 rounded bg-surface-container text-on-surface-variant hover:text-primary transition-colors border border-outline-variant/20"
              >
                engineer
              </button>
              <button
                type="button"
                onClick={() => { setUsername('reviewer'); setPassword('Reviewer123!'); }}
                className="px-2 py-0.5 rounded bg-surface-container text-on-surface-variant hover:text-amber-400 transition-colors border border-outline-variant/20"
              >
                reviewer
              </button>
              <button
                type="button"
                onClick={() => { setUsername('admin'); setPassword('Admin123!'); }}
                className="px-2 py-0.5 rounded bg-surface-container text-on-surface-variant hover:text-tertiary transition-colors border border-outline-variant/20"
              >
                admin
              </button>
              <button
                type="button"
                onClick={() => { setUsername('auditor'); setPassword('Auditor123!'); }}
                className="px-2 py-0.5 rounded bg-surface-container text-on-surface-variant hover:text-secondary transition-colors border border-outline-variant/20"
              >
                auditor
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-2 py-2.5 rounded-lg bg-primary-container text-surface font-mono text-xs font-bold hover:shadow-cyan-glow transition-all flex items-center justify-center gap-2 disabled:opacity-50"
          >
            <span>{loading ? 'Authenticating...' : 'Authenticate Enclave Session'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        <div className="pt-2 border-t border-outline-variant/20 text-center font-mono text-[10px] text-tertiary flex items-center justify-center gap-1.5">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Local Enclave · Zero Telemetry · Argon2id Authenticated</span>
        </div>
      </div>
    </div>
  );
};
