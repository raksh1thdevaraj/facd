import datetime
import re
from typing import List, Optional, Tuple

from app.schemas.pipeline import CertificateFields, ConsistencyCheckItem
from app.schemas.primitives import BoundingBox, CheckStatus
from app.schemas.text_consistency import AnomalousRegion, AnomalyType, TextConsistencyConfig


class LogicalConsistencyValidator:
    """Validates temporal chronology, calendar feasibility, numeric grade boundaries,
    and degree qualification logic in certificate entities.
    """

    def __init__(self, config: Optional[TextConsistencyConfig] = None):
        self.config = config or TextConsistencyConfig()

    def analyze(
        self,
        fields: CertificateFields,
        raw_text: Optional[str] = None,
    ) -> Tuple[float, List[AnomalousRegion], List[ConsistencyCheckItem]]:
        """Perform chronological and numerical grade feasibility checks.

        Returns:
            Tuple of:
            - logical_score [0.0, 1.0]
            - list of AnomalousRegion
            - list of ConsistencyCheckItem
        """
        anomalies: List[AnomalousRegion] = []
        checks: List[ConsistencyCheckItem] = []
        now = datetime.datetime.now(datetime.timezone.utc).date()

        # 1. Date Chronology and Future Date Validation
        date_score, date_anomalies, date_check = self._validate_dates(fields, raw_text, now)
        anomalies.extend(date_anomalies)
        checks.append(date_check)

        # 2. Grade and Marks Feasibility Validation
        grade_score, grade_anomalies, grade_check = self._validate_grades(fields, raw_text)
        anomalies.extend(grade_anomalies)
        checks.append(grade_check)

        # 3. Overall composite logical score
        logical_score = min(date_score, grade_score)
        if anomalies:
            logical_score = min(logical_score, max(0.0, 1.0 - (0.35 * len(anomalies))))

        return round(logical_score, 3), anomalies, checks

    def _validate_dates(
        self,
        fields: CertificateFields,
        raw_text: Optional[str],
        now: datetime.date,
    ) -> Tuple[float, List[AnomalousRegion], ConsistencyCheckItem]:
        """Validate that issue dates and graduation dates are realistic and not in the future."""
        issue_date_str = fields.issue_date
        full_text = (raw_text or "") + " " + (issue_date_str or "")

        anomalies: List[AnomalousRegion] = []
        parsed_issue_date: Optional[datetime.date] = None

        if issue_date_str:
            parsed_issue_date = self._parse_date(issue_date_str)

        # Also search for 4-digit years in raw text
        years = [int(y) for y in re.findall(r"\b(19\d\d|20\d\d)\b", full_text)]

        # Check for future issue date
        if parsed_issue_date and parsed_issue_date > now:
            desc = (
                f"Issue date '{issue_date_str}' ({parsed_issue_date.isoformat()}) is in the future"
            )
            anomalies.append(
                AnomalousRegion(
                    anomaly_type=AnomalyType.LOGICAL_CONTRADICTION,
                    severity=1.0,
                    description=desc,
                    bbox=BoundingBox(x1=0.0, y1=0.85, x2=0.5, y2=0.95),
                    token_text=issue_date_str,
                )
            )
            return (
                0.20,
                anomalies,
                ConsistencyCheckItem(
                    rule_id="RULE_DATE_CHRONOLOGY",
                    name="Date Chronology & Feasibility",
                    status=CheckStatus.FAILED,
                    confidence=1.0,
                    details=desc,
                    field_affected="issue_date",
                ),
            )

        # Check for future years in text exceeding current year + 1
        future_years = [y for y in years if y > now.year + 1]
        if future_years:
            desc = f"Extracted academic year {future_years[0]} is in the future"
            anomalies.append(
                AnomalousRegion(
                    anomaly_type=AnomalyType.LOGICAL_CONTRADICTION,
                    severity=0.95,
                    description=desc,
                    bbox=BoundingBox(x1=0.0, y1=0.85, x2=0.5, y2=0.95),
                    token_text=str(future_years[0]),
                )
            )
            return (
                0.30,
                anomalies,
                ConsistencyCheckItem(
                    rule_id="RULE_DATE_CHRONOLOGY",
                    name="Date Chronology & Feasibility",
                    status=CheckStatus.FAILED,
                    confidence=1.0,
                    details=desc,
                    field_affected="issue_date",
                ),
            )

        # Check for impossible historical dates (e.g. before 1950)
        ancient_years = [y for y in years if y < 1950]
        if ancient_years:
            desc = (
                f"Extracted academic year {ancient_years[0]} precedes "
                "modern certificate records (< 1950)"
            )
            anomalies.append(
                AnomalousRegion(
                    anomaly_type=AnomalyType.LOGICAL_CONTRADICTION,
                    severity=0.80,
                    description=desc,
                    bbox=BoundingBox(x1=0.0, y1=0.85, x2=0.5, y2=0.95),
                    token_text=str(ancient_years[0]),
                )
            )
            return (
                0.50,
                anomalies,
                ConsistencyCheckItem(
                    rule_id="RULE_DATE_CHRONOLOGY",
                    name="Date Chronology & Feasibility",
                    status=CheckStatus.WARNING,
                    confidence=0.85,
                    details=desc,
                    field_affected="issue_date",
                ),
            )

        return (
            1.0,
            [],
            ConsistencyCheckItem(
                rule_id="RULE_DATE_CHRONOLOGY",
                name="Date Chronology & Feasibility",
                status=CheckStatus.PASSED,
                confidence=1.0,
                details="Dates conform to chronological expectations and do not lie in the future.",
                field_affected="issue_date",
            ),
        )

    def _validate_grades(
        self,
        fields: CertificateFields,
        raw_text: Optional[str],
    ) -> Tuple[float, List[AnomalousRegion], ConsistencyCheckItem]:
        """Validate numeric grade / CGPA / percentage bounds and honors consistency."""
        grade_str = fields.grade_or_marks or ""
        search_text = f"{grade_str} {raw_text or ''}"

        anomalies: List[AnomalousRegion] = []

        # 1. Check for CGPA out of bounds
        cgpa_match = re.search(
            r"(?:CGPA|GPA|CPI)\s*(?:of|is|:)?\s*([0-9]+(?:\.[0-9]+)?)", search_text, re.IGNORECASE
        )
        if cgpa_match:
            val = float(cgpa_match.group(1))
            if val > 10.0:
                desc = f"Extracted CGPA ({val}) exceeds maximum scale of 10.0"
                anomalies.append(
                    AnomalousRegion(
                        anomaly_type=AnomalyType.LOGICAL_CONTRADICTION,
                        severity=1.0,
                        description=desc,
                        bbox=BoundingBox(x1=0.2, y1=0.5, x2=0.8, y2=0.7),
                        token_text=cgpa_match.group(0),
                    )
                )
                return (
                    0.20,
                    anomalies,
                    ConsistencyCheckItem(
                        rule_id="RULE_GRADE_BOUNDS",
                        name="Academic Grade Feasibility",
                        status=CheckStatus.FAILED,
                        confidence=1.0,
                        details=desc,
                        field_affected="grade_or_marks",
                    ),
                )

        # 2. Check for Percentage out of bounds
        pct_match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*%", search_text)
        if pct_match:
            pct_val = float(pct_match.group(1))
            if pct_val > 100.0:
                desc = (
                    f"Extracted percentage ({pct_val}%) exceeds maximum theoretical limit of 100%"
                )
                anomalies.append(
                    AnomalousRegion(
                        anomaly_type=AnomalyType.LOGICAL_CONTRADICTION,
                        severity=1.0,
                        description=desc,
                        bbox=BoundingBox(x1=0.2, y1=0.5, x2=0.8, y2=0.7),
                        token_text=pct_match.group(0),
                    )
                )
                return (
                    0.20,
                    anomalies,
                    ConsistencyCheckItem(
                        rule_id="RULE_GRADE_BOUNDS",
                        name="Academic Grade Feasibility",
                        status=CheckStatus.FAILED,
                        confidence=1.0,
                        details=desc,
                        field_affected="grade_or_marks",
                    ),
                )

            # Division contradiction: low percentage with "Distinction"
            if pct_val < 60.0 and re.search(
                r"\b(distinction|first\s*class)\b", search_text, re.IGNORECASE
            ):
                desc = (
                    f"Contradiction between score ({pct_val}%) and honors classification "
                    f"('Distinction/First Class' requires >= 60%)"
                )
                anomalies.append(
                    AnomalousRegion(
                        anomaly_type=AnomalyType.LOGICAL_CONTRADICTION,
                        severity=0.85,
                        description=desc,
                        bbox=BoundingBox(x1=0.2, y1=0.5, x2=0.8, y2=0.7),
                        token_text=pct_match.group(0),
                    )
                )
                return (
                    0.40,
                    anomalies,
                    ConsistencyCheckItem(
                        rule_id="RULE_GRADE_BOUNDS",
                        name="Academic Grade Feasibility",
                        status=CheckStatus.FAILED,
                        confidence=0.90,
                        details=desc,
                        field_affected="grade_or_marks",
                    ),
                )

        return (
            1.0,
            [],
            ConsistencyCheckItem(
                rule_id="RULE_GRADE_BOUNDS",
                name="Academic Grade Feasibility",
                status=CheckStatus.PASSED,
                confidence=1.0,
                details="Grades and performance metrics lie within standard academic ranges.",
                field_affected="grade_or_marks",
            ),
        )

    def _parse_date(self, date_str: str) -> Optional[datetime.date]:
        """Try standard date formats to parse the date string."""
        date_str = date_str.strip()
        formats = [
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%B %d, %Y",
            "%b %d, %Y",
            "%d %B %Y",
            "%d %b %Y",
            "%Y/%m/%d",
        ]
        for fmt in formats:
            try:
                return datetime.datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        # Regex fallback for YYYY-MM-DD or DD/MM/YYYY inside text
        iso_match = re.search(
            r"\b(20\d\d|19\d\d)[-/](0[1-9]|1[0-2])[-/](0[1-9]|[12]\d|3[01])\b", date_str
        )
        if iso_match:
            try:
                return datetime.date(
                    int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3))
                )
            except ValueError:
                pass

        return None
