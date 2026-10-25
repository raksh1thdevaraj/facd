import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { authService } from '../services/authService';
import {
  ShieldCheck,
  LogIn,
  UserPlus,
  Loader2,
  KeyRound,
  Mail,
  User,
  Shield,
  ShieldAlert,
} from 'lucide-react';

export const LoginPage: React.FC = () => {
  const [isRegister, setIsRegister] = useState<boolean>(false);
  const [isForgot, setIsForgot] = useState<boolean>(false);
  const [identifier, setIdentifier] = useState<string>('');
  const [displayName, setDisplayName] = useState<string>('');
  const [email, setEmail] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [confirmPassword, setConfirmPassword] = useState<string>('');
  const [forgotEmail, setForgotEmail] = useState<string>('');

  const [submitting, setSubmitting] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successNotice, setSuccessNotice] = useState<string | null>(null);

  const { login, register, isAuthenticated, userProfile } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // If already authenticated and approved/admin, redirect appropriately
  useEffect(() => {
    if (isAuthenticated && userProfile) {
      if (userProfile.status === 'pending') {
        navigate('/pending-approval', { replace: true });
      } else if (userProfile.role === 'admin') {
        navigate('/admin', { replace: true });
      } else if (userProfile.status === 'approved') {
        navigate('/', { replace: true });
      }
    }
  }, [isAuthenticated, userProfile, navigate]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessNotice(null);
    setSubmitting(true);

    try {
      if (!identifier.trim() || !password) {
        throw new Error('Please enter your email or username and password.');
      }

      const profile = await login({
        email: identifier.includes('@') ? identifier.trim() : undefined,
        username: !identifier.includes('@') ? identifier.trim() : undefined,
        password,
      });

      if (profile.status === 'rejected') {
        setErrorMessage('Account registration request declined by administrator.');
        return;
      }

      if (profile.status === 'pending') {
        navigate('/pending-approval', { replace: true });
        return;
      }

      if (profile.role === 'admin') {
        navigate('/admin', { replace: true });
      } else {
        const from = (location.state as any)?.from?.pathname || '/';
        navigate(from, { replace: true });
      }
    } catch (err: unknown) {
      setErrorMessage(
        err instanceof Error ? err.message : 'Invalid credentials. Please verify your details.'
      );
    } finally {
      setSubmitting(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessNotice(null);
    setSubmitting(true);

    try {
      const cleanName = displayName.trim();
      const cleanEmail = email.trim();

      if (!cleanName) throw new Error('Full Name / Display Name is required.');
      if (!cleanEmail) throw new Error('Email address is required.');
      if (password.length < 8) throw new Error('Password must be at least 8 characters long.');
      if (password !== confirmPassword) throw new Error('Passwords do not match.');

      const res = await register({
        displayName: cleanName,
        email: cleanEmail,
        password,
      });

      if (res.userProfile.role === 'admin' && res.userProfile.status === 'approved') {
        navigate('/admin', { replace: true });
      } else {
        navigate('/pending-approval', { replace: true });
      }
    } catch (err: unknown) {
      setErrorMessage(
        err instanceof Error ? err.message : 'Registration failed. Please check your details.'
      );
    } finally {
      setSubmitting(false);
    }
  };

  const handleForgot = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessNotice(null);
    setSubmitting(true);

    try {
      if (!forgotEmail.trim()) throw new Error('Please enter your email address.');
      await authService.resetPassword(forgotEmail.trim());
      setSuccessNotice(`Password reset instructions sent to ${forgotEmail}. Please check your inbox.`);
    } catch (err: unknown) {
      setErrorMessage(
        err instanceof Error ? err.message : 'Failed to send password reset email.'
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center p-4 bg-[#f8fafc]">
      <div className="max-w-md w-full space-y-6">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="w-14 h-14 rounded-2xl bg-indigo-50 text-indigo-700 border border-indigo-200/80 flex items-center justify-center mx-auto shadow-sm">
            <ShieldCheck className="w-7 h-7" />
          </div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            Institutional Verification Console
          </h1>
          <p className="text-xs text-slate-500">
            Cryptographic Marks Card Authentication & Forensic Ledger
          </p>
        </div>

        {/* Main Card */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8 space-y-6">
          {/* Sign In / Register Tabs */}
          {!isForgot && (
            <div className="flex rounded-xl bg-slate-100 p-1 text-xs font-semibold">
              <button
                type="button"
                onClick={() => {
                  setIsRegister(false);
                  setErrorMessage(null);
                  setSuccessNotice(null);
                }}
                className={`flex-1 py-2 rounded-lg transition-colors cursor-pointer ${
                  !isRegister
                    ? 'bg-white text-slate-900 shadow-sm'
                    : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                Sign In
              </button>
              <button
                type="button"
                onClick={() => {
                  setIsRegister(true);
                  setErrorMessage(null);
                  setSuccessNotice(null);
                }}
                className={`flex-1 py-2 rounded-lg transition-colors cursor-pointer ${
                  isRegister
                    ? 'bg-white text-slate-900 shadow-sm'
                    : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                Register
              </button>
            </div>
          )}

          {/* Error Message */}
          {errorMessage && (
            <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-start space-x-2.5">
              <ShieldAlert className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <span className="leading-relaxed font-medium">{errorMessage}</span>
            </div>
          )}

          {/* Success Message */}
          {successNotice && (
            <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 flex items-start space-x-2.5">
              <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
              <span className="leading-relaxed font-medium">{successNotice}</span>
            </div>
          )}

          {isForgot ? (
            /* Forgot Password Form */
            <form onSubmit={handleForgot} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-700 font-semibold mb-1.5">Email Address</label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                  <input
                    type="email"
                    required
                    value={forgotEmail}
                    onChange={(e) => setForgotEmail(e.target.value)}
                    placeholder="name@institution.edu"
                    className="w-full pl-10 pr-3.5 py-2.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 focus:outline-none focus:bg-white focus:border-indigo-600 text-xs"
                  />
                </div>
              </div>
              <button
                type="submit"
                disabled={submitting}
                className="w-full inline-flex items-center justify-center space-x-2 py-2.5 rounded-xl bg-indigo-700 hover:bg-indigo-800 text-white font-semibold text-xs shadow-sm disabled:opacity-50 cursor-pointer"
              >
                {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <span>Send Reset Link</span>}
              </button>
              <div className="text-center pt-2">
                <button
                  type="button"
                  onClick={() => setIsForgot(false)}
                  className="text-xs text-slate-500 hover:text-slate-800 cursor-pointer"
                >
                  &larr; Back to Sign In
                </button>
              </div>
            </form>
          ) : !isRegister ? (
            /* Sign In Form */
            <form onSubmit={handleLogin} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-700 font-semibold mb-1.5">
                  Email Address or Username
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                  <input
                    type="text"
                    required
                    value={identifier}
                    onChange={(e) => setIdentifier(e.target.value)}
                    placeholder="e.g. admin@facd.edu or user@vtu.ac.in"
                    className="w-full pl-10 pr-3.5 py-2.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 focus:outline-none focus:bg-white focus:border-indigo-600 text-xs"
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="block text-slate-700 font-semibold">Password</label>
                  <button
                    type="button"
                    onClick={() => setIsForgot(true)}
                    className="text-[11px] text-indigo-600 hover:text-indigo-700 font-medium cursor-pointer"
                  >
                    Forgot Password?
                  </button>
                </div>
                <div className="relative">
                  <KeyRound className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full pl-10 pr-3.5 py-2.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 focus:outline-none focus:bg-white focus:border-indigo-600 text-xs"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="w-full inline-flex items-center justify-center space-x-2 py-2.5 rounded-xl bg-indigo-700 hover:bg-indigo-800 text-white font-semibold text-xs shadow-sm disabled:opacity-50 cursor-pointer transition-colors"
              >
                {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <LogIn className="w-4 h-4" />}
                <span>{submitting ? 'Authenticating...' : 'Sign In'}</span>
              </button>
            </form>
          ) : (
            /* Register Form */
            <form onSubmit={handleRegister} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-700 font-semibold mb-1.5">Candidate Full Name</label>
                <div className="relative">
                  <User className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                  <input
                    type="text"
                    required
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    placeholder="e.g. Dr. Rajesh Kumar"
                    className="w-full pl-10 pr-3.5 py-2.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 focus:outline-none focus:bg-white focus:border-indigo-600 text-xs"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-700 font-semibold mb-1.5">Institutional Email</label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@university.edu"
                    className="w-full pl-10 pr-3.5 py-2.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 focus:outline-none focus:bg-white focus:border-indigo-600 text-xs"
                  />
                </div>
                <p className="text-[10px] text-slate-500 mt-1">
                  Note: Accounts require administrator approval before verification console access.
                </p>
              </div>

              <div>
                <label className="block text-slate-700 font-semibold mb-1.5">Password</label>
                <div className="relative">
                  <KeyRound className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Minimum 8 characters"
                    className="w-full pl-10 pr-3.5 py-2.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 focus:outline-none focus:bg-white focus:border-indigo-600 text-xs"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-700 font-semibold mb-1.5">Confirm Password</label>
                <div className="relative">
                  <Shield className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                  <input
                    type="password"
                    required
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Repeat password"
                    className="w-full pl-10 pr-3.5 py-2.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 focus:outline-none focus:bg-white focus:border-indigo-600 text-xs"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={submitting || (confirmPassword !== '' && password !== confirmPassword)}
                className="w-full inline-flex items-center justify-center space-x-2 py-2.5 rounded-xl bg-indigo-700 hover:bg-indigo-800 text-white font-semibold text-xs shadow-sm disabled:opacity-50 cursor-pointer transition-colors"
              >
                {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <UserPlus className="w-4 h-4" />}
                <span>{submitting ? 'Creating Account...' : 'Submit Registration'}</span>
              </button>
            </form>
          )}

          {/* Quick Notice */}
          <div className="pt-2 text-center text-[11px] text-slate-400 border-t border-slate-100">
            Institutional Forensic Security &bull; VTU Affiliated Validation Engine
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
