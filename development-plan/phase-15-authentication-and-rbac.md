# Phase 15 — Authentication & Role-Based Access Control (RBAC)

## 1. Purpose

Implement the authentication, authorization, and Role-Based Access Control (RBAC) security subsystem. This module provides secure user registration, credential hashing with bcrypt, stateless JSON Web Token (JWT) issuance (access tokens and refresh tokens), session lifecycle management, and fine-grained endpoint authorization enforcing three distinct user roles: **Admin**, **Institutional Verifier**, and **Public / Guest User**.

## 2. Why This Phase Exists

Academic certificate verification handles sensitive personally identifiable information (PII) of students, institutional trade secrets (confidential graduation records), and administrative controls:
- Public or unauthorized users must not be permitted to view confidential institutional student lists or tamper with official university certificate templates.
- Password hashes must be cryptographically protected against rainbow table and brute-force attacks using modern salted key-derivation functions (bcrypt).
- Stateless JWT authentication allows the frontend SPA and backend API to communicate securely across requests without server-side session memory bloat.
- Role-based permissions guarantee that only authorized University Registrars and System Administrators can register master templates or inspect full audit logs.

## 3. Requirements Covered

| Requirement | Description | Implementation in this Phase |
|---|---|---|
| **FR-USR-01** | User registration and authentication (JWT tokens, bcrypt password hashing) | Passlib/bcrypt hasher, OAuth2 password bearer flow, JWT token issuer |
| **FR-USR-02** | Role-Based Access Control (RBAC) for Admin, Institutional Verifier, and Public User | FastAPI permission dependencies (`require_role`, `require_admin`, etc.) |
| **FR-USR-03** | User profile management and active session tracking | Profile endpoints (`GET /api/v1/auth/me`, update profile, change password) |
| **FR-USR-04** | Token refresh and secure logout / session revocation | Refresh token rotation and Redis/memory token blocklist |
| **NFR-02** | Security & Credential Protection | Bcrypt cost factor 12, short-lived access tokens (15m), secure refresh tokens (7d) |
| **TC-USR-01** | User registration and password hashing test | Chip USR-11 |
| **TC-USR-02** | User login, JWT token issuance, and expiration test | Chip USR-11 |
| **TC-USR-03** | Role-based access enforcement test (Admin vs Verifier vs Public) | Chip USR-12 |
| **TC-USR-04** | Token refresh and revocation test | Chip USR-12 |
| **TC-USR-05** | Protected endpoint access rejection test (invalid/expired token) | Chip USR-12 |

## 4. Inputs

- User credentials from HTTP login/register requests (`email`, `password`, `full_name`, `institution_id`).
- Secret key and JWT parameters from environment variables (`SECRET_KEY`, `ALGORITHM = HS256`, `ACCESS_TOKEN_EXPIRE_MINUTES = 15`, `REFRESH_TOKEN_EXPIRE_DAYS = 7`).
- `app_user` database table from Phase 14.

## 5. Outputs

- Authenticated session response: `{"access_token": str, "refresh_token": str, "token_type": "bearer", "expires_in": int, "user": UserResponse}`.
- Reusable FastAPI authentication dependencies: `get_current_user`, `get_current_active_user`, `require_admin`, `require_institutional_verifier`.
- Database records in `app_user` table populated with salted bcrypt hashes.

## 6. Dependencies

- **Previous phases:** Phase 01 (Foundation), Phase 14 (Database Schema).
- **Libraries:** `passlib[bcrypt]`, `python-jose[cryptography]` (or `PyJWT`), `fastapi`, `pydantic`, `pytest`.

## 7. Files and Folder Structure

```
backend/
├── app/
│   ├── core/
│   │   ├── security.py                # Password hashing and JWT encoding/decoding
│   │   └── rbac.py                    # Role definitions and permission checks
│   ├── schemas/
│   │   ├── auth.py                    # Token, TokenData, LoginRequest schemas
│   │   └── user.py                    # UserCreate, UserUpdate, UserResponse schemas
│   ├── services/
│   │   └── auth_service.py            # Registration, authentication, token issuance
│   └── api/
│       ├── deps.py                    # Reusable FastAPI auth dependencies
│       └── v1/
│           └── endpoints/
│               └── auth.py            # /api/v1/auth endpoints
└── tests/
    └── integration/
        ├── test_auth_registration.py
        ├── test_jwt_tokens.py
        └── test_rbac_permissions.py
```

