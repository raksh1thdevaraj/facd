import { 
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut,
  updateProfile,
  sendEmailVerification,
  sendPasswordResetEmail,
  onAuthStateChanged,
  User as FirebaseUser
} from 'firebase/auth';
import { 
  doc, 
  getDoc, 
  setDoc,
  updateDoc,
  collection, 
  onSnapshot,
  query,
  orderBy,
  serverTimestamp,
  getDocs
} from 'firebase/firestore';
import { auth, db } from '../config/firebase';
import { 
  LoginCredentials, 
  RegisterData, 
  TokenResponse, 
  UserProfile, 
  UserRole, 
  UserStatus,
  OrganizationType,
  isDisposableEmail
} from '../types/auth';
import { apiClient } from './api';

/**
 * Format Firebase Auth and API errors into clear, user-friendly messages.
 */
export function formatAuthError(error: any): string {
  const code = error?.code || '';
  if (code === 'auth/email-already-in-use') {
    return 'An account with this corporate/institutional email already exists.';
  }
  if (
    code === 'auth/user-not-found' ||
    code === 'auth/wrong-password' ||
    code === 'auth/invalid-credential' ||
    code === 'auth/invalid-login-credentials'
  ) {
    return 'Invalid email/username or password.';
  }
  if (code === 'auth/too-many-requests') {
    return 'Too many attempts. Please try again in a few minutes.';
  }
  if (code === 'auth/weak-password') {
    return 'Password must be at least 8 characters.';
  }
  if (code === 'auth/invalid-email') {
    return 'Please enter a valid official email address.';
  }
  return error?.message || 'Authentication failed. Please check credentials.';
}

/** Check if email matches designated seed administrator accounts */
export function isDesignatedAdminEmail(email: string): boolean {
  const cleanEmail = email.trim().toLowerCase();
  const configuredSeed = import.meta.env.VITE_INITIAL_ADMIN_EMAIL?.trim().toLowerCase();
  if (configuredSeed && cleanEmail === configuredSeed) {
    return true;
  }
  const defaultAdmins = ['admin@facd.edu', 'admin@vtu.ac.in', 'admin@certishield.ai'];
  if (defaultAdmins.includes(cleanEmail)) {
    return true;
  }
  if (cleanEmail.startsWith('admin@')) {
    return true;
  }
  return false;
}

