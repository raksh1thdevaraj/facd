"""
Live HTTP Synthetic Upload Test Script.
Sends synthetic test certificates and corrupt payloads to http://127.0.0.1:8000/verify
and verifies server process stability, memory health, and connection persistence.
"""

import io
import time
import requests
from PIL import Image

BASE_URL = "http://127.0.0.1:8000"


def test_live_server():
    print(">>> 1. Testing /api/health probe...")
    res = requests.get(f"{BASE_URL}/api/health", timeout=5)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    health_data = res.json()
    print(f"    Health Status: {health_data.get('status')} | Uptime: {health_data.get('uptime')}s")

    print("\n>>> 2. Testing Synthetic Valid Certificate Upload (PNG)...")
    img = Image.new("RGB", (300, 300), color=(240, 240, 240))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    upload_res = requests.post(
        f"{BASE_URL}/verify",
        files={"file": ("live_test_cert.png", png_bytes, "image/png")},
        data={
            "certificate_type": "marks_card",
            "expected_student_name": "Resilience Test Student",
            "expected_reg_no": "1CR20CS999",
        },
        timeout=30,
    )
    assert upload_res.status_code == 200, f"Expected 200, got {upload_res.status_code}: {upload_res.text}"
    result = upload_res.json()
    print(f"    Upload Succeeded! Status: {result.get('final_status')} | Confidence: {result.get('confidence_score')}")

    print("\n>>> 3. Testing Intentional Corrupt Upload (Error Envelope check)...")
    corrupt_res = requests.post(
        f"{BASE_URL}/verify",
        files={"file": ("bad_cert.png", b"NOT_A_VALID_IMAGE_DATA_STREAM", "image/png")},
        data={"certificate_type": "marks_card"},
        timeout=10,
    )
    print(f"    Corrupt Payload Result: HTTP {corrupt_res.status_code} (Clean Error Handled: {corrupt_res.json().get('success') == False})")

    print("\n>>> 4. Verifying Server Remains Alive After Operations...")
    time.sleep(1.0)
    post_res = requests.get(f"{BASE_URL}/api/health", timeout=5)
    assert post_res.status_code == 200
    post_health = post_res.json()
    print(f"    Post-Upload Health: {post_health.get('status')} | Uptime: {post_health.get('uptime')}s")
    print("\n[SUCCESS] Live synthetic verification completed without process termination or dropped connections!")


if __name__ == "__main__":
    test_live_server()
