import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { InteractiveViewer } from '../components/results/InteractiveViewer';
import { OverlayAnomaly } from '../types/report';

describe('InteractiveViewer Component (TC-FE-04)', () => {
  const mockAnomalies: OverlayAnomaly[] = [
    { x: 20, y: 30, width: 40, height: 10, layer: 'ocr', label: 'Student Name' },
    { x: 50, y: 60, width: 30, height: 15, layer: 'forensics', label: 'Copy-Move Artifact' },
  ];

  it('renders zoom in, zoom out, and reset controls', () => {
    render(
      <InteractiveViewer
        documentImageUrl="https://example.com/certificate.png"
        anomalies={mockAnomalies}
      />
    );

    expect(screen.getByText('100%')).toBeInTheDocument();
    const zoomInBtn = screen.getByTitle(/zoom in/i);
    const zoomOutBtn = screen.getByTitle(/zoom out/i);
    const resetBtn = screen.getByTitle(/reset zoom/i);

    fireEvent.click(zoomInBtn);
    expect(screen.getByText('125%')).toBeInTheDocument();

    fireEvent.click(zoomOutBtn);
    expect(screen.getByText('100%')).toBeInTheDocument();

    fireEvent.click(zoomInBtn);
    fireEvent.click(zoomInBtn);
    expect(screen.getByText('150%')).toBeInTheDocument();
    fireEvent.click(resetBtn);
    expect(screen.getByText('100%')).toBeInTheDocument();
  });

  it('toggles evidence layers independently', () => {
    render(
      <InteractiveViewer
        documentImageUrl="https://example.com/certificate.png"
        anomalies={mockAnomalies}
      />
    );

    const ocrToggle = screen.getByRole('button', { name: /ocr bounding boxes/i });
    const forensicsToggle = screen.getByRole('button', { name: /forensics anomaly boxes/i });

    expect(screen.getByText('Student Name')).toBeInTheDocument();
    expect(screen.getByText('Copy-Move Artifact')).toBeInTheDocument();

    // Toggle off OCR
    fireEvent.click(ocrToggle);
    expect(screen.queryByText('Student Name')).not.toBeInTheDocument();
    expect(screen.getByText('Copy-Move Artifact')).toBeInTheDocument();

    // Toggle off Forensics
    fireEvent.click(forensicsToggle);
    expect(screen.queryByText('Copy-Move Artifact')).not.toBeInTheDocument();
  });
});