export const authService = {
  /**
   * Listen to Firebase auth state changes.
   */
  onAuthStateChanged(callback: (user: FirebaseUser | null) => void) {
    return onAuthStateChanged(auth, callback);
  },

  /**
   * Resolve an email address from either an email or username string.
   */
  async resolveEmail(identifier: string): Promise<string> {
    const trimmed = identifier.trim();
    if (trimmed.includes('@')) {
      return trimmed.toLowerCase();
    }

    const cacheKey = `user_email_${trimmed.toLowerCase()}`;
    try {
      const cached = localStorage.getItem(cacheKey);
      if (cached && cached.includes('@')) {
        return cached.trim().toLowerCase();
      }
    } catch {
      // Local storage not available
    }

    try {
      const snap = await getDocs(collection(db, 'users'));
      for (const d of snap.docs) {
        const data = d.data();
        const u = data.username ? String(data.username).trim() : (data.fullName || data.displayName || '');
        if (String(u).toLowerCase() === trimmed.toLowerCase()) {
          if (data.email) {
            const resolved = String(data.email).trim().toLowerCase();
            try {
              localStorage.setItem(cacheKey, resolved);
            } catch {}
            return resolved;
          }
        }
      }
    } catch (err) {
      console.warn('[resolveEmail] Firestore username lookup error:', err);
    }

    // Default aliases
    if (trimmed.toLowerCase() === 'admin') {
      return 'admin@facd.edu';
    }

    return trimmed;
  },

  /**
   * Register a new enterprise organization user in Firebase Auth and initialize Firestore user document.
   * Document ID: user.uid
   * Exact Model:
   * {
   *   "uid": "USER_AUTH_UID",
   *   "fullName": "Rajesh Kumar",
   *   "email": "rajesh@company.com",
   *   "organizationType": "CORPORATE_HIRING",
   *   "organizationName": "Wipro Technologies",
   *   "designation": "Technical Recruiter",
   *   "officialIdentifier": "EMP-94021",
   *   "role": "verifier",
   *   "status": "pending",
   *   "createdAt": "SERVER_TIMESTAMP",
   *   "approvalMetadata": {
   *     "reviewedBy": null,
   *     "reviewedAt": null,
   *     "rejectionReason": null
   *   }
   * }
   */
  async register(data: RegisterData): Promise<{ success: boolean; email: string; username: string; userProfile: UserProfile }> {
    const email = data.email.trim().toLowerCase();
    const fullName = (data.fullName || data.displayName || data.name || data.full_name || email.split('@')[0]).trim();
    const organizationType: OrganizationType = data.organizationType || 'CORPORATE_HIRING';
    const organizationName = (data.organizationName || 'Institutional Entity').trim();
    const designation = (data.designation || 'Credential Verifier').trim();
    const officialIdentifier = (data.officialIdentifier || 'N/A').trim();
    const password = data.password;

    // 1. Enforce non-disposable corporate/institutional email check
    if (isDisposableEmail(email)) {
      throw new Error('Please use an official corporate or institutional work email. Disposable temporary email providers are strictly prohibited.');
    }

    try {
      // 2. Create account with Firebase Auth
      const userCredential = await createUserWithEmailAndPassword(auth, email, password);
      const fbUser = userCredential.user;

      // 3. Set profile display name
      await updateProfile(fbUser, { displayName: fullName });

      // 4. Check for Initial Admin Bootstrap
      const isInitialAdmin = isDesignatedAdminEmail(email);
      const role: UserRole = isInitialAdmin ? 'admin' : (data.role || 'verifier');
      const status: UserStatus = isInitialAdmin ? 'approved' : 'pending';

      const userProfile: UserProfile = {
        uid: fbUser.uid,
        fullName: fullName,
        email: email,
        organizationType: organizationType,
        organizationName: organizationName,
        designation: designation,
        officialIdentifier: officialIdentifier,
        role: role,
        status: status,
        createdAt: serverTimestamp(),
        approvalMetadata: {
          reviewedBy: isInitialAdmin ? 'system_bootstrap' : null,
          reviewedAt: isInitialAdmin ? serverTimestamp() : null,
          rejectionReason: null,
        },
        // Backward-compatibility aliases
        displayName: fullName,
        id: fbUser.uid,
        username: fullName,
        full_name: fullName,
        approvedAt: isInitialAdmin ? serverTimestamp() : null,
        approvedBy: isInitialAdmin ? 'system_bootstrap' : null,
        institution_id: data.institution_id || organizationName,
        is_active: status === 'approved',
      };

      // 5. Save to Firestore users collection
      try {
        await setDoc(doc(db, 'users', fbUser.uid), userProfile);
        try {
          localStorage.setItem(`user_email_${fullName.toLowerCase()}`, email);
        } catch {}
      } catch (firestoreErr) {
        console.warn('Firestore user doc write error:', firestoreErr);
      }

      // Background local synchronization with backend API if accessible
      try {
        await apiClient.post('/auth/register', {
          name: fullName,
          full_name: fullName,
          email: email,
          password: password,
          role: role,
          institution_id: data.institution_id || organizationName,
        });
      } catch {
        // Non-blocking sync
      }

      return { success: true, email, username: fullName, userProfile };
    } catch (err: any) {
      throw new Error(formatAuthError(err));
    }
  },

  /**
   * Sign in using Firebase Authentication and fetch Firestore user document.
   * If status === 'rejected', sign out immediately and display declined message.
   */
  async login(credentials: LoginCredentials): Promise<TokenResponse> {
    const rawIdentifier = credentials.email || credentials.username || '';
    if (!rawIdentifier.trim()) {
      throw new Error('Please enter your corporate or institutional email');
    }
    const resolvedEmail = await this.resolveEmail(rawIdentifier);

    if (!resolvedEmail.includes('@')) {
      throw new Error(`Email "${rawIdentifier}" was not found. Please sign in using your registered institutional email.`);
    }

    let fbUser: FirebaseUser | null = null;

    try {
      const userCredential = await signInWithEmailAndPassword(auth, resolvedEmail, credentials.password);
      fbUser = userCredential.user;
    } catch (fbErr: any) {
      const code = fbErr?.code;
      // Fallback for backend seeded users if any
      if (
        code === 'auth/user-not-found' ||
        code === 'auth/invalid-credential' ||
        code === 'auth/invalid-login-credentials' ||
        code === 'auth/wrong-password'
      ) {
        try {
          const res = await apiClient.post<TokenResponse>('/auth/login', {
            email: resolvedEmail,
            password: credentials.password,
          });
          const tokenData = res.data;
          localStorage.setItem('access_token', tokenData.access_token);
          if (tokenData.refresh_token) {
            localStorage.setItem('refresh_token', tokenData.refresh_token);
          }
          return tokenData;
        } catch {
          throw new Error('Invalid username/email or password.');
        }
      }
      throw new Error(formatAuthError(fbErr));
    }

    if (!fbUser) {
      throw new Error('Authentication failed.');
    }

    // Fetch User Profile from Firestore
    const profile = await this.getUserProfile(fbUser.uid, fbUser);

    // Gating check: Rejected users
    if (profile.status === 'rejected') {
      await signOut(auth);
      this.clearTokens();
      const reason = profile.approvalMetadata?.rejectionReason;
      throw new Error(
        reason
          ? `Account registration request declined: ${reason}`
          : 'Account registration request declined by administrator.'
      );
    }

    const idToken = await fbUser.getIdToken(true);
    const refreshToken = fbUser.refreshToken || '';

    localStorage.setItem('access_token', idToken);
    localStorage.setItem('refresh_token', refreshToken);

    return {
      access_token: idToken,
      refresh_token: refreshToken,
      token_type: 'bearer',
      expires_in: 3600,
      user: profile,
    };
  },

  /**
   * Retrieve user profile from Firestore `users/{uid}`.
   * Auto-bootstraps document if missing.
   */
  async getUserProfile(uid: string, fbUser?: FirebaseUser | null): Promise<UserProfile> {
    const userDocRef = doc(db, 'users', uid);
    try {
      const userSnap = await getDoc(userDocRef);
      if (userSnap.exists()) {
        const data = userSnap.data();
        const role: UserRole = data.role === 'admin' ? 'admin' : (data.role === 'user' ? 'user' : 'verifier');
        const status: UserStatus = data.status || (role === 'admin' ? 'approved' : 'pending');
        const fullName = data.fullName || data.displayName || data.username || data.full_name || fbUser?.displayName || 'Institutional Verifier';

        return {
          uid: uid,
          id: uid,
          fullName: fullName,
          email: data.email || fbUser?.email || '',
          organizationType: data.organizationType || 'CORPORATE_HIRING',
          organizationName: data.organizationName || data.institution_id || 'Enterprise Organization',
          designation: data.designation || 'Verification Specialist',
          officialIdentifier: data.officialIdentifier || 'EMP-UNKNOWN',
          role: role,
          status: status,
          createdAt: data.createdAt,
          approvalMetadata: data.approvalMetadata || {
            reviewedBy: data.approvedBy || null,
            reviewedAt: data.approvedAt || null,
            rejectionReason: null,
          },
          displayName: fullName,
          approvedAt: data.approvedAt || data.approvalMetadata?.reviewedAt || null,
          approvedBy: data.approvedBy || data.approvalMetadata?.reviewedBy || null,
          username: data.username || fullName,
          full_name: fullName,
          is_active: status === 'approved',
          institution_id: data.organizationName || data.institution_id || null,
        };
      }
    } catch (err) {
      console.warn('Error reading Firestore user profile:', err);
    }

    // Fallback: Bootstrap document
    const userEmail = fbUser?.email || '';
    const isInitialAdmin = isDesignatedAdminEmail(userEmail);
    const role: UserRole = isInitialAdmin ? 'admin' : 'verifier';
    const status: UserStatus = isInitialAdmin ? 'approved' : 'pending';
    const fullName = fbUser?.displayName || (userEmail ? userEmail.split('@')[0] : 'Institutional Verifier');

    const newProfile: UserProfile = {
      uid: uid,
      id: uid,
      fullName: fullName,
      email: userEmail,
      organizationType: isInitialAdmin ? 'ACADEMIC_INSTITUTION' : 'CORPORATE_HIRING',
      organizationName: isInitialAdmin ? 'Visvesvaraya Technological University' : 'Partner Enterprise',
      designation: isInitialAdmin ? 'Platform Administrator' : 'Lead Recruiter',
      officialIdentifier: isInitialAdmin ? 'ADMIN-ROOT' : 'EMP-PENDING',
      role: role,
      status: status,
      createdAt: serverTimestamp(),
      approvalMetadata: {
        reviewedBy: isInitialAdmin ? 'system_bootstrap' : null,
        reviewedAt: isInitialAdmin ? serverTimestamp() : null,
        rejectionReason: null,
      },
      displayName: fullName,
      username: fullName,
      full_name: fullName,
      is_active: status === 'approved',
      approvedAt: isInitialAdmin ? serverTimestamp() : null,
      approvedBy: isInitialAdmin ? 'system_bootstrap' : null,
      institution_id: null,
    };

    try {
      await setDoc(userDocRef, newProfile, { merge: true });
    } catch (setErr) {
      console.warn('Could not bootstrap user doc in Firestore:', setErr);
    }

    return newProfile;
  },

  /**
   * Legacy alias for getUserProfile.
   */
  async getProfileForUid(uid: string, fbUser?: FirebaseUser | null): Promise<UserProfile> {
    return this.getUserProfile(uid, fbUser);
  },

  /**
   * Get current authenticated user profile.
   */
  async getProfile(): Promise<UserProfile> {
    await auth.authStateReady();
    const fbUser = auth.currentUser;
    if (fbUser) {
      return this.getUserProfile(fbUser.uid, fbUser);
    }
    throw new Error('Not authenticated');
  },

  /**
   * Approve a pending user account with review metadata (Admin Action).
   */
  async approveUser(targetUid: string, adminUid: string): Promise<void> {
    const userRef = doc(db, 'users', targetUid);
    await updateDoc(userRef, {
      status: 'approved',
      'approvalMetadata.reviewedBy': adminUid,
      'approvalMetadata.reviewedAt': serverTimestamp(),
      'approvalMetadata.rejectionReason': null,
      approvedAt: serverTimestamp(),
      approvedBy: adminUid,
      is_active: true,
    });
  },

  /**
   * Reject a user account with optional rejection reason (Admin Action).
   */
  async rejectUser(targetUid: string, adminUid: string, rejectionReason?: string): Promise<void> {
    const userRef = doc(db, 'users', targetUid);
    await updateDoc(userRef, {
      status: 'rejected',
      'approvalMetadata.reviewedBy': adminUid,
      'approvalMetadata.reviewedAt': serverTimestamp(),
      'approvalMetadata.rejectionReason': rejectionReason || 'Institutional credentials could not be verified by administrator.',
      approvedAt: null,
      approvedBy: adminUid,
      is_active: false,
    });
  },

  /**
   * Update a user's role (Admin Action: Promote to Admin / Demote to Verifier).
   */
  async updateUserRole(targetUid: string, newRole: UserRole): Promise<void> {
    const userRef = doc(db, 'users', targetUid);
    await updateDoc(userRef, {
      role: newRole,
    });
  },

  /**
   * Subscribe to real-time updates for all organization users (Admin Dashboard).
   */
  subscribeToUsers(callback: (users: UserProfile[]) => void): () => void {
    const usersCollection = collection(db, 'users');

    const mapDocs = (docs: any[]): UserProfile[] => {
      return docs.map((d) => {
        const data = d.data();
        const role: UserRole = data.role === 'admin' ? 'admin' : (data.role === 'user' ? 'user' : 'verifier');
        const status: UserStatus = data.status || (role === 'admin' ? 'approved' : 'pending');
        const fullName = data.fullName || data.displayName || data.username || data.full_name || 'Candidate';
        return {
          uid: d.id,
          id: d.id,
          fullName: fullName,
          email: data.email || '',
          organizationType: data.organizationType || 'CORPORATE_HIRING',
          organizationName: data.organizationName || data.institution_id || 'Enterprise Organization',
          designation: data.designation || 'Verification Specialist',
          officialIdentifier: data.officialIdentifier || 'EMP-UNKNOWN',
          role: role,
          status: status,
          createdAt: data.createdAt,
          approvalMetadata: data.approvalMetadata || {
            reviewedBy: data.approvedBy || null,
            reviewedAt: data.approvedAt || null,
            rejectionReason: null,
          },
          displayName: fullName,
          approvedAt: data.approvedAt || data.approvalMetadata?.reviewedAt || null,
          approvedBy: data.approvedBy || data.approvalMetadata?.reviewedBy || null,
          username: data.username || fullName,
          full_name: fullName,
          is_active: status === 'approved',
          institution_id: data.organizationName || data.institution_id || null,
        } as UserProfile;
      });
    };

    try {
      const q = query(usersCollection, orderBy('createdAt', 'desc'));
      return onSnapshot(
        q,
        (snapshot) => {
          callback(mapDocs(snapshot.docs));
        },
        (err) => {
          console.warn('[subscribeToUsers] Index fallback listening without ordering:', err);
          return onSnapshot(usersCollection, (snap) => {
            callback(mapDocs(snap.docs));
          });
        }
      );
    } catch {
      return onSnapshot(usersCollection, (snap) => {
        callback(mapDocs(snap.docs));
      });
    }
  },

  /**
   * Sign out current user.
   */
  async logout(): Promise<void> {
    try {
      await signOut(auth);
    } finally {
      this.clearTokens();
    }
  },

  /**
   * Send password reset email via Firebase Auth.
   */
  async resetPassword(email: string): Promise<void> {
    try {
      await sendPasswordResetEmail(auth, email.trim());
    } catch (err: any) {
      throw new Error(formatAuthError(err));
    }
  },

  /**
   * Resend email verification link.
   */
  async resendVerificationEmail(identifier: string, password?: string): Promise<void> {
    try {
      const resolvedEmail = await this.resolveEmail(identifier);
      if (!password) {
        throw new Error('Password is required to resend verification email.');
      }
      const userCredential = await signInWithEmailAndPassword(auth, resolvedEmail, password);
      await sendEmailVerification(userCredential.user);
      await signOut(auth);
    } catch (err: any) {
      throw new Error(formatAuthError(err));
    }
  },

  isAuthenticated(): boolean {
    return !!(auth.currentUser || localStorage.getItem('access_token'));
  },

  clearTokens(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },
};