---

## 8. Implementation Chips

---

### CHIP USR-01 — Password Hashing & Salt Verification (Bcrypt)

**Objective:** Implement cryptographic password hashing using Passlib with bcrypt (work factor / cost = 12) to securely hash and verify user passwords (FR-USR-01, NFR-02).

**Why:** Passwords must never be stored in plaintext. Bcrypt with cost factor 12 provides high resistance against GPU-accelerated brute-force attacks while executing in ~100ms on server CPUs.

**Dependencies:** Phase 01 Foundation.

**Files to create:**
- `backend/app/core/security.py`

**Implementation:**
1. Configure Passlib `CryptContext`:
   ```python
   pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

   def get_password_hash(password: str) -> str:
       return pwd_context.hash(password)

   def verify_password(plain_password: str, hashed_password: str) -> bool:
       return pwd_context.verify(plain_password, hashed_password)
   ```
2. Implement password strength validation:
   - Minimum length: 8 characters.
   - At least 1 uppercase letter, 1 lowercase letter, 1 digit, 1 special character (`!@#$%^&*`).

**Acceptance Criteria:**
- Hashes passwords with salted bcrypt; verifies valid passwords; rejects invalid passwords (TC-USR-01).

---

### CHIP USR-02 — JWT Access & Refresh Token Encoding and Decoding

**Objective:** Implement stateless JSON Web Token (JWT) creation, signing, and verification using HMAC-SHA256 (`HS256`) with distinct expiry periods for access tokens (15 minutes) and refresh tokens (7 days) (FR-USR-01, NFR-02).

**Why:** Short-lived access tokens limit exposure if intercepted over the network; long-lived refresh tokens allow seamless background token rotation without forcing users to re-enter credentials constantly.

**Dependencies:** CHIP USR-01.

**Files to modify:**
- `backend/app/core/security.py`

**Implementation:**
1. Implement token encoders:
   ```python
   def create_access_token(subject: str, role: str, expires_delta: Optional[timedelta] = None) -> str:
       expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
       to_encode = {"sub": str(subject), "role": role, "type": "access", "exp": expire}
       return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

   def create_refresh_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
       expire = datetime.utcnow() + (expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))
       to_encode = {"sub": str(subject), "type": "refresh", "exp": expire, "jti": str(uuid.uuid4())}
       return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
   ```
2. Implement `decode_token(token: str) -> dict`:
   - Validates signature and expiration.
   - Raises `JWTError` or `TokenExpiredError` if invalid or expired.

**Acceptance Criteria:**
- Issues and decodes signed JWTs; rejects tampered or expired tokens (TC-USR-02, TC-USR-05).

---

### CHIP USR-03 — Role-Based Access Control (RBAC) Hierarchy & Permissions

**Objective:** Define the role hierarchy (`ADMIN`, `INSTITUTION_VERIFIER`, `PUBLIC_USER`) and specify granular permission mappings across system operations (FR-USR-02).

**Why:** Ensures clear security boundaries between administrative platform maintainers, authorized university registrars, and public guest users.

**Dependencies:** Phase 01 Foundation.

**Files to create:**
- `backend/app/core/rbac.py`

**Implementation:**
1. Define User Role Enum:
   ```python
   class UserRole(str, Enum):
       ADMIN = "ADMIN"
       INSTITUTION_VERIFIER = "INSTITUTION_VERIFIER"
       PUBLIC_USER = "PUBLIC_USER"
   ```
