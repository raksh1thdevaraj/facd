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
  collection, 
  getDocs,
  serverTimestamp
} from 'firebase/firestore';
import { auth, db } from '../config/firebase';
import { LoginCredentials, RegisterData, TokenResponse, User, UserRole } from '../types/auth';
import { apiClient } from './api';

/**
 * Format Firebase Auth and API errors into clear, user-friendly messages.
 */
export function formatAuthError(error: any): string {
  const code = error?.code || '';
  if (code === 'auth/email-already-in-use') {
    return 'An account with this email already exists.';
  }
  if (
    code === 'auth/user-not-found' ||
    code === 'auth/wrong-password' ||
    code === 'auth/invalid-credential' ||
    code === 'auth/invalid-login-credentials'
  ) {
    return 'Invalid username/email or password.';
  }
  if (code === 'auth/too-many-requests') {
    return 'Too many attempts. Please try again in a few minutes.';
  }
  if (code === 'auth/weak-password') {
    return 'Password should be at least 6 characters.';
  }
  if (code === 'auth/invalid-email') {
    return 'Please enter a valid email address.';
  }
  return error?.message || 'Authentication failed. Please check credentials.';
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

    // 1. Check local storage cache first
    const cacheKey = `user_email_${trimmed.toLowerCase()}`;
    try {
      const cached = localStorage.getItem(cacheKey);
      if (cached && cached.includes('@')) {
        return cached.trim().toLowerCase();
      }
    } catch {
      // Local storage not available
    }

    // 2. Query Firestore users collection for matching username
    try {
      const snap = await getDocs(collection(db, 'users'));
      for (const d of snap.docs) {
        const data = d.data();
        const u = data.username ? String(data.username).trim() : '';
        const uLower = data.username_lower ? String(data.username_lower).trim().toLowerCase() : u.toLowerCase();
        if (uLower === trimmed.toLowerCase() || u.toLowerCase() === trimmed.toLowerCase()) {
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

    // 3. Fallback for known accounts/aliases
    if (trimmed.toLowerCase() === 'admin') {
      return 'admin@certishield.ai';
    }
    if (trimmed.toLowerCase() === 'rakshith') {
      return 'rakshithdevaraj2005@gmail.com';
    }
    if (trimmed.toLowerCase() === 'raksh') {
      return 'saviourlordking@gmail.com';
    }

    return trimmed;
  },

  /**
   * Register a new user with Firebase email verification.
   * Creates Firebase user, updates display name, creates Firestore document with emailVerified: false,
   * sends verification email, and immediately signs out until confirmed.
   */
  async register(data: RegisterData): Promise<{ success: boolean; email: string; username: string }> {
    const email = data.email.trim().toLowerCase();
    const username = (data.username || data.name || email.split('@')[0]).trim();
    const password = data.password;

    try {
      // 1. Create account
      const userCredential = await createUserWithEmailAndPassword(auth, email, password);
      const user = userCredential.user;

      // 2. Set the display username
      await updateProfile(user, { displayName: username });

      // 3. Store user record in Firestore (with lowercase index and cache)
      try {
        await setDoc(doc(db, 'users', user.uid), {
          username: username,
          username_lower: username.toLowerCase(),
          email: email,
          role: 'user',
          createdAt: serverTimestamp(),
          emailVerified: false,
        });
        try {
          localStorage.setItem(`user_email_${username.toLowerCase()}`, email);
        } catch {}
      } catch (firestoreErr) {
        console.warn('Firestore user doc write restricted by security rules:', firestoreErr);
      }

      // 4. Send Firebase verification email
      await sendEmailVerification(user);

      // 5. Sign out immediately until email is confirmed
      await signOut(auth);

      // Background local synchronization with backend API if accessible
      try {
        await apiClient.post('/auth/register', {
          name: username,
          full_name: username,
          email: email,
          password: password,
          role: 'user',
          institution_id: data.institution_id || null,
        });
      } catch {
        // Non-blocking sync
      }

      return { success: true, email, username };
    } catch (err: any) {
      throw new Error(formatAuthError(err));
    }
  },

  /**
   * Sign in using Firebase Authentication with email verification check and automatic role detection.
   * Fallback to Backend JWT API for local seeded system accounts (e.g. admin@certishield.ai).
   */
  async login(credentials: LoginCredentials): Promise<TokenResponse> {
    const rawIdentifier = credentials.email || credentials.username || '';
    if (!rawIdentifier.trim()) {
      throw new Error('Please enter your email or username');
    }
    const resolvedEmail = await this.resolveEmail(rawIdentifier);

    // If identifier was a username that could not be resolved
    if (!resolvedEmail.includes('@')) {
      throw new Error(`Username "${rawIdentifier}" was not found. Please sign in using your email address.`);
    }

    // 1. Authenticate credentials via Firebase Auth
    let fbUser: FirebaseUser | null = null;
    let authError: any = null;

    try {
      const userCredential = await signInWithEmailAndPassword(auth, resolvedEmail, credentials.password);
      fbUser = userCredential.user;
    } catch (fbErr: any) {
      console.warn('[Firebase Login Auth Error]', fbErr?.code, fbErr?.message, 'for email:', resolvedEmail);
      authError = fbErr;
      const code = fbErr?.code;

      // If user is not found in Firebase or invalid credential, try FastAPI backend
      // (supports seeded local admin like admin@certishield.ai)
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
          const roleStr = String(tokenData.user.role || '').toLowerCase();
          tokenData.user.role = roleStr === 'admin' ? 'admin' : 'user';
          return tokenData;
        } catch {
          throw new Error('Invalid username/email or password.');
        }
      }
      throw new Error(formatAuthError(fbErr));
    }

    if (!fbUser) {
      throw new Error(formatAuthError(authError));
    }

    // 2. Refresh user to ensure latest emailVerified status from Firebase servers
    try {
      await fbUser.reload();
    } catch {
      // Non-fatal if reload fails
    }

    // Email verification guard
    if (!fbUser.emailVerified) {
      await signOut(auth);
      throw new Error('Email not verified. Please verify your email using the link sent to your inbox before signing in.');
    }

    // 3. Automatic role detection via Firestore and custom claims
    let detectedRole: UserRole = 'user';
    try {
      const tokenResult = await fbUser.getIdTokenResult();
      if (
        tokenResult.claims.admin === true ||
        fbUser.email?.toLowerCase().includes('admin@')
      ) {
        detectedRole = 'admin';
      } else {
        try {
          const adminDoc = await getDoc(doc(db, 'admins', fbUser.uid));
          if (adminDoc.exists()) {
            detectedRole = 'admin';
          }
        } catch {
          // Ignore if admins collection query is restricted
        }

        try {
          const userDoc = await getDoc(doc(db, 'users', fbUser.uid));
          if (userDoc.exists() && userDoc.data()?.role === 'admin') {
            detectedRole = 'admin';
          }
        } catch {
          // Ignore if users doc query is restricted
        }
      }
    } catch {
      // Default to user role
    }

    const idToken = await fbUser.getIdToken(true);
    const refreshToken = fbUser.refreshToken || '';

    localStorage.setItem('access_token', idToken);
    localStorage.setItem('refresh_token', refreshToken);

    const userProfile: User = {
      id: fbUser.uid,
      email: fbUser.email || resolvedEmail,
      username: fbUser.displayName || (fbUser.email ? fbUser.email.split('@')[0] : 'user'),
      full_name: fbUser.displayName || (detectedRole === 'admin' ? 'System Administrator' : 'Verified User'),
      role: detectedRole,
      institution_id: null,
      is_active: true,
      created_at: new Date().toISOString(),
    };

    return {
      access_token: idToken,
      refresh_token: refreshToken,
      token_type: 'bearer',
      expires_in: 3600,
      user: userProfile,
    };
  },

  /**
   * Resend Firebase email verification link to user.
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

  /**
   * Retrieve the current user's profile from Backend API or Firebase.
   */
  async getProfile(): Promise<User> {
    const token = localStorage.getItem('access_token');
    if (token) {
      try {
        const res = await apiClient.get<User>('/auth/me');
        const user = res.data;
        user.role = String(user.role).toLowerCase() === 'admin' ? 'admin' : 'user';
        return user;
      } catch {
        // Fallback to Firebase
      }
    }

    await auth.authStateReady();
    const fbUser = auth.currentUser;
    if (fbUser) {
      return this.getProfileForUid(fbUser.uid, fbUser);
    }

    throw new Error('Not authenticated');
  },

  /**
   * Internal helper to fetch user document by UID from Firestore.
   */
  async getProfileForUid(uid: string, fbUser?: FirebaseUser | null): Promise<User> {
    let role: UserRole = 'user';
    try {
      const tokenResult = fbUser ? await fbUser.getIdTokenResult() : null;
      if (
        tokenResult?.claims?.admin === true ||
        fbUser?.email?.toLowerCase().includes('admin@')
      ) {
        role = 'admin';
      }

      try {
        const adminDoc = await getDoc(doc(db, 'admins', uid));
        if (adminDoc.exists()) {
          role = 'admin';
        }
      } catch {
        // Ignore if admins collection is restricted
      }

      try {
        const userDoc = await getDoc(doc(db, 'users', uid));
        if (userDoc.exists()) {
          const data = userDoc.data();
          if (data.role === 'admin') {
            role = 'admin';
          }
          return {
            id: uid,
            email: data.email || fbUser?.email || '',
            username: data.username || (data.email ? data.email.split('@')[0] : 'user'),
            full_name: data.full_name || fbUser?.displayName || (role === 'admin' ? 'System Administrator' : 'Verified User'),
            role: role,
            institution_id: data.institution_id || null,
            is_active: data.is_active ?? true,
            created_at: data.created_at?.toDate ? data.created_at.toDate().toISOString() : (data.created_at || new Date().toISOString()),
          };
        }
      } catch {
        // Ignore if user doc is restricted
      }
    } catch {
      // Fallback
    }

    return {
      id: uid,
      email: fbUser?.email || '',
      username: fbUser?.displayName || (fbUser?.email ? fbUser.email.split('@')[0] : 'user'),
      full_name: fbUser?.displayName || (role === 'admin' ? 'System Administrator' : 'Verified User'),
      role: role,
      institution_id: null,
      is_active: true,
      created_at: new Date().toISOString(),
    };
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

  async changePassword(current_password: string, new_password: string): Promise<void> {
    await apiClient.post('/auth/change-password', {
      current_password,
      new_password,
    });
  },

  isAuthenticated(): boolean {
    return !!(auth.currentUser || localStorage.getItem('access_token'));
  },

  clearTokens(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },
};
