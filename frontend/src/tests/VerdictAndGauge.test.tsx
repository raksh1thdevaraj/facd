import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { VerdictBanner } from '../components/results/VerdictBanner';
import { ScoreGauge } from '../components/results/ScoreGauge';

describe('VerdictBanner & ScoreGauge Components (TC-FE-03)', () => {
  it('renders AUTHENTIC verdict banner with score and SHA256', () => {
    render(
      <VerdictBanner
        verdict="AUTHENTIC"
        authenticityScore={0.942}
        sha256Hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        reportId="rep-12345678"
      />
    );

    expect(screen.getByText(/CERTIFICATE VERIFIED AS AUTHENTIC/i)).toBeInTheDocument();
    expect(screen.getByText('94.2%')).toBeInTheDocument();
    expect(
      screen.getByText('e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')
    ).toBeInTheDocument();
  });

  it('renders MANIPULATED verdict banner properly', () => {
    render(
      <VerdictBanner
        verdict="MANIPULATED"
        authenticityScore={0.21}
        sha256Hash="deadbeef123456"
        reportId="rep-manipulated"
      />
    );

    expect(screen.getByText(/TAMPERING & MANIPULATION DETECTED/i)).toBeInTheDocument();
    expect(screen.getByText('21.0%')).toBeInTheDocument();
  });

  it('allows copying SHA256 hash to clipboard', async () => {
    const clipboardSpy = vi.spyOn(navigator.clipboard, 'writeText');

    render(
      <VerdictBanner
        verdict="AUTHENTIC"
        authenticityScore={0.9}
        sha256Hash="abcdef123456"
        reportId="rep-copy-test"
      />
    );

    const copyBtn = screen.getByRole('button', { name: /copy hash/i });
    fireEvent.click(copyBtn);

    expect(clipboardSpy).toHaveBeenCalledWith('abcdef123456');
    expect(await screen.findByText(/copied/i)).toBeInTheDocument();
  });

  it('renders ScoreGauge with calculated percentage and status text', () => {
    const { rerender } = render(<ScoreGauge score={0.88} />);
    expect(screen.getByText('88.0%')).toBeInTheDocument();
    expect(screen.getByText('Authentic')).toBeInTheDocument();

    rerender(<ScoreGauge score={0.62} />);
    expect(screen.getByText('62.0%')).toBeInTheDocument();
    expect(screen.getByText('Suspicious')).toBeInTheDocument();

    rerender(<ScoreGauge score={0.25} />);
    expect(screen.getByText('25.0%')).toBeInTheDocument();
    expect(screen.getByText('Manipulated')).toBeInTheDocument();
  });
});