2. Define permission matrix:
   - **`ADMIN`:**
     - Full access to all certificates across all institutions.
     - Register, update, and deactivate institutions.
     - View complete system-wide audit logs (`GET /api/v1/audit-logs`).
     - Manage system users and roles.
   - **`INSTITUTION_VERIFIER` (University Registrar / Verifier):**
     - Upload certificates for verification.
     - Access verification history for their own institution (`institution_id`).
     - Register master templates for their own institution.
     - Bulk-upload student records for their own institution.
   - **`PUBLIC_USER`:**
     - Upload individual certificate for one-off verification.
     - View resulting verification report.
     - Verify reports via QR code verification endpoint.
     - No access to other users' certificates or institutional records.

**Acceptance Criteria:**
- Formal role hierarchy and permission checks strictly defined and documented.

---

### CHIP USR-04 — FastAPI Authentication & Authorization Dependencies

**Objective:** Implement FastAPI dependency injection functions (`get_current_user`, `require_role`, `require_admin`, `require_institution_access`) to protect endpoints declaratively (FR-USR-02).

**Why:** Declarative dependencies ensure endpoint security is enforced in a single, reusable line of code without boilerplate checks inside route handlers.

**Dependencies:** CHIP USR-02, CHIP USR-03, Phase 14 Database.

**Files to create:**
- `backend/app/api/deps.py`

**Implementation:**
1. Configure `OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")`.
2. Implement `get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> AppUser`:
   - Decode token, extract `sub` (user_id).
   - Fetch user from database: `db.get(AppUser, user_id)`.
   - If user not found or `not user.is_active`: raise HTTP 401 Unauthorized.
   - Return authenticated `AppUser`.
3. Implement `require_role(*allowed_roles: UserRole)`:
   ```python
   def require_role(*allowed_roles: UserRole):
       def role_checker(current_user: AppUser = Depends(get_current_user)) -> AppUser:
           if current_user.role not in allowed_roles:
               raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions for this operation.")
           return current_user
       return role_checker
   ```
4. Define convenience dependencies:
   - `require_admin = require_role(UserRole.ADMIN)`
   - `require_verifier = require_role(UserRole.ADMIN, UserRole.INSTITUTION_VERIFIER)`
5. Implement `get_optional_user` for public endpoints that can optionally associate uploads with logged-in users.

**Acceptance Criteria:**
- Enforces role requirements; returns HTTP 401 on missing/invalid token and HTTP 403 on insufficient role (TC-USR-03, TC-USR-05).

---

### CHIP USR-05 — Authentication Service & User Registration

**Objective:** Implement `AuthService` handling user registration, duplicate email checks, password hashing, and credentials verification (FR-USR-01).

**Why:** Encapsulates business logic for onboarding users and authenticating login attempts.

**Dependencies:** CHIP USR-01, CHIP USR-02.

**Files to create:**
- `backend/app/services/auth_service.py`
- `backend/app/schemas/user.py`

**Implementation:**
1. Implement `register_user(db: Session, user_in: UserCreate) -> AppUser`:
   - Verify email uniqueness: `SELECT * FROM app_user WHERE email = user_in.email`.
   - If exists, raise `DuplicateEmailError` (HTTP 409).
   - Hash password: `pwd_hash = get_password_hash(user_in.password)`.
   - Create and commit `AppUser` record.
   - Log audit event: `USER_REGISTERED`.
2. Implement `authenticate_user(db: Session, email: str, password: str) -> Optional[AppUser]`:
   - Query user by email.
   - Verify password hash via `verify_password`.
   - Return user or `None`.

**Acceptance Criteria:**
- Registers users with hashed passwords and rejects duplicate emails (TC-USR-01).

---

### CHIP USR-06 — Login and JWT Token Issuance Endpoints

**Objective:** Implement `POST /api/v1/auth/login` (OAuth2 password flow and JSON body) issuing access and refresh tokens, and `POST /api/v1/auth/register` (FR-USR-01).

**Why:** Standard authentication endpoints conforming to OpenAPI security specifications.

**Dependencies:** CHIP USR-04, CHIP USR-05.

**Files to create:**
- `backend/app/api/v1/endpoints/auth.py`
- `backend/app/schemas/auth.py`

