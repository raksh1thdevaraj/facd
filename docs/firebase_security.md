# Firebase Security Architecture & Rule Enforcement

**Project:** AI-Based Detection of Fake or Manipulated Academic Certificates  
**Authority:** Strict Least Privilege & Tamper Resistance  

---

## 1. Security Architecture Principles

1. **Deny by Default:** Unauthenticated requests cannot read or write to any collection or storage path.
2. **Role Immutability:** Users cannot elevate their own role upon document creation or update. Only administrators can alter role claims.
3. **Verdict Immutability:** Forensic authenticity scores (`authenticityScore`, `fraudRiskScore`, `finalStatus`) cannot be modified by standard users.
4. **Storage Isolation:** Users can only write files to their assigned user path prefix (`/certificates/{userId}/*`). File sizes are constrained to 15MB maximum and restricted to approved MIME types (`application/pdf`, `image/png`, `image/jpeg`, `image/webp`).

---

## 2. Cloud Firestore Rules Breakdown

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    
    function isAuthenticated() {
      return request.auth != null;
    }
    function isOwner(userId) {
      return isAuthenticated() && request.auth.uid == userId;
    }
    function isAdmin() {
      return isAuthenticated() && (request.auth.token.role in ['ADMIN', 'admin']);
    }
    function isVerifier() {
      return isAuthenticated() && (
        request.auth.token.role in ['INSTITUTION_VERIFIER', 'ADMIN', 'verifier', 'admin']
      );
    }

    match /users/{userId} {
      allow read: if isOwner(userId) || isVerifier();
      allow create: if isOwner(userId) && (
        !('role' in request.resource.data) || 
        request.resource.data.role in ['PUBLIC_USER', 'user', 'student', 'guest'] ||
        isAdmin()
      );
      allow update: if (isOwner(userId) && request.resource.data.role == resource.data.role) || isAdmin();
      allow delete: if isAdmin();
    }

    match /certificates/{certId} {
      allow read: if isAuthenticated() && (
        resource.data.ownerId == request.auth.uid ||
        resource.data.userId == request.auth.uid ||
        isVerifier()
      );
      allow create: if isAuthenticated() && (
        request.resource.data.ownerId == request.auth.uid ||
        request.resource.data.userId == request.auth.uid
      );
      allow update: if isVerifier() || (
        isOwner(resource.data.ownerId) &&
        request.resource.data.authenticityScore == resource.data.authenticityScore &&
        request.resource.data.finalStatus == resource.data.finalStatus
      );
      allow delete: if isAdmin() || isOwner(resource.data.ownerId);
    }

    match /course_verifications/{verificationId} {
      allow read: if isAuthenticated() && (
        resource.data.userId == request.auth.uid ||
        resource.data.ownerId == request.auth.uid ||
        isVerifier()
      );
      allow write: if isVerifier();
    }

    match /audit_logs/{logId} {
      allow read: if isVerifier();
      allow write: if isVerifier();
    }
  }
}
```

---

## 3. Storage Rules Breakdown

```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    function isAuthenticated() {
      return request.auth != null;
    }
    function isOwner(userId) {
      return isAuthenticated() && request.auth.uid == userId;
    }
    function isVerifier() {
      return isAuthenticated() && (
        request.auth.token.role in ['INSTITUTION_VERIFIER', 'ADMIN', 'verifier', 'admin']
      );
    }

    match /certificates/{userId}/{allPaths=**} {
      allow read: if isOwner(userId) || isVerifier();
      allow write: if isOwner(userId)
                   && request.resource.size < 15 * 1024 * 1024
                   && (request.resource.contentType.matches('image/.*') || request.resource.contentType == 'application/pdf');
    }
  }
}
```
