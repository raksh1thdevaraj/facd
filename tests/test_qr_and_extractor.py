"""Unit & Integration Tests for Active QR/URL Verification and High-Accuracy Anchor Extraction.

Validates:
1. Active QR Code & URL Whitelist Verification.
2. Anchor-based spatial field extraction on REVA University and CBSE mark sheets.
3. Unified cross-verification decision logic & score fusion.
"""

from __future__ import annotations

import cv2
import numpy as np
import pytest

from src.extractors.certificate_extractor import HighAccuracyCertificateExtractor
from src.verifiers.qr_url_verifier import QRURLVerifier
from src.verifiers.unified_cross_verifier import UnifiedCrossVerifier


# ==============================================================================
# 1. QRURLVerifier Tests
# ==============================================================================

def test_qr_url_whitelisted_domains():
    verifier = QRURLVerifier()

    # Test Case: Official REVA / University Solutions result portal
    res1 = verifier.verify_payload(
        "https://universitysolutions.in/reva/results?regNo=R21EN001&name=RAKSHITH%20DEVARAJ&sgpa=8.85"
    )
    assert res1["qr_present"] is True
    assert res1["domain_valid"] is True
    assert res1["verified"] is True
    assert "universitysolutions.in" in res1["domain"]

    # Test Case: Coursera credential
    res2 = verifier.verify_payload("https://coursera.org/verify/ABC123XYZ")
    assert res2["qr_present"] is True
    assert res2["domain_valid"] is True
    assert res2["verified"] is True

    # Test Case: NPTEL credential
    res3 = verifier.verify_payload("https://nptel.ac.in/noc/Ecertificate/?q=NPTEL22CS01")
    assert res3["qr_present"] is True
    assert res3["domain_valid"] is True
    assert res3["verified"] is True

    # Test Case: DigiLocker credential
    res4 = verifier.verify_payload("https://digilocker.gov.in/verify/doc123")
    assert res4["qr_present"] is True
    assert res4["domain_valid"] is True
    assert res4["verified"] is True


def test_qr_url_spoofed_or_untrusted_domain():
    verifier = QRURLVerifier()

    # Untrusted domain attempting phishing
    res = verifier.verify_payload("https://fake-reva-university.ru/verify?id=123")
    assert res["qr_present"] is True
    assert res["domain_valid"] is False
    assert res["verified"] is False
    assert "Untrusted or spoofed domain" in res["reason"]


def test_qr_structured_json_payload():
    verifier = QRURLVerifier()
    payload = (
        '{"name": "RAKSHITH DEVARAJ", "reg_no": "R21EN001", "institution": "REVA UNIVERSITY", "sgpa": "8.85"}'
    )
    res = verifier.verify_payload(payload)
    assert res["qr_present"] is True
    assert res["is_url"] is False
    assert res["verified"] is True
    assert res["payload_data"]["name"] == "RAKSHITH DEVARAJ"
    assert res["payload_data"]["sgpa"] == "8.85"


def test_qr_pipe_delimited_digilocker_payload():
    verifier = QRURLVerifier()
    payload = "R21EN001|RAKSHITH DEVARAJ|2024|0x9F82AB"
    res = verifier.verify_payload(payload)
    assert res["qr_present"] is True
    assert res["verified"] is True
    assert res["payload_data"]["reg_no"] == "R21EN001"
    assert res["payload_data"]["name"] == "RAKSHITH DEVARAJ"


# ==============================================================================
# 2. HighAccuracyCertificateExtractor Tests
# ==============================================================================

def test_anchor_field_extraction_reva_student_portal():
    extractor = HighAccuracyCertificateExtractor()

    # Synthetic realistic REVA University marks card text layout
    reva_portal_text = """
    REVA UNIVERSITY, BENGALURU
    RUKMINI KNOWLEDGE PARK, KATTIGENAHALLI, YELAHANKA, BENGALURU - 560064
    PROVISIONAL GRADE / MARKS STATEMENT - B.TECH CSE
    Father Name: DEVARAJU K M
    Mother Name: SARASWATHI
    Student Name: RAKSHITH DEVARAJ
    Reg No: R21EN001
    Semester: 6
    Branch: COMPUTER SCIENCE AND ENGINEERING
    Course: B.TECH (ARTIFICIAL INTELLIGENCE & MACHINE LEARNING)
    S.G.P.A: 8.85
    CGPA: 8.72
    RESULT: PASS WITH DISTINCTION
    """

    inst = extractor._extract_institution(reva_portal_text)
    name = extractor._extract_anchor_field(
        {}, reva_portal_text, ["Student Name", "Candidate Name", "Name"]
    )
    father = extractor._extract_anchor_field({}, reva_portal_text, ["Father Name", "Father's Name"])
    mother = extractor._extract_anchor_field({}, reva_portal_text, ["Mother Name", "Mother's Name"])
    reg = extractor._extract_regex(
        reva_portal_text, r"(?:Reg\.?\s*No\.?|Roll\s*No\.?)\s*[:\-]?\s*([A-Z0-9]+)"
    )
    sgpa = extractor._extract_regex(
        reva_portal_text, r"(?:S\.G\.P\.A|SGPA)\s*[:\-]?\s*(\d+\.?\d*)"
    )

    # Verifications
    assert "REVA UNIVERSITY" in inst
    assert name == "RAKSHITH DEVARAJ"
    assert father == "DEVARAJU K M"
    assert mother == "SARASWATHI"
    assert reg == "R21EN001"
    assert sgpa == "8.85"


