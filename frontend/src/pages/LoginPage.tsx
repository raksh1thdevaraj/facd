import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { authService } from '../services/authService';
import { OrganizationType, isDisposableEmail } from '../types/auth';
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
  Building2,
  Briefcase,
  BadgeCheck,
  Globe,
  Info
} from 'lucide-react';

interface LoginPageProps {
  initialMode?: 'login' | 'register';
}

export const LoginPage: React.FC<LoginPageProps> = ({ initialMode = 'login' }) => {
  const location = useLocation();
  const queryMode = new URLSearchParams(location.search).get('mode');
  const isDirectRegisterPath = location.pathname === '/register' || location.pathname === '/signup';

  const [isRegister, setIsRegister] = useState<boolean>(
    initialMode === 'register' || queryMode === 'register' || isDirectRegisterPath
  );
  const [isForgot, setIsForgot] = useState<boolean>(false);

  // Sign In State
  const [identifier, setIdentifier] = useState<string>('');
  const [password, setPassword] = useState<string>('');

  // Enterprise Onboarding State
  const [fullName, setFullName] = useState<string>('');
  const [workEmail, setWorkEmail] = useState<string>('');
  const [organizationType, setOrganizationType] = useState<OrganizationType>('CORPORATE_HIRING');
  const [organizationName, setOrganizationName] = useState<string>('');
  const [designation, setDesignation] = useState<string>('');
  const [officialIdentifier, setOfficialIdentifier] = useState<string>('');
  const [confirmPassword, setConfirmPassword] = useState<string>('');

  // Forgot Password State
  const [forgotEmail, setForgotEmail] = useState<string>('');

  // UI / Status State
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successNotice, setSuccessNotice] = useState<string | null>(null);
  const [emailWarning, setEmailWarning] = useState<string | null>(null);

  const { login, register, isAuthenticated, userProfile } = useAuth();
  const navigate = useNavigate();

  // Route if already authenticated
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

  // Live disposable email validation
  useEffect(() => {
    if (!workEmail.trim() || !workEmail.includes('@')) {
      setEmailWarning(null);
      return;
    }
    if (isDisposableEmail(workEmail)) {
      setEmailWarning('Disposable temporary email providers are strictly prohibited. Please use your official corporate or university email.');
    } else {
      setEmailWarning(null);
    }
  }, [workEmail]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessNotice(null);
    setSubmitting(true);

    try {
      if (!identifier.trim() || !password) {
        throw new Error('Please enter your corporate or institutional email and password.');
      }

      const profile = await login({
        email: identifier.includes('@') ? identifier.trim() : undefined,
        username: !identifier.includes('@') ? identifier.trim() : undefined,
        password,
      });

      if (profile.status === 'rejected') {
        const reason = profile.approvalMetadata?.rejectionReason;
        setErrorMessage(
          reason
            ? `Account registration request declined: ${reason}`
            : 'Account registration request declined by administrator.'
        );
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
      const cleanFullName = fullName.trim();
      const cleanEmail = workEmail.trim().toLowerCase();
      const cleanOrgName = organizationName.trim();
      const cleanDesignation = designation.trim();
      const cleanIdentifier = officialIdentifier.trim();

      if (!cleanFullName) throw new Error('Full Name is required.');
      if (!cleanEmail) throw new Error('Official Work / Corporate Email is required.');
      if (isDisposableEmail(cleanEmail)) {
        throw new Error('Please use an official corporate or institutional work email. Disposable email providers are not permitted.');
      }
      if (!cleanOrgName) throw new Error('Organization / University Name is required.');
      if (!cleanDesignation) throw new Error('Designation / Role in Company is required.');
      if (!cleanIdentifier) throw new Error('Official Employee ID or Corporate Website URL is required.');
      if (password.length < 8) throw new Error('Password must be at least 8 characters long.');
      if (password !== confirmPassword) throw new Error('Passwords do not match.');

      const res = await register({
        fullName: cleanFullName,
        email: cleanEmail,
        organizationType,
        organizationName: cleanOrgName,
        designation: cleanDesignation,
        officialIdentifier: cleanIdentifier,
        password,
      });

      if (res.userProfile.role === 'admin' && res.userProfile.status === 'approved') {
        navigate('/admin', { replace: true });
      } else {
        navigate('/pending-approval', { replace: true });
      }
    } catch (err: unknown) {
      setErrorMessage(
        err instanceof Error ? err.message : 'Registration failed. Please check your submitted organization credentials.'
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
      <div className={`w-full ${isRegister ? 'max-w-xl' : 'max-w-md'} space-y-6 transition-all duration-200`}>
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="w-14 h-14 rounded-2xl bg-indigo-50 text-indigo-700 border border-indigo-200/80 flex items-center justify-center mx-auto shadow-sm">
            <ShieldCheck className="w-7 h-7" />
          </div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            Institutional Verification Console
          </h1>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            {isRegister
              ? 'Enterprise Organization & Institutional Verifier Onboarding'
              : 'Cryptographic Marks Card Authentication & Forensic Ledger'}
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
                Enterprise Registration
              </button>
            </div>
          )}

          {/* Vetting Context Banner for Registration */}
          {isRegister && !isForgot && (
            <div className="p-3.5 rounded-xl bg-indigo-50/70 border border-indigo-100 text-xs text-indigo-900 flex items-start space-x-2.5">
              <Info className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
              <div className="space-y-0.5">
                <span className="font-semibold block">Institutional Vetting Required</span>
                <span className="text-[11px] text-indigo-700 leading-relaxed block">
                  Public signups are prohibited. Accounts are audited by administrators to verify employer affiliation before credential inspection access is activated.
                </span>
              </div>
            </div>
          )}

          {/* Error Message */}
          {errorMessage && (
            <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-start space-x-2.5">
              <ShieldAlert className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <span className="leading-relaxed font-medium">{errorMessage}</span>
            </div>
          )}

          {/* Disposable Email Warning */}
          {emailWarning && (
            <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-800 flex items-start space-x-2.5">
              <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
              <span className="leading-relaxed font-medium">{emailWarning}</span>
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
                <label className="block text-slate-700 font-semibold mb-1.5">Official Email Address</label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                  <input
                    type="email"
                    required
                    value={forgotEmail}
                    onChange={(e) => setForgotEmail(e.target.value)}
                    placeholder="name@institution.edu or corporate email"
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
                  Corporate or Institutional Email
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                  <input
                    type="text"
                    required
                    value={identifier}
                    onChange={(e) => setIdentifier(e.target.value)}
                    placeholder="e.g. recruiter@company.com or verifier@vtu.ac.in"
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
                <span>{submitting ? 'Authenticating...' : 'Sign In to Console'}</span>
              </button>
            </form>
          ) : (
            /* Enterprise Organization Registration Form */
            <form onSubmit={handleRegister} className="space-y-4 text-xs">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Full Name */}
                <div>
                  <label className="block text-slate-700 font-semibold mb-1.5">
                    Full Name <span className="text-rose-500">*</span>
                  </label>
                  <div className="relative">
                    <User className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                    <input
                      type="text"
                      required
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="e.g. Rajesh Kumar"
                      className="w-full pl-10 pr-3.5 py-2.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 focus:outline-none focus:bg-white focus:border-indigo-600 text-xs"
                    />
                  </div>
                </div>

                {/* Work / Corporate Email */}
                <div>
                  <label className="block text-slate-700 font-semibold mb-1.5">
                    Work / Corporate Email <span className="text-rose-500">*</span>
                  </label>
                  <div className="relative">
                    <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                    <input
                      type="email"
                      required
                      value={workEmail}
                      onChange={(e) => setWorkEmail(e.target.value)}
                      placeholder="e.g. rajesh@wipro.com"
                      className={`w-full pl-10 pr-3.5 py-2.5 rounded-xl bg-slate-50 border text-slate-900 focus:outline-none focus:bg-white text-xs ${
                        emailWarning ? 'border-amber-400 focus:border-amber-500' : 'border-slate-200 focus:border-indigo-600'
                      }`}
                    />
                  </div>
                </div>
              </div>

              {/* Organization Type Dropdown */}
              <div>
                <label className="block text-slate-700 font-semibold mb-1.5">
                  Organization Type <span className="text-rose-500">*</span>
                </label>
                <div className="relative">
                  <Building2 className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                  <select
                    value={organizationType}
                    onChange={(e) => setOrganizationType(e.target.value as OrganizationType)}
                    className="w-full pl-10 pr-3.5 py-2.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 focus:outline-none focus:bg-white focus:border-indigo-600 text-xs font-medium cursor-pointer"
                  >
                    <option value="CORPORATE_HIRING">
                      Corporate / Enterprise Hiring (e.g., TCS, Infosys, Wipro, Startup HR)
                    </option>
                    <option value="ACADEMIC_INSTITUTION">
                      Academic Institution / University (e.g., College Admissions Office, Registrar)
                    </option>
                    <option value="BGV_AGENCY">
                      Background Verification Agency (BGV)
                    </option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Organization Name */}
                <div>
                  <label className="block text-slate-700 font-semibold mb-1.5">
                    Organization Name <span className="text-rose-500">*</span>
                  </label>
                  <div className="relative">
                    <Building2 className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                    <input
                      type="text"
                      required
                      value={organizationName}
                      onChange={(e) => setOrganizationName(e.target.value)}
                      placeholder="e.g. Wipro Technologies / RVCE"
                      className="w-full pl-10 pr-3.5 py-2.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 focus:outline-none focus:bg-white focus:border-indigo-600 text-xs"
                    />
                  </div>
                </div>

                {/* Designation / Role in Company */}
                <div>
                  <label className="block text-slate-700 font-semibold mb-1.5">
                    Designation / Role in Company <span className="text-rose-500">*</span>
                  </label>
                  <div className="relative">
                    <Briefcase className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                    <input
                      type="text"
                      required
                      value={designation}
                      onChange={(e) => setDesignation(e.target.value)}
                      placeholder="e.g. Senior Technical Recruiter"
                      className="w-full pl-10 pr-3.5 py-2.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 focus:outline-none focus:bg-white focus:border-indigo-600 text-xs"
                    />
                  </div>
                </div>
              </div>

              {/* Official Employee ID / Corporate Website URL */}
              <div>
                <label className="block text-slate-700 font-semibold mb-1.5">
                  Official Employee ID or Corporate Website URL <span className="text-rose-500">*</span>
                </label>
                <div className="relative">
                  <BadgeCheck className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                  <input
                    type="text"
                    required
                    value={officialIdentifier}
                    onChange={(e) => setOfficialIdentifier(e.target.value)}
                    placeholder="e.g. EMP-94021 or https://wipro.com"
                    className="w-full pl-10 pr-3.5 py-2.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 focus:outline-none focus:bg-white focus:border-indigo-600 text-xs"
                  />
                </div>
                <p className="text-[10px] text-slate-500 mt-1">
                  Used by system administrators to audit and authenticate your institutional authorization.
                </p>
              </div>

              {/* Passwords */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-slate-700 font-semibold mb-1.5">
                    Password <span className="text-rose-500">*</span>
                  </label>
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
                  <label className="block text-slate-700 font-semibold mb-1.5">
                    Confirm Password <span className="text-rose-500">*</span>
                  </label>
                  <div className="relative">
                    <Shield className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                    <input
                      type="password"
                      required
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="Repeat password"
                      className={`w-full pl-10 pr-3.5 py-2.5 rounded-xl bg-slate-50 border text-slate-900 focus:outline-none focus:bg-white text-xs ${
                        confirmPassword && password !== confirmPassword
                          ? 'border-rose-400'
                          : 'border-slate-200 focus:border-indigo-600'
                      }`}
                    />
                  </div>
                </div>
              </div>

              <button
                type="submit"
                disabled={submitting || (confirmPassword !== '' && password !== confirmPassword) || !!emailWarning}
                className="w-full inline-flex items-center justify-center space-x-2 py-3 rounded-xl bg-indigo-700 hover:bg-indigo-800 text-white font-semibold text-xs shadow-sm disabled:opacity-50 cursor-pointer transition-colors"
              >
                {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <UserPlus className="w-4 h-4" />}
                <span>{submitting ? 'Submitting Credentials for Vetting...' : 'Submit Organization Onboarding Request'}</span>
              </button>
            </form>
          )}

          {/* Quick Notice */}
          <div className="pt-2 text-center text-[11px] text-slate-400 border-t border-slate-100 flex items-center justify-center space-x-1">
            <Globe className="w-3 h-3 text-slate-400" />
            <span>Institutional Forensic Security &bull; VTU Marks Card Verification Ledger</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
