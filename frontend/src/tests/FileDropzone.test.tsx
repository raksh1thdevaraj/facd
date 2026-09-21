import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { FileDropzone } from '../components/upload/FileDropzone';

describe('FileDropzone Component (TC-FE-01)', () => {
  it('renders dropzone prompt and browse button', () => {
    const handleSelected = vi.fn();
    render(<FileDropzone onFileSelected={handleSelected} />);

    expect(screen.getByText(/drag and drop academic certificate here/i)).toBeInTheDocument();
    expect(screen.getByText(/browse file from device/i)).toBeInTheDocument();
  });

  it('rejects files larger than 10 MB and shows error message', () => {
    const handleSelected = vi.fn();
    render(<FileDropzone onFileSelected={handleSelected} />);

    // Create 11 MB dummy file
    const largeFile = new File(['a'.repeat(1024)], 'large_certificate.pdf', {
      type: 'application/pdf',
    });
    Object.defineProperty(largeFile, 'size', { value: 11 * 1024 * 1024 });

    const input = screen.getByText(/drag and drop academic certificate here/i).closest('div')?.querySelector('input[type="file"]') as HTMLInputElement;
    expect(input).toBeInTheDocument();

    fireEvent.change(input, { target: { files: [largeFile] } });

    expect(handleSelected).not.toHaveBeenCalled();
    expect(screen.getByText(/exceeds the maximum 10 MB limit/i)).toBeInTheDocument();
  });

  it('rejects unsupported file formats', () => {
    const handleSelected = vi.fn();
    render(<FileDropzone onFileSelected={handleSelected} />);

    const invalidFile = new File(['dummy content'], 'document.docx', {
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    });

    const input = screen.getByText(/drag and drop academic certificate here/i).closest('div')?.querySelector('input[type="file"]') as HTMLInputElement;

    fireEvent.change(input, { target: { files: [invalidFile] } });

    expect(handleSelected).not.toHaveBeenCalled();
    expect(screen.getByText(/unsupported format/i)).toBeInTheDocument();
  });

  it('accepts valid PDF file and triggers onFileSelected', () => {
    const handleSelected = vi.fn();
    render(<FileDropzone onFileSelected={handleSelected} />);

    const validPdf = new File(['%PDF-1.4 dummy content'], 'diploma.pdf', {
      type: 'application/pdf',
    });

    const input = screen.getByText(/drag and drop academic certificate here/i).closest('div')?.querySelector('input[type="file"]') as HTMLInputElement;

    fireEvent.change(input, { target: { files: [validPdf] } });

    expect(handleSelected).toHaveBeenCalledTimes(1);
    expect(handleSelected).toHaveBeenCalledWith(validPdf);
  });
});