**Implementation:**
1. `POST /api/v1/auth/login`:
   - Accepts `OAuth2PasswordRequestForm` or JSON `LoginRequest(email, password)`.
   - Authenticates credentials.
   - Generates access token (15m) and refresh token (7d).
   - Returns `TokenResponse` with tokens, role, and expiry timestamp.
   - Records audit log: `USER_LOGIN_SUCCESS`.
2. `POST /api/v1/auth/register`:
   - Accepts `UserCreate` schema.
   - Returns `UserResponse` with HTTP 201 Created.

**Acceptance Criteria:**
- Successfully authenticates valid credentials and returns JWT token pair (TC-USR-02).

---

### CHIP USR-07 — Refresh Token Rotation & Session Revocation

**Objective:** Implement `POST /api/v1/auth/refresh` to exchange a valid refresh token for a new access token, and `POST /api/v1/auth/logout` to revoke tokens (FR-USR-04).

**Why:** Allows users to maintain continuous sessions securely without exposing their password repeatedly.

**Dependencies:** CHIP USR-02.

**Files to modify:**
- `backend/app/api/v1/endpoints/auth.py`

**Implementation:**
1. `POST /api/v1/auth/refresh`:
   - Accepts `refresh_token` string.
   - Decodes token, verifies `type == "refresh"`.
   - Checks if refresh token ID (`jti`) is in revocation blocklist.
   - Fetches user; issues fresh access token and rotated refresh token.
2. `POST /api/v1/auth/logout`:
   - Accepts current tokens and adds refresh token `jti` to revocation blocklist (stored in memory / Redis with TTL matching token expiry).

**Acceptance Criteria:**
- Issues new access token on valid refresh token; rejects revoked tokens (TC-USR-04).

---

### CHIP USR-08 — User Profile & Password Change Endpoints

**Objective:** Implement `GET /api/v1/auth/me` to fetch current user profile and `POST /api/v1/auth/change-password` to update credentials (FR-USR-03).

**Why:** Allows authenticated users to view their account status and rotate their passwords securely.

**Dependencies:** CHIP USR-04.

**Files to modify:**
- `backend/app/api/v1/endpoints/auth.py`

**Implementation:**
1. `GET /api/v1/auth/me`:
   - Returns current user details, assigned role, and institution affiliation.
2. `POST /api/v1/auth/change-password`:
   - Requires `current_password` and `new_password`.
   - Verifies `current_password` before updating hash to `new_password`.
   - Revokes all existing refresh tokens for the user.

**Acceptance Criteria:**
- Returns profile and safely updates passwords.

---

### CHIP USR-09 — Initial Database Seeding Script (Admin & Sample Users)

**Objective:** Implement a database seeding script (`backend/scripts/seed_database.py`) to create default institutions, an initial Admin account, and sample Institutional Verifiers for local testing.

**Why:** Provides developers and automated testing environments with pre-configured accounts immediately upon setup.

**Dependencies:** CHIP USR-05.

**Files to create:**
- `backend/scripts/seed_database.py`

**Implementation:**
1. Seed default institutions:
   - "National Institute of Technology" (Code: `NIT01`)
   - "State Technical University" (Code: `STU02`)
2. Seed default users:
   - Admin: `admin@certverify.org` / `Admin@12345!` (Role: `ADMIN`)
   - Verifier: `verifier@nit.edu` / `Verifier@12345!` (Role: `INSTITUTION_VERIFIER`, Institution: `NIT01`)
   - Public: `student@example.com` / `Student@12345!` (Role: `PUBLIC_USER`)
3. Script is idempotent: skips user creation if email already exists in database.

**Acceptance Criteria:**
- Seeds default institutions and user accounts cleanly.

---

### CHIP USR-10 — Security Hardening & Rate Limiting on Auth Endpoints

**Objective:** Apply brute-force protection and IP-based rate limiting (5 failed login attempts per minute) on `/api/v1/auth/login` using `slowapi`.

**Why:** Prevents credential-stuffing and brute-force password guessing attacks against user accounts.

**Dependencies:** CHIP USR-06.

**Files to modify:**
- `backend/app/api/v1/endpoints/auth.py`

