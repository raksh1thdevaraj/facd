import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Clock, RefreshCw, LogOut, CheckCircle2, ShieldAlert } from 'lucide-react';

export const PendingApprovalPage: React.FC = () => {
  const { userProfile, refreshProfile, logout, isApproved } = useAuth();
  const [checking, setChecking] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const navigate = useNavigate();

  // If status changes to approved, navigate automatically to the workspace
  useEffect(() => {
    if (isApproved || userProfile?.status === 'approved') {
      navigate('/', { replace: true });
    }
  }, [isApproved, userProfile, navigate]);

  const handleCheckStatus = async () => {
    setChecking(true);
    setStatusMessage(null);
    try {
      const updated = await refreshProfile();
      if (updated?.status === 'approved') {
        setStatusMessage('Your account has been approved! Redirecting...');
        setTimeout(() => {
          navigate('/', { replace: true });
        }, 1200);
      } else if (updated?.status === 'rejected') {
        setStatusMessage('Account registration request declined by administrator.');
      } else {
        setStatusMessage('Status is still pending verification. Please check back shortly.');
      }
    } catch {
      setStatusMessage('Unable to refresh status. Please try again.');
    } finally {
      setChecking(false);
    }
  };

  const handleSignOut = async () => {
    await logout();
    navigate('/login', { replace: true });
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center p-4 bg-[#f8fafc]">
      <div className="max-w-md w-full bg-white rounded-2xl border border-slate-200 shadow-sm p-8 text-center space-y-6">
        {/* Hourglass/Clock Icon */}
        <div className="w-16 h-16 rounded-2xl bg-amber-50 text-amber-600 border border-amber-200/80 flex items-center justify-center mx-auto shadow-sm">
          <Clock className="w-8 h-8 animate-pulse" />
        </div>

        {/* Heading & Body */}
        <div className="space-y-2">
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            Approval Pending
          </h1>
          <p className="text-sm text-slate-600 leading-relaxed">
            Your account has been registered and is awaiting administrator verification. Access will be unlocked once approved.
          </p>
        </div>

        {/* User Reference Card */}
        {userProfile && (
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-100 text-left space-y-1.5 font-mono text-xs">
            <div className="flex justify-between text-slate-500">
              <span>Account:</span>
              <span className="font-semibold text-slate-800">{userProfile.email}</span>
            </div>
            <div className="flex justify-between text-slate-500">
              <span>Status:</span>
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-100 text-amber-800 border border-amber-200">
                Pending Approval
              </span>
            </div>
          </div>
        )}

        {/* Status notification banner */}
        {statusMessage && (
          <div
            className={`p-3 rounded-xl text-xs flex items-center space-x-2 border ${
              statusMessage.includes('approved')
                ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                : statusMessage.includes('declined')
                ? 'bg-rose-50 text-rose-800 border-rose-200'
                : 'bg-slate-100 text-slate-700 border-slate-200'
            }`}
          >
            {statusMessage.includes('approved') ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            ) : statusMessage.includes('declined') ? (
              <ShieldAlert className="w-4 h-4 text-rose-600 shrink-0" />
            ) : (
              <Clock className="w-4 h-4 text-slate-500 shrink-0" />
            )}
            <span className="text-left font-medium">{statusMessage}</span>
          </div>
        )}

        {/* Actions */}
        <div className="flex flex-col sm:flex-row items-center gap-3 pt-2">
          <button
            type="button"
            onClick={handleCheckStatus}
            disabled={checking}
            className="w-full sm:flex-1 py-2.5 px-4 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs transition-colors flex items-center justify-center space-x-2 shadow-sm cursor-pointer disabled:opacity-60"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${checking ? 'animate-spin' : ''}`} />
            <span>{checking ? 'Checking...' : 'Check Status'}</span>
          </button>

          <button
            type="button"
            onClick={handleSignOut}
            className="w-full sm:w-auto py-2.5 px-4 rounded-xl bg-white hover:bg-slate-50 text-slate-700 font-semibold text-xs border border-slate-200 transition-colors flex items-center justify-center space-x-1.5 cursor-pointer"
          >
            <LogOut className="w-3.5 h-3.5 text-slate-500" />
            <span>Sign Out</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default PendingApprovalPage;
