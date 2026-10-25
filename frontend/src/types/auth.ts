/**
 * Authentication and authorization types for the Two-Role Authentication System.
 * Supported Roles:
 * - 'user': Standard user / forensic verifier (pending admin approval upon signup)
 * - 'admin': System Administrator & Security Lead (user approval, role promotion, audit oversight)
 *
 * Supported Statuses:
 * - 'pending': Awaiting administrator verification
 * - 'approved': Account verified and active
 * - 'rejected': Account request declined by administrator
 */

export type UserRole = 'user' | 'admin';
export type UserStatus = 'pending' | 'approved' | 'rejected';

export interface UserProfile {
  uid: string;
  email: string;
  displayName: string;
  role: UserRole;
  status: UserStatus;
  createdAt: any;
  approvedAt: any | null;
  approvedBy: string | null;
  // Backwards compatibility aliases
  id?: string;
  username?: string;
  full_name?: string;
  institution_id?: string | null;
  is_active?: boolean;
  created_at?: string;
}

export type User = UserProfile;

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: UserProfile;
}

export interface LoginCredentials {
  email?: string;
  username?: string;
  password: string;
}

export interface RegisterData {
  email: string;
  displayName?: string;
  name?: string;
  full_name?: string;
  username?: string;
  password: string;
  role?: UserRole;
  institution_id?: string | null;
}

/** Check if user possesses administrative privileges */
export const isAdminUser = (user: UserProfile | null): boolean => {
  if (!user) return false;
  return user.role === 'admin';
};

/** Check if user is approved */
export const isApprovedUser = (user: UserProfile | null): boolean => {
  if (!user) return false;
  return user.status === 'approved';
};

/** Check if user is pending */
export const isPendingUser = (user: UserProfile | null): boolean => {
  if (!user) return false;
  return user.status === 'pending';
};

/** Check if user is rejected */
export const isRejectedUser = (user: UserProfile | null): boolean => {
  if (!user) return false;
  return user.status === 'rejected';
};

/** Check if user possesses standard user role */
export const isPublicUser = (user: UserProfile | null): boolean => {
  if (!user) return false;
  return user.role === 'user';
};
