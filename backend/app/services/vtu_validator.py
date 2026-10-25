"""
Authoritative Visvesvaraya Technological University (VTU) Schema Validator.

Enforces deterministic institutional rules for VTU and affiliated engineering colleges:
1. 10-character USN validation with regional, college, year, branch, and sequence parsing.
2. Official VTU CBCS & NEP Letter Grade to Grade Point mappings.
3. Deterministic SGPA arithmetic verification with tolerance delta <= 0.01.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

VTU_REGIONS: Dict[str, str] = {
    "1": "Bengaluru Region (Belagavi Jurisdiction)",
    "2": "Belagavi Region (Headquarters)",
    "3": "Kalaburagi Region",
    "4": "Mysuru Region",
}

VTU_COLLEGE_CODES: Dict[str, str] = {
    "MS": "M.S. Ramaiah Institute of Technology (MSRIT), Bengaluru",
    "RV": "R.V. College of Engineering (RVCE), Bengaluru",
    "BM": "B.M.S. College of Engineering (BMSCE), Bengaluru",
    "PE": "P.E.S. Institute of Technology (PESIT), Bengaluru",
    "DS": "Dayananda Sagar College of Engineering (DSCE), Bengaluru",
    "BI": "Bangalore Institute of Technology (BIT), Bengaluru",
    "SI": "Siddaganga Institute of Technology (SIT), Tumakuru",
    "NI": "National Institute of Engineering (NIE), Mysuru",
    "UV": "University Visvesvaraya College of Engineering (UVCE), Bengaluru",
    "GA": "Global Academy of Technology (GAT), Bengaluru",
    "JS": "JSS Academy of Technical Education (JSSATE), Bengaluru",
    "OX": "The Oxford College of Engineering, Bengaluru",
    "RN": "R.N.S. Institute of Technology (RNSIT), Bengaluru",
    "NH": "New Horizon College of Engineering (NHCE), Bengaluru",
    "MV": "Sir M. Visvesvaraya Institute of Technology (SMVIT), Bengaluru",
    "SJ": "B.M.S. Institute of Technology & Management (BMSIT), Bengaluru",
    "AM": "AMC Engineering College, Bengaluru",
    "ME": "B.N.M. Institute of Technology (BNMIT), Bengaluru",
    "AT": "Atria Institute of Technology, Bengaluru",
    "CR": "CMR Institute of Technology (CMRIT), Bengaluru",
    "KL": "K.L.E. Technological University, Belagavi/Hubballi",
    "GI": "Gogte Institute of Technology (GIT), Belagavi",
    "SD": "SDM College of Engineering and Technology, Dharwad",
    "PD": "P.D.A. College of Engineering, Kalaburagi",
    "BK": "Basaveshwar Engineering College (BEC), Bagalkot",
    "BY": "Bapuji Institute of Engineering and Technology (BIET), Davangere",
}

VTU_BRANCH_CODES: Dict[str, str] = {
    "CS": "Computer Science & Engineering",
    "IS": "Information Science & Engineering",
    "EC": "Electronics & Communication Engineering",
    "EE": "Electrical & Electronics Engineering",
    "ME": "Mechanical Engineering",
    "CV": "Civil Engineering",
    "AI": "Artificial Intelligence & Machine Learning",
    "CD": "Computer Science & Design",
    "AD": "Artificial Intelligence & Data Science",
    "CB": "Computer Science & Business Systems",
    "BT": "Biotechnology",
    "AE": "Aeronautical Engineering",
    "AS": "Aerospace Engineering",
    "CH": "Chemical Engineering",
    "IM": "Industrial Engineering & Management",
    "TE": "Telecommunication Engineering",
}

VTU_CBCS_GRADE_POINTS: Dict[str, int] = {
    "O": 10,
    "A+": 9,
    "A": 8,
    "B+": 7,
    "B": 6,
    "C": 5,
    "P": 4,
    "F": 0,
}

USN_PATTERN = re.compile(r"^([1-4])([A-Z]{2})([0-9]{2})([A-Z]{2})([0-9]{3})$", re.IGNORECASE)


class VTUSchemaValidator:
    """Deterministic validator for VTU academic mark sheets."""

    @classmethod
    def parse_and_validate_usn(cls, usn: str) -> Dict[str, Any]:
        """
        Validate and dissect a 10-character VTU University Seat Number (USN).
        Format: [Region(1-4)][College(2)][Year(2)][Branch(2)][Roll(3)]
        """
        cleaned = (usn or "").strip().upper()
        match = USN_PATTERN.match(cleaned)

        if not match:
            return {
                "is_valid": False,
                "usn": cleaned,
                "error": "Invalid USN format. VTU USN must be exactly 10 alphanumeric characters [1-4][A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{3}.",
                "details": None,
            }

        region_digit, college_code, year_code, branch_code, roll_seq = match.groups()

        region_name = VTU_REGIONS.get(region_digit, "Unknown VTU Regional Center")
        college_name = VTU_COLLEGE_CODES.get(college_code, f"VTU Affiliated College [{college_code}]")
        branch_name = VTU_BRANCH_CODES.get(branch_code, f"Engineering Branch [{branch_code}]")

        admission_year = 2000 + int(year_code)

        return {
            "is_valid": True,
            "usn": cleaned,
            "error": None,
            "details": {
                "region_digit": region_digit,
                "region_name": region_name,
                "college_code": college_code,
                "college_name": college_name,
                "admission_year": admission_year,
                "branch_code": branch_code,
                "branch_name": branch_name,
                "roll_sequence": int(roll_seq),
            },
        }

    @classmethod
    def calculate_sgpa(
        cls,
        courses: List[Dict[str, Any]],
        printed_sgpa: Optional[float] = None,
        tolerance: float = 0.01,
    ) -> Dict[str, Any]:
        """
        Compute Semester Grade Point Average (SGPA) using official VTU CBCS Ordinance:
        SGPA = sum(Credits_i * GradePoints_i) / sum(Credits_i)

        Returns discrepancy boolean if |Printed - Calculated| > tolerance.
        """
        if not courses:
            return {
                "total_credits": 0.0,
                "total_quality_points": 0.0,
                "calculated_sgpa": 0.0,
                "printed_sgpa": printed_sgpa,
                "delta": 0.0,
                "is_discrepancy": False,
                "verdict": "UNVERIFIED",
                "breakdown": [],
            }

        total_credits = 0.0
        total_quality_points = 0.0
        breakdown: List[Dict[str, Any]] = []

        for item in courses:
            credits = float(item.get("credits", 0.0))
            grade = str(item.get("grade", "")).strip().upper()

            # Determine grade points
            if "grade_points" in item and item["grade_points"] is not None:
                grade_pts = int(item["grade_points"])
            else:
                grade_pts = VTU_CBCS_GRADE_POINTS.get(grade, 0)

            quality_points = round(credits * grade_pts, 2)
            total_credits += credits
            total_quality_points += quality_points

            breakdown.append({
                "code": item.get("code") or item.get("course_code") or "",
                "title": item.get("title") or item.get("course_name") or "",
                "credits": credits,
                "grade": grade,
                "grade_points": grade_pts,
                "quality_points": quality_points,
            })

        calculated_sgpa = (
            round(total_quality_points / total_credits, 2) if total_credits > 0 else 0.0
        )

        delta = 0.0
        is_discrepancy = False
        verdict = "AUTHENTIC"

        if printed_sgpa is not None:
            delta = round(abs(printed_sgpa - calculated_sgpa), 2)
            if delta > tolerance:
                is_discrepancy = True
                verdict = "FRAUDULENT"

        return {
            "total_credits": round(total_credits, 2),
            "total_quality_points": round(total_quality_points, 2),
            "calculated_sgpa": calculated_sgpa,
            "printed_sgpa": printed_sgpa,
            "delta": delta,
            "tolerance": tolerance,
            "is_discrepancy": is_discrepancy,
            "verdict": verdict,
            "breakdown": breakdown,
        }
