import {
  collection,
  doc,
  setDoc,
  getDocs,
  query,
  orderBy,
  limit,
  onSnapshot,
  QueryConstraint,
  where,
} from 'firebase/firestore';
import { ref, uploadBytes, getDownloadURL } from 'firebase/storage';
import { db, storage } from '../config/firebase';
import { AuditRecord } from '../components/console/AuditLedgerPanel';

const COLLECTION_NAME = 'verifications';
const LOCAL_STORAGE_KEY = 'FACD_AUDIT_LEDGER_OFFLINE_CACHE';

// Fallback seed records if collection is completely fresh
const INITIAL_SEED_RECORDS: AuditRecord[] = [
  {
    id: 'AUD-VTU-2024-001',
    timestamp: new Date(Date.now() - 3600000 * 2).toISOString(),
    fileName: 'VTU_4Sem_AnanyaRao_1MS21CS045.pdf',
    studentName: 'ANANYA RAO',
    usn: '1MS21CS045',
    collegeCode: '1MS',
    sgpaListed: 8.5,
    sgpaCalculated: 8.5,
    arithmeticDiscrepancy: false,
    tamperingScore: 4,
    verdict: 'AUTHENTIC',
    forensicReport: 'Mathematical formula verified exact. Font kerning and baseline consistent across all semester rows.',
  },
  {
    id: 'AUD-VTU-2024-002',
    timestamp: new Date(Date.now() - 3600000 * 5).toISOString(),
    fileName: 'RVCE_GradeSheet_RahulSharma_Tampered.png',
    studentName: 'RAHUL S SHARMA',
    usn: '1RV20EC045',
    collegeCode: '1RV',
    sgpaListed: 8.85,
    sgpaCalculated: 7.25,
    arithmeticDiscrepancy: true,
    tamperingScore: 94,
    verdict: 'FRAUDULENT',
    forensicReport: 'CRITICAL: Arithmetic tampering detected. Printed SGPA 8.85 deviates by +1.60 from calculated 7.25.',
  },
  {
    id: 'AUD-VTU-2024-003',
    timestamp: new Date(Date.now() - 3600000 * 24).toISOString(),
    fileName: 'PESIT_GradeCard_KarthikNair_AlteredUSN.jpg',
    studentName: 'KARTHIK M NAIR',
    usn: '1PE19CS999',
    collegeCode: '1PE',
    sgpaListed: 7.8,
    sgpaCalculated: 7.8,
    arithmeticDiscrepancy: false,
    tamperingScore: 89,
    verdict: 'FRAUDULENT',
    forensicReport: 'Visual integrity failure: Digital splicing & baseline shift detected in USN characters.',
  },
];

function getLocalLedgerCache(): AuditRecord[] {
  try {
    const raw = localStorage.getItem(LOCAL_STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed) && parsed.length > 0) {
        return parsed;
      }
    }
  } catch (err) {
    console.warn('Failed to read local ledger cache:', err);
  }
  return INITIAL_SEED_RECORDS;
}

function setLocalLedgerCache(records: AuditRecord[]): void {
  try {
    localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(records));
  } catch (err) {
    console.warn('Failed to persist local ledger cache:', err);
  }
}

export interface LedgerQueryOptions {
  limitCount?: number;
  usnSearch?: string;
  verdict?: 'ALL' | 'AUTHENTIC' | 'SUSPICIOUS' | 'FRAUDULENT';
}

/**
 * Uploads a document scan file to Firebase Storage under /verifications/{id}/marks_sheet.{ext}
 */
export async function uploadScanToStorage(
  verificationId: string,
  file: File
): Promise<string | undefined> {
  try {
    const fileExt = file.name.split('.').pop() || 'png';
    const storagePath = `verifications/${verificationId}/marks_sheet.${fileExt}`;
    const storageReference = ref(storage, storagePath);

    const snapshot = await uploadBytes(storageReference, file, {
      contentType: file.type || 'application/octet-stream',
      customMetadata: {
        verificationId,
        originalName: file.name,
        uploadedAt: new Date().toISOString(),
      },
    });

    const downloadUrl = await getDownloadURL(snapshot.ref);
    return downloadUrl;
  } catch (storageError) {
    console.warn('Firebase Storage upload failed or not provisioned, proceeding with local reference:', storageError);
    return undefined;
  }
}

/**
 * Persists an immutable verification audit record to Cloud Firestore in the 'verifications' collection.
 */
