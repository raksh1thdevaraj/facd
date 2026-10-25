import { describe, it, expect, beforeEach } from 'vitest';
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider, useAuth } from '../context/AuthContext';
import { ProtectedView } from '../components/auth/ProtectedView';
import { AuthGatewayModal } from '../components/auth/AuthGatewayModal';
import { EnterpriseHeader } from '../components/common/EnterpriseHeader';

// Test harness for ProtectedView redirection
const ProtectedAppHarness: React.FC = () => {
  return (
    <div>
      <Routes>
        <Route path="/" element={<div data-testid="landing-view">Inspection Console</div>} />
        <Route path="/login" element={<div data-testid="landing-view">Inspection Console</div>} />
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

describe('Institutional Console & Protected Authentication Gateway', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('redirects unauthenticated user and opens auth modal with prompt', async () => {
    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/verify']}>
          <ProtectedAppHarness />
        </MemoryRouter>
      </AuthProvider>
    );

    expect(await screen.findByTestId('landing-view')).toBeInTheDocument();
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();

    expect(
      await screen.findByText('Authentication required to access verification tools.')
    ).toBeInTheDocument();
  });

  it('opens AuthGatewayModal with forensic officer login form', async () => {
    render(
      <AuthProvider>
        <MemoryRouter>
          <ModalTester />
        </MemoryRouter>
      </AuthProvider>
    );

    const openBtn = screen.getByTestId('open-modal-btn');
    fireEvent.click(openBtn);

    expect(screen.getByText(/Forensic Officer Gateway/i)).toBeInTheDocument();
    expect(
      screen.getByText('Authentication required to access verification tools.')
    ).toBeInTheDocument();

    expect(screen.getByLabelText(/Username or Institutional Email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^Password$/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Sign In as Forensic Officer/i })).toBeInTheDocument();
  });

  it('renders EnterpriseHeader with VTU scheme selector', () => {
    render(
      <AuthProvider>
        <MemoryRouter>
          <EnterpriseHeader currentScheme="VTU_2021_CBCS" onSchemeChange={() => {}} />
        </MemoryRouter>
      </AuthProvider>
    );

    expect(screen.getByText(/VERIDOC/i)).toBeInTheDocument();
    expect(screen.getByText(/VTU MARKS CARD FORENSICS/i)).toBeInTheDocument();
    expect(screen.getByText(/VTU 2021 CBCS Scheme/i)).toBeInTheDocument();
  });
});
