import io
from pathlib import Path

import pytest
from PIL import Image

from app.core.exceptions import (
    CorruptedFileError,
    EmptyFileError,
    FileTooLargeError,
    InsufficientResolutionError,
    InvalidFileError,
    UnsupportedFileTypeError,
)
from app.modules.ingestion.validator import IngestionValidator


def test_valid_jpeg_signature_accepted():
    stream = io.BytesIO(b"\xff\xd8\xff\xe0" + b"\x00" * 28)
    mime = IngestionValidator.validate_file_signature(stream, "cert.jpg")
    assert mime == "image/jpeg"
    assert stream.tell() == 0


def test_valid_png_signature_accepted():
    stream = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * 24)
    mime = IngestionValidator.validate_file_signature(stream, "cert.png")
    assert mime == "image/png"
    assert stream.tell() == 0


def test_valid_pdf_signature_accepted():
    stream = io.BytesIO(b"%PDF-1.7\r\n" + b"\x00" * 22)
    mime = IngestionValidator.validate_file_signature(stream, "cert.pdf")
    assert mime == "application/pdf"
    assert stream.tell() == 0


def test_disguised_executable_rejected():
    # Windows MZ header
    stream = io.BytesIO(b"MZ\x90\x00\x03\x00\x00\x00" + b"\x00" * 24)
    with pytest.raises(UnsupportedFileTypeError):
        IngestionValidator.validate_file_signature(stream, "evil.jpg")


def test_plain_text_renamed_to_pdf_rejected():
    stream = io.BytesIO(b"Hello world, this is a plain text file")
    with pytest.raises(UnsupportedFileTypeError):
        IngestionValidator.validate_file_signature(stream, "fake.pdf")


def test_empty_file_signature_rejected():
    stream = io.BytesIO(b"")
    with pytest.raises(EmptyFileError):
        IngestionValidator.validate_file_signature(stream, "empty.png")


def test_short_header_rejected():
    stream = io.BytesIO(b"\xff\xd8")
    with pytest.raises(InvalidFileError):
        IngestionValidator.validate_file_signature(stream, "short.jpg")


def test_validate_file_size_limits():
    # 0 bytes
    with pytest.raises(EmptyFileError):
        IngestionValidator.validate_file_size(0, max_bytes=10 * 1024 * 1024)

    # Within 10MB limit
    IngestionValidator.validate_file_size(10 * 1024 * 1024, max_bytes=10 * 1024 * 1024)
    IngestionValidator.validate_file_size(5 * 1024 * 1024, max_bytes=10 * 1024 * 1024)

    # Exceeding 10MB limit
    with pytest.raises(FileTooLargeError):
        IngestionValidator.validate_file_size(10 * 1024 * 1024 + 1, max_bytes=10 * 1024 * 1024)


def test_validate_dimensions():
    # Valid landscape
    w, h = IngestionValidator.validate_dimensions(800, 600)
    assert (w, h) == (800, 600)

    # Valid portrait
    w, h = IngestionValidator.validate_dimensions(600, 800)
    assert (w, h) == (600, 800)

    # High res landscape
    w, h = IngestionValidator.validate_dimensions(1920, 1080)
    assert (w, h) == (1920, 1080)

    # Undersized
    with pytest.raises(InsufficientResolutionError):
        IngestionValidator.validate_dimensions(799, 599)

    with pytest.raises(InsufficientResolutionError):
        IngestionValidator.validate_dimensions(500, 500)


def test_validate_image_integrity_valid_image(tmp_path: Path):
    img_path = tmp_path / "valid.png"
    img = Image.new("RGB", (800, 600), color=(255, 255, 255))
    img.save(img_path, format="PNG")

    width, height = IngestionValidator.validate_image_integrity(img_path, "image/png")
    assert width == 800
    assert height == 600


def test_validate_image_integrity_corrupted_image(tmp_path: Path):
    corrupt_path = tmp_path / "corrupt.jpg"
    # Write valid JPEG header but garbage truncated payload
    corrupt_path.write_bytes(
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00corruptdata"
    )

    with pytest.raises(CorruptedFileError):
        IngestionValidator.validate_image_integrity(corrupt_path, "image/jpeg")
