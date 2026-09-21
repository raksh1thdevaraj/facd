# Dataset Documentation & Benchmark References

## AI-Based Academic & Course Certificate Fraud Detection

This document catalogs all datasets, benchmark references, licensing terms, and acquisition procedures supporting the certificate verification platform.

---

## 1. External Research Datasets

| Dataset | Repository / Source | Focus Area | License / Restrictions | Acquisition Protocol |
|---|---|---|---|---|
| **DocTamper** | [qcf-568/DocTamper](https://github.com/qcf-568/DocTamper) | Document text tampering, pixel-level manipulation masks | Academic Research Only (Authorized Access) | See [dataset/external/DocTamper/README.md](external/DocTamper/README.md) |
| **AIForge-Doc** | [scamai/aiforge-doc](https://github.com/scamai/aiforge-doc) | Generative inpainting & AI-edited document forgeries | Research / CC-BY-NC | Clone repository scripts; do not commit large files |
| **QR Threat Detection** | [KyleVincentPino/qr-threat-detection-dataset](https://github.com/KyleVincentPino/qr-threat-detection-dataset) | Malicious, tampered, and benign QR classification | Open Source Research | Use for QR risk feature calibration |
| **CEDAR Signatures** | [nikostsagk/signature-verification](https://github.com/nikostsagk/signature-verification) | Offline genuine and forged signature representations | Educational / CEDAR License | Offline feature calibration for signatory checks |
| **Omni-IML** | [qcf-568/OmniIML](https://github.com/qcf-568/OmniIML) | Image manipulation localization (optional advanced benchmark) | Research Use | Optional benchmark for localized tampering masks |

---

## 2. Custom Course Certificate Dataset (`dataset/course_certificates/`)

To support specific online-credential verification scenarios (including QR detection, verification URLs, and copied-QR attacks), a dedicated dataset is maintained.

### Directory Structure
```text
dataset/course_certificates/
├── genuine/                     # Legitimate completion certificates with active QR links
├── tampered/
│   ├── name_changed/            # Text-edited student/candidate names
│   ├── certificate_id_changed/  # Modified credential alphanumeric IDs
│   ├── date_changed/            # Spliced completion or issue dates
│   ├── course_changed/          # Altered course titles/programs
│   ├── grade_changed/           # Tampered grades, scores, or honors
│   ├── logo_changed/            # Replaced institutional logos/crests
│   ├── seal_changed/            # Modified embossed or colored seals
│   ├── signature_changed/       # Inconsistent instructor signatures
│   ├── qr_replaced/             # Malicious or broken QR code overlays
│   ├── qr_copied/               # Valid QR code transplanted from another credential
│   └── multiple_fields/         # Complex multi-field tampering
└── metadata.csv                 # Ground truth annotations and evaluation splits
```

### Dataset Split Strategy (Leakage Prevention)
To prevent data leakage, samples derived from the same base template or institutional issuer remain strictly within the same partition:
- **Training**: 70%
- **Validation**: 15%
- **Testing**: 15%

---

## 3. Data Privacy & Git Storage Policy
- **NO PRIVATE CERTIFICATES**: Under no circumstances should real personal academic records or certificates be collected without consent.
- **NO LARGE BINARIES IN GIT**: Raw images and large archives must be stored locally under `storage/` or external data drives and are excluded via `.gitignore`.
