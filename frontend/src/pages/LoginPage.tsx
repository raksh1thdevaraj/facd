import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { authService } from '../services/authService';
import { ShieldCheck, LogIn, UserPlus, AlertCircle, Loader2, MailCheck, ArrowRight, KeyRound, Mail, User, Shield } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const [isRegister, setIsRegister] = useState<boolean>(false);
  const [isForgot, setIsForgot] = useState<boolean>(false);
  const [identifier, setIdentifier] = useState<string>('');
  const [username, setUsername] = useState<string>('');
  const [email, setEmail] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [confirmPassword, setConfirmPassword] = useState<string>('');
  const [forgotEmail, setForgotEmail] = useState<string>('');

  const [submitting, setSubmitting] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successNotice, setSuccessNotice] = useState<string | null>(null);
  const [registeredEmail, setRegisteredEmail] = useState<string | null>(null);

  const { login, register } = useAuth();
  const navigate = useNavigate();

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

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessNotice(null);
    setSubmitting(true);

    try {
      if (!identifier.trim() || !password) {
        throw new Error('Please enter your username or email and password.');
      }

      const user = await login({
        email: identifier.includes('@') ? identifier.trim() : undefined,
        username: !identifier.includes('@') ? identifier.trim() : undefined,
        password,
      });

      if (user.role === 'admin') {
        navigate('/admin');
      } else {
        navigate('/verify');
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
      const cleanUsername = username.trim();
      const cleanEmail = email.trim();

      if (!cleanUsername) throw new Error('Username is required.');
      if (!cleanEmail) throw new Error('Email address is required.');
      if (password.length < 8) throw new Error('Password must be at least 8 characters long.');
      if (password !== confirmPassword) throw new Error('Passwords do not match.');

      const res = await register({
        username: cleanUsername,
        email: cleanEmail,
        password,
        role: 'user',
      });

      setRegisteredEmail(res.email);
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
    <div className="max-w-md mx-auto my-8 space-y-6">
      <div className="text-center space-y-2">
        <div className="p-3 bg-emerald-600/20 text-emerald-400 rounded-2xl w-fit mx-auto border border-emerald-500/30">
          <ShieldCheck className="w-8 h-8" />
        </div>
        <h2 className="text-2xl font-extrabold text-slate-100">
          {registeredEmail
            ? 'Verify Your Email'
            : isForgot
            ? 'Reset Password'
            : isRegister
            ? 'Create Forensic Verifier Account'
            : 'Sign in to CertiShield'}
        </h2>
        <p className="text-xs text-slate-400">
          Access high-throughput verification pipelines and cryptographic auditing
        </p>
      </div>

      <div className="glass-card rounded-2xl p-6 sm:p-8 border border-slate-800 shadow-2xl space-y-6">
        {/* Toggle Mode (hidden if verification sent or forgot password) */}
        {!registeredEmail && !isForgot && (
          <div className="flex rounded-xl bg-slate-900/80 p-1 border border-slate-800 text-xs font-semibold">
            <button
              type="button"
              onClick={() => {
                setIsRegister(false);
                setErrorMessage(null);
                setSuccessNotice(null);
              }}
              className={`flex-1 py-2 rounded-lg transition-colors cursor-pointer ${
                !isRegister
                  ? 'bg-slate-800 text-slate-100 shadow'
                  : 'text-slate-400 hover:text-slate-200'
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
                  ? 'bg-slate-800 text-slate-100 shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Register
            </button>
          </div>
        )}

        {errorMessage && (
          <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-800/60 text-xs text-rose-300 flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {successNotice && (
          <div className="p-3 rounded-xl bg-emerald-950/40 border border-emerald-800/60 text-xs text-emerald-300 flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{successNotice}</span>
          </div>
        )}

        {/* Verification Sent Screen */}
        {registeredEmail ? (
          <div className="text-center py-4 space-y-4">
            <div className="w-16 h-16 rounded-3xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center mx-auto text-emerald-400 shadow-xl">
              <MailCheck className="w-8 h-8" />
            </div>
            <div className="space-y-1.5">
              <h4 className="text-base font-bold text-white">Verification Link Sent</h4>
              <p className="text-xs text-slate-300">We've sent a verification email to:</p>
              <p className="text-xs font-mono font-bold text-emerald-400 bg-slate-900 py-1.5 px-3 rounded-lg border border-slate-800 inline-block">
                {registeredEmail}
              </p>
              <p className="text-[11px] text-slate-400 pt-2">
                Please click the link in your email to verify your address before signing in.
              </p>
            </div>
            <button
              type="button"
              onClick={() => {
                setIdentifier(registeredEmail);
                setRegisteredEmail(null);
                setIsRegister(false);
              }}
              className="w-full py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-lg flex items-center justify-center space-x-2 cursor-pointer"
            >
              <span>Proceed to Sign In</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        ) : isForgot ? (
          /* Forgot Password Screen */
          <form onSubmit={handleForgot} className="space-y-4 text-xs sm:text-sm">
            <div>
              <label className="block text-slate-300 font-medium mb-1.5">Email Address</label>
              <input
                type="email"
                required
                value={forgotEmail}
                onChange={(e) => setForgotEmail(e.target.value)}
                placeholder="name@institution.edu"
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 focus:outline-none focus:border-emerald-500 placeholder-slate-600"
              />
            </div>
            <button
              type="submit"
              disabled={submitting}
              className="w-full inline-flex items-center justify-center space-x-2 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-sm shadow-lg disabled:opacity-50 cursor-pointer"
            >
              {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <span>Send Password Reset Link</span>}
            </button>
            <div className="text-center pt-2">
              <button
                type="button"
                onClick={() => setIsForgot(false)}
                className="text-xs text-slate-400 hover:text-white cursor-pointer"
              >
                &larr; Back to Sign In
              </button>
            </div>
          </form>
        ) : !isRegister ? (
          /* Sign In Form */
          <form onSubmit={handleLogin} className="space-y-4 text-xs sm:text-sm">
            <div>
              <label className="block text-slate-300 font-medium mb-1.5">Username or Email</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
                <input
                  type="text"
                  required
                  value={identifier}
                  onChange={(e) => setIdentifier(e.target.value)}
                  placeholder="e.g. user@institution.edu or username"
                  className="w-full pl-10 pr-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 focus:outline-none focus:border-emerald-500 placeholder-slate-600"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-slate-300 font-medium">Password</label>
                <button
                  type="button"
                  onClick={() => setIsForgot(true)}
                  className="text-[11px] text-emerald-400 hover:text-emerald-300 cursor-pointer"
                >
                  Forgot Password?
                </button>
              </div>
              <div className="relative">
                <KeyRound className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-10 pr-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 focus:outline-none focus:border-emerald-500 placeholder-slate-600"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full inline-flex items-center justify-center space-x-2 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-sm shadow-lg disabled:opacity-50 cursor-pointer"
            >
              {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <LogIn className="w-4 h-4" />}
              <span>{submitting ? 'Please wait...' : 'Sign In'}</span>
            </button>
          </form>
        ) : (
          /* Registration Form */
          <form onSubmit={handleRegister} className="space-y-4 text-xs sm:text-sm">
            <div>
              <label className="block text-slate-300 font-medium mb-1.5">Username</label>
              <div className="relative">
                <User className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
                <input
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="e.g. jdoe_verifier"
                  className="w-full pl-10 pr-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 focus:outline-none focus:border-emerald-500 placeholder-slate-600"
                />
              </div>
            </div>

            <div>
              <label className="block text-slate-300 font-medium mb-1.5">Email Address</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@institution.edu"
                  className="w-full pl-10 pr-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 focus:outline-none focus:border-emerald-500 placeholder-slate-600"
                />
              </div>
            </div>

            <div>
              <label className="block text-slate-300 font-medium mb-1.5">Password</label>
              <div className="relative">
                <KeyRound className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-10 pr-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 focus:outline-none focus:border-emerald-500 placeholder-slate-600"
                />
              </div>
              {password && (
                <div className="mt-2 space-y-1">
                  <div className="flex items-center justify-between text-[10px]">
                    <span className="text-slate-400">Strength:</span>
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

            <div>
              <label className="block text-slate-300 font-medium mb-1.5">Confirm Password</label>
              <div className="relative">
                <Shield className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
                <input
                  type="password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  className={`w-full pl-10 pr-3.5 py-2.5 rounded-xl bg-slate-900 border text-slate-100 focus:outline-none placeholder-slate-600 ${
                    confirmPassword && password !== confirmPassword
                      ? 'border-rose-500'
                      : 'border-slate-800 focus:border-emerald-500'
                  }`}
                />
              </div>
              {confirmPassword && password !== confirmPassword && (
                <p className="text-[10px] text-rose-400 mt-1">Passwords do not match.</p>
              )}
            </div>

            <button
              type="submit"
              disabled={submitting || (confirmPassword !== '' && password !== confirmPassword)}
              className="w-full inline-flex items-center justify-center space-x-2 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-sm shadow-lg disabled:opacity-50 cursor-pointer"
            >
              {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <UserPlus className="w-4 h-4" />}
              <span>{submitting ? 'Please wait...' : 'Create Account'}</span>
            </button>
          </form>
        )}
      </div>
    </div>
  );
};
