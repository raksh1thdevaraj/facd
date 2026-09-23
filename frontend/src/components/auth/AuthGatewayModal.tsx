import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { authService } from '../../services/authService';
import {
  ShieldCheck,
  Lock,
  Mail,
  User,
  KeyRound,
  X,
  AlertCircle,
  Loader2,
  ArrowRight,
  MailCheck,
  CheckCircle2,
  Shield,
} from 'lucide-react';

export const AuthGatewayModal: React.FC = () => {
  const {
    isAuthModalOpen,
    closeAuthModal,
    authModalMessage,
    login,
    register,
  } = useAuth();
  const navigate = useNavigate();

  // Mode states: 'login' | 'register' | 'forgot' | 'verify_sent'
  const [viewMode, setViewMode] = useState<'login' | 'register' | 'forgot' | 'verify_sent'>('login');

  // Form states
  const [identifier, setIdentifier] = useState<string>('');
  const [username, setUsername] = useState<string>('');
  const [email, setEmail] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [confirmPassword, setConfirmPassword] = useState<string>('');
  const [forgotEmail, setForgotEmail] = useState<string>('');

  // Status & feedback
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successNotice, setSuccessNotice] = useState<string | null>(null);
  const [registeredEmail, setRegisteredEmail] = useState<string>('');

  if (!isAuthModalOpen) return null;

  // Password strength calculation
  const getPasswordStrength = (pwd: string): { score: number; label: string; color: string } => {
    if (!pwd) return { score: 0, label: 'Empty', color: 'bg-slate-700' };
    let score = 0;
    if (pwd.length >= 8) score += 1;
    if (/[A-Z]/.test(pwd)) score += 1;
    if (/[0-9]/.test(pwd)) score += 1;
    if (/[^A-Za-z0-9]/.test(pwd)) score += 1;

    switch (score) {
      case 1:
        return { score: 1, label: 'Weak', color: 'bg-rose-500' };
      case 2:
        return { score: 2, label: 'Fair', color: 'bg-amber-500' };
      case 3:
        return { score: 3, label: 'Good', color: 'bg-teal-500' };
      case 4:
        return { score: 4, label: 'Strong', color: 'bg-emerald-500' };
      default:
        return { score: 0, label: 'Weak', color: 'bg-rose-500' };
    }
  };

  const pwdStrength = getPasswordStrength(password);

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessNotice(null);
    setLoading(true);

    try {
      if (!identifier.trim() || !password) {
        throw new Error('Please enter your username or email and password.');
      }

      const loggedInUser = await login({
        email: identifier.includes('@') ? identifier.trim() : undefined,
        username: !identifier.includes('@') ? identifier.trim() : undefined,
        password,
      });

      // Close modal and execute automatic role-based routing
      closeAuthModal();
      if (loggedInUser.role === 'admin') {
        navigate('/admin');
      } else {
        navigate('/verify');
      }
    } catch (err: unknown) {
      setErrorMessage(
        err instanceof Error ? err.message : 'Invalid credentials. Please verify your details.'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessNotice(null);
    setLoading(true);

    try {
      const cleanUsername = username.trim();
      const cleanEmail = email.trim();

      if (!cleanUsername) {
        throw new Error('Username is required.');
      }
      if (!cleanEmail) {
        throw new Error('Email address is required.');
      }
      if (password.length < 8) {
        throw new Error('Password must be at least 8 characters long.');
      }
      if (password !== confirmPassword) {
        throw new Error('Passwords do not match. Please verify your confirm password.');
      }

      const res = await register({
        username: cleanUsername,
        email: cleanEmail,
        password,
        role: 'user', // Defaults strictly to standard user permissions
      });

      setRegisteredEmail(res.email);
      setViewMode('verify_sent');
    } catch (err: unknown) {
      setErrorMessage(
        err instanceof Error ? err.message : 'Registration failed. Please check your inputs.'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleForgotSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessNotice(null);
    setLoading(true);

    try {
      if (!forgotEmail.trim()) {
        throw new Error('Please enter your email address to receive password reset instructions.');
      }
      await authService.resetPassword(forgotEmail.trim());
      setSuccessNotice(`Password reset link sent to ${forgotEmail}. Please check your inbox.`);
    } catch (err: unknown) {
      setErrorMessage(
        err instanceof Error ? err.message : 'Failed to send password reset email.'
      );
    } finally {
      setLoading(false);
    }
  };

  const switchToLogin = (prefillIdentifier?: string) => {
    setViewMode('login');
    setErrorMessage(null);
    setSuccessNotice(null);
    if (prefillIdentifier) {
      setIdentifier(prefillIdentifier);
    }
  };

  const switchToRegister = () => {
    setViewMode('register');
    setErrorMessage(null);
    setSuccessNotice(null);
  };

  const switchToForgot = () => {
    setViewMode('forgot');
    setErrorMessage(null);
    setSuccessNotice(null);
    if (identifier.includes('@')) {
      setForgotEmail(identifier);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 backdrop-blur-md bg-black/80 animate-in fade-in duration-200">
      <div className="relative w-full max-w-md rounded-3xl bg-[#0e1424] border border-slate-700/80 shadow-2xl shadow-emerald-950/40 overflow-hidden">
        {/* Close Button */}
        <button
          onClick={closeAuthModal}
          className="absolute top-4 right-4 p-2 rounded-full text-slate-400 hover:text-white hover:bg-slate-800 transition-colors z-10 cursor-pointer"
          aria-label="Close"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Header */}
        <div className="px-8 pt-8 pb-5 border-b border-slate-800/80 bg-gradient-to-b from-slate-900/70 to-transparent">
          <div className="flex items-center space-x-3 mb-1">
            <div className="p-2.5 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 text-white shadow-lg shadow-emerald-500/25">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-xl font-black text-white tracking-tight font-display">
                CertiShield Security Gateway
              </h3>
              <p className="text-xs text-slate-400">
                {viewMode === 'register'
                  ? 'Create account to access verification tools'
                  : viewMode === 'forgot'
                  ? 'Recover your account credentials'
                  : viewMode === 'verify_sent'
                  ? 'Email verification required'
                  : 'Sign in to access forensic certificate verification'}
              </p>
            </div>
          </div>

          {/* Prompt Message Banner if redirected from guarded route */}
          {authModalMessage && viewMode === 'login' && (
            <div className="mt-3 p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center space-x-2 text-xs text-amber-300">
              <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
              <span className="font-medium">{authModalMessage}</span>
            </div>
          )}
        </div>

        {/* Modal Body */}
        <div className="p-8 space-y-4">
          {/* Error Message Alert */}
          {errorMessage && (
            <div className="p-3.5 rounded-xl bg-rose-950/40 border border-rose-800/60 text-xs text-rose-300 animate-in fade-in space-y-2">
              <div className="flex items-start space-x-2.5">
                <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                <span className="leading-relaxed">{errorMessage}</span>
              </div>
              {errorMessage.includes('Email not verified') && identifier && password && (
                <div className="pt-1 pl-6">
                  <button
                    type="button"
                    onClick={async () => {
                      try {
                        setLoading(true);
                        await authService.resendVerificationEmail(identifier, password);
                        setSuccessNotice(`Verification email resent to ${identifier}. Please check your inbox and spam folder.`);
                        setErrorMessage(null);
                      } catch (err: any) {
                        setErrorMessage(err.message || 'Failed to resend verification email.');
                      } finally {
                        setLoading(false);
                      }
                    }}
                    className="font-bold underline text-emerald-400 hover:text-emerald-300 cursor-pointer text-[11px]"
                  >
                    Click here to resend verification link &rarr;
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Success Notice Alert */}
          {successNotice && (
            <div className="p-3.5 rounded-xl bg-emerald-950/40 border border-emerald-800/60 flex items-start space-x-2.5 text-xs text-emerald-300 animate-in fade-in">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <span className="leading-relaxed">{successNotice}</span>
            </div>
          )}

          {/* ======================= VIEW 1: LOGIN ======================= */}
          {viewMode === 'login' && (
            <form onSubmit={handleLoginSubmit} className="space-y-4">
              <div>
                <label
                  htmlFor="login-identifier"
                  className="block text-xs font-semibold text-slate-300 mb-1.5"
                >
                  Username or Email
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
                  <input
                    id="login-identifier"
                    type="text"
                    required
                    placeholder="e.g. user@institution.edu or username"
                    value={identifier}
                    onChange={(e) => setIdentifier(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-colors"
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label
                    htmlFor="login-password"
                    className="block text-xs font-semibold text-slate-300"
                  >
                    Password
                  </label>
                  <button
                    type="button"
                    onClick={switchToForgot}
                    className="text-[11px] text-emerald-400 hover:text-emerald-300 transition-colors cursor-pointer"
                  >
                    Forgot Password?
                  </button>
                </div>
                <div className="relative">
                  <KeyRound className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
                  <input
                    id="login-password"
                    type="password"
                    required
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-colors"
                  />
                </div>
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-xs shadow-lg shadow-emerald-600/25 flex items-center justify-center space-x-2 transition-all cursor-pointer disabled:opacity-50 hover:scale-[1.01] active:scale-[0.99]"
                >
                  {loading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <>
                      <Lock className="w-4 h-4" />
                      <span>Sign In</span>
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </div>

              <div className="flex items-center justify-center text-xs text-slate-400 pt-3 border-t border-slate-800/80">
                <span>Need an account?</span>
                <button
                  type="button"
                  onClick={switchToRegister}
                  className="ml-1.5 font-semibold text-emerald-400 hover:text-emerald-300 transition-colors cursor-pointer"
                >
                  Register
                </button>
              </div>
            </form>
          )}

          {/* ======================= VIEW 2: REGISTRATION ======================= */}
          {viewMode === 'register' && (
            <form onSubmit={handleRegisterSubmit} className="space-y-3.5">
              {/* Strictly "Username" */}
              <div>
                <label
                  htmlFor="reg-username"
                  className="block text-xs font-semibold text-slate-300 mb-1"
                >
                  Username
                </label>
                <div className="relative">
                  <User className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
                  <input
                    id="reg-username"
                    type="text"
                    required
                    placeholder="e.g. jdoe_verifier"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-colors"
                  />
                </div>
              </div>

              {/* Strictly "Email Address" */}
              <div>
                <label
                  htmlFor="reg-email"
                  className="block text-xs font-semibold text-slate-300 mb-1"
                >
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
                  <input
                    id="reg-email"
                    type="email"
                    required
                    placeholder="name@institution.edu"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-colors"
                  />
                </div>
              </div>

              {/* Password with Strength Indicator */}
              <div>
                <label
                  htmlFor="reg-password"
                  className="block text-xs font-semibold text-slate-300 mb-1"
                >
                  Password
                </label>
                <div className="relative">
                  <KeyRound className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
                  <input
                    id="reg-password"
                    type="password"
                    required
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-colors"
                  />
                </div>

                {/* Strength Meter Bar */}
                {password && (
                  <div className="mt-2 space-y-1">
                    <div className="flex items-center justify-between text-[10px]">
                      <span className="text-slate-400">Password Strength:</span>
                      <span className={`font-bold ${pwdStrength.score >= 3 ? 'text-emerald-400' : pwdStrength.score === 2 ? 'text-amber-400' : 'text-rose-400'}`}>
                        {pwdStrength.label}
                      </span>
                    </div>
                    <div className="grid grid-cols-4 gap-1.5 h-1">
                      {[1, 2, 3, 4].map((step) => (
                        <div
                          key={step}
                          className={`rounded-full transition-colors ${
                            pwdStrength.score >= step ? pwdStrength.color : 'bg-slate-800'
                          }`}
                        />
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Confirm Password */}
              <div>
                <label
                  htmlFor="reg-confirm-password"
                  className="block text-xs font-semibold text-slate-300 mb-1"
                >
                  Confirm Password
                </label>
                <div className="relative">
                  <Shield className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
                  <input
                    id="reg-confirm-password"
                    type="password"
                    required
                    placeholder="••••••••"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className={`w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-900 border text-xs text-white placeholder-slate-500 focus:outline-none transition-colors ${
                      confirmPassword && password !== confirmPassword
                        ? 'border-rose-500 focus:border-rose-400'
                        : 'border-slate-700 focus:border-emerald-500'
                    }`}
                  />
                </div>
                {confirmPassword && password !== confirmPassword && (
                  <p className="text-[10px] text-rose-400 mt-1">Passwords do not match.</p>
                )}
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={loading || (confirmPassword !== '' && password !== confirmPassword)}
                  className="w-full py-3 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-xs shadow-lg shadow-emerald-600/25 flex items-center justify-center space-x-2 transition-all cursor-pointer disabled:opacity-50 hover:scale-[1.01] active:scale-[0.99]"
                >
                  {loading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <>
                      <Lock className="w-4 h-4" />
                      <span>Create Account</span>
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </div>

              <div className="flex items-center justify-center text-xs text-slate-400 pt-3 border-t border-slate-800/80">
                <span>Already have an account?</span>
                <button
                  type="button"
                  onClick={() => switchToLogin()}
                  className="ml-1.5 font-semibold text-emerald-400 hover:text-emerald-300 transition-colors cursor-pointer"
                >
                  Sign In
                </button>
              </div>
            </form>
          )}

          {/* ======================= VIEW 3: VERIFICATION EMAIL SENT ======================= */}
          {viewMode === 'verify_sent' && (
            <div className="text-center py-4 space-y-4 animate-in fade-in">
              <div className="w-16 h-16 rounded-3xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center mx-auto text-emerald-400 shadow-xl shadow-emerald-950/50">
                <MailCheck className="w-8 h-8" />
              </div>
              <div className="space-y-1.5">
                <h4 className="text-base font-bold text-white">Verification Link Sent</h4>
                <p className="text-xs text-slate-300 max-w-sm mx-auto leading-relaxed">
                  We've sent a verification email to:
                </p>
                <p className="text-xs font-mono font-bold text-emerald-400 bg-slate-900 py-1.5 px-3 rounded-lg border border-slate-800 inline-block">
                  {registeredEmail}
                </p>
                <p className="text-[11px] text-slate-400 max-w-xs mx-auto pt-2">
                  Please click the link in your email to activate your account, then sign in below.
                </p>
              </div>

              <button
                type="button"
                onClick={() => switchToLogin(registeredEmail)}
                className="w-full py-3 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-xs shadow-lg shadow-emerald-600/25 flex items-center justify-center space-x-2 transition-all cursor-pointer"
              >
                <span>Proceed to Sign In</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* ======================= VIEW 4: FORGOT PASSWORD ======================= */}
          {viewMode === 'forgot' && (
            <form onSubmit={handleForgotSubmit} className="space-y-4">
              <div>
                <label
                  htmlFor="forgot-email"
                  className="block text-xs font-semibold text-slate-300 mb-1.5"
                >
                  Registered Email Address
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
                  <input
                    id="forgot-email"
                    type="email"
                    required
                    placeholder="name@institution.edu"
                    value={forgotEmail}
                    onChange={(e) => setForgotEmail(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-colors"
                  />
                </div>
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-xs shadow-lg shadow-emerald-600/25 flex items-center justify-center space-x-2 transition-all cursor-pointer disabled:opacity-50"
                >
                  {loading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <>
                      <Mail className="w-4 h-4" />
                      <span>Send Password Reset Link</span>
                    </>
                  )}
                </button>
              </div>

              <div className="text-center pt-2">
                <button
                  type="button"
                  onClick={() => switchToLogin()}
                  className="text-xs text-slate-400 hover:text-white transition-colors cursor-pointer"
                >
                  &larr; Back to Sign In
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};
