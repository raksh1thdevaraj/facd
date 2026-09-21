import { 
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut,
  updateProfile,
  sendPasswordResetEmail,
  onAuthStateChanged,
  User as FirebaseUser
} from 'firebase/auth';
import { 
  doc, 
  getDoc, 
  setDoc, 
  collection, 
  query, 
  where, 
  getDocs,
  serverTimestamp 
} from 'firebase/firestore';
import { auth, db } from '../config/firebase';
import { LoginCredentials, RegisterData, TokenResponse, User, UserRole } from '../types/auth';
import { apiClient } from './api';

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
      return trimmed;
    }
    // Query Firestore users collection for matching username
    try {
      const q = query(collection(db, 'users'), where('username', '==', trimmed));
      const querySnapshot = await getDocs(q);
      if (!querySnapshot.empty) {
        const data = querySnapshot.docs[0].data();
        if (data.email) {
          return data.email;
        }
      }
    } catch {
      // Fallback to synthetic email if query fails
    }
    return `${trimmed}@example.com`;
  },

  /**
   * Sign in using Firebase Email/Password Authentication.
   */
  async login(credentials: LoginCredentials): Promise<TokenResponse> {
    const rawIdentifier = credentials.email || credentials.username || '';
    if (!rawIdentifier) {
      throw new Error('Please enter your email or username');
    }
    const resolvedEmail = await this.resolveEmail(rawIdentifier);
    const userCredential = await signInWithEmailAndPassword(auth, resolvedEmail, credentials.password);
    const fbUser = userCredential.user;
    const idToken = await fbUser.getIdToken(true);
    const refreshToken = fbUser.refreshToken || '';

    localStorage.setItem('access_token', idToken);
    localStorage.setItem('refresh_token', refreshToken);

    // Fetch user profile from Firestore
    let userProfile: User;
    try {
      userProfile = await this.getProfileForUid(fbUser.uid, fbUser);
    } catch {
      userProfile = {
        id: fbUser.uid,
        email: fbUser.email || resolvedEmail,
        username: fbUser.email?.split('@')[0] || 'user',
        full_name: fbUser.displayName || 'Forensic Analyst',
        role: 'PUBLIC_USER' as UserRole,
        institution_id: null,
        is_active: true,
        created_at: new Date().toISOString(),
      };
    }

    return {
      access_token: idToken,
      refresh_token: refreshToken,
      token_type: 'bearer',
      expires_in: 3600,
      user: userProfile,
    };
  },

  /**
   * Register a new user using Firebase Email/Password Auth & create a Firestore record.
   */
  async register(data: RegisterData): Promise<User> {
    const resolvedEmail = data.email.trim();
    const userCredential = await createUserWithEmailAndPassword(auth, resolvedEmail, data.password);
    const fbUser = userCredential.user;

    // Update display name
    if (data.full_name) {
      try {
        await updateProfile(fbUser, { displayName: data.full_name });
      } catch (err) {
        console.warn('Could not update Firebase displayName:', err);
      }
    }

    const assignedRole: UserRole = data.role || 'PUBLIC_USER';
    const username = data.username?.trim() || resolvedEmail.split('@')[0];

    const newUserDoc: User = {
      id: fbUser.uid,
      email: resolvedEmail,
      username,
      full_name: data.full_name || username,
      role: assignedRole,
      institution_id: data.institution_id || null,
      is_active: true,
      created_at: new Date().toISOString(),
    };

    // Save profile to Firestore users/{uid}
    try {
      const userRef = doc(db, 'users', fbUser.uid);
      await setDoc(userRef, {
        ...newUserDoc,
        createdAtServer: serverTimestamp(),
      });
    } catch (err) {
      console.error('Failed to create user record in Firestore:', err);
      // Even if firestore doc creation encounters rule delay, keep user profile
    }

    const idToken = await fbUser.getIdToken();
    localStorage.setItem('access_token', idToken);
    localStorage.setItem('refresh_token', fbUser.refreshToken || '');

    return newUserDoc;
  },

  /**
   * Retrieve the current user's profile from Firestore or Auth.
   */
  async getProfile(): Promise<User> {
    await auth.authStateReady();
    const fbUser = auth.currentUser;

    if (!fbUser) {
      const token = localStorage.getItem('access_token');
      if (!token) {
        throw new Error('Not authenticated');
      }
      // Fallback: ask backend API
      const res = await apiClient.get<User>('/auth/me');
      return res.data;
    }

    return this.getProfileForUid(fbUser.uid, fbUser);
  },

  /**
   * Internal helper to fetch user document by UID from Firestore.
   */
  async getProfileForUid(uid: string, fbUser?: FirebaseUser | null): Promise<User> {
    const userRef = doc(db, 'users', uid);
    const docSnap = await getDoc(userRef);

    if (docSnap.exists()) {
      const data = docSnap.data();
      return {
        id: uid,
        email: data.email || fbUser?.email || '',
        username: data.username || (data.email ? data.email.split('@')[0] : 'user'),
        full_name: data.full_name || fbUser?.displayName || 'Forensic Analyst',
        role: (data.role as UserRole) || 'PUBLIC_USER',
        institution_id: data.institution_id || null,
        is_active: data.is_active ?? true,
        created_at: data.created_at || new Date().toISOString(),
      };
    }

    // Default fallback from Firebase Auth User
    return {
      id: uid,
      email: fbUser?.email || '',
      username: fbUser?.email ? fbUser.email.split('@')[0] : 'user',
      full_name: fbUser?.displayName || 'Forensic Analyst',
      role: 'PUBLIC_USER',
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
    await sendPasswordResetEmail(auth, email);
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
