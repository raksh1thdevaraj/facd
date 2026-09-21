"""Test fixtures for End-to-End integration test suite."""

import sys
from pathlib import Path

import pytest
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Ensure backend root is in sys.path
backend_root = Path(__file__).resolve().parent.parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))


@pytest.fixture
def genuine_sample_path() -> Path:
    """Path to known genuine certificate image."""
    path = backend_root.parent / "datasets" / "synthetic_manipulated" / "genuine" / "GEN_00001.png"
    if not path.exists():
        pytest.skip(f"Genuine test sample missing at {path}")
    return path


@pytest.fixture
def manipulated_sample_path() -> Path:
    """Path to known manipulated certificate image."""
    path = (
        backend_root.parent / "datasets" / "synthetic_manipulated" / "manipulated" / "MAN_00001.png"
    )
    if not path.exists():
        pytest.skip(f"Manipulated test sample missing at {path}")
    return path


@pytest.fixture
def sample_multipage_pdf(tmp_path: Path) -> Path:
    """Generate a clean 3-page academic transcript PDF."""
    pdf_path = tmp_path / "sample_transcript_3pages.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    for page in range(1, 4):
        c.drawString(100, 700, f"Official Academic Transcript - Page {page} of 3")
        c.drawString(100, 650, "Candidate: Test Student | Registration: REG-2024-9988")
        c.drawString(100, 600, "Bachelor of Technology in Computer Science")
        c.showPage()
    c.save()
    return pdf_path
