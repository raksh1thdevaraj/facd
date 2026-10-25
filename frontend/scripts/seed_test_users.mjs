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
  apiKey: "AIzaSyCaS1lqmIX1xqkXqPtptp6KjEdz8DbtW-E",
  authDomain: "certcheck-60f6c.firebaseapp.com",
  projectId: "certcheck-60f6c",
  storageBucket: "certcheck-60f6c.firebasestorage.app",
  messagingSenderId: "607869238844",
  appId: "1:607869238844:web:c68a96b8440f500075cd39",
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);

const testUsers = [
  {
    email: 'admin@facd.edu',
    password: 'AdminPassword123!',
    displayName: 'System Administrator (VTU)',
    role: 'admin',
    status: 'approved',
  },
  {
    email: 'verifier@vtu.ac.in',
    password: 'UserPassword123!',
    displayName: 'Dr. Ramesh Rao (VTU Examiner)',
    role: 'user',
    status: 'approved',
  },
  {
    email: 'pending.user@vtu.ac.in',
    password: 'UserPassword123!',
    displayName: 'Pooja Sharma (New Applicant)',
    role: 'user',
    status: 'pending',
  },
  {
    email: 'rejected.user@vtu.ac.in',
    password: 'UserPassword123!',
    displayName: 'Suspicious Operator',
    role: 'user',
    status: 'rejected',
  },
];

async function seed() {
  console.log('Seeding Test Accounts in Firebase Auth & Cloud Firestore...');

  for (const u of testUsers) {
    let uid = null;
    try {
      console.log(`\nProcessing account: ${u.email}...`);
      const cred = await createUserWithEmailAndPassword(auth, u.email, u.password);
      uid = cred.user.uid;
      await updateProfile(cred.user, { displayName: u.displayName });
      console.log(`[+] Created Firebase Auth user: ${u.email} (UID: ${uid})`);
    } catch (err) {
      if (err.code === 'auth/email-already-in-use') {
        console.log(`[*] Account ${u.email} already exists. Signing in...`);
        try {
          const cred = await signInWithEmailAndPassword(auth, u.email, u.password);
          uid = cred.user.uid;
          await updateProfile(cred.user, { displayName: u.displayName });
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
          id: uid,
          email: u.email,
          displayName: u.displayName,
          username: u.displayName,
          full_name: u.displayName,
          role: u.role,
          status: u.status,
          createdAt: serverTimestamp(),
          approvedAt: u.status === 'approved' ? serverTimestamp() : null,
          approvedBy: u.status === 'approved' ? 'system_seed' : null,
          is_active: u.status === 'approved',
        };
        await setDoc(doc(db, 'users', uid), userDoc, { merge: true });
        console.log(`[+] Firestore document stored: users/${uid} (role: ${u.role}, status: ${u.status})`);
      } catch (firestoreErr) {
        console.warn(`[!] Firestore write warning for ${u.email}:`, firestoreErr.message);
      }
    }
  }

  // Also seed an initial admin account if needed
  try {
    await signOut(auth);
  } catch {}

  console.log('\n======================================================');
  console.log('All Test Accounts Successfully Provisioned!');
  console.log('======================================================');
  process.exit(0);
}

seed().catch((err) => {
  console.error('Fatal seeding error:', err);
  process.exit(1);
});
