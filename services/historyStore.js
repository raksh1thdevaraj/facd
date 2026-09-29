/**
 * Lightweight Local Storage Handler for Verification History (Node.js / JavaScript).
 *
 * Persists and retrieves certificate verification audit records to/from `data/history.json`.
 * Implements atomic file writes, filtering, sorting, pagination, and single-record retrieval.
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// Canonical paths
const PROJECT_ROOT = path.resolve(__dirname, '..');
const DEFAULT_DATA_DIR = path.join(PROJECT_ROOT, 'data');
const DEFAULT_HISTORY_FILE = path.join(DEFAULT_DATA_DIR, 'history.json');

class HistoryStore {
  constructor(filePath = null, maxRecords = 1000) {
    this.filePath = filePath
      ? path.resolve(filePath)
      : path.resolve(process.env.HISTORY_FILE_PATH || DEFAULT_HISTORY_FILE);
    this.maxRecords = maxRecords;
    this.ensureStoreFile();
  }

  ensureStoreFile() {
    try {
      const dir = path.dirname(this.filePath);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
      if (!fs.existsSync(this.filePath)) {
        fs.writeFileSync(this.filePath, JSON.stringify([], null, 2), 'utf-8');
      }
    } catch (err) {
      console.warn(`[HistoryStore] Could not initialize file ${this.filePath}:`, err.message);
    }
    return this.filePath;
  }

  readAll() {
    try {
      if (fs.existsSync(this.filePath)) {
        const raw = fs.readFileSync(this.filePath, 'utf-8');
        const data = JSON.parse(raw);
        if (Array.isArray(data)) {
          return data;
        }
      }
    } catch (err) {
      console.warn(`[HistoryStore] Failed reading store ${this.filePath}:`, err.message);
    }
    return [];
  }

  getById(recordId) {
    const records = this.readAll();
    const target = String(recordId).trim();
    return records.find((r) => String(r.id || '').trim() === target) || null;
  }

  appendRecord(record) {
    this.ensureStoreFile();

    const recId = String(record.id || crypto.randomUUID());
    const timestamp = record.timestamp || new Date().toISOString();

    const rawVerdict = String(record.verdict || 'SUSPICIOUS').toUpperCase();
    let normalizedVerdict = 'SUSPICIOUS';
    if (rawVerdict.includes('AUTHENTIC') || rawVerdict.includes('VERIFIED')) {
      normalizedVerdict = 'AUTHENTIC';
    } else if (rawVerdict.includes('FRAUD') || rawVerdict.includes('REJECT') || rawVerdict.includes('MANIPULATED')) {
      normalizedVerdict = 'FRAUDULENT';
    }

    const confScore = Math.max(0.0, Math.min(1.0, parseFloat(record.confidence_score != null ? record.confidence_score : 0.85)));

    const entry = {
      id: recId,
      timestamp: timestamp,
      original_filename: String(record.original_filename || 'unknown_certificate'),
      document_type: String(record.document_type || 'VTU_MARKSCARD'),
      student_name: String(record.student_name || 'Not Detected'),
      identifier: String(record.identifier || record.usn || record.reg_no || 'Not Detected'),
      issuer: String(record.issuer || record.institution || 'Visvesvaraya Technological University'),
      verdict: normalizedVerdict,
      confidence_score: Number(confScore.toFixed(4)),
      qr_status: Boolean(record.qr_status),
      tampering_flags: Array.isArray(record.tampering_flags) ? record.tampering_flags : [],
      remarks: String(record.remarks || ''),
      full_details: record.full_details || {},
    };

    const records = this.readAll();
    const existingIndex = records.findIndex((r) => String(r.id) === recId);

    if (existingIndex !== -1) {
      records[existingIndex] = entry;
    } else {
      records.unshift(entry);
    }

    const trimmed = records.slice(0, this.maxRecords);

    // Atomic write
    const tempPath = `${this.filePath}.${crypto.randomBytes(4).toString('hex')}.tmp`;
    try {
      fs.writeFileSync(tempPath, JSON.stringify(trimmed, null, 2), 'utf-8');
      fs.renameSync(tempPath, this.filePath);
    } catch (err) {
      if (fs.existsSync(tempPath)) {
        try { fs.unlinkSync(tempPath); } catch (_) {}
      }
      throw err;
    }

    return entry;
  }

  listRecords(options = {}) {
    const {
      page = 1,
      limit = 20,
      order = 'desc',
      search = null,
      usn = null,
      studentName = null,
      verdict = null,
      documentType = null,
    } = options;

    let records = this.readAll();

    if (search) {
      const q = search.toLowerCase().trim();
      records = records.filter((r) =>
        (r.student_name && r.student_name.toLowerCase().includes(q)) ||
        (r.identifier && r.identifier.toLowerCase().includes(q)) ||
        (r.issuer && r.issuer.toLowerCase().includes(q)) ||
        (r.original_filename && r.original_filename.toLowerCase().includes(q))
      );
    }

    if (usn) {
      const u = usn.toLowerCase().trim();
      records = records.filter((r) => r.identifier && r.identifier.toLowerCase().includes(u));
    }

    if (studentName) {
      const sn = studentName.toLowerCase().trim();
      records = records.filter((r) => r.student_name && r.student_name.toLowerCase().includes(sn));
    }

    if (verdict && verdict.toUpperCase() !== 'ALL') {
      const v = verdict.toUpperCase().trim();
      records = records.filter((r) => r.verdict && r.verdict.toUpperCase() === v);
    }

    if (documentType && documentType.toUpperCase() !== 'ALL') {
      const dt = documentType.toLowerCase().trim();
      records = records.filter((r) => r.document_type && r.document_type.toLowerCase() === dt);
    }

    records.sort((a, b) => {
      const timeA = new Date(a.timestamp || 0).getTime();
      const timeB = new Date(b.timestamp || 0).getTime();
      return order === 'asc' ? timeA - timeB : timeB - timeA;
    });

    const total = records.length;
    const totalPages = Math.max(1, Math.ceil(total / limit));
    const startIdx = (Math.max(1, page) - 1) * limit;
    const paginated = records.slice(startIdx, startIdx + limit);

    return {
      items: paginated,
      total,
      page,
      limit,
      totalPages,
    };
  }

  deleteRecord(recordId) {
    const records = this.readAll();
    const target = String(recordId).trim();
    const filtered = records.filter((r) => String(r.id || '').trim() !== target);

    if (filtered.length === records.length) {
      return false;
    }

    const tempPath = `${this.filePath}.${crypto.randomBytes(4).toString('hex')}.tmp`;
    try {
      fs.writeFileSync(tempPath, JSON.stringify(filtered, null, 2), 'utf-8');
      fs.renameSync(tempPath, this.filePath);
      return true;
    } catch (err) {
      if (fs.existsSync(tempPath)) {
        try { fs.unlinkSync(tempPath); } catch (_) {}
      }
      return false;
    }
  }

  clear() {
    this.ensureStoreFile();
    const tempPath = `${this.filePath}.${crypto.randomBytes(4).toString('hex')}.tmp`;
    try {
      fs.writeFileSync(tempPath, JSON.stringify([], null, 2), 'utf-8');
      fs.renameSync(tempPath, this.filePath);
      return true;
    } catch (err) {
      if (fs.existsSync(tempPath)) {
        try { fs.unlinkSync(tempPath); } catch (_) {}
      }
      return false;
    }
  }
}

// Default singleton
const defaultHistoryStore = new HistoryStore();

module.exports = {
  HistoryStore,
  historyStore: defaultHistoryStore,
  appendRecord: (record) => defaultHistoryStore.appendRecord(record),
  readHistory: () => defaultHistoryStore.readAll(),
  getRecordById: (id) => defaultHistoryStore.getById(id),
  deleteRecord: (id) => defaultHistoryStore.deleteRecord(id),
  clearHistory: () => defaultHistoryStore.clear(),
};
