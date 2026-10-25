import { initializeApp, getApps, getApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';
import { getStorage } from 'firebase/storage';

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "AIzaSyAAHMa3V3Y1nazh_e0GmSPJo5b0BHQTjfI",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "facd-c42c2.firebaseapp.com",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "facd-c42c2",
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "facd-c42c2.firebasestorage.app",
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "554646611774",
  appId: import.meta.env.VITE_FIREBASE_APP_ID || "1:554646611774:web:32f1739ffe7507e0676e6f",
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID || "G-Z25FMZKTH7"
};

// Initialize Firebase once
export const app = getApps().length > 0 ? getApp() : initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);
export const storage = getStorage(app);

export default app;
