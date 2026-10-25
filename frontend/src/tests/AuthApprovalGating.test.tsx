import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { AuthContext, AuthContextType } from '../context/AuthContext';
import { ProtectedRoute } from '../components/auth/ProtectedRoute';
import { AdminRoute } from '../components/auth/AdminRoute';
import { PendingApprovalPage } from '../pages/PendingApprovalPage';
import { AdminDashboardPage } from '../pages/admin/AdminDashboardPage';
import { LoginPage } from '../pages/LoginPage';
import { authService } from '../services/authService';
import { UserProfile, isDisposableEmail } from '../types/auth';

const createMockAuthContext = (overrides: Partial<AuthContextType> = {}): AuthContextType => {
  const baseProfile: UserProfile = {
    uid: 'user-123',
    id: 'user-123',
    fullName: 'Test Verifier',
    email: 'test@wipro.com',
    organizationType: 'CORPORATE_HIRING',
    organizationName: 'Wipro Technologies',
    designation: 'Technical Recruiter',
    officialIdentifier: 'EMP-94021',
    displayName: 'Test Verifier',
    role: 'verifier',
    status: 'approved',
    createdAt: '2026-10-25T12:00:00Z',
    approvalMetadata: {
      reviewedBy: 'admin-001',
      reviewedAt: '2026-10-25T12:30:00Z',
      rejectionReason: null,
    },
    approvedAt: '2026-10-25T12:30:00Z',
    approvedBy: 'admin-001',
    is_active: true,
  };

  return {
    currentUser: { uid: 'user-123', email: 'test@wipro.com' } as any,
    userProfile: baseProfile,
    user: baseProfile,
    loading: false,
    isAuthenticated: true,
    isAdmin: false,
    isApproved: true,
    isPending: false,
    isRejected: false,
    isPublic: true,
    isAuthModalOpen: false,
    activeAuthRole: null,
    authModalMessage: null,
    openAuthModal: vi.fn(),
    closeAuthModal: vi.fn(),
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    refreshProfile: vi.fn(),
    ...overrides,
  };
};

