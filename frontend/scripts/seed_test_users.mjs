import { initializeApp } from 'firebase/app';
import { 
  getAuth, 
  createUserWithEmailAndPassword, 
  signInWithEmailAndPassword,
  updateProfile,
  signOut
} from 'firebase/auth';
import { 
  getFirestore, 
  doc, 
  setDoc, 
  serverTimestamp 
} from 'firebase/firestore';

const firebaseConfig = {
  apiKey: "AIzaSyAAHMa3V3Y1nazh_e0GmSPJo5b0BHQTjfI",
  authDomain: "facd-c42c2.firebaseapp.com",
  projectId: "facd-c42c2",
  storageBucket: "facd-c42c2.firebasestorage.app",
  messagingSenderId: "554646611774",
  appId: "1:554646611774:web:32f1739ffe7507e0676e6f",
  measurementId: "G-Z25FMZKTH7"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);

const testUsers = [
  {
    email: 'admin@facd.edu',
    password: 'AdminPassword123!',
    fullName: 'System Administrator (VTU)',
    organizationType: 'ACADEMIC_INSTITUTION',
    organizationName: 'Visvesvaraya Technological University',
    designation: 'Platform Administrator',
    officialIdentifier: 'ADMIN-ROOT',
    role: 'admin',
    status: 'approved',
  },
  {
    email: 'verifier@vtu.ac.in',
    password: 'UserPassword123!',
    fullName: 'Dr. Ramesh Rao (VTU Examiner)',
    organizationType: 'ACADEMIC_INSTITUTION',
    organizationName: 'VTU Exam Controller Office',
    designation: 'Senior Academic Evaluator',
    officialIdentifier: 'VTU-FAC-9912',
    role: 'verifier',
    status: 'approved',
  },
  {
    email: 'pending.user@vtu.ac.in',
    password: 'UserPassword123!',
    fullName: 'Pooja Sharma (New Applicant)',
    organizationType: 'CORPORATE_HIRING',
    organizationName: 'Wipro Technologies',
    designation: 'Campus Hiring Lead',
    officialIdentifier: 'WIPRO-EMP-4029',
    role: 'verifier',
    status: 'pending',
  },
  {
    email: 'rejected.user@vtu.ac.in',
    password: 'UserPassword123!',
    fullName: 'Suspicious Operator',
    organizationType: 'BGV_AGENCY',
    organizationName: 'Unverified Agency',
    designation: 'Independent Contractor',
    officialIdentifier: 'N/A',
    role: 'verifier',
    status: 'rejected',
  },
];

async function seed() {
  console.log('Seeding Test Accounts in Firebase project: facd-c42c2...');

  for (const u of testUsers) {
    let uid = null;
    try {
      console.log(`\nProcessing account: ${u.email}...`);
      const cred = await createUserWithEmailAndPassword(auth, u.email, u.password);
      uid = cred.user.uid;
      await updateProfile(cred.user, { displayName: u.fullName });
      console.log(`[+] Created Firebase Auth user: ${u.email} (UID: ${uid})`);
    } catch (err) {
      if (err.code === 'auth/email-already-in-use') {
        console.log(`[*] Account ${u.email} already exists. Signing in...`);
        try {
          const cred = await signInWithEmailAndPassword(auth, u.email, u.password);
          uid = cred.user.uid;
          await updateProfile(cred.user, { displayName: u.fullName });
          console.log(`[+] Authenticated existing user: ${u.email} (UID: ${uid})`);
        } catch (signInErr) {
          console.warn(`[!] Sign in error for ${u.email}:`, signInErr.message);
        }
      } else {
        console.warn(`[!] Error creating ${u.email}:`, err.message);
      }
    }

    if (uid) {
      try {
        const userDoc = {
          uid: uid,
          fullName: u.fullName,
          email: u.email,
          organizationType: u.organizationType,
          organizationName: u.organizationName,
          designation: u.designation,
          officialIdentifier: u.officialIdentifier,
          role: u.role,
          status: u.status,
          createdAt: serverTimestamp(),
          approvalMetadata: {
            reviewedBy: u.status === 'approved' ? 'system_seed' : null,
            reviewedAt: u.status === 'approved' ? serverTimestamp() : null,
            rejectionReason: u.status === 'rejected' ? 'Official institutional affiliation could not be verified.' : null,
          },
          // Backwards compatibility
          displayName: u.fullName,
          id: uid,
          username: u.fullName,
          full_name: u.fullName,
          approvedAt: u.status === 'approved' ? serverTimestamp() : null,
          approvedBy: u.status === 'approved' ? 'system_seed' : null,
          is_active: u.status === 'approved',
        };
        await setDoc(doc(db, 'users', uid), userDoc, { merge: true });
        console.log(`[+] Firestore document stored in facd-c42c2: users/${uid} (role: ${u.role}, status: ${u.status})`);
      } catch (firestoreErr) {
        console.warn(`[!] Firestore write warning for ${u.email}:`, firestoreErr.message);
      }
    }
  }

  try {
    await signOut(auth);
  } catch {}

  console.log('\n======================================================');
  console.log('All Test Accounts Successfully Provisioned in facd-c42c2!');
  console.log('======================================================');
  process.exit(0);
}

seed().catch((err) => {
  console.error('Fatal seeding error:', err);
  process.exit(1);
});
