export type UserRole = 'ADMIN' | 'INSTITUTION_VERIFIER' | 'PUBLIC_USER';

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
  username?: string;
  password: string;
  full_name: string;
  role?: UserRole;
  institution_id?: string | null;
}