describe('Enterprise Organization Onboarding & Approval Gating Engine', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Disposable Email Check Utility', () => {
    it('detects and flags disposable email providers', () => {
      expect(isDisposableEmail('test@mailinator.com')).toBe(true);
      expect(isDisposableEmail('user@tempmail.com')).toBe(true);
      expect(isDisposableEmail('applicant@10minutemail.com')).toBe(true);
      expect(isDisposableEmail('recruiter@wipro.com')).toBe(false);
      expect(isDisposableEmail('registrar@rvce.edu.in')).toBe(false);
    });
  });

  describe('ProtectedRoute Route Guard', () => {
    it('redirects unauthenticated users to /login', () => {
      const mockContext = createMockAuthContext({
        isAuthenticated: false,
        currentUser: null,
        userProfile: null,
        user: null,
      });

      render(
        <AuthContext.Provider value={mockContext}>
          <MemoryRouter initialEntries={['/protected']}>
            <Routes>
              <Route
                path="/protected"
                element={
                  <ProtectedRoute>
                    <div>Secret Workspace</div>
                  </ProtectedRoute>
                }
              />
              <Route path="/login" element={<div>Login Page Mock</div>} />
            </Routes>
          </MemoryRouter>
        </AuthContext.Provider>
      );

      expect(screen.getByText('Login Page Mock')).toBeInTheDocument();
      expect(screen.queryByText('Secret Workspace')).not.toBeInTheDocument();
    });

    it('redirects pending users (status === "pending") to /pending-approval', () => {
      const pendingProfile: UserProfile = {
        uid: 'user-pending',
        fullName: 'Pending Candidate',
        email: 'pending@tcs.com',
        organizationType: 'CORPORATE_HIRING',
        organizationName: 'TCS Talent Acquisition',
        designation: 'Campus Hiring Lead',
        officialIdentifier: 'TCS-83921',
        displayName: 'Pending Candidate',
        role: 'verifier',
        status: 'pending',
        createdAt: '2026-10-25T10:00:00Z',
        approvalMetadata: {
          reviewedBy: null,
          reviewedAt: null,
          rejectionReason: null,
        },
      };

      const mockContext = createMockAuthContext({
        isAuthenticated: true,
        userProfile: pendingProfile,
        user: pendingProfile,
        isApproved: false,
        isPending: true,
      });

      render(
        <AuthContext.Provider value={mockContext}>
          <MemoryRouter initialEntries={['/protected']}>
            <Routes>
              <Route
                path="/protected"
                element={
                  <ProtectedRoute>
                    <div>Secret Workspace</div>
                  </ProtectedRoute>
                }
              />
              <Route path="/pending-approval" element={<div>Pending Approval View Mock</div>} />
            </Routes>
          </MemoryRouter>
        </AuthContext.Provider>
      );

      expect(screen.getByText('Pending Approval View Mock')).toBeInTheDocument();
      expect(screen.queryByText('Secret Workspace')).not.toBeInTheDocument();
    });

    it('displays declined message when user registration is rejected (status === "rejected")', () => {
      const rejectedProfile: UserProfile = {
        uid: 'user-rejected',
        fullName: 'Rejected Candidate',
        email: 'rejected@unknown.org',
        organizationType: 'BGV_AGENCY',
        organizationName: 'Unverified Agency',
        designation: 'Agent',
        officialIdentifier: 'N/A',
        displayName: 'Rejected Candidate',
        role: 'verifier',
        status: 'rejected',
        createdAt: '2026-10-25T10:00:00Z',
        approvalMetadata: {
          reviewedBy: 'admin-001',
          reviewedAt: '2026-10-25T10:30:00Z',
          rejectionReason: 'Invalid corporate registration details',
        },
      };

      const mockContext = createMockAuthContext({
        isAuthenticated: true,
        userProfile: rejectedProfile,
        user: rejectedProfile,
        isApproved: false,
        isPending: false,
        isRejected: true,
      });

      render(
        <AuthContext.Provider value={mockContext}>
          <MemoryRouter initialEntries={['/protected']}>
            <Routes>
              <Route
                path="/protected"
                element={
                  <ProtectedRoute>
                    <div>Secret Workspace</div>
                  </ProtectedRoute>
                }
              />
            </Routes>
          </MemoryRouter>
        </AuthContext.Provider>
      );

      expect(
        screen.getByText('Account registration request declined by administrator.')
      ).toBeInTheDocument();
      expect(screen.queryByText('Secret Workspace')).not.toBeInTheDocument();
    });

    it('renders children when user is approved (status === "approved")', () => {
      const mockContext = createMockAuthContext({
        isAuthenticated: true,
        isApproved: true,
        isPending: false,
      });

      render(
        <AuthContext.Provider value={mockContext}>
          <MemoryRouter initialEntries={['/protected']}>
            <Routes>
              <Route
                path="/protected"
                element={
                  <ProtectedRoute>
                    <div>Institutional Forensic Console</div>
                  </ProtectedRoute>
                }
              />
            </Routes>
          </MemoryRouter>
        </AuthContext.Provider>
      );

      expect(screen.getByText('Institutional Forensic Console')).toBeInTheDocument();
    });
  });

  describe('AdminRoute Guard', () => {
    it('redirects non-admin users to /workspace', () => {
      const mockContext = createMockAuthContext({
        isAuthenticated: true,
        isAdmin: false,
        isApproved: true,
      });

      render(
        <AuthContext.Provider value={mockContext}>
          <MemoryRouter initialEntries={['/admin']}>
            <Routes>
              <Route
                path="/admin"
                element={
                  <AdminRoute>
                    <div>Super Secret Admin Dashboard</div>
                  </AdminRoute>
                }
              />
              <Route path="/workspace" element={<div>Workspace Console Redirect</div>} />
            </Routes>
          </MemoryRouter>
        </AuthContext.Provider>
      );

      expect(screen.getByText('Workspace Console Redirect')).toBeInTheDocument();
      expect(screen.queryByText('Super Secret Admin Dashboard')).not.toBeInTheDocument();
    });

    it('allows approved admin users into the admin console', () => {
      const adminProfile: UserProfile = {
        uid: 'admin-lead',
        fullName: 'VTU Exam Controller',
        email: 'admin@vtu.ac.in',
        organizationType: 'ACADEMIC_INSTITUTION',
        organizationName: 'Visvesvaraya Technological University',
        designation: 'Registrar (Evaluation)',
        officialIdentifier: 'VTU-REG-001',
        displayName: 'VTU Exam Controller',
        role: 'admin',
        status: 'approved',
        createdAt: '2026-10-01T00:00:00Z',
        approvalMetadata: {
          reviewedBy: 'system',
          reviewedAt: '2026-10-01T00:00:00Z',
          rejectionReason: null,
        },
      };

      const mockContext = createMockAuthContext({
        isAuthenticated: true,
        isAdmin: true,
        isApproved: true,
        userProfile: adminProfile,
        user: adminProfile,
      });

      render(
        <AuthContext.Provider value={mockContext}>
          <MemoryRouter initialEntries={['/admin']}>
            <Routes>
              <Route
                path="/admin"
                element={
                  <AdminRoute>
                    <div>Super Secret Admin Dashboard</div>
                  </AdminRoute>
                }
              />
            </Routes>
          </MemoryRouter>
        </AuthContext.Provider>
      );

      expect(screen.getByText('Super Secret Admin Dashboard')).toBeInTheDocument();
    });
  });

  describe('PendingApprovalPage View', () => {
    it('renders Approval Pending heading, submitted organization info, and action buttons', () => {
      const pendingProfile: UserProfile = {
        uid: 'candidate-99',
        fullName: 'Suresh Patil',
        email: 'suresh.patil@infosys.com',
        organizationType: 'CORPORATE_HIRING',
        organizationName: 'Infosys Limited',
        designation: 'Lead Technical Recruiter',
        officialIdentifier: 'INFY-29402',
        displayName: 'Suresh Patil',
        role: 'verifier',
        status: 'pending',
        createdAt: '2026-10-25T11:00:00Z',
        approvalMetadata: {
          reviewedBy: null,
          reviewedAt: null,
          rejectionReason: null,
        },
      };

      const mockRefresh = vi.fn().mockResolvedValue(pendingProfile);
      const mockLogout = vi.fn().mockResolvedValue(undefined);

      const mockContext = createMockAuthContext({
        userProfile: pendingProfile,
        refreshProfile: mockRefresh,
        logout: mockLogout,
        isApproved: false,
      });

      render(
        <AuthContext.Provider value={mockContext}>
          <MemoryRouter>
            <PendingApprovalPage />
          </MemoryRouter>
        </AuthContext.Provider>
      );

      expect(screen.getByText('Approval Pending')).toBeInTheDocument();
      expect(
        screen.getByText(
          /Your account has been registered and is awaiting administrator verification/i
        )
      ).toBeInTheDocument();
      expect(screen.getByText('Suresh Patil')).toBeInTheDocument();
      expect(screen.getByText('Infosys Limited')).toBeInTheDocument();
      expect(screen.getByText('Corporate Hiring')).toBeInTheDocument();
      expect(screen.getByText('Lead Technical Recruiter')).toBeInTheDocument();
      expect(screen.getByText('INFY-29402')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /check status/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /sign out/i })).toBeInTheDocument();

      // Click Check Status
      fireEvent.click(screen.getByRole('button', { name: /check status/i }));
      expect(mockRefresh).toHaveBeenCalled();

      // Click Sign Out
      fireEvent.click(screen.getByRole('button', { name: /sign out/i }));
      expect(mockLogout).toHaveBeenCalled();
    });
  });

  describe('Enterprise Registration Form UI', () => {
    it('renders all institutional fields and organization dropdown options', () => {
      const mockRegister = vi.fn().mockResolvedValue({
        success: true,
        email: 'rajesh@wipro.com',
        username: 'Rajesh Kumar',
        userProfile: {
          uid: 'uid-wipro',
          role: 'verifier',
          status: 'pending',
        },
      });

      const mockContext = createMockAuthContext({
        isAuthenticated: false,
        currentUser: null,
        userProfile: null,
        register: mockRegister,
      });

      render(
        <AuthContext.Provider value={mockContext}>
          <MemoryRouter initialEntries={['/register']}>
            <LoginPage initialMode="register" />
          </MemoryRouter>
        </AuthContext.Provider>
      );

      expect(screen.getByText(/Enterprise Organization & Institutional Verifier Onboarding/i)).toBeInTheDocument();
      expect(screen.getByPlaceholderText('e.g. Rajesh Kumar')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('e.g. rajesh@wipro.com')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('e.g. Wipro Technologies / RVCE')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('e.g. Senior Technical Recruiter')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('e.g. EMP-94021 or https://wipro.com')).toBeInTheDocument();
      expect(screen.getByRole('combobox')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /submit organization onboarding request/i })).toBeInTheDocument();
    });
  });

  describe('AdminDashboardPage User Management & Real-Time Approval UI', () => {
    const mockUsers: UserProfile[] = [
      {
        uid: 'user-001',
        fullName: 'Dr. Ananya Rao',
        email: 'applicant1@pes.edu',
        organizationType: 'ACADEMIC_INSTITUTION',
        organizationName: 'PES University Admissions',
        designation: 'Assistant Dean of Admissions',
        officialIdentifier: 'PESU-ADM-102',
        displayName: 'Dr. Ananya Rao',
        role: 'verifier',
        status: 'pending',
        createdAt: '2026-10-25T08:00:00Z',
        approvalMetadata: {
          reviewedBy: null,
          reviewedAt: null,
          rejectionReason: null,
        },
      },
      {
        uid: 'user-002',
        fullName: 'Prof. K. Venkatesh',
        email: 'examiner@bmsce.ac.in',
        organizationType: 'ACADEMIC_INSTITUTION',
        organizationName: 'BMS College of Engineering',
        designation: 'Controller of Examinations',
        officialIdentifier: 'BMS-COE-88',
        displayName: 'Prof. K. Venkatesh',
        role: 'verifier',
        status: 'approved',
        createdAt: '2026-10-24T09:00:00Z',
        approvalMetadata: {
          reviewedBy: 'admin-lead',
          reviewedAt: '2026-10-24T10:00:00Z',
          rejectionReason: null,
        },
      },
    ];

    it('renders organization vetting metrics bar and table with sector badges', async () => {
      vi.spyOn(authService, 'subscribeToUsers').mockImplementation((callback) => {
        callback(mockUsers);
        return () => {};
      });

      const mockApprove = vi.spyOn(authService, 'approveUser').mockResolvedValue(undefined);
      const mockReject = vi.spyOn(authService, 'rejectUser').mockResolvedValue(undefined);

      const adminProfile: UserProfile = {
        uid: 'admin-lead',
        fullName: 'VTU Exam Controller',
        email: 'admin@vtu.ac.in',
        organizationType: 'ACADEMIC_INSTITUTION',
        organizationName: 'Visvesvaraya Technological University',
        designation: 'System Administrator',
        officialIdentifier: 'VTU-001',
        displayName: 'VTU Exam Controller',
        role: 'admin',
        status: 'approved',
        createdAt: '2026-10-01T00:00:00Z',
        approvalMetadata: {
          reviewedBy: 'system',
          reviewedAt: '2026-10-01T00:00:00Z',
          rejectionReason: null,
        },
      };

      const mockContext = createMockAuthContext({
        currentUser: { uid: 'admin-lead', email: 'admin@vtu.ac.in' } as any,
        userProfile: adminProfile,
        isAdmin: true,
      });

      render(
        <AuthContext.Provider value={mockContext}>
          <MemoryRouter>
            <AdminDashboardPage />
          </MemoryRouter>
        </AuthContext.Provider>
      );

      // Verify Metrics Bar
      expect(screen.getByText('Total Onboarded Organizations')).toBeInTheDocument();
      expect(screen.getByText('Pending Vetting & Approvals')).toBeInTheDocument();
      expect(screen.getByText('Active Verified Accounts')).toBeInTheDocument();

      // Verify Table Columns and Entries
      await waitFor(() => {
        expect(screen.getByText('Dr. Ananya Rao')).toBeInTheDocument();
        expect(screen.getByText('applicant1@pes.edu')).toBeInTheDocument();
        expect(screen.getByText('PES University Admissions')).toBeInTheDocument();
        expect(screen.getByText('Prof. K. Venkatesh')).toBeInTheDocument();
        expect(screen.getByText('BMS College of Engineering')).toBeInTheDocument();
      });

      // Verify Status Pills
      expect(screen.getByText('Pending Vetting')).toBeInTheDocument();
      expect(screen.getByText('Approved')).toBeInTheDocument();

      // Test Approve Action on Pending User
      const approveButtons = screen.getAllByRole('button', { name: /approve/i });
      fireEvent.click(approveButtons[0]);
      await waitFor(() => {
        expect(mockApprove).toHaveBeenCalledWith('user-001', 'admin-lead');
      });

      // Test Reject Action (Opens modal and confirms)
      await waitFor(() => {
        expect(screen.getAllByRole('button', { name: /reject/i }).length).toBeGreaterThan(0);
      });
      const rejectButtons = screen.getAllByRole('button', { name: /reject/i });
      fireEvent.click(rejectButtons[0]);

      // Verify Modal Opens
      expect(screen.getByText('Decline Organization Registration')).toBeInTheDocument();
      const confirmRejectBtn = screen.getByRole('button', { name: /confirm rejection/i });
      fireEvent.click(confirmRejectBtn);

      await waitFor(() => {
        expect(mockReject).toHaveBeenCalledWith('user-001', 'admin-lead', expect.any(String));
      });
    });
  });
});