**Acceptance Criteria:**
- Blocks IP after 5 consecutive failed login attempts within 60 seconds with HTTP 429 Too Many Requests.

---

### CHIP USR-11 — Unit Tests: Registration, Hashing and Token Issuance

**Objective:** Test user registration, bcrypt password hashing, login token generation, and token expiration behavior (TC-USR-01, TC-USR-02).

**Dependencies:** CHIP USR-01, CHIP USR-02, CHIP USR-06.

**Files to create:**
- `backend/tests/integration/test_auth_registration.py`
- `backend/tests/integration/test_jwt_tokens.py`

**Implementation:**
1. Test `test_password_hashing_and_verification()`: Verify bcrypt hash verification and salted non-identity (TC-USR-01).
2. Test `test_user_registration_and_duplicate_rejection()`: Assert duplicate email returns HTTP 409 (TC-USR-01).
3. Test `test_valid_login_returns_jwt_tokens()`: Assert valid credentials return access and refresh tokens (TC-USR-02).
4. Test `test_token_decoding_and_expiration()`: Verify expired token raises 401 Unauthorized (TC-USR-02).

**Acceptance Criteria:**
- 100% test pass rate across registration and token generation tests.

---

### CHIP USR-12 — Unit Tests: RBAC Permissions and Token Revocation

**Objective:** Test role-based access enforcement (Admin vs Verifier vs Public) and token revocation / protected endpoint rejection (TC-USR-03, TC-USR-04, TC-USR-05).

**Dependencies:** CHIP USR-03, CHIP USR-04, CHIP USR-07.

**Files to create:**
- `backend/tests/integration/test_rbac_permissions.py`

**Implementation:**
1. Test `test_admin_endpoint_rejects_public_user()`: Public user accessing `/api/v1/audit-logs` returns HTTP 403 Forbidden (TC-USR-03).
2. Test `test_admin_endpoint_permits_admin()`: Admin user accessing `/api/v1/audit-logs` returns HTTP 200 (TC-USR-03).
3. Test `test_token_refresh_flow()`: Refresh token produces valid new access token (TC-USR-04).
4. Test `test_protected_endpoint_rejects_unauthenticated()`: Request without Bearer token returns HTTP 401 (TC-USR-05).

**Acceptance Criteria:**
- All RBAC permission and token revocation tests pass with correct HTTP status codes.

---

## 9. Implementation Order and Dependencies

```
CHIP USR-01 (Password Hashing / Bcrypt)
    ↓
CHIP USR-02 (JWT Token Issuance & Decoding)
    ↓
CHIP USR-03 (RBAC Role & Permission Matrix)
    ↓
CHIP USR-04 (FastAPI Auth Dependencies) ──┐
    ↓                                     │
CHIP USR-05 (Auth Service Logic)          │
    ↓                                     │
CHIP USR-06 (Login & Register Endpoints)  │
    ↓                                     │
CHIP USR-07 (Refresh & Revocation)        │
    ↓                                     │
CHIP USR-08 (Profile & Password Change) ◄─┘
    ↓
CHIP USR-09 (Database Seeding) & CHIP USR-10 (Rate Limiting)
    ↓
CHIP USR-11 & CHIP USR-12 (Unit & Integration Tests)
```

---

## 10. Phase Completion Checklist

- [ ] Bcrypt password hashing configured with cost factor 12.
- [ ] JWT tokens issued with 15-minute access expiry and 7-day refresh expiry.
- [ ] Three user roles implemented: `ADMIN`, `INSTITUTION_VERIFIER`, and `PUBLIC_USER`.
- [ ] Declarative FastAPI dependencies protect endpoints via `require_admin` and `require_verifier`.
- [ ] User registration, login, token refresh, and profile endpoints operational.
- [ ] Rate limiting prevents brute-force login attacks.
- [ ] Database seeding script creates initial Admin and Verifier accounts.
- [ ] Unauthorized requests return HTTP 401; forbidden role requests return HTTP 403.
- [ ] Test cases TC-USR-01 through TC-USR-05 passing with 100% success rate.
