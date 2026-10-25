import shutil
from pathlib import Path
from typing import List

from PIL import Image

from app.core.exceptions import EncryptedPdfError, PDFConversionError


def is_poppler_installed() -> bool:
    """Check if the poppler pdftoppm executable is available on system PATH."""
    return shutil.which("pdftoppm") is not None


class PDFRasterizer:
    """Rasterizes PDF documents into 300 DPI high-resolution PNG images.

    Supports pdf2image (Poppler) with automatic graceful fallback to pypdfium2.
    """

    @classmethod
    def rasterize_pdf(
        cls,
        pdf_path: Path,
        output_dir: Path,
        dpi: int = 300,
        max_pages: int = 3,
    ) -> List[Path]:
        """Convert up to max_pages pages of a PDF to high-resolution PNG images.

        Saves images to output_dir and returns list of generated file paths.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        generated_paths: List[Path] = []

        # Attempt with pdf2image if poppler is present
        if is_poppler_installed():
            try:
                import pdf2image
                from pdf2image.exceptions import PDFPageCountError, PDFSyntaxError

                try:
                    images = pdf2image.convert_from_path(
                        str(pdf_path),
                        dpi=dpi,
                        fmt="png",
                        first_page=1,
                        last_page=max_pages,
                        thread_count=2,
                    )
                    for idx, img in enumerate(images, start=1):
                        out_file = output_dir / f"{pdf_path.stem}_page_{idx}.png"
                        img.save(out_file, format="PNG")
                        generated_paths.append(out_file)
                    return generated_paths
                except (PDFSyntaxError, PDFPageCountError) as exc:
                    err_msg = str(exc).lower()
                    if "password" in err_msg or "encrypted" in err_msg:
                        raise EncryptedPdfError(
                            "Password-protected PDF files cannot be processed. "
                            "Please upload an unprotected copy."
                        ) from exc
                    # Fall back to pypdfium2 if Poppler fails on this file
                    pass
            except EncryptedPdfError:
                raise
            except Exception:
                # Fall through to pypdfium2 fallback
                pass

        # Robust zero-dependency fallback using pypdfium2
        try:
            import pypdfium2 as pdfium

            try:
                doc = pdfium.PdfDocument(str(pdf_path))
            except pdfium.PdfiumError as exc:
                err_str = str(exc).lower()
                if "password" in err_str or "encrypted" in err_str:
                    raise EncryptedPdfError(
                        "Password-protected PDF files cannot be processed. "
                        "Please upload an unprotected copy."
                    ) from exc
                raise PDFConversionError(f"Failed to open PDF document: {exc}") from exc

            num_pages = len(doc)
            if num_pages == 0:
                raise PDFConversionError("PDF contains no pages.")

            pages_to_render = min(num_pages, max_pages)
            # Default PDF point size is 72 DPI. Target DPI / 72 gives rendering scale.
            scale = dpi / 72.0

            for page_idx in range(pages_to_render):
                page = doc.get_page(page_idx)
                rendered = page.render(scale=scale)  # type: ignore[arg-type]
                pil_image = rendered.to_pil()

                # If dimensions are abnormally small, scale up cleanly for OCR and forensic analysis
                w, h = pil_image.size
                if w < 100 or h < 100:
                    raise PDFConversionError(
                        f"Rasterized page {page_idx + 1} dimensions ({w}x{h}) are too small to contain a valid certificate."
                    )
                if w < 800 or h < 800:
                    min_dim = min(w, h)
                    upscale_factor = max(1.0, 1200.0 / min_dim)
                    new_w, new_h = int(w * upscale_factor), int(h * upscale_factor)
                    pil_image = pil_image.resize((new_w, new_h), resample=Image.Resampling.LANCZOS)

                out_file = output_dir / f"{pdf_path.stem}_page_{page_idx + 1}.png"
                pil_image.save(out_file, format="PNG")
                generated_paths.append(out_file)

            return generated_paths

        except (EncryptedPdfError, PDFConversionError):
            raise
        except Exception as exc:
            raise PDFConversionError(f"Error during PDF rasterization: {exc}") from exc

    @classmethod
    def extract_text_from_pdf(cls, pdf_path: Path) -> str:
        """Extract digital text directly from PDF pages using pypdfium2."""
        try:
            import pypdfium2 as pdfium

            doc = pdfium.PdfDocument(str(pdf_path))
            texts: List[str] = []
            for page in doc:
                textpage = page.get_textpage()
                t = textpage.get_text_range()
                if t:
                    texts.append(t)
            return "\n".join(texts)
        except Exception:
            return ""
