import { initializeApp, getApps, getApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';
import { getStorage } from 'firebase/storage';

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "AIzaSyCaS1lqmIX1xqkXqPtptp6KjEdz8DbtW-E",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "facd.firebaseapp.com",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "facd",
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "facd.firebasestorage.app",
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "607869238844",
  appId: import.meta.env.VITE_FIREBASE_APP_ID || "1:607869238844:web:c68a96b8440f500075cd39",
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID || "G-2MSH58W09X"
};

// Initialize Firebase once
export const app = getApps().length > 0 ? getApp() : initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);
export const storage = getStorage(app);

export default app;
