/**
 * Authentication and authorization types for Enterprise Organization Onboarding.
 *
 * Supported Roles:
 * - 'verifier': Verified Institutional / Corporate Verifier (pending administrator vetting)
 * - 'user': Legacy / standard verification user
 * - 'admin': System Administrator & Forensic Lead (account vetting, approval, role delegation)
 *
 * Supported Statuses:
 * - 'pending': Account registered and awaiting administrator verification of credentials
 * - 'approved': Account reviewed and approved for examination console access
 * - 'rejected': Account registration declined by administrator
 */

export type UserRole = 'verifier' | 'user' | 'admin';
export type UserStatus = 'pending' | 'approved' | 'rejected';

export type OrganizationType = 'CORPORATE_HIRING' | 'ACADEMIC_INSTITUTION' | 'BGV_AGENCY';

export interface ApprovalMetadata {
  reviewedBy: string | null;
  reviewedAt: any | null;
  rejectionReason: string | null;
}

export interface UserProfile {
  uid: string;
  fullName: string;
  email: string;
  organizationType: OrganizationType;
  organizationName: string;
  designation: string;
  officialIdentifier: string;
  role: UserRole;
  status: UserStatus;
  createdAt: any;
  approvalMetadata?: ApprovalMetadata;

  // Backwards-compatibility & convenience aliases
  displayName?: string;
  approvedAt?: any | null;
  approvedBy?: string | null;
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
  fullName?: string;
  email: string;
  organizationType?: OrganizationType;
  organizationName?: string;
  designation?: string;
  officialIdentifier?: string;
  password: string;

  // Legacy optional properties
  displayName?: string;
  name?: string;
  full_name?: string;
  username?: string;
  role?: UserRole;
  institution_id?: string | null;
}

/** Disposable email domain blacklist for institutional vetting */
const DISPOSABLE_EMAIL_DOMAINS = new Set([
  'mailinator.com',
  'tempmail.com',
  'temp-mail.org',
  '10minutemail.com',
  'guerrillamail.com',
  'throwawaymail.com',
  'trashmail.com',
  'yopmail.com',
  'sharklasers.com',
  'dispostable.com',
  'getairmail.com',
  'fakemailgenerator.com',
  'mohmal.com',
  'generator.email',
  'emailondeck.com',
  'nada.ltd',
  'crazymailing.com',
]);

/** Check if email is from a known temporary or disposable provider */
export const isDisposableEmail = (email: string): boolean => {
  const clean = email.trim().toLowerCase();
  const parts = clean.split('@');
  if (parts.length !== 2) return false;
  return DISPOSABLE_EMAIL_DOMAINS.has(parts[1]);
};

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

/** Check if user possesses standard verification role */
export const isPublicUser = (user: UserProfile | null): boolean => {
  if (!user) return false;
  return user.role === 'user' || user.role === 'verifier';
};
