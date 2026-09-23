import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Navbar } from './components/common/Navbar';
import { InstitutionalFooter } from './components/landing/InstitutionalFooter';
import { LandingPage } from './pages/LandingPage';
import { UploadPage } from './pages/UploadPage';
import { ResultsPage } from './pages/ResultsPage';
import { VerifyReportPage } from './pages/VerifyReportPage';
import { HistoryPage } from './pages/HistoryPage';
import { LoginPage } from './pages/LoginPage';
import { NotFoundPage } from './pages/NotFoundPage';
import { AdminDashboardPage } from './pages/admin/AdminDashboardPage';
import { CourseVerificationPage } from './pages/CourseVerificationPage';
import { PublicVerifyPage } from './pages/PublicVerifyPage';
import { ProtectedView } from './components/auth/ProtectedView';
import { AuthGatewayModal } from './components/auth/AuthGatewayModal';

const AppContent: React.FC = () => {
  const { isAuthenticated, user } = useAuth();

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-100 flex flex-col selection:bg-emerald-500/30 selection:text-emerald-200">
      <Navbar />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
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
