import React, { createContext, useState, useEffect, ReactNode } from 'react';
import { User as FirebaseUser } from 'firebase/auth';
import { UserProfile, UserRole, LoginCredentials, RegisterData } from '../types/auth';
import { authService } from '../services/authService';

export interface AuthContextType {
  currentUser: FirebaseUser | null;
  userProfile: UserProfile | null;
  user: UserProfile | null; // backwards-compatible alias
  loading: boolean;
  isAuthenticated: boolean;
  isAdmin: boolean;
  isApproved: boolean;
  isPending: boolean;
  isRejected: boolean;
  isPublic: boolean;
  isAuthModalOpen: boolean;
  activeAuthRole: UserRole | null;
  authModalMessage: string | null;
  openAuthModal: (defaultRole?: UserRole, message?: string) => void;
  closeAuthModal: () => void;
  login: (credentials: LoginCredentials) => Promise<UserProfile>;
  register: (data: RegisterData) => Promise<{ success: boolean; email: string; username: string; userProfile: UserProfile }>;
  logout: () => Promise<void>;
  refreshProfile: () => Promise<UserProfile | null>;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [currentUser, setCurrentUser] = useState<FirebaseUser | null>(null);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState<boolean>(false);
  const [activeAuthRole, setActiveAuthRole] = useState<UserRole | null>(null);
  const [authModalMessage, setAuthModalMessage] = useState<string | null>(null);

  const openAuthModal = (defaultRole?: UserRole, message?: string) => {
    if (defaultRole) setActiveAuthRole(defaultRole);
    setAuthModalMessage(message || null);
    setIsAuthModalOpen(true);
  };

  const closeAuthModal = () => {
    setIsAuthModalOpen(false);
    setAuthModalMessage(null);
  };

  const refreshProfile = async (): Promise<UserProfile | null> => {
    try {
      if (currentUser) {
        const profile = await authService.getUserProfile(currentUser.uid, currentUser);
        setUserProfile(profile);
        return profile;
      }
      const profile = await authService.getProfile();
      setUserProfile(profile);
      return profile;
    } catch {
      setUserProfile(null);
      return null;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Subscribe to Firebase Auth state changes
    const unsubscribe = authService.onAuthStateChanged(async (fbUser) => {
      setCurrentUser(fbUser);
      if (fbUser) {
        try {
          const profile = await authService.getUserProfile(fbUser.uid, fbUser);
          setUserProfile(profile);
        } catch (err) {
          console.error('[AuthContext] Error fetching user profile on auth state change:', err);
          setUserProfile(null);
        }
      } else {
        setUserProfile(null);
      }
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  const login = async (credentials: LoginCredentials): Promise<UserProfile> => {
    const res = await authService.login(credentials);
    setUserProfile(res.user);
    setIsAuthModalOpen(false);
    setAuthModalMessage(null);
    return res.user;
  };

  const register = async (
    data: RegisterData
  ): Promise<{ success: boolean; email: string; username: string; userProfile: UserProfile }> => {
    const res = await authService.register(data);
    setUserProfile(res.userProfile);
    return res;
  };

  const logout = async () => {
    await authService.logout();
    setCurrentUser(null);
    setUserProfile(null);
  };

  const isAdmin = userProfile?.role === 'admin';
  const isApproved = userProfile?.status === 'approved';
  const isPending = userProfile?.status === 'pending';
  const isRejected = userProfile?.status === 'rejected';
  const isPublic = userProfile?.role === 'user';
  const isAuthenticated = !!currentUser && !!userProfile;

  return (
    <AuthContext.Provider
      value={{
        currentUser,
        userProfile,
        user: userProfile,
        loading,
        isAuthenticated,
        isAdmin,
        isApproved,
        isPending,
        isRejected,
        isPublic,
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