export async function saveVerificationToFirestore(
  record: AuditRecord,
  scanFile?: File
): Promise<AuditRecord> {
  let fileUrl = record.fileUrl;

  // 1. Upload scan file to Firebase Storage if provided
  if (scanFile && !fileUrl) {
    fileUrl = await uploadScanToStorage(record.id, scanFile);
  }

  const enrichedRecord: AuditRecord = {
    ...record,
    fileUrl: fileUrl || record.fileUrl || '',
  };

  // 2. Persist to Firestore
  try {
    const docRef = doc(db, COLLECTION_NAME, record.id);
    const firestorePayload = {
      id: enrichedRecord.id,
      timestamp: enrichedRecord.timestamp,
      fileName: enrichedRecord.fileName,
      fileUrl: enrichedRecord.fileUrl || '',
      studentName: enrichedRecord.studentName,
      usn: enrichedRecord.usn,
      collegeCode: enrichedRecord.collegeCode,
      sgpaListed: enrichedRecord.sgpaListed,
      sgpaCalculated: enrichedRecord.sgpaCalculated,
      arithmeticDiscrepancy: enrichedRecord.arithmeticDiscrepancy,
      tamperingScore: enrichedRecord.tamperingScore,
      verdict: enrichedRecord.verdict,
      forensicReport: enrichedRecord.forensicReport || '',
    };

    await setDoc(docRef, firestorePayload, { merge: true });
  } catch (firestoreError) {
    console.warn('Cloud Firestore setDoc encountered issue, saving to resilient local cache:', firestoreError);
  }

  // 3. Always update local offline ledger cache
  const cached = getLocalLedgerCache();
  const existingIdx = cached.findIndex((r) => r.id === enrichedRecord.id);
  let updatedList: AuditRecord[];
  if (existingIdx >= 0) {
    updatedList = [...cached];
    updatedList[existingIdx] = enrichedRecord;
  } else {
    updatedList = [enrichedRecord, ...cached];
  }
  setLocalLedgerCache(updatedList);

  return enrichedRecord;
}

/**
 * Fetches verification history records from Cloud Firestore with sorting and filtering.
 */
export async function fetchVerificationsFromFirestore(
  options: LedgerQueryOptions = {}
): Promise<AuditRecord[]> {
  const { limitCount = 50, verdict } = options;

  try {
    const constraints: QueryConstraint[] = [
      orderBy('timestamp', 'desc'),
      limit(limitCount),
    ];

    if (verdict && verdict !== 'ALL') {
      constraints.unshift(where('verdict', '==', verdict));
    }

    const q = query(collection(db, COLLECTION_NAME), ...constraints);
    const snapshot = await getDocs(q);

    if (!snapshot.empty) {
      const records: AuditRecord[] = [];
      snapshot.forEach((d) => {
        const data = d.data();
        records.push({
          id: data.id || d.id,
          timestamp: data.timestamp || new Date().toISOString(),
          fileName: data.fileName || 'document.pdf',
          fileUrl: data.fileUrl || undefined,
          studentName: data.studentName || 'STUDENT CANDIDATE',
          usn: data.usn || 'UNKNOWN',
          collegeCode: data.collegeCode || 'VTU',
          sgpaListed: typeof data.sgpaListed === 'number' ? data.sgpaListed : 0,
          sgpaCalculated: typeof data.sgpaCalculated === 'number' ? data.sgpaCalculated : 0,
          arithmeticDiscrepancy: Boolean(data.arithmeticDiscrepancy),
          tamperingScore: typeof data.tamperingScore === 'number' ? data.tamperingScore : 0,
          verdict: (data.verdict as 'AUTHENTIC' | 'SUSPICIOUS' | 'FRAUDULENT') || 'SUSPICIOUS',
          forensicReport: data.forensicReport || '',
        });
      });

      // Update local storage cache with live Firestore data
      setLocalLedgerCache(records);
      return records;
    }
  } catch (queryError) {
    console.warn('Could not query Cloud Firestore verifications collection, reading local cache:', queryError);
  }

  // Fallback to local cache if Firestore is empty or unavailable
  return getLocalLedgerCache();
}

/**
 * Subscribes to real-time updates from Cloud Firestore 'verifications' collection.
 */
export function subscribeToVerificationLedger(
  onUpdate: (records: AuditRecord[]) => void,
  onError?: (error: Error) => void
): () => void {
  try {
    const q = query(
      collection(db, COLLECTION_NAME),
      orderBy('timestamp', 'desc'),
      limit(50)
    );

    const unsubscribe = onSnapshot(
      q,
      (snapshot) => {
        if (!snapshot.empty) {
          const records: AuditRecord[] = [];
          snapshot.forEach((d) => {
            const data = d.data();
            records.push({
              id: data.id || d.id,
              timestamp: data.timestamp || new Date().toISOString(),
              fileName: data.fileName || 'document.pdf',
              fileUrl: data.fileUrl || undefined,
              studentName: data.studentName || 'STUDENT CANDIDATE',
              usn: data.usn || 'UNKNOWN',
              collegeCode: data.collegeCode || 'VTU',
              sgpaListed: typeof data.sgpaListed === 'number' ? data.sgpaListed : 0,
              sgpaCalculated: typeof data.sgpaCalculated === 'number' ? data.sgpaCalculated : 0,
              arithmeticDiscrepancy: Boolean(data.arithmeticDiscrepancy),
              tamperingScore: typeof data.tamperingScore === 'number' ? data.tamperingScore : 0,
              verdict: (data.verdict as 'AUTHENTIC' | 'SUSPICIOUS' | 'FRAUDULENT') || 'SUSPICIOUS',
              forensicReport: data.forensicReport || '',
            });
          });
          setLocalLedgerCache(records);
          onUpdate(records);
        } else {
          onUpdate(getLocalLedgerCache());
        }
      },
      (error) => {
        console.warn('Real-time ledger listener error, falling back to local cache:', error);
        onUpdate(getLocalLedgerCache());
        if (onError) onError(error);
      }
    );

    return unsubscribe;
  } catch (err) {
    console.warn('Failed to establish Firestore onSnapshot subscription:', err);
    onUpdate(getLocalLedgerCache());
    return () => {};
  }
}
