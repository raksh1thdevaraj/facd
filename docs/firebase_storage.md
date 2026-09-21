# Firebase Cloud Storage Structure & Quotas

**Project:** AI-Based Detection of Fake or Manipulated Academic Certificates  
**Bucket:** `certcheck-60f6c.firebasestorage.app`  

---

## 1. Directory Structure

```text
gs://certcheck-60f6c.firebasestorage.app/
└── certificates/
    └── {userId}/
        └── {certificateId}/
            ├── original_document.pdf
            ├── preprocessed_canvas.png
            ├── qr_region_crop.png
            └── ela_heatmap.png
```

---

## 2. Quotas & Constraints

- **Maximum Upload Size:** 15MB (`15 * 1024 * 1024` bytes)
- **Supported Formats:**
  - `application/pdf`
  - `image/png`
  - `image/jpeg`
  - `image/webp`
- **Ownership Partitioning:** Strict multi-tenant isolation keyed by `userId`.
