import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ProtectedView } from './components/auth/ProtectedView';
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
const NotFoundPage = React.lazy(() =>
  import('./pages/NotFoundPage').then((m) => ({ default: m.NotFoundPage }))
);
const AdminDashboardPage = React.lazy(() =>
  import('./pages/admin/AdminDashboardPage').then((m) => ({ default: m.AdminDashboardPage }))
);

const RouteLoadingFallback: React.FC = () => (
  <div className="min-h-[60vh] flex flex-col items-center justify-center space-y-3">
    <Loader2 className="w-8 h-8 text-indigo-700 animate-spin" />
    <span className="text-xs text-slate-500 font-mono tracking-wider">
      Loading institutional forensic module...
    </span>
  </div>
);

const AppContent: React.FC = () => {
  const { isAuthenticated } = useAuth();

  return (
    <div className="min-h-screen bg-[#f8fafc] text-slate-900 flex flex-col selection:bg-indigo-500/20 selection:text-indigo-900">
      <React.Suspense fallback={<RouteLoadingFallback />}>
        <Routes>
          {/* Master Institutional Examination & Inspection Console */}
          <Route path="/" element={<InspectionConsolePage />} />
          <Route path="/console" element={<InspectionConsolePage />} />
          <Route path="/verify" element={<InspectionConsolePage />} />
          <Route path="/dashboard" element={<Navigate to="/" replace />} />

          {/* Audit Ledger & History */}
          <Route
            path="/history"
            element={
              <ProtectedView>
                <HistoryPage />
              </ProtectedView>
            }
          />

          {/* Forensic Results Dossier */}
          <Route
            path="/results/:id"
            element={
              <ProtectedView>
                <ResultsPage />
              </ProtectedView>
            }
          />

          {/* Public Verification Report */}
          <Route path="/verify-report/:id" element={<VerifyReportPage />} />

          {/* Dedicated Login */}
          <Route
            path="/login"
            element={
              isAuthenticated ? (
                <Navigate to="/" replace />
              ) : (
                <LoginPage />
              )
            }
          />

          {/* Admin Management Console */}
          <Route
            path="/admin"
            element={
              <ProtectedView requiredRole="admin">
                <AdminDashboardPage />
              </ProtectedView>
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
