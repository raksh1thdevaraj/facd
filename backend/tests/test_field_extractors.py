from app.modules.ocr.field_extractors.cert_id_extractor import CertificateIdExtractor
from app.modules.ocr.field_extractors.date_extractor import DateExtractor
from app.modules.ocr.field_extractors.degree_extractor import DegreeExtractor
from app.modules.ocr.field_extractors.grade_extractor import GradeExtractor
from app.modules.ocr.field_extractors.institution_extractor import (
    InstitutionExtractor,
)
from app.modules.ocr.field_extractors.name_extractor import StudentNameExtractor
from app.modules.ocr.field_extractors.roll_no_extractor import RollNumberExtractor
from app.modules.ocr.spatial_analyzer import SpatialLayoutAnalyzer
from app.modules.ocr.token_builder import TokenBuilder


def _build_tokens_from_lines(lines_text, img_w=1200, img_h=1000):
    tokens = []
    y_step = int(img_h / (len(lines_text) + 2))
    for i, line_str in enumerate(lines_text):
        y_pos = (i + 1) * y_step
        words = line_str.split()
        curr_x = 50
        for w in words:
            tok_w = max(20, len(w) * 14)
            tok = TokenBuilder.create_token(
                text=w,
                confidence=0.95,
                pixel_x=curr_x,
                pixel_y=y_pos,
                pixel_w=tok_w,
                pixel_h=28,
                img_width=img_w,
                img_height=img_h,
            )
            tokens.append(tok)
            curr_x += tok_w + 10
    return tokens


def test_student_name_extractor_prefix():
    lines_text = [
        "THIS IS TO CERTIFY THAT",
        "ALICE MARIE SMITH",
        "HAVING SATISFIED ALL REQUIREMENTS",
    ]
    tokens = _build_tokens_from_lines(lines_text)
    lines = SpatialLayoutAnalyzer.group_tokens_into_lines(tokens)

    extractor = StudentNameExtractor()
    extracted = extractor.extract(lines, tokens)

    assert extracted is not None
    assert extracted.field_name == "student_name"
    assert "ALICE MARIE SMITH" in extracted.value
    assert extracted.confidence >= 0.90


def test_student_name_extractor_labeled():
    lines_text = [
        "NATIONAL UNIVERSITY OF SINGAPORE",
        "Student Name: BOB VANCE",
        "Degree: Bachelor of Science",
    ]
    tokens = _build_tokens_from_lines(lines_text)
    lines = SpatialLayoutAnalyzer.group_tokens_into_lines(tokens)

    extractor = StudentNameExtractor()
    extracted = extractor.extract(lines, tokens)

    assert extracted is not None
    assert extracted.value == "BOB VANCE"


def test_roll_number_extractor_usn_and_labeled():
    lines_text = [
        "VISVESVARAYA TECHNOLOGICAL UNIVERSITY",
        "CANDIDATE USN: 1MS20CS042",
        "DEGREE OF BACHELOR OF ENGINEERING",
    ]
    tokens = _build_tokens_from_lines(lines_text)
    lines = SpatialLayoutAnalyzer.group_tokens_into_lines(tokens)

    extractor = RollNumberExtractor()
    extracted = extractor.extract(lines, tokens)

    assert extracted is not None
    assert extracted.field_name == "register_number"
    assert extracted.value == "1MS20CS042"


def test_degree_extractor():
    lines_text = [
        "THIS IS TO CERTIFY THAT THE CANDIDATE HAS BEEN CONFERRED THE",
        "DEGREE OF Bachelor of Technology in Computer Science and Engineering",
        "WITH ALL RIGHTS AND PRIVILEGES",
    ]
    tokens = _build_tokens_from_lines(lines_text)
    lines = SpatialLayoutAnalyzer.group_tokens_into_lines(tokens)

    extractor = DegreeExtractor()
    extracted = extractor.extract(lines, tokens)

    assert extracted is not None
    assert extracted.field_name == "course_degree"
    assert "Bachelor of Technology" in extracted.value
    assert "Computer Science" in extracted.value


def test_institution_extractor():
    lines_text = [
        "NATIONAL INSTITUTE OF TECHNOLOGY KARNATAKA",
        "SURATHKAL, MANGALORE",
        "THIS IS TO CERTIFY THAT",
    ]
    tokens = _build_tokens_from_lines(lines_text)
    lines = SpatialLayoutAnalyzer.group_tokens_into_lines(tokens)

    extractor = InstitutionExtractor()
    extracted = extractor.extract(lines, tokens)

    assert extracted is not None
    assert extracted.field_name == "institution_name"
    assert "NATIONAL INSTITUTE OF TECHNOLOGY" in extracted.value


def test_date_extractor_various_formats():
    lines_text = [
        "DEGREE CONFERRED ON 15th June 2024",
        "UNDER THE SEAL OF THE SENATE",
    ]
    tokens = _build_tokens_from_lines(lines_text)
    lines = SpatialLayoutAnalyzer.group_tokens_into_lines(tokens)

    extractor = DateExtractor()
    extracted = extractor.extract(lines, tokens)

    assert extracted is not None
    assert extracted.field_name == "issue_date"
    assert extracted.value == "2024-06-15"


def test_grade_extractor():
    lines_text = [
        "OVERALL PERFORMANCE: CGPA: 9.45 / 10.0 First Class with Distinction",
        "CONVOCATION 2024",
    ]
    tokens = _build_tokens_from_lines(lines_text)
    lines = SpatialLayoutAnalyzer.group_tokens_into_lines(tokens)

    extractor = GradeExtractor()
    extracted = extractor.extract(lines, tokens)

    assert extracted is not None
    assert extracted.field_name == "grade_or_marks"
    assert "9.45" in extracted.value
    assert "First Class With Distinction" in extracted.value


def test_cert_id_and_qr_code_extractor():
    # Test printed serial label
    lines_text = [
        "CERTIFICATE NO: VTU-2024-889921",
    ]
    tokens = _build_tokens_from_lines(lines_text)
    lines = SpatialLayoutAnalyzer.group_tokens_into_lines(tokens)

    extractor = CertificateIdExtractor()
    extracted = extractor.extract(lines, tokens)

    assert extracted is not None
    assert extracted.field_name == "certificate_number"
    assert extracted.value == "VTU-2024-889921"
