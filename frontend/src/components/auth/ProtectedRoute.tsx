import React from 'react';
import { Navigate, useLocation, Outlet } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Loader2, ShieldX } from 'lucide-react';

interface ProtectedRouteProps {
  children?: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, userProfile, isApproved, isPending, isRejected, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center space-y-3 bg-[#f8fafc]">
        <Loader2 className="w-8 h-8 text-indigo-700 animate-spin" />
        <span className="text-xs text-slate-500 font-mono tracking-wider">
          Verifying security clearance...
        </span>
      </div>
    );
  }

  // 1. Not Authenticated
  if (!isAuthenticated || !userProfile) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // 2. Account Rejected
  if (isRejected || userProfile.status === 'rejected') {
    return (
      <div className="min-h-[70vh] flex items-center justify-center p-4 bg-[#f8fafc]">
        <div className="max-w-md w-full bg-white rounded-2xl p-8 border border-rose-200 shadow-sm text-center space-y-4">
          <div className="w-12 h-12 rounded-full bg-rose-50 text-rose-600 flex items-center justify-center mx-auto border border-rose-100">
            <ShieldX className="w-6 h-6" />
          </div>
          <h2 className="text-xl font-bold text-slate-900">Access Restricted</h2>
          <p className="text-sm text-slate-600 leading-relaxed">
            Account registration request declined by administrator.
          </p>
          <div className="pt-2">
            <a
              href="/login"
              className="inline-flex items-center px-4 py-2 text-xs font-semibold rounded-lg bg-slate-900 text-white hover:bg-slate-800 transition-colors"
            >
              Return to Sign In
            </a>
          </div>
        </div>
      </div>
    );
  }

  // 3. Approval Pending
  if (isPending || userProfile.status === 'pending') {
    return <Navigate to="/pending-approval" replace />;
  }

  // 4. Approved
  if (isApproved || userProfile.status === 'approved') {
    return children ? <>{children}</> : <Outlet />;
  }

  // Fallback redirect to pending approval if unclassified status
  return <Navigate to="/pending-approval" replace />;
};

export default ProtectedRoute;
