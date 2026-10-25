"""
Unit tests for VTUSchemaValidator.
"""

from __future__ import annotations

import pytest
from app.services.vtu_validator import VTUSchemaValidator


def test_vtu_valid_usn_parsing():
    result = VTUSchemaValidator.parse_and_validate_usn("1MS21CS045")
    assert result["is_valid"] is True
    assert result["error"] is None
    details = result["details"]
    assert details["region_digit"] == "1"
    assert "Bengaluru" in details["region_name"]
    assert details["college_code"] == "MS"
    assert "Ramaiah" in details["college_name"]
    assert details["admission_year"] == 2021
    assert details["branch_code"] == "CS"
    assert details["branch_name"] == "Computer Science & Engineering"
    assert details["roll_sequence"] == 45


def test_vtu_invalid_usn_formats():
    invalid_cases = [
        "1MS21CS04",     # 9 chars (short)
        "5MS21CS045",    # Invalid region 5
        "1M21CS045",     # 1-letter college code
        "1MS21CSS045",   # 11 chars
        "INVALID_USN",   # random string
        "",              # empty string
    ]
    for usn in invalid_cases:
        res = VTUSchemaValidator.parse_and_validate_usn(usn)
        assert res["is_valid"] is False
        assert res["details"] is None
        assert "Invalid USN format" in res["error"]


def test_vtu_sgpa_exact_calculation():
    # 8-course standard semester
    courses = [
        {"code": "21CS41", "title": "Maths", "credits": 3.0, "grade": "A+"},      # 3 * 9 = 27
        {"code": "21CS42", "title": "Algorithms", "credits": 4.0, "grade": "A+"}, # 4 * 9 = 36
        {"code": "21CS43", "title": "Microcontrollers", "credits": 3.0, "grade": "A"}, # 3 * 8 = 24
        {"code": "21CS44", "title": "OS", "credits": 3.0, "grade": "A"},          # 3 * 8 = 24
        {"code": "21CSL46", "title": "Algo Lab", "credits": 1.5, "grade": "O"},   # 1.5 * 10 = 15
        {"code": "21CSL47", "title": "Micro Lab", "credits": 1.5, "grade": "A+"},# 1.5 * 9 = 13.5
        {"code": "21UH49", "title": "UHV", "credits": 1.0, "grade": "A"},         # 1 * 8 = 8
        {"code": "21CIP48", "title": "Ethics", "credits": 1.0, "grade": "A"},     # 1 * 8 = 8
    ]
    # Total credits = 3 + 4 + 3 + 3 + 1.5 + 1.5 + 1 + 1 = 18.0
    # Total quality pts = 27 + 36 + 24 + 24 + 15 + 13.5 + 8 + 8 = 155.5
    # Calculated SGPA = 155.5 / 18.0 = 8.6388... -> 8.64

    res = VTUSchemaValidator.calculate_sgpa(courses, printed_sgpa=8.64)
    assert res["total_credits"] == 18.0
    assert res["total_quality_points"] == 155.5
    assert res["calculated_sgpa"] == 8.64
    assert res["is_discrepancy"] is False
    assert res["verdict"] == "AUTHENTIC"
    assert res["delta"] == 0.0


def test_vtu_sgpa_tampering_detected():
    # Same courses yielding 8.64, but printed SGPA altered to 9.50
    courses = [
        {"code": "21CS41", "credits": 3.0, "grade": "A+"},
        {"code": "21CS42", "credits": 4.0, "grade": "A+"},
        {"code": "21CS43", "credits": 3.0, "grade": "A"},
        {"code": "21CS44", "credits": 3.0, "grade": "A"},
        {"code": "21CSL46", "credits": 1.5, "grade": "O"},
        {"code": "21CSL47", "credits": 1.5, "grade": "A+"},
        {"code": "21UH49", "credits": 1.0, "grade": "A"},
        {"code": "21CIP48", "credits": 1.0, "grade": "A"},
    ]
    res = VTUSchemaValidator.calculate_sgpa(courses, printed_sgpa=9.50)
    assert res["calculated_sgpa"] == 8.64
    assert res["delta"] == round(abs(9.50 - 8.64), 2)
    assert res["is_discrepancy"] is True
    assert res["verdict"] == "FRAUDULENT"
