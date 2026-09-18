import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pypdf
from PIL import ExifTags, Image

EDITING_SOFTWARE_KEYWORDS = [
    "photoshop",
    "gimp",
    "canva",
    "paint.net",
    "illustrator",
    "coreldraw",
    "inkscape",
    "pixlr",
    "acrobat",
    "affinity",
]


def _parse_pdf_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse standard PDF date format, e.g. D:20240915123000+00'00'."""
    if not date_str or not isinstance(date_str, str):
        return None
    cleaned = date_str.replace("D:", "").strip()
    match = re.match(r"^(\d{4})(\d{2})(\d{2})(\d{2})?(\d{2})?(\d{2})?", cleaned)
    if match:
        year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
        hour = int(match.group(4) or 0)
        minute = int(match.group(5) or 0)
        second = int(match.group(6) or 0)
        try:
            return datetime(year, month, day, hour, minute, second)
        except ValueError:
            return None
    return None


def _parse_exif_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse EXIF datetime string, e.g. '2024:09:15 12:30:00'."""
    if not date_str or not isinstance(date_str, str):
        return None
    for fmt in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"):
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None


class MetadataExtractor:
    """Extracts forensic metadata from image and PDF files."""

    @classmethod
    def extract(cls, file_path: Path, mime_type: str) -> Dict[str, Any]:
        """Dispatch metadata extraction based on MIME type or extension."""
        if mime_type == "application/pdf" or file_path.suffix.lower() == ".pdf":
            return cls.extract_pdf_metadata(file_path)
        return cls.extract_image_metadata(file_path)

    @classmethod
    def extract_image_metadata(cls, file_path: Path) -> Dict[str, Any]:
        """Extract EXIF tags, software strings, and camera hardware signatures from images."""
        raw_metadata: Dict[str, Any] = {}
        software: Optional[str] = None
        creation_date: Optional[datetime] = None
        modification_date: Optional[datetime] = None
        has_exif = False
        suspicious_indicators: List[str] = []

        try:
            with Image.open(file_path) as img:
                exif_data = img._getexif()
                if exif_data:
                    has_exif = True
                    for tag_id, value in exif_data.items():
                        tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                        # Filter non-serializable byte arrays
                        if isinstance(value, bytes):
                            try:
                                value = value.decode("utf-8", errors="ignore").strip()
                            except Exception:
                                value = str(value)
                        raw_metadata[tag_name] = value

                    # Check software signature
                    software = raw_metadata.get("Software") or raw_metadata.get(
                        "ProcessingSoftware"
                    )
                    if software:
                        software = str(software).strip()

                    # Check dates
                    date_orig = raw_metadata.get("DateTimeOriginal") or raw_metadata.get(
                        "DateTimeDigitized"
                    )
                    date_mod = raw_metadata.get("DateTime")
                    creation_date = _parse_exif_date(date_orig)
                    modification_date = _parse_exif_date(date_mod)

                # Check PNG text chunks if PNG
                if img.format == "PNG" and hasattr(img, "text"):
                    for k, v in img.text.items():
                        raw_metadata[k] = v
                        if k.lower() in ("software", "tool"):
                            software = v
                        if k.lower() in ("creation time", "date:create"):
                            creation_date = creation_date or _parse_exif_date(v)
                        if k.lower() in ("modification time", "date:modify"):
                            modification_date = modification_date or _parse_exif_date(v)

        except Exception:
            # Metadata extraction is best-effort and must never crash ingestion
            pass

        # Check for editing software keywords
        if software:
            lower_software = software.lower()
            for kw in EDITING_SOFTWARE_KEYWORDS:
                if kw in lower_software:
                    suspicious_indicators.append(
                        f"Graphic editing software signature detected: '{software}'"
                    )
                    break

        if creation_date and modification_date:
            diff = (modification_date - creation_date).total_seconds()
            if diff > 86400:  # Modified more than 24h after creation
                hours = diff / 3600
                suspicious_indicators.append(
                    f"Significant timestamp discrepancy: modified {hours:.1f} hours after creation"
                )

        return {
            "raw_metadata": raw_metadata,
            "software": software,
            "creation_date": creation_date,
            "modification_date": modification_date,
            "has_exif": has_exif,
            "suspicious_indicators": suspicious_indicators,
        }

    @classmethod
    def extract_pdf_metadata(cls, file_path: Path) -> Dict[str, Any]:
        """Extract document metadata from PDF trailer and dictionary entries."""
        raw_metadata: Dict[str, Any] = {}
        software: Optional[str] = None
        creation_date: Optional[datetime] = None
        modification_date: Optional[datetime] = None
        suspicious_indicators: List[str] = []
        page_count = 1

        try:
            reader = pypdf.PdfReader(str(file_path))
            page_count = len(reader.pages)
            meta = reader.metadata
            if meta:
                for k, v in meta.items():
                    key = k.lstrip("/")
                    raw_metadata[key] = str(v)

                creator = raw_metadata.get("Creator")
                producer = raw_metadata.get("Producer")
                software_parts = [s for s in [creator, producer] if s]
                software = " / ".join(software_parts) if software_parts else None

                creation_date = _parse_pdf_date(raw_metadata.get("CreationDate"))
                modification_date = _parse_pdf_date(raw_metadata.get("ModDate"))

        except Exception:
            # Best-effort
            pass

        if software:
            lower_software = software.lower()
            for kw in EDITING_SOFTWARE_KEYWORDS:
                if kw in lower_software:
                    suspicious_indicators.append(
                        f"PDF editing/creation software signature detected: '{software}'"
                    )
                    break

        if creation_date and modification_date:
            diff = (modification_date - creation_date).total_seconds()
            if diff > 86400:
                suspicious_indicators.append(
                    f"PDF timestamp discrepancy: modified {diff / 3600:.1f} hours after creation"
                )

        return {
            "raw_metadata": raw_metadata,
            "software": software,
            "creation_date": creation_date,
            "modification_date": modification_date,
            "has_exif": False,
            "suspicious_indicators": suspicious_indicators,
            "page_count": page_count,
        }
