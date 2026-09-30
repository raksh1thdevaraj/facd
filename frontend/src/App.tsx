import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Navbar } from './components/common/Navbar';
import { InstitutionalFooter } from './components/landing/InstitutionalFooter';
import { LandingPage } from './pages/LandingPage';
import { ProtectedView } from './components/auth/ProtectedView';
import { AuthGatewayModal } from './components/auth/AuthGatewayModal';

// Route-level code splitting to optimize initial bundle and dashboard load
const UploadPage = React.lazy(() =>
  import('./pages/UploadPage').then((m) => ({ default: m.UploadPage }))
);
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
const CourseVerificationPage = React.lazy(() =>
  import('./pages/CourseVerificationPage').then((m) => ({ default: m.CourseVerificationPage }))
);
const PublicVerifyPage = React.lazy(() =>
  import('./pages/PublicVerifyPage').then((m) => ({ default: m.PublicVerifyPage }))
);

const RouteLoadingFallback: React.FC = () => (
  <div className="min-h-[50vh] flex flex-col items-center justify-center space-y-3">
    <Loader2 className="w-8 h-8 text-emerald-400 animate-spin" />
    <span className="text-xs text-slate-400 font-mono tracking-wider">Loading enclave module...</span>
  </div>
);

const AppContent: React.FC = () => {
  const { isAuthenticated, user } = useAuth();

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-100 flex flex-col selection:bg-emerald-500/30 selection:text-emerald-200">
      <Navbar />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <React.Suspense fallback={<RouteLoadingFallback />}>
          <Routes>
          {/* Default Root: Landing Page when unauthenticated or public */}
          <Route path="/" element={<LandingPage />} />

          {/* Verification Hub: Protected for authenticated users */}
          <Route
            path="/verify"
            element={
              <ProtectedView>
                <PublicVerifyPage />
              </ProtectedView>
            }
          />

          {/* Unified Dashboard Redirection: routes users to their respective workspaces */}
          <Route
            path="/dashboard"
            element={
              <ProtectedView>
                <Navigate to={user?.role === 'admin' ? '/admin' : '/verify'} replace />
              </ProtectedView>
            }
          />

          {/* Protected Feature / Scanner Portal */}
          <Route
            path="/upload"
            element={
              <ProtectedView>
                <UploadPage />
              </ProtectedView>
            }
          />

          {/* Protected Course Verification */}
          <Route
            path="/course-verification"
            element={
              <ProtectedView>
                <CourseVerificationPage />
              </ProtectedView>
            }
          />

          {/* Protected Results & Forensic Dossier */}
          <Route
            path="/results/:id"
            element={
              <ProtectedView>
                <ResultsPage />
              </ProtectedView>
            }
          />

          {/* Public or Protected Verification Badge Report */}
          <Route path="/verify-report/:id" element={<VerifyReportPage />} />

          {/* Protected Verification History */}
          <Route
            path="/history"
            element={
              <ProtectedView>
                <HistoryPage />
              </ProtectedView>
            }
          />

          {/* Dedicated Login Page Fallback */}
          <Route
            path="/login"
            element={
              isAuthenticated ? (
                <Navigate to={user?.role === 'admin' ? '/admin' : '/verify'} replace />
              ) : (
                <LoginPage />
              )
            }
          />

          {/* Protected Admin Console: Strictly requires 'admin' role */}
          <Route
            path="/admin"
            element={
              <ProtectedView requiredRole="admin">
                <AdminDashboardPage />
              </ProtectedView>
            }
          />

          <Route path="*" element={<NotFoundPage />} />
        </Routes>
        </React.Suspense>
      </main>

      {/* Institutional Cryptographic Footer */}
      <InstitutionalFooter />

      {/* Global Interactive Authentication Modal */}
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
