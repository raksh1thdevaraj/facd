import { describe, it, expect, beforeEach } from 'vitest';
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider, useAuth } from '../context/AuthContext';
import { ProtectedView } from '../components/auth/ProtectedView';
import { AuthGatewayModal } from '../components/auth/AuthGatewayModal';
import { ProblemSolutionMatrix } from '../components/landing/ProblemSolutionMatrix';
import { ResearchMatrix } from '../components/landing/ResearchMatrix';

// Test harness for ProtectedView redirection
const ProtectedAppHarness: React.FC = () => {
  return (
    <div>
      <Routes>
        <Route path="/" element={<div data-testid="landing-view">Public Landing View</div>} />
        <Route
          path="/verify"
          element={
            <ProtectedView>
              <div data-testid="protected-content">Secret Forensic Workspace</div>
            </ProtectedView>
          }
        />
      </Routes>
      <AuthGatewayModal />
    </div>
  );
};

// Modal Trigger Tester
const ModalTester: React.FC = () => {
  const { openAuthModal, user } = useAuth();
  return (
    <div>
      <button
        onClick={() => openAuthModal(undefined, 'Authentication required to access verification tools.')}
        data-testid="open-modal-btn"
      >
        Open Auth
      </button>
      {user && <span data-testid="active-username">{user.full_name}</span>}
      <AuthGatewayModal />
    </div>
  );
};

describe('Landing Page & Protected Authentication Gateway', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('redirects unauthenticated user to landing page and opens auth modal with prompt', async () => {
    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/verify']}>
          <ProtectedAppHarness />
        </MemoryRouter>
      </AuthProvider>
    );

    // Unauthenticated user should be redirected to landing view
    expect(await screen.findByTestId('landing-view')).toBeInTheDocument();
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();

    // Modal should have been triggered with the required message
    expect(
      await screen.findByText('Authentication required to access verification tools.')
    ).toBeInTheDocument();
  });

  it('opens AuthGatewayModal with simplified login form and switches to registration with strict Username label', async () => {
    render(
      <AuthProvider>
        <MemoryRouter>
          <ModalTester />
        </MemoryRouter>
      </AuthProvider>
    );

    // Click trigger
    const openBtn = screen.getByTestId('open-modal-btn');
    fireEvent.click(openBtn);

    // Modal header and prompt banner should be visible
    expect(screen.getByText(/CertiShield Security Gateway/i)).toBeInTheDocument();
    expect(
      screen.getByText('Authentication required to access verification tools.')
    ).toBeInTheDocument();

    // Verify Login Form fields (NO role selection tabs)
    expect(screen.getByLabelText(/Username or Email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^Password$/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Sign In/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Forgot Password\?/i })).toBeInTheDocument();

    // Verify role tabs are completely eliminated
    expect(screen.queryByText('Public Verifier')).not.toBeInTheDocument();
    expect(screen.queryByText('System Administrator')).not.toBeInTheDocument();

    // Switch to Register Mode
    const registerSwitcher = screen.getByRole('button', { name: /Register/i });
    fireEvent.click(registerSwitcher);

    // Strictly separate fields with strict "Username" label
    expect(screen.getByLabelText(/^Username$/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText('e.g. jdoe_verifier')).toBeInTheDocument();
    expect(screen.getByLabelText(/Email Address/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText('name@institution.edu')).toBeInTheDocument();
    expect(screen.getByLabelText(/Confirm Password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Create Account/i })).toBeInTheDocument();
  });

  it('renders ProblemSolutionMatrix with interactive category filter', () => {
    render(<ProblemSolutionMatrix />);
    expect(screen.getByText(/LITERATURE SURVEY & SYSTEM COMPARATIVE MATRIX/i)).toBeInTheDocument();

    // Filter to OCR
    const ocrFilter = screen.getByRole('button', { name: 'OCR' });
    fireEvent.click(ocrFilter);

    expect(screen.getByText(/Single-Engine OCR Blindspots/i)).toBeInTheDocument();
  });

  it('renders ResearchMatrix with 99.4% tamper precision benchmark', () => {
    render(<ResearchMatrix />);
    expect(screen.getByText('99.4%')).toBeInTheDocument();
    expect(screen.getByText(/Rigorous Benchmark Evaluation/i)).toBeInTheDocument();
  });
});
