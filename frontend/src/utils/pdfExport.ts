import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';

export interface ExportPdfOptions {
  filename?: string;
  onStart?: () => void;
  onSuccess?: () => void;
  onError?: (err: Error) => void;
}

/**
 * Capture an authoritative certificate DOM node and compile into a standard A4 portrait 300DPI PDF.
 */
export async function exportCertificateElementToPdf(
  element: HTMLElement,
  options?: ExportPdfOptions
): Promise<void> {
  const filename = options?.filename || 'CertiShield_Forensic_Verification_Audit.pdf';

  try {
    options?.onStart?.();

    // High-resolution canvas rendering with anti-aliasing
    const canvas = await html2canvas(element, {
      scale: 2, // 2x device pixel ratio for 300 DPI print crispness
      useCORS: true,
      logging: false,
      backgroundColor: '#fafaf9', // Formal parchment backdrop
      windowWidth: element.scrollWidth,
      windowHeight: element.scrollHeight,
    });

    const imgData = canvas.toDataURL('image/jpeg', 0.98);

    // Standard A4 dimensions in mm: 210 x 297
    const pdf = new jsPDF({
      orientation: 'portrait',
      unit: 'mm',
      format: 'a4',
      compress: true,
    });

    const pageWidth = 210;
    const pageHeight = 297;

    // Calculate scaling to perfectly fit single A4 page
    const imgWidth = pageWidth;
    const imgHeight = (canvas.height * imgWidth) / canvas.width;

    // If fits within 1 page, render single page; else scale proportionally to avoid awkward slice
    if (imgHeight <= pageHeight) {
      pdf.addImage(imgData, 'JPEG', 0, 0, imgWidth, imgHeight, undefined, 'FAST');
    } else {
      // Scale proportionally to fit within 297mm
      const scale = pageHeight / imgHeight;
      const fittedWidth = imgWidth * scale;
      const xOffset = (pageWidth - fittedWidth) / 2;
      pdf.addImage(imgData, 'JPEG', xOffset, 0, fittedWidth, pageHeight, undefined, 'FAST');
    }

    pdf.save(filename);
    options?.onSuccess?.();
  } catch (err: unknown) {
    const error = err instanceof Error ? err : new Error('Failed to generate audit certificate PDF');
    options?.onError?.(error);
    throw error;
  }
}