def test_anchor_field_extraction_cbse_marksheet():
    extractor = HighAccuracyCertificateExtractor()

    cbse_text = """
    CENTRAL BOARD OF SECONDARY EDUCATION
    SENIOR SCHOOL CERTIFICATE EXAMINATION 2023
    Roll No: 11624892
    Candidate's Name: AARAV SHARMA
    Mother's Name: PRIYA SHARMA
    Father's Name: RAJESH SHARMA
    School: DELHI PUBLIC SCHOOL, R.K. PURAM
    Result: PASS
    """

    inst = extractor._extract_institution(cbse_text)
    name = extractor._extract_anchor_field(
        {}, cbse_text, ["Candidate's Name", "Candidate Name", "Student Name", "Name"]
    )
    roll = extractor._extract_regex(cbse_text, r"(?:Roll\s*No\.?|Reg\.?\s*No\.?)\s*[:\-]?\s*([0-9]+)")
    father = extractor._extract_anchor_field({}, cbse_text, ["Father's Name", "Father Name"])

    assert "CENTRAL BOARD" in inst
    assert name == "AARAV SHARMA"
    assert roll == "11624892"
    assert father == "RAJESH SHARMA"


def test_preprocessing_pipeline_produces_binary_image():
    extractor = HighAccuracyCertificateExtractor()
    # Create test canvas
    canvas = np.full((1200, 1000, 3), 240, dtype=np.uint8)
    cv2.putText(
        canvas, "REVA UNIVERSITY", (100, 150), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (20, 20, 20), 2
    )

    processed = extractor.preprocess_image_for_ocr(canvas)
    assert isinstance(processed, np.ndarray)
    assert len(processed.shape) == 2  # Grayscale binary
    # Check that image was rescaled up since height was < 1500
    assert processed.shape[0] >= 1700
    # Values should be 0 or 255 (Otsu thresholded)
    unique_vals = np.unique(processed)
    assert set(unique_vals).issubset({0, 255})


# ==============================================================================
# 3. UnifiedCrossVerifier Tests
# ==============================================================================

def test_unified_verifier_matching_qr_and_text():
    verifier = UnifiedCrossVerifier()

    # Generate synthetic genuine test document with valid QR code
    canvas = np.full((1800, 1400, 3), 255, dtype=np.uint8)
    cv2.putText(
        canvas, "REVA UNIVERSITY, BENGALURU", (200, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 2
    )
    cv2.putText(
        canvas, "Student Name: RAKSHITH DEVARAJ", (200, 350), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2
    )
    cv2.putText(
        canvas, "Reg No: R21EN001", (200, 450), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2
    )
    cv2.putText(
        canvas, "SGPA: 8.85", (200, 550), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2
    )

    # Encode QR code into document using cv2 or qrcode
    import qrcode

    qr_payload = (
        "https://universitysolutions.in/reva/verify?regNo=R21EN001&name=RAKSHITH%20DEVARAJ&sgpa=8.85"
    )
    qr_img = qrcode.make(qr_payload)
    qr_np = np.array(qr_img.convert("RGB"))
    qr_np_resized = cv2.resize(qr_np, (250, 250))
    canvas[200:450, 1050:1300] = qr_np_resized

    result = verifier.verify_certificate(canvas)

    assert "qr_verification" in result
    assert result["qr_verification"]["qr_present"] is True
    assert result["qr_verification"]["domain_valid"] is True
    assert result["cross_verification"]["name_similarity"] >= 90.0
    assert result["cross_verification"]["matches_qr"] is True
    assert result["final_status"] == "VERIFIED"
    assert result["color"] == "emerald"


def test_unified_verifier_rejects_untrusted_qr_domain():
    verifier = UnifiedCrossVerifier()

    canvas = np.full((1800, 1400, 3), 255, dtype=np.uint8)
    cv2.putText(
        canvas, "REVA UNIVERSITY", (200, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 2
    )
    cv2.putText(
        canvas, "Student Name: RAKSHITH DEVARAJ", (200, 350), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2
    )

    # Spoofed phishing domain
    import qrcode

    qr_payload = "https://untrusted-fake-university.cc/verify?regNo=R21EN001&name=RAKSHITH%20DEVARAJ"
    qr_img = qrcode.make(qr_payload)
    qr_np = np.array(qr_img.convert("RGB"))
    qr_np_resized = cv2.resize(qr_np, (250, 250))
    canvas[200:450, 1050:1300] = qr_np_resized

    result = verifier.verify_certificate(canvas)

    assert result["qr_verification"]["qr_present"] is True
    assert result["qr_verification"]["domain_valid"] is False
    assert result["final_status"] == "REJECTED"
    assert result["color"] == "red"
    assert any("Untrusted or spoofed" in r for r in result["rejection_reasons"])


def test_unified_verifier_rejects_name_tampering_discrepancy():
    verifier = UnifiedCrossVerifier()

    # Document text says "RAKSHITH DEVARAJ"
    canvas = np.full((1800, 1400, 3), 255, dtype=np.uint8)
    cv2.putText(
        canvas, "REVA UNIVERSITY", (200, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 2
    )
    cv2.putText(
        canvas, "Student Name: RAKSHITH DEVARAJ", (200, 350), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2
    )

    # QR says a completely different name (e.g. Forger replaced text on marks card)
    import qrcode

    qr_payload = "https://universitysolutions.in/reva/verify?regNo=R21EN001&name=MICHAEL%20SCOTT"
    qr_img = qrcode.make(qr_payload)
    qr_np = np.array(qr_img.convert("RGB"))
    qr_np_resized = cv2.resize(qr_np, (250, 250))
    canvas[200:450, 1050:1300] = qr_np_resized

    result = verifier.verify_certificate(canvas)

    assert result["cross_verification"]["name_similarity"] < 80.0
    assert result["final_status"] == "REJECTED"
    assert result["color"] == "red"
    assert any("Name discrepancy" in r for r in result["rejection_reasons"])
