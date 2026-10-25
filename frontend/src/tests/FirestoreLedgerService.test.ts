import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  saveVerificationToFirestore,
  fetchVerificationsFromFirestore,
  subscribeToVerificationLedger,
} from '../services/firestoreLedgerService';
import { AuditRecord } from '../components/console/AuditLedgerPanel';

// Mock Firebase config
vi.mock('../config/firebase', () => ({
  db: {},
  storage: {},
  auth: {},
}));

// Mock Firebase Firestore methods
vi.mock('firebase/firestore', () => ({
  collection: vi.fn(),
  doc: vi.fn(),
  setDoc: vi.fn().mockResolvedValue(undefined),
  getDocs: vi.fn().mockResolvedValue({
    empty: false,
    forEach: (cb: any) => {
      cb({
        id: 'AUD-VTU-TEST-001',
        data: () => ({
          id: 'AUD-VTU-TEST-001',
          timestamp: '2024-10-25T10:00:00.000Z',
          fileName: 'marks_sheet_test.pdf',
          studentName: 'VIKRAM PATIL',
          usn: '1RV21CS100',
          collegeCode: '1RV',
          sgpaListed: 8.75,
          sgpaCalculated: 8.75,
          arithmeticDiscrepancy: false,
          tamperingScore: 5,
          verdict: 'AUTHENTIC',
          forensicReport: 'Verified successfully',
        }),
      });
    },
  }),
  query: vi.fn(),
  orderBy: vi.fn(),
  limit: vi.fn(),
  where: vi.fn(),
  onSnapshot: vi.fn((_q, callback) => {
    callback({
      empty: false,
      forEach: (cb: any) => {
        cb({
          id: 'AUD-VTU-TEST-001',
          data: () => ({
            id: 'AUD-VTU-TEST-001',
            timestamp: '2024-10-25T10:00:00.000Z',
            fileName: 'marks_sheet_test.pdf',
            studentName: 'VIKRAM PATIL',
            usn: '1RV21CS100',
            collegeCode: '1RV',
            sgpaListed: 8.75,
            sgpaCalculated: 8.75,
            arithmeticDiscrepancy: false,
            tamperingScore: 5,
            verdict: 'AUTHENTIC',
            forensicReport: 'Verified successfully',
          }),
        });
      },
    });
    return vi.fn(); // unsubscribe function
  }),
}));

// Mock Firebase Storage methods
vi.mock('firebase/storage', () => ({
  ref: vi.fn(),
  uploadBytes: vi.fn().mockResolvedValue({
    ref: {},
  }),
  getDownloadURL: vi.fn().mockResolvedValue('https://storage.googleapis.com/facd/verifications/AUD-123/marks.pdf'),
}));

describe('FirestoreLedgerService Unit Tests', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('saves an audit record to Firestore and updates local cache', async () => {
    const record: AuditRecord = {
      id: 'AUD-TEST-SAVE-01',
      timestamp: new Date().toISOString(),
      fileName: 'test_card.pdf',
      studentName: 'MEGHANA GOWDA',
      usn: '1BM20IS045',
      collegeCode: '1BM',
      sgpaListed: 8.5,
      sgpaCalculated: 8.5,
      arithmeticDiscrepancy: false,
      tamperingScore: 2,
      verdict: 'AUTHENTIC',
      forensicReport: 'Integrity verified exact.',
    };

    const saved = await saveVerificationToFirestore(record);
    expect(saved.id).toBe(record.id);
    expect(saved.studentName).toBe('MEGHANA GOWDA');

    // Check that localStorage cache was updated
    const cached = JSON.parse(localStorage.getItem('FACD_AUDIT_LEDGER_OFFLINE_CACHE') || '[]');
    expect(cached.some((r: AuditRecord) => r.id === record.id)).toBe(true);
  });

  it('fetches verification records from Firestore', async () => {
    const records = await fetchVerificationsFromFirestore();
    expect(Array.isArray(records)).toBe(true);
    expect(records.length).toBeGreaterThan(0);
    expect(records[0].usn).toBe('1RV21CS100');
    expect(records[0].verdict).toBe('AUTHENTIC');
  });

  it('establishes a real-time onSnapshot subscription and triggers callback', () => {
    const onUpdate = vi.fn();
    const unsubscribe = subscribeToVerificationLedger(onUpdate);

    expect(typeof unsubscribe).toBe('function');
    expect(onUpdate).toHaveBeenCalled();
    const calledWith = onUpdate.mock.calls[0][0];
    expect(Array.isArray(calledWith)).toBe(true);
    expect(calledWith[0].studentName).toBe('VIKRAM PATIL');
  });
});
