# Firebase Integration & Setup Guide

**Project:** AI-Based Detection of Fake or Manipulated Academic Certificates  
**Firebase Project ID:** `certcheck-60f6c`  
**Firebase Web App ID:** `1:607869238844:web:c68a96b8440f500075cd39`  
**Storage Bucket:** `certcheck-60f6c.firebasestorage.app`  

---

## 1. Overview

This project has been migrated to utilize Google Firebase for:
1. **Authentication**: Firebase Authentication with Email/Password sign-in, token refresh, and password reset.
2. **Database**: Cloud Firestore storing user profiles, academic certificates, course verifications, and audit logs.
3. **File Storage**: Firebase Cloud Storage with rule-guarded user directories for tamper-proof certificate uploads.

---

## 2. Firebase Configuration Details

### Frontend (`frontend/.env`)
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_FIREBASE_API_KEY=AIzaSyCaS1lqmIX1xqkXqPtptp6KjEdz8DbtW-E
VITE_FIREBASE_AUTH_DOMAIN=certcheck-60f6c.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=certcheck-60f6c
VITE_FIREBASE_STORAGE_BUCKET=certcheck-60f6c.firebasestorage.app
VITE_FIREBASE_MESSAGING_SENDER_ID=607869238844
VITE_FIREBASE_APP_ID=1:607869238844:web:c68a96b8440f500075cd39
VITE_FIREBASE_MEASUREMENT_ID=G-2MSH58W09X
```

### Backend (`.env`)
```env
FIREBASE_PROJECT_ID=certcheck-60f6c
FIREBASE_APP_ID=1:607869238844:web:c68a96b8440f500075cd39
FIREBASE_STORAGE_BUCKET=certcheck-60f6c.firebasestorage.app
FIREBASE_CREDENTIALS_PATH=
USE_FIREBASE_AUTH=True
USE_FIRESTORE=True
```

---

## 3. CLI Commands & Management

In accordance with official Firebase Agent skills, always invoke the Firebase CLI via `npx`:

```bash
# Check active project
npx -y firebase-tools@latest use certcheck-60f6c

# Deploy authentication configuration (Email/Password)
npx -y firebase-tools@latest deploy --only auth

# Deploy Firestore Security Rules & Indexes
npx -y firebase-tools@latest deploy --only firestore

# Deploy Cloud Storage Security Rules
npx -y firebase-tools@latest deploy --only storage
```

---

## 4. Enabling Cloud Firestore in Google Cloud Console

If Cloud Firestore was not previously activated on the project `certcheck-60f6c`, enable it with a single click:
1. Visit: [Firebase Console Database](https://console.firebase.google.com/project/certcheck-60f6c/firestore)
2. Click **Create Database**.
3. Select Database location (e.g., `nam5 (us-central)` or `asia-south1`) and Mode: **Production mode** (our `firestore.rules` will automatically safeguard all collections).
4. Run `npx -y firebase-tools@latest deploy --only firestore`.
