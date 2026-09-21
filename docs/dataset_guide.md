# Dataset Guide: Academic & Course Certificate Integrity Benchmarks

**Authoritative Documentation on Datasets, Acquisition, Licenses, and Synthetic Augmentation**  
**Project:** AI-Based Detection of Fake or Manipulated Academic Certificates  
**Path:** `docs/dataset_guide.md`  

---

## 1. Executive Summary & Ethics Standard

Document verification and forgery detection models require diverse, high-fidelity datasets spanning physical tampering, synthetic generative inpainting, and digital credential discrepancies.

> [!IMPORTANT]
> **Strict Privacy & Legal Compliance**:
> Under no circumstances may private student transcripts or proprietary certificates be scraped, redistributed, or committed to public version control without explicit authorization. All datasets utilized within this project are either:
> 1. Open research benchmarks under permissible academic/research licenses.
> 2. Synthetically generated specimens using standardized, public certificate layouts created specifically for fraud detection research.

---

## 2. Integrated Research Repositories

### 2.1 Dataset A — DocTamper
- **Repository**: [https://github.com/qcf-568/DocTamper](https://github.com/qcf-568/DocTamper)
- **Primary Use**: Document text tampering, character substitution, numerical grade alteration, and pixel-level tampering localization masks.
- **License / Access**: Research-only license with formal access application required by authors.
- **Acquisition Protocol**:
  Detailed manual application instructions are maintained at `dataset/external/DocTamper/README.md`. Raw binaries are excluded from Git via `.gitignore`.

### 2.2 Dataset B — AIForge-Doc
- **Repository**: [https://github.com/scamai/aiforge-doc](https://github.com/scamai/aiforge-doc)
- **Secondary Reference**: [https://github.com/scamai/gpt_image2_doc_forgery_paper](https://github.com/scamai/gpt_image2_doc_forgery_paper)
- **Primary Use**: AI-generated document forgeries, diffusion-based text inpainting, neural font hallucination, and generative document manipulation.
- **License**: CC-BY-NC 4.0 (Non-commercial research).

### 2.3 Dataset C — QR Threat Detection Dataset
- **Repository**: [https://github.com/KyleVincentPino/qr-threat-detection-dataset](https://github.com/KyleVincentPino/qr-threat-detection-dataset)
- **Primary Use**: QR code classification, corrupted QR recovery, malicious URL detection, and adversarial QR perturbations.
- **Classes**: `benign`, `tampered`, `malicious`.
- **License**: MIT License.

### 2.4 Dataset D — CEDAR Signature Verification Dataset
- **Repository Reference**: [https://github.com/nikostsagk/signature-verification](https://github.com/nikostsagk/signature-verification)
- **Primary Use**: Handwritten signatory stroke modeling, genuine signature verification, and skilled signature forgery detection.
- **License**: Academic research license.

### 2.5 Dataset E — Omni-IML (Optional High-Compute)
- **Repository**: [https://github.com/qcf-568/OmniIML](https://github.com/qcf-568/OmniIML)
- **Primary Use**: Generalized image manipulation localization benchmark. Evaluated when GPU infrastructure permits.

---

## 3. Custom Course Certificate Dataset (`dataset/course_certificates/`)

Public datasets lack the multi-modal coupling between physical certificate documents, embedded QR codes, and live online verification records. To solve this, we synthesized a dedicated research dataset of **4,700 samples** with known ground truth.

### 3.1 Directory Structure
```text
dataset/course_certificates/
├── genuine/                     # 1,500 Authentic certificate specimens
├── tampered/                    # 3,200 Controlled manipulation variants
│   ├── name_changed/            # 300 samples: Student name substituted
│   ├── certificate_id_changed/  # 300 samples: Credential ID substituted
│   ├── date_changed/            # 300 samples: Completion/issue date altered
│   ├── course_changed/          # 300 samples: Course curriculum altered
│   ├── grade_changed/           # 300 samples: Score/honors inflated
│   ├── logo_changed/            # 200 samples: Institutional seal replaced
│   ├── seal_changed/            # 200 samples: Embossed seal altered
│   ├── signature_changed/       # 200 samples: Signatory modified
│   ├── qr_replaced/             # 300 samples: Broken/corrupt QR inserted
│   ├── qr_copied/               # 300 samples: Valid QR pointing to Credential A
│   │                            #               spliced onto Certificate B
│   └── multiple_fields/         # 500 samples: Multi-field compound attacks
├── metadata.csv                 # Ground truth labels & split assignments
└── features_course_certs.csv    # 14-D normalized feature vectors
```

### 3.2 Metadata Schema (`metadata.csv`)
| Column | Type | Description |
|---|---|---|
| `image_id` | `str` | Unique sample identifier (e.g., `sample_0001`) |
| `template_id` | `str` | Base layout template ID for leakage prevention |
| `authenticity` | `int` | Binary ground truth: `1` = Genuine, `0` = Tampered |
| `tamper_type` | `str` | Manipulation category (`genuine`, `name_changed`, `qr_copied`, etc.) |
| `field_changed` | `str` | Specific field modified (`none`, `candidate_name`, `qr_payload`, etc.) |
| `qr_present` | `int` | QR detection flag (`1` / `0`) |
| `qr_valid` | `int` | QR decodability flag (`1` / `0`) |
| `online_match` | `int` | Live online record alignment flag (`1` / `0`) |
| `split` | `str` | Dataset partition (`train`, `val`, `test`) |
| `file_path` | `str` | Relative path to image file |

---

## 4. Group-Based Split Strategy (Zero Data Leakage)

Standard random splitting results in severe evaluation optimism because tampered derivatives of template $K$ leak into both train and test sets.

We enforce **Template Group-Based Splitting**:
- **Train Set**: **70%** (3,312 samples)
- **Validation Set**: **15%** (656 samples)
- **Test Set**: **15%** (732 samples)
- **Leakage Guarantee**:
  $$\text{Templates}(\text{Train}) \cap \text{Templates}(\text{Test}) = \emptyset$$
  $$\text{Templates}(\text{Train}) \cap \text{Templates}(\text{Val}) = \emptyset$$

---

## 5. Reproduction & Execution Scripts

All dataset processing is completely automated via standalone scripts in `dataset/scripts/`:

```powershell
# 1. Prepare directory structure
python dataset/scripts/prepare_certificate_dataset.py

# 2. Structure QR threat evaluation vectors
python dataset/scripts/prepare_qr_dataset.py --count 50

# 3. Generate synthetic tampered dataset & 14-D feature vectors
python dataset/scripts/generate_tampered_certificates.py

# 4. Verify split balance and leakage integrity
python dataset/scripts/create_metadata.py

# Or run complete pipeline in one command:
python dataset/scripts/prepare_datasets.py
```
