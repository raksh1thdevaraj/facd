import React from 'react';
import { Navigate, useLocation, Outlet } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Loader2 } from 'lucide-react';

interface AdminRouteProps {
  children?: React.ReactNode;
}

export const AdminRoute: React.FC<AdminRouteProps> = ({ children }) => {
  const { isAuthenticated, userProfile, isAdmin, isApproved, isPending, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center space-y-3 bg-[#f8fafc]">
        <Loader2 className="w-8 h-8 text-indigo-700 animate-spin" />
        <span className="text-xs text-slate-500 font-mono tracking-wider">
          Verifying administrative authorization...
        </span>
      </div>
    );
  }

  // 1. Not Authenticated
  if (!isAuthenticated || !userProfile) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // 2. Pending Approval
  if (isPending || userProfile.status === 'pending') {
    return <Navigate to="/pending-approval" replace />;
  }

  // 3. Authenticated and Approved, but Not Admin -> redirect to /workspace
  if (!isAdmin || userProfile.role !== 'admin' || !isApproved) {
    return <Navigate to="/workspace" replace />;
  }

  // 4. Admin and Approved
  return children ? <>{children}</> : <Outlet />;
};

export default AdminRoute;
