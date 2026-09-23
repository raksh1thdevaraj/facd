/**
 * Authentication and authorization types for the Two-Role Certificate Verification Engine.
 * Strictly supports TWO primary operational roles:
 * - 'public': Public Verifier (frictionless marks card and course certificate validation)
 * - 'admin': System Administrator & Forensic Lead (telemetry, models, behavioral logs)
 */

export type UserRole = 'user' | 'admin';

export interface User {
  id: string;
  email: string;
  username?: string;
  full_name: string;
  role: UserRole;
  institution_id?: string | null;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface LoginCredentials {
  email?: string;
  username?: string;
  password: string;
}

export interface RegisterData {
  email: string;
  name?: string;
  full_name?: string;
  username?: string;
  password: string;
  role?: UserRole;
  institution_id?: string | null;
}

/** Check if user possesses administrative privileges */
export const isAdminUser = (user: User | null): boolean => {
  if (!user) return false;
  return user.role === 'admin';
};

/** Check if user possesses registered verifier privileges */
export const isPublicUser = (user: User | null): boolean => {
  if (!user) return false;
  return user.role === 'user';
};

