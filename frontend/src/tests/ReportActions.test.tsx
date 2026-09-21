import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ReportActions } from '../components/results/ReportActions';
import { reportService } from '../services/reportService';

describe('ReportActions Component (TC-FE-05)', () => {
  it('triggers PDF download on button click', async () => {
    const pdfSpy = vi.spyOn(reportService, 'downloadReportPdf').mockResolvedValue();

    render(<ReportActions reportId="test-rep-id" />);

    const downloadBtn = screen.getByRole('button', { name: /download official pdf/i });
    fireEvent.click(downloadBtn);

    await waitFor(() => {
      expect(pdfSpy).toHaveBeenCalledWith('test-rep-id');
    });
  });

  it('triggers JSON export on button click', async () => {
    const jsonSpy = vi.spyOn(reportService, 'downloadReportJson').mockResolvedValue();

    render(<ReportActions reportId="test-rep-id" />);

    const jsonBtn = screen.getByRole('button', { name: /download json/i });
    fireEvent.click(jsonBtn);

    await waitFor(() => {
      expect(jsonSpy).toHaveBeenCalledWith('test-rep-id');
    });
  });

  it('copies public verification link to clipboard', async () => {
    const clipSpy = vi.spyOn(navigator.clipboard, 'writeText');

    render(<ReportActions reportId="test-rep-id" />);

    const shareBtn = screen.getByRole('button', { name: /share public url/i });
    fireEvent.click(shareBtn);

    expect(clipSpy).toHaveBeenCalledWith(expect.stringContaining('/verify-report/test-rep-id'));
    expect(await screen.findByText(/link copied/i)).toBeInTheDocument();
  });

  it('verifies report cryptographic signature', async () => {
    vi.spyOn(reportService, 'verifyReportIntegrity').mockResolvedValue({
      is_valid: true,
      message: 'Signature intact',
    });

    render(<ReportActions reportId="test-rep-id" />);

    const verifyBtn = screen.getByRole('button', { name: /verify signature/i });
    fireEvent.click(verifyBtn);

    expect(
      await screen.findByText(/hmac-sha256 signature verified: document payload is untampered/i)
    ).toBeInTheDocument();
  });
});
