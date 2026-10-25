import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { AdminRoute } from './components/auth/AdminRoute';
import { AuthGatewayModal } from './components/auth/AuthGatewayModal';
import { InspectionConsolePage } from './pages/InspectionConsolePage';

// Lazy loaded auxiliary pages
const ResultsPage = React.lazy(() =>
  import('./pages/ResultsPage').then((m) => ({ default: m.ResultsPage }))
);
const VerifyReportPage = React.lazy(() =>
  import('./pages/VerifyReportPage').then((m) => ({ default: m.VerifyReportPage }))
);
const HistoryPage = React.lazy(() =>
  import('./pages/HistoryPage').then((m) => ({ default: m.HistoryPage }))
);
const LoginPage = React.lazy(() =>
  import('./pages/LoginPage').then((m) => ({ default: m.LoginPage }))
);
const PendingApprovalPage = React.lazy(() =>
  import('./pages/PendingApprovalPage').then((m) => ({ default: m.PendingApprovalPage }))
);
const NotFoundPage = React.lazy(() =>
  import('./pages/NotFoundPage').then((m) => ({ default: m.NotFoundPage }))
);
const AdminDashboardPage = React.lazy(() =>
  import('./pages/admin/AdminDashboardPage').then((m) => ({ default: m.AdminDashboardPage }))
);

const RouteLoadingFallback: React.FC = () => (
  <div className="min-h-[60vh] flex flex-col items-center justify-center space-y-3 bg-[#f8fafc]">
    <Loader2 className="w-8 h-8 text-indigo-700 animate-spin" />
    <span className="text-xs text-slate-500 font-mono tracking-wider">
      Loading institutional forensic module...
    </span>
  </div>
);

const AppContent: React.FC = () => {
  const { isAuthenticated, userProfile } = useAuth();

  return (
    <div className="min-h-screen bg-[#f8fafc] text-slate-900 flex flex-col selection:bg-indigo-500/20 selection:text-indigo-900">
      <React.Suspense fallback={<RouteLoadingFallback />}>
        <Routes>
          {/* Master Institutional Examination & Inspection Console (Protected) */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <InspectionConsolePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/console"
            element={
              <ProtectedRoute>
                <InspectionConsolePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/verify"
            element={
              <ProtectedRoute>
                <InspectionConsolePage />
              </ProtectedRoute>
            }
          />
          <Route path="/workspace" element={<Navigate to="/" replace />} />
          <Route path="/dashboard" element={<Navigate to="/" replace />} />

          {/* Pending Approval Gating View (Public for authenticated pending users) */}
          <Route path="/pending-approval" element={<PendingApprovalPage />} />

          {/* Audit Ledger & History (Protected) */}
          <Route
            path="/history"
            element={
              <ProtectedRoute>
                <HistoryPage />
              </ProtectedRoute>
            }
          />

          {/* Forensic Results Dossier (Protected) */}
          <Route
            path="/results/:id"
            element={
              <ProtectedRoute>
                <ResultsPage />
              </ProtectedRoute>
            }
          />

          {/* Public Verification Report (Public) */}
          <Route path="/verify-report/:id" element={<VerifyReportPage />} />

          {/* Dedicated Login & Enterprise Onboarding */}
          <Route
            path="/login"
            element={
              isAuthenticated && userProfile?.status === 'approved' ? (
                userProfile.role === 'admin' ? (
                  <Navigate to="/admin" replace />
                ) : (
                  <Navigate to="/" replace />
                )
              ) : isAuthenticated && userProfile?.status === 'pending' ? (
                <Navigate to="/pending-approval" replace />
              ) : (
                <LoginPage initialMode="login" />
              )
            }
          />
          <Route
            path="/register"
            element={
              isAuthenticated && userProfile?.status === 'approved' ? (
                <Navigate to="/" replace />
              ) : isAuthenticated && userProfile?.status === 'pending' ? (
                <Navigate to="/pending-approval" replace />
              ) : (
                <LoginPage initialMode="register" />
              )
            }
          />
          <Route
            path="/signup"
            element={
              isAuthenticated && userProfile?.status === 'approved' ? (
                <Navigate to="/" replace />
              ) : isAuthenticated && userProfile?.status === 'pending' ? (
                <Navigate to="/pending-approval" replace />
              ) : (
                <LoginPage initialMode="register" />
              )
            }
          />

          {/* Admin Supervisory Dashboard (AdminRoute Protected) */}
          <Route
            path="/admin"
            element={
              <AdminRoute>
                <AdminDashboardPage />
              </AdminRoute>
            }
          />

          {/* Fallback */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </React.Suspense>

      {/* Global Authentication Modal */}
      <AuthGatewayModal />
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppContent />
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;
