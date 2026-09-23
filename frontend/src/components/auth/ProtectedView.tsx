import React, { useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Navigate } from 'react-router-dom';
import { ShieldAlert, Loader2 } from 'lucide-react';
import { UserRole } from '../../types/auth';

interface ProtectedViewProps {
  children: React.ReactNode;
  requiredRole?: UserRole;
  fallbackTitle?: string;
  fallbackDescription?: string;
}

export const ProtectedView: React.FC<ProtectedViewProps> = ({
  children,
  requiredRole,
}) => {
  const { isAuthenticated, loading, openAuthModal, user } = useAuth();

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      openAuthModal(undefined, 'Authentication required to access verification tools.');
    }
  }, [loading, isAuthenticated, openAuthModal]);

  if (loading) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center space-y-4">
        <Loader2 className="w-10 h-10 animate-spin text-emerald-400" />
        <div className="text-center space-y-1">
          <p className="text-sm font-mono text-emerald-400">VERIFYING AUTHENTICATED SESSION...</p>
          <p className="text-xs text-slate-500">Validating cryptographic credentials</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  if (requiredRole && user?.role !== requiredRole) {
    // If admin is required and user is not admin
    if (requiredRole === 'admin' && user?.role !== 'admin') {
      return (
        <div className="max-w-md mx-auto my-16 glass-card rounded-2xl p-8 border border-rose-800/60 text-center space-y-4">
          <div className="p-3 bg-rose-500/20 text-rose-400 rounded-2xl w-fit mx-auto border border-rose-500/30">
            <ShieldAlert className="w-8 h-8" />
          </div>
          <h3 className="text-lg font-bold text-slate-100">Access Denied</h3>
          <p className="text-xs text-slate-400">
            Your account role (<span className="font-mono text-emerald-400">{user?.role}</span>) does not have permission to view administrative controls.
          </p>
        </div>
      );
    }
  }

  return <>{children}</>;
};
