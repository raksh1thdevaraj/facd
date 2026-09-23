import React, { createContext, useState, useEffect, ReactNode } from 'react';
import { User, UserRole, LoginCredentials, RegisterData, isAdminUser, isPublicUser } from '../types/auth';
import { authService } from '../services/authService';

export interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  isAdmin: boolean;
  isPublic: boolean;
  isAuthModalOpen: boolean;
  activeAuthRole: UserRole | null;
  authModalMessage: string | null;
  openAuthModal: (defaultRole?: UserRole, message?: string) => void;
  closeAuthModal: () => void;
  login: (credentials: LoginCredentials) => Promise<User>;
  register: (data: RegisterData) => Promise<{ success: boolean; email: string; username: string }>;
  logout: () => Promise<void>;
  refreshProfile: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState<boolean>(false);
  const [activeAuthRole, setActiveAuthRole] = useState<UserRole | null>(null);
  const [authModalMessage, setAuthModalMessage] = useState<string | null>(null);

  const openAuthModal = (defaultRole?: UserRole, message?: string) => {
    if (defaultRole) setActiveAuthRole(defaultRole);
    if (message) {
      setAuthModalMessage(message);
    } else {
      setAuthModalMessage(null);
    }
    setIsAuthModalOpen(true);
  };

  const closeAuthModal = () => {
    setIsAuthModalOpen(false);
    setAuthModalMessage(null);
  };

  const refreshProfile = async () => {
    try {
      const profile = await authService.getProfile();
      setUser(profile);
    } catch {
      setUser(null);
      authService.clearTokens();
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Attempt session restoration from stored token or Firebase
    const initAuth = async () => {
      try {
        const token = localStorage.getItem('access_token');
        if (token) {
          const profile = await authService.getProfile();
          setUser(profile);
        }
      } catch {
        setUser(null);
        authService.clearTokens();
      } finally {
        setLoading(false);
      }
    };

    initAuth();

    // Subscribe to Firebase Auth state listener if present
    const unsubscribe = authService.onAuthStateChanged(async (fbUser) => {
      if (fbUser) {
        // Only restore session if email is verified
        if (fbUser.emailVerified) {
          try {
            const profile = await authService.getProfileForUid(fbUser.uid, fbUser);
            setUser(profile);
            const token = await fbUser.getIdToken();
            localStorage.setItem('access_token', token);
          } catch (err) {
            console.error('Error fetching user profile on auth state change:', err);
          }
        }
      }
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  const login = async (credentials: LoginCredentials): Promise<User> => {
    const res = await authService.login(credentials);
    setUser(res.user);
    setIsAuthModalOpen(false);
    setAuthModalMessage(null);
    return res.user;
  };

  const register = async (data: RegisterData): Promise<{ success: boolean; email: string; username: string }> => {
    const res = await authService.register(data);
    return res;
  };

  const logout = async () => {
    await authService.logout();
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated: !!user,
        isAdmin: isAdminUser(user),
        isPublic: isPublicUser(user),
        isAuthModalOpen,
        activeAuthRole,
        authModalMessage,
        openAuthModal,
        closeAuthModal,
        login,
        register,
        logout,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export { useAuth } from '../hooks/useAuth';
