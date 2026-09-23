import React, { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { UserRole } from '../../types/auth';
import { ShieldAlert } from 'lucide-react';

interface RoleGuardProps {
  children: ReactNode;
  allowedRoles?: UserRole[];
}

export const RoleGuard: React.FC<RoleGuardProps> = ({
  children,
  allowedRoles = ['admin'],
}) => {
  const { user, isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-[400px] flex items-center justify-center text-slate-400">
        <span className="text-sm">Verifying security credentials...</span>
      </div>
    );
  }

  // If not authenticated, redirect to login with return path
  if (!isAuthenticated || !user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check role authorization (admin has access everywhere)
  const hasAccess =
    user.role === 'admin' ||
    Boolean(allowedRoles && allowedRoles.includes(user.role));

  if (!hasAccess) {
    return (
      <div className="max-w-md mx-auto my-16 glass-card rounded-2xl p-8 border border-rose-800/60 text-center space-y-4">
        <div className="p-3 bg-rose-500/20 text-rose-400 rounded-2xl w-fit mx-auto border border-rose-500/30">
          <ShieldAlert className="w-8 h-8" />
        </div>
        <h3 className="text-lg font-bold text-slate-100">Access Denied</h3>
        <p className="text-xs text-slate-400">
          Your account role (<span className="font-mono text-emerald-400">{user.role}</span>) does not have permission to view administrative controls.
        </p>
      </div>
    );
  }

  return <>{children}</>;
};
