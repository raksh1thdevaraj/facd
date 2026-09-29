"""E2E Verification Contract Test & QR Multi-Stage Test."""

import io
import json
import numpy as np
import cv2
import requests
import qrcode
from PIL import Image

def generate_vtu_test_image():
    """Create a synthetic VTU marks card with a top-right QR code."""
    img = np.full((1200, 900, 3), 255, dtype=np.uint8)
    
    # Title
    cv2.putText(img, "VISVESVARAYA TECHNOLOGICAL UNIVERSITY", (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    cv2.putText(img, "BELAGAVI, KARNATAKA", (300, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
    cv2.putText(img, "PROVISIONAL MARKS CARD - B.E. DEGREE", (180, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    
    # Student Data
    cv2.putText(img, "USN: 1MS21CS001", (100, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.putText(img, "Student Name: ADITYA SHARMA", (100, 310), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.putText(img, "Branch: COMPUTER SCIENCE AND ENGINEERING", (100, 360), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
    cv2.putText(img, "SGPA: 8.75", (100, 410), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    
    # Top-right QR Code pointing to VTU results portal
    qr = qrcode.QRCode(box_size=4, border=2)
    qr.add_data("https://results.vtu.ac.in/vitaviresultcbcs24/resultpage.php?usn=1MS21CS001")
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_np = np.array(qr_img.convert("RGB"))
    qr_h, qr_w = qr_np.shape[:2]
    
    # Place QR in top-right
    img[80:80+qr_h, 680:680+qr_w] = qr_np
    
    _, enc = cv2.imencode(".png", img)
    return enc.tobytes()

def generate_coursera_test_image():
    """Create a synthetic Coursera certificate with bottom-right verification URL and QR."""
    img = np.full((900, 1200, 3), 255, dtype=np.uint8)
    
    cv2.putText(img, "COURSERA VERIFIED CERTIFICATE", (350, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2)
    cv2.putText(img, "This is to certify that", (480, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (50, 50, 50), 1)
    cv2.putText(img, "ROHAN GUPTA", (430, 290), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 0, 0), 2)
    cv2.putText(img, "has successfully completed Neural Networks and Deep Learning", (240, 360), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (30, 30, 30), 2)
    cv2.putText(img, "Certificate ID: COURSERA9876543210", (150, 750), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (50, 50, 50), 1)
    cv2.putText(img, "Verify at https://coursera.org/verify/COURSERA9876543210", (150, 780), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (50, 50, 50), 1)
    
    # Bottom-right QR code
    qr = qrcode.QRCode(box_size=4, border=2)
    qr.add_data("https://coursera.org/verify/COURSERA9876543210")
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_np = np.array(qr_img.convert("RGB"))
    qr_h, qr_w = qr_np.shape[:2]
    
    img[650:650+qr_h, 950:950+qr_w] = qr_np
    
    _, enc = cv2.imencode(".png", img)
    return enc.tobytes()

def test_vtu_verification():
    print("--- Testing VTU Marks Card Verification ---")
    img_bytes = generate_vtu_test_image()
    files = {"file": ("vtu_sample.png", img_bytes, "image/png")}
    data = {"certificate_type": "marks_card"}
    
    resp = requests.post("http://127.0.0.1:8000/api/v1/verify", files=files, data=data, timeout=60)
    print("Status code:", resp.status_code)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    body = resp.json()
    print("Response JSON keys:", list(body.keys()))
    print("document_type:", body.get("document_type"))
    print("extracted_data:", body.get("extracted_data"))
    print("qr_verification:", body.get("qr_verification"))
    print("rag_validation:", body.get("rag_validation"))
    print("verdict:", body.get("verdict"))
    print("confidence_score:", body.get("confidence_score"))
    
    # Contract validation (Step 5)
    assert body.get("success") is True
    assert body.get("source") == "live_extraction"
    assert body.get("document_type") == "VTU_MARKSCARD"
    assert "student_name" in body["extracted_data"]
    assert "identifier" in body["extracted_data"]
    assert "issuer" in body["extracted_data"]
    assert "date" in body["extracted_data"]
    assert "score_or_cgpa" in body["extracted_data"]
    assert "detected" in body["qr_verification"]
    assert "matches_document_text" in body["qr_verification"]
    assert "schema_matched" in body["rag_validation"]
    assert "arithmetic_valid" in body["rag_validation"]
    assert "anomalies_detected" in body["rag_validation"]
    assert body.get("verdict") in ["AUTHENTIC", "SUSPICIOUS", "FRAUDULENT"]
    assert isinstance(body.get("confidence_score"), (int, float))
    print(">>> VTU Marks Card Contract: PASSED\n")

def test_coursera_verification():
    print("--- Testing Coursera Certificate Verification ---")
    img_bytes = generate_coursera_test_image()
    files = {"file": ("coursera_sample.png", img_bytes, "image/png")}
    data = {"certificate_type": "course_certificate"}
    
    resp = requests.post("http://127.0.0.1:8000/api/v1/verify", files=files, data=data, timeout=30)
    print("Status code:", resp.status_code)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    body = resp.json()
    print("document_type:", body.get("document_type"))
    print("extracted_data:", body.get("extracted_data"))
    print("qr_verification:", body.get("qr_verification"))
    print("rag_validation:", body.get("rag_validation"))
    print("verdict:", body.get("verdict"))
    
    assert body.get("document_type") == "ONLINE_COURSE_CERTIFICATE"
    assert body["qr_verification"]["detected"] is True
    assert "coursera.org" in str(body["qr_verification"]["payload_or_url"])
    print(">>> Coursera Certificate Contract: PASSED\n")

if __name__ == "__main__":
    test_vtu_verification()
    test_coursera_verification()
    print("ALL TESTS PASSED SUCCESSFULLY!")
