import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { AuthContext, AuthContextType } from '../context/AuthContext';
import { ProtectedRoute } from '../components/auth/ProtectedRoute';
import { AdminRoute } from '../components/auth/AdminRoute';
import { PendingApprovalPage } from '../pages/PendingApprovalPage';
import { AdminDashboardPage } from '../pages/admin/AdminDashboardPage';
import { authService } from '../services/authService';
import { UserProfile } from '../types/auth';

const createMockAuthContext = (overrides: Partial<AuthContextType> = {}): AuthContextType => ({
  currentUser: { uid: 'user-123', email: 'test@institution.edu' } as any,
  userProfile: {
    uid: 'user-123',
    id: 'user-123',
    email: 'test@institution.edu',
    displayName: 'Test User',
    role: 'user',
    status: 'approved',
    createdAt: '2026-10-25T12:00:00Z',
    approvedAt: '2026-10-25T12:30:00Z',
    approvedBy: 'admin-001',
    is_active: true,
  },
  user: {
    uid: 'user-123',
    id: 'user-123',
    email: 'test@institution.edu',
    displayName: 'Test User',
    role: 'user',
    status: 'approved',
    createdAt: '2026-10-25T12:00:00Z',
    approvedAt: '2026-10-25T12:30:00Z',
    approvedBy: 'admin-001',
    is_active: true,
  },
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
});

describe('Two-Role Authentication & Approval Gating Engine', () => {
  beforeEach(() => {
    vi.clearAllMocks();
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
        email: 'pending@institution.edu',
        displayName: 'Pending Candidate',
        role: 'user',
        status: 'pending',
        createdAt: '2026-10-25T10:00:00Z',
        approvedAt: null,
        approvedBy: null,
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
        email: 'rejected@institution.edu',
        displayName: 'Rejected Candidate',
        role: 'user',
        status: 'rejected',
        createdAt: '2026-10-25T10:00:00Z',
        approvedAt: null,
        approvedBy: 'admin-001',
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
        email: 'admin@vtu.ac.in',
        displayName: 'VTU Exam Controller',
        role: 'admin',
        status: 'approved',
        createdAt: '2026-10-01T00:00:00Z',
        approvedAt: '2026-10-01T00:00:00Z',
        approvedBy: 'system',
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
    it('renders Approval Pending heading, instructions, and interactive action buttons', () => {
      const pendingProfile: UserProfile = {
        uid: 'candidate-99',
        email: 'candidate@rvce.edu.in',
        displayName: 'Suresh Patil',
        role: 'user',
        status: 'pending',
        createdAt: '2026-10-25T11:00:00Z',
        approvedAt: null,
        approvedBy: null,
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
      expect(screen.getByText('candidate@rvce.edu.in')).toBeInTheDocument();
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

  describe('AdminDashboardPage User Management & Real-Time Approval UI', () => {
    const mockUsers: UserProfile[] = [
      {
        uid: 'user-001',
        email: 'applicant1@pes.edu',
        displayName: 'Dr. Ananya Rao',
        role: 'user',
        status: 'pending',
        createdAt: '2026-10-25T08:00:00Z',
        approvedAt: null,
        approvedBy: null,
      },
      {
        uid: 'user-002',
        email: 'examiner@bmsce.ac.in',
        displayName: 'Prof. K. Venkatesh',
        role: 'user',
        status: 'approved',
        createdAt: '2026-10-24T09:00:00Z',
        approvedAt: '2026-10-24T10:00:00Z',
        approvedBy: 'admin-lead',
      },
      {
        uid: 'user-003',
        email: 'suspicious@unknown.net',
        displayName: 'Unknown Operator',
        role: 'user',
        status: 'rejected',
        createdAt: '2026-10-23T14:00:00Z',
        approvedAt: null,
        approvedBy: 'admin-lead',
      },
    ];

    it('renders metrics bar and user management table with status pills', async () => {
      vi.spyOn(authService, 'subscribeToUsers').mockImplementation((callback) => {
        callback(mockUsers);
        return () => {};
      });

      const mockApprove = vi.spyOn(authService, 'approveUser').mockResolvedValue(undefined);
      const mockReject = vi.spyOn(authService, 'rejectUser').mockResolvedValue(undefined);

      const adminProfile: UserProfile = {
        uid: 'admin-lead',
        email: 'admin@vtu.ac.in',
        displayName: 'VTU Exam Controller',
        role: 'admin',
        status: 'approved',
        createdAt: '2026-10-01T00:00:00Z',
        approvedAt: '2026-10-01T00:00:00Z',
        approvedBy: 'system',
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
      expect(screen.getByText('Total Registered Users')).toBeInTheDocument();
      expect(screen.getByText('Pending Approvals')).toBeInTheDocument();
      expect(screen.getByText('Active Accounts (Approved)')).toBeInTheDocument();

      // Verify Table Columns and Entries
      await waitFor(() => {
        expect(screen.getByText('Dr. Ananya Rao')).toBeInTheDocument();
        expect(screen.getByText('applicant1@pes.edu')).toBeInTheDocument();
        expect(screen.getByText('Prof. K. Venkatesh')).toBeInTheDocument();
        expect(screen.getByText('examiner@bmsce.ac.in')).toBeInTheDocument();
      });

      // Verify Status Pills
      expect(screen.getByText('Pending Approval')).toBeInTheDocument();
      expect(screen.getByText('Approved')).toBeInTheDocument();
      expect(screen.getByText('Rejected')).toBeInTheDocument();

      // Test Approve Action on Pending User
      const approveButtons = screen.getAllByRole('button', { name: /approve/i });
      fireEvent.click(approveButtons[0]);
      await waitFor(() => {
        expect(mockApprove).toHaveBeenCalledWith('user-001', 'admin-lead');
      });

      // Test Reject Action on User
      await waitFor(() => {
        expect(screen.getAllByRole('button', { name: /reject/i }).length).toBeGreaterThan(0);
      });
      const rejectButtons = screen.getAllByRole('button', { name: /reject/i });
      fireEvent.click(rejectButtons[0]);
      await waitFor(() => {
        expect(mockReject).toHaveBeenCalledWith('user-001', 'admin-lead');
      });
    });
  });
});
