// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { VerificationHistorySection } from '../components/history/VerificationHistorySection';
import { VerificationDetailModal } from '../components/history/VerificationDetailModal';
import { historyService } from '../services/historyService';
import { VerificationHistorySummary, VerificationHistoryDetail } from '../types/history';

describe('VerificationHistorySection Component', () => {
  const mockItems: VerificationHistorySummary[] = [
    {
      id: 'hist-1',
      timestamp: '2026-09-20T10:00:00Z',
      original_filename: 'vtu_marks_aarav.pdf',
      document_type: 'VTU_MARKSCARD',
      student_name: 'Aarav Sharma',
      identifier: '1CR19CS001',
      issuer: 'Visvesvaraya Technological University',
      verdict: 'AUTHENTIC',
      confidence_score: 0.985,
      qr_status: true,
      tampering_flags: [],
      remarks: 'All marks match institutional record.',
    },
    {
      id: 'hist-2',
      timestamp: '2026-09-21T11:00:00Z',
      original_filename: 'coursera_dl.png',
      document_type: 'ONLINE_COURSE_CERTIFICATE',
      student_name: 'Priya Nair',
      identifier: 'CRS-DL-889',
      issuer: 'Coursera',
      verdict: 'SUSPICIOUS',
      confidence_score: 0.65,
      qr_status: false,
      tampering_flags: ['Domain mismatch advisory'],
      remarks: 'Domain requires manual registrar check.',
    },
    {
      id: 'hist-3',
      timestamp: '2026-09-22T12:00:00Z',
      original_filename: 'spliced_cert.png',
      document_type: 'VTU_MARKSCARD',
      student_name: 'Vikram Sen',
      identifier: '1RV18EC999',
      issuer: 'VTU',
      verdict: 'FRAUDULENT',
      confidence_score: 0.15,
      qr_status: false,
      tampering_flags: ['Spliced CGPA', 'Baseline Shift'],
      remarks: 'Image tampering detected.',
    },
  ];

  const mockDetail: VerificationHistoryDetail = {
    ...mockItems[0],
    full_details: {
      extracted_data: {
        student_name: 'Aarav Sharma',
        identifier: '1CR19CS001',
        issuer: 'Visvesvaraya Technological University',
        date: '2026-06-15',
        score_or_cgpa: '9.45',
      },
      rag_validation: {
        schema_matched: true,
        arithmetic_valid: true,
        anomalies_detected: [],
      },
      qr_verification: {
        detected: true,
        payload_or_url: 'https://results.vtu.ac.in/verify/1CR19CS001',
        matches_document_text: true,
      },
    },
  };

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders VerificationDetailModal directly without crash', () => {
    render(<VerificationDetailModal record={mockDetail} onClose={() => {}} />);
    expect(screen.getByText(/extracted document credentials/i)).toBeInTheDocument();
  });

  it('renders history table with headers, student credentials, and visual badges', async () => {
    vi.spyOn(historyService, 'getHistory').mockResolvedValue(mockItems);
    render(<VerificationHistorySection />);

    await waitFor(() => {
      // Check Student Name & USN
      expect(screen.getByText('Aarav Sharma')).toBeInTheDocument();
      expect(screen.getByText('1CR19CS001')).toBeInTheDocument();

      // Check Visual Badges
      expect(screen.getByText('AUTHENTIC')).toBeInTheDocument();
      expect(screen.getByText('SUSPICIOUS')).toBeInTheDocument();
      expect(screen.getByText('FRAUDULENT')).toBeInTheDocument();

      // Check Confidence %
      expect(screen.getByText('98.5%')).toBeInTheDocument();
      expect(screen.getByText('65.0%')).toBeInTheDocument();
      expect(screen.getByText('15.0%')).toBeInTheDocument();
    });
  });

  it('renders clean placeholder empty state banner when no verifications exist', async () => {
    vi.spyOn(historyService, 'getHistory').mockResolvedValue([]);
    const onUploadClick = vi.fn();

    render(<VerificationHistorySection onNavigateToUpload={onUploadClick} />);

    await waitFor(() => {
      expect(
        screen.getByText(/no certificate verifications recorded yet\. upload a document to start\./i)
      ).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /verify a certificate/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /verify a certificate/i }));
    expect(onUploadClick).toHaveBeenCalledTimes(1);
  });

  it('filters history records dynamically via search input and verdict dropdown', async () => {
    const getHistorySpy = vi.spyOn(historyService, 'getHistory').mockResolvedValue(mockItems);

    render(<VerificationHistorySection />);

    await waitFor(() => {
      expect(screen.getByText('Aarav Sharma')).toBeInTheDocument();
    });

    // Test Search input
    const searchInput = screen.getByPlaceholderText(/search filename or id/i);
    fireEvent.change(searchInput, { target: { value: 'Priya' } });

    await waitFor(() => {
      expect(getHistorySpy).toHaveBeenCalledWith(
        expect.objectContaining({
          search: 'Priya',
        })
      );
    });

    // Test Verdict dropdown filter
    const verdictSelect = screen.getAllByRole('combobox')[0];
    fireEvent.change(verdictSelect, { target: { value: 'AUTHENTIC' } });

    await waitFor(() => {
      expect(getHistorySpy).toHaveBeenCalledWith(
        expect.objectContaining({
          verdict: 'AUTHENTIC',
        })
      );
    });
  });

  it('opens detail modal upon clicking View Details with extracted data, RAG, and QR payload', async () => {
    vi.spyOn(historyService, 'getHistory').mockResolvedValue([mockItems[0]]);
    vi.spyOn(historyService, 'getHistoryDetail').mockResolvedValue(mockDetail);

    render(<VerificationHistorySection />);

    await waitFor(() => {
      expect(screen.getByText('Aarav Sharma')).toBeInTheDocument();
    });

    const rowElement = screen.getByText('Aarav Sharma');
    fireEvent.click(rowElement);

    await waitFor(() => {
      // Extracted credentials
      expect(screen.getByText(/extracted document credentials/i)).toBeInTheDocument();
      expect(screen.getByText(/9\.45/)).toBeInTheDocument();

      // RAG Ground truth
      expect(screen.getByText(/rag ground-truth & schema verification/i)).toBeInTheDocument();
      expect(screen.getByText(/matched/i)).toBeInTheDocument();
      expect(screen.getByText(/consistent/i)).toBeInTheDocument();

      // QR Code payload
      expect(screen.getByText(/cryptographic qr code validation/i)).toBeInTheDocument();
      expect(screen.getByText('https://results.vtu.ac.in/verify/1CR19CS001')).toBeInTheDocument();

      // Zero tampering badge
      expect(screen.getByText(/zero tampering or font splicing anomalies detected/i)).toBeInTheDocument();
    });

    // Close modal
    const closeBtn = screen.getByRole('button', { name: /close inspector/i });
    fireEvent.click(closeBtn);

    await waitFor(() => {
      expect(screen.queryByText(/close inspector/i)).not.toBeInTheDocument();
    });
  });

  it('re-fetches history automatically when refreshTrigger prop changes', async () => {
    const getHistorySpy = vi.spyOn(historyService, 'getHistory').mockResolvedValue(mockItems);

    const { rerender } = render(<VerificationHistorySection refreshTrigger={1} />);

    await waitFor(() => {
      expect(getHistorySpy).toHaveBeenCalledTimes(1);
    });

    rerender(<VerificationHistorySection refreshTrigger={2} />);

    await waitFor(() => {
      expect(getHistorySpy).toHaveBeenCalledTimes(2);
    });
  });
});
