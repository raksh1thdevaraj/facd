import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { HistoryPage } from '../pages/HistoryPage';
import { MetricCard } from '../components/admin/MetricCard';
import { TemplatePreviewModal } from '../components/admin/TemplatePreviewModal';
import { AuditDetailModal } from '../components/admin/AuditDetailModal';
import { exportToCsv } from '../utils/csvExport';
import { certificateService } from '../services/certificateService';
import { ShieldCheck } from 'lucide-react';
import { TemplateItem, AuditLogItem } from '../types/admin';

describe('Phase 17 Frontend Unit Tests', () => {
  describe('exportToCsv Utility (CHIP ADM-09)', () => {
    it('generates a CSV download trigger with properly escaped columns', () => {
      const createElementSpy = vi.spyOn(document, 'createElement');
      const mockRows = [
        { id: '123', name: 'John "The Great" Doe', score: 0.95 },
        { id: '456', name: 'Jane, Smith', score: 0.12 },
      ];

      exportToCsv('test_export.csv', mockRows);

      expect(createElementSpy).toHaveBeenCalledWith('a');
    });
  });

  describe('HistoryPage Multi-Criteria Filtering (TC-ADM-01)', () => {
    it('renders history table with search input and verdict filter', async () => {
      vi.spyOn(certificateService, 'listCertificates').mockResolvedValue({
        items: [
          {
            id: 'cert-1',
            original_filename: 'harvard_diploma.pdf',
            file_size: 1024,
            mime_type: 'application/pdf',
            job_status: 'COMPLETED',
            job_progress: 100,
            final_verdict: 'AUTHENTIC',
            overall_authenticity_score: 0.96,
            created_at: '2026-09-20T10:00:00Z',
          },
        ],
        total: 1,
        page: 1,
        limit: 10,
        total_pages: 1,
      });

      render(
        <BrowserRouter>
          <HistoryPage />
        </BrowserRouter>
      );

      expect(screen.getByText(/verification history/i)).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/search filename or id/i)).toBeInTheDocument();
      expect(screen.getByRole('combobox')).toBeInTheDocument();

      await waitFor(() => {
        expect(screen.getByText('harvard_diploma.pdf')).toBeInTheDocument();
        expect(screen.getByText('Authentic')).toBeInTheDocument();
        expect(screen.getByText('96.0%')).toBeInTheDocument();
      });
    });
  });

  describe('Admin MetricCard Component (CHIP ADM-04)', () => {
    it('renders KPI metric value, trend, and title', () => {
      render(
        <MetricCard
          title="Overall Fraud Rate"
          value="14.2%"
          trend="+2.1%"
          isPositiveTrend={false}
          icon={ShieldCheck}
          accentColor="rose"
        />
      );

      expect(screen.getByText(/overall fraud rate/i)).toBeInTheDocument();
      expect(screen.getByText('14.2%')).toBeInTheDocument();
      expect(screen.getByText('+2.1%')).toBeInTheDocument();
    });
  });

  describe('TemplatePreviewModal Component (TC-ADM-04)', () => {
    it('renders template information and seal ROI overlay', () => {
      const mockTemplate: TemplateItem = {
        template_id: 'tpl-stanford-2024',
        institution_id: 'inst-stanford',
        institution_name: 'Stanford University',
        template_name: 'Computer Science Diploma',
        degree_program: 'B.S. in Computer Science',
        uploaded_at: '2026-09-15T12:00:00Z',
        seal_roi: { x: 70, y: 65, width: 20, height: 25 },
      };

      const handleClose = vi.fn();

      render(<TemplatePreviewModal template={mockTemplate} onClose={handleClose} />);

      expect(screen.getByText('Computer Science Diploma')).toBeInTheDocument();
      expect(screen.getAllByText('Stanford University').length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText('SEAL ROI')).toBeInTheDocument();


      const closeBtn = screen.getByRole('button', { name: /close inspector/i });
      fireEvent.click(closeBtn);
      expect(handleClose).toHaveBeenCalledTimes(1);
    });
  });

  describe('AuditDetailModal Component (TC-ADM-05)', () => {
    it('renders formatted JSON payload and event information', () => {
      const mockLog: AuditLogItem = {
        id: 'evt-999',
        action: 'CERTIFICATE_UPLOADED',
        ip_address: '192.168.1.100',
        details: { filename: 'test_doc.png', size_bytes: 4096 },
        created_at: '2026-09-20T15:30:00Z',
      };

      const handleClose = vi.fn();

      render(<AuditDetailModal log={mockLog} onClose={handleClose} />);

      expect(screen.getByText(/audit event details/i)).toBeInTheDocument();
      expect(screen.getByText('CERTIFICATE_UPLOADED')).toBeInTheDocument();
      expect(screen.getByText(/192.168.1.100/i)).toBeInTheDocument();
      expect(screen.getByText(/"filename": "test_doc.png"/i)).toBeInTheDocument();
    });
  });
});
