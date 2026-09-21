import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { PipelineStepper } from '../components/progress/PipelineStepper';

describe('PipelineStepper Component (TC-FE-02)', () => {
  it('renders all 6 pipeline stages and active progress', () => {
    render(
      <PipelineStepper
        progress={45}
        stageIndex={2}
        status="PROCESSING"
      />
    );

    expect(screen.getByText('45%')).toBeInTheDocument();
    expect(screen.getByText(/Ingestion & Hashing/i)).toBeInTheDocument();
    expect(screen.getByText(/Preprocessing & Rectification/i)).toBeInTheDocument();
    expect(screen.getByText(/OCR & Layout Extraction/i)).toBeInTheDocument();
    expect(screen.getByText(/Forensics & Consistency/i)).toBeInTheDocument();
    expect(screen.getByText(/Multimodal ML Ensemble/i)).toBeInTheDocument();
    expect(screen.getByText(/Dossier Generation/i)).toBeInTheDocument();
  });

  it('renders completed state when status is COMPLETED', () => {
    render(
      <PipelineStepper
        progress={100}
        stageIndex={5}
        status="COMPLETED"
      />
    );

    expect(screen.getByText('100%')).toBeInTheDocument();
    expect(screen.getByText(/Verification Pipeline Finished/i)).toBeInTheDocument();
  });

  it('renders failure banner when status is FAILED', () => {
    render(
      <PipelineStepper
        progress={35}
        stageIndex={1}
        status="FAILED"
        error="Severe image corruption detected"
      />
    );

    expect(screen.getByText(/Verification Pipeline Halted/i)).toBeInTheDocument();
    expect(screen.getByText(/Severe image corruption detected/i)).toBeInTheDocument();
  });
});
