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
  const { isAuthenticated, loading, openAuthModal, userProfile, isPending, isAdmin } = useAuth();

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      openAuthModal(undefined, 'Authentication required to access verification tools.');
    }
  }, [loading, isAuthenticated, openAuthModal]);

  if (loading) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center space-y-4 bg-[#f8fafc]">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-700" />
        <div className="text-center space-y-1">
          <p className="text-xs font-mono text-indigo-900 tracking-wider">VERIFYING AUTHENTICATED SESSION...</p>
          <p className="text-xs text-slate-500">Validating institutional credentials</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated || !userProfile) {
    return <Navigate to="/login" replace />;
  }

  // Pending approval gating
  if (isPending || userProfile.status === 'pending') {
    return <Navigate to="/pending-approval" replace />;
  }

  // Role validation
  if (requiredRole === 'admin' && !isAdmin) {
    return (
      <div className="max-w-md mx-auto my-16 bg-white rounded-2xl p-8 border border-rose-200 shadow-sm text-center space-y-4">
        <div className="p-3 bg-rose-50 text-rose-600 rounded-2xl w-fit mx-auto border border-rose-100">
          <ShieldAlert className="w-8 h-8" />
        </div>
        <h3 className="text-lg font-bold text-slate-900">Access Denied</h3>
        <p className="text-xs text-slate-600">
          Your account role (<span className="font-mono text-indigo-700">{userProfile?.role}</span>) does not have permission to view administrative controls.
        </p>
      </div>
    );
  }

  return <>{children}</>;
};

export default ProtectedView;
