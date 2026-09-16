# Phase 10 — Deep Learning Visual Model

## 1. Purpose

Implement the deep learning visual classification subsystem. This branch fine-tunes a pretrained Convolutional Neural Network (CNN) backbone (EfficientNet-B0 / ResNet-50 via PyTorch/torchvision) on certificate images to learn subtle visual, texture, border, and pixel-level tampering patterns directly from raw pixel data. The model produces visual forgery predictions, visual feature embeddings (512-dimensional vector for multimodal fusion in Phase 11), and Grad-CAM (Gradient-weighted Class Activation Mapping) heatmaps for visual explainability.

## 2. Why This Phase Exists

While Phase 09’s classical ML model operates on hand-engineered tabular features, deep learning models excel at discovering un-modeled pixel patterns:
- Micro-texture inconsistencies across paper backgrounds and anti-copy guilloche patterns.
- Subtle boundary seams around spliced photos, stamps, or signatures that evade SIFT keypoint thresholds.
- Printer dithering and halftoning artifacts (inkjet vs. laser printer dot structures).
- Rich visual feature embeddings: The penultimate layer outputs a compact, highly descriptive 512-dimensional representation of visual authenticity that fuses directly with textual embeddings in Phase 11.
- Grad-CAM heatmaps: Backpropagating classification gradients into the final convolutional layer highlights exactly which visual pixels led the CNN to classify a document as fraudulent.

## 3. Requirements Covered

| Requirement | Description | Implementation in this Phase |
|---|---|---|
| **FR-DL-01** | Pretrained CNN backbone fine-tuning (EfficientNet-B0 / ResNet-50) | PyTorch transfer learning pipeline with frozen backbone and custom classification head |
| **FR-DL-02** | Comprehensive data augmentation pipeline (rotation, jitter, erasing, noise) | Torchvision augmentation transforms simulating scanning and photography distortions |
| **FR-DL-03** | Visual feature embedding extraction (512-dim vector from penultimate layer) | Forward hook / embedding extractor for downstream multimodal fusion |
| **FR-DL-04** | Grad-CAM heatmap generation for visual explainability | PyTorch Grad-CAM integration visualizing salient tampering regions |
| **FR-DL-05** | Deep learning performance target: Accuracy $\ge 90\%$, F1-Score $\ge 0.90$ | Learning rate scheduling, early stopping, and binary cross-entropy with logits |
| **NFR-01** | High accuracy ($\ge 90\%$ F1-score) | Modern CNN architecture fine-tuned on balanced certificate dataset |
| **NFR-03** | Inference latency ($< 500$ms on CPU, $< 100$ms on GPU) | TorchScript / ONNX export and batch dimension optimization |
| **TC-DL-01** | CNN backbone loading and fine-tuning test | Chip DL-11 |
| **TC-DL-02** | Deep learning evaluation metrics verification ($\ge 90\%$ Acc/F1) | Chip DL-11 |
| **TC-DL-03** | Visual feature embedding extraction test (512-dim vector) | Chip DL-12 |
| **TC-DL-04** | Grad-CAM visualization of manipulated regions test | Chip DL-12 |
| **TC-DL-05** | Inference latency and memory benchmarking test | Chip DL-12 |

## 4. Inputs

- Labeled image dataset from Phase 02 (`ml/data/train/`, `ml/data/val/`, `ml/data/test/`).
- Preprocessed enhanced certificate images from Phase 04.
- Hyperparameter configuration (`ml/configs/dl_model_config.json`).

## 5. Outputs

- Trained PyTorch model checkpoint (`ml/models/visual_cnn_best.pt`).
- Quantized / TorchScript production artifact (`ml/models/visual_cnn_scripted.pt`).
- Visual embedding extractor returning `np.ndarray` of shape `(512,)`.
- Grad-CAM heatmap visualization overlay (`storage/reports/{uuid}_gradcam_overlay.png`).
- Model evaluation report and training history loss curves (`ml/reports/dl_training_history.json`, `ml/reports/dl_roc_curve.png`).
- Production visual inference service (`VisualCNNService`).

## 6. Dependencies

- **Previous phases:** Phase 01 (Foundation), Phase 02 (Dataset), Phase 04 (Preprocessing).
- **Libraries:** `torch` (PyTorch 2.x), `torchvision`, `numpy`, `Pillow`, `opencv-python-headless`, `matplotlib`, `pytorch-grad-cam` (or custom autograd Grad-CAM), `pydantic`.

## 7. Files and Folder Structure

```
backend/
├── app/
│   ├── modules/
│   │   └── visual_model/
│   │       ├── __init__.py
│   │       ├── network.py             # CNN architecture definition (Backbone + Head)
│   │       ├── transforms.py          # PyTorch image normalization and resizing
│   │       ├── embedding_extractor.py # Penultimate layer 512D visual vector extractor
│   │       ├── gradcam.py             # Grad-CAM heatmap generator
│   │       └── service.py             # Orchestrator: VisualCNNService
│   └── schemas/
│       └── visual_prediction.py       # Pydantic schemas: VisualPredictionResult
├── ml/
│   ├── configs/
│   │   └── dl_model_config.json       # Hyperparameters (batch_size, lr, epochs, image_size)
│   ├── scripts/
│   │   ├── dataset_loader.py          # PyTorch Dataset and DataLoader with augmentations
│   │   ├── train_visual_cnn.py        # Training loop, validation, and early stopping
│   │   ├── evaluate_visual_cnn.py     # Test evaluation, ROC-AUC, confusion matrix
│   │   └── export_visual_model.py     # TorchScript / ONNX export and quantization
│   ├── models/
│   │   └── visual_cnn_best.pt
│   └── reports/
│       ├── dl_metrics.json
│       ├── dl_loss_curves.png
│       └── sample_gradcam.png
└── tests/
    └── unit/
        ├── test_visual_network.py
        ├── test_visual_transforms.py
        ├── test_embedding_extractor.py
        ├── test_gradcam.py
        └── test_visual_service.py
```

---

## 8. Implementation Chips

---

### CHIP DL-01 — Visual CNN Architecture & Custom Classification Head

**Objective:** Define the neural network architecture using a pretrained backbone (EfficientNet-B0 or ResNet-50) with a custom binary classification head and feature embedding projection layer (FR-DL-01, FR-DL-03).

**Why:** Pretrained ImageNet weights provide rich low-level visual filters (edges, textures, gradients). Replacing the final 1000-class head with a custom pooling and projection head allows binary authenticity classification while isolating a clean 512D embedding vector for multimodal fusion.

**Dependencies:** Phase 01 Foundation.

**Files to create:**
- `backend/app/modules/visual_model/network.py`

**Implementation:**
1. Implement `CertificateVisualCNN(nn.Module)`:
   ```python
   class CertificateVisualCNN(nn.Module):
       def __init__(self, backbone_name: str = "efficientnet_b0", pretrained: bool = True, embedding_dim: int = 512):
           super().__init__()
           if backbone_name == "efficientnet_b0":
               weights = models.EfficientNet_B0_Weights.DEFAULT if pretrained else None
               base_model = models.efficientnet_b0(weights=weights)
               in_features = base_model.classifier[1].in_features  # 1280
               base_model.classifier = nn.Identity()
               self.backbone = base_model
           elif backbone_name == "resnet50":
               weights = models.ResNet50_Weights.DEFAULT if pretrained else None
               base_model = models.resnet50(weights=weights)
               in_features = base_model.fc.in_features  # 2048
               base_model.fc = nn.Identity()
               self.backbone = base_model

           # Visual embedding projection layer (512-dim)
           self.embedding_layer = nn.Sequential(
               nn.Linear(in_features, embedding_dim),
               nn.BatchNorm1d(embedding_dim),
               nn.ReLU(inplace=True),
               nn.Dropout(p=0.3),
           )

           # Binary classification output head (logits)
           self.classifier = nn.Linear(embedding_dim, 1)

       def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
           features = self.backbone(x)                     # (B, in_features)
           embeddings = self.embedding_layer(features)     # (B, 512)
           logits = self.classifier(embeddings)            # (B, 1)
           return logits.squeeze(-1), embeddings
   ```
2. Support model freezing: Implement `freeze_backbone()` and `unfreeze_backbone()` methods for two-stage transfer learning.

**Inputs:** Input image tensor of shape `(B, 3, H, W)`.

**Outputs:** Logits tensor of shape `(B,)` and embeddings tensor of shape `(B, 512)`.

**Acceptance Criteria:**
- Network instantiates cleanly, passes dummy tensor of shape `(2, 3, 512, 512)`, and outputs correct logits and 512D embeddings.

---

### CHIP DL-02 — Data Augmentation & Normalization Pipeline

**Objective:** Implement PyTorch `transforms.Compose` pipelines for training (aggressive augmentations) and inference/validation (deterministic normalization) (FR-DL-02).

**Why:** Synthetic certificate datasets can suffer from overfitting to specific template colors. Data augmentation forces the CNN to learn invariant geometric and texture artifacts rather than memorizing template text.

**Dependencies:** CHIP DL-01.

**Files to create:**
- `backend/app/modules/visual_model/transforms.py`

**Implementation:**
1. ImageNet standard normalization: `mean = [0.485, 0.456, 0.406]`, `std = [0.229, 0.224, 0.225]`.
2. Input resolution: Standardize to $512 \times 512$ pixels (or $224 \times 224$ for fast CPU mode).
3. Training transform pipeline:
   - `transforms.Resize((512, 512))`
   - `transforms.RandomHorizontalFlip(p=0.0)` (Never flip certificates horizontally — text would be mirrored!)
   - `transforms.RandomRotation(degrees=(-5, 5), fill=255)` (Simulate scan tilt)
   - `transforms.ColorJitter(brightness=0.15, contrast=0.2, saturation=0.1, hue=0.05)` (Simulate scanner color variations)
   - `transforms.GaussianBlur(kernel_size=3, sigma=(0.1, 1.0))` (Simulate out-of-focus capture, $p=0.3$)
   - `transforms.ToTensor()`
   - `transforms.RandomErasing(p=0.2, scale=(0.02, 0.1), ratio=(0.5, 2.0), value=255)` (Simulate folded/obscured text)
   - `transforms.Normalize(mean=mean, std=std)`
4. Validation and Inference transform pipeline:
   - `transforms.Resize((512, 512))`
   - `transforms.ToTensor()`
   - `transforms.Normalize(mean=mean, std=std)`

**Acceptance Criteria:**
- Training transforms apply realistic physical document augmentations without corrupting readability.
- Validation transforms are strictly deterministic.

---

### CHIP DL-03 — PyTorch Dataset & Balanced DataLoader Implementation

**Objective:** Implement custom `CertificateDataset` reading images from Phase 02 split directories with multi-worker prefetching and class-balanced sampling.

**Why:** Ensures high-throughput GPU/CPU utilization during training and prevents majority-class bias if the dataset has class imbalance.

**Dependencies:** CHIP DL-02, Phase 02 Dataset.

**Files to create:**
- `ml/scripts/dataset_loader.py`

**Implementation:**
1. Implement `CertificateImageDataset(Dataset)`:
   - Read image file paths and labels (`0 = Genuine`, `1 = Manipulated`) from split CSV manifests.
   - Load image using `PIL.Image.open(path).convert("RGB")`.
   - Apply assigned transform pipeline.
   - Return dictionary: `{"image": tensor, "label": float_tensor, "path": str}`.
2. Implement `create_dataloaders(config: dict) -> Tuple[DataLoader, DataLoader, DataLoader]`:
   - Compute class sample weights: `weights = 1.0 / class_counts`.
   - Use `WeightedRandomSampler` for training split if class imbalance exceeds 60:40.
   - Set `num_workers=4`, `pin_memory=True` (if CUDA available), `batch_size=16` (or 32).

**Acceptance Criteria:**
- Loads images efficiently without memory leaks; returns balanced batches.

---

### CHIP DL-04 — Two-Stage Transfer Learning Training Loop

**Objective:** Implement training script using two-stage fine-tuning (Stage 1: Frozen backbone, train head only; Stage 2: Unfreeze upper layers with discriminative learning rates) (FR-DL-01, FR-DL-05).

**Why:** Prevents destroying pretrained ImageNet feature filters in early epochs. Stage 1 aligns the custom 512D head, while Stage 2 fine-tunes top convolutional layers specifically on certificate forgery textures.

**Dependencies:** CHIP DL-01, CHIP DL-02, CHIP DL-03.

**Files to create:**
- `ml/scripts/train_visual_cnn.py`

**Implementation:**
1. Loss function: `BCEWithLogitsLoss(pos_weight=pos_weight)`.
2. Stage 1 (Epochs 1–5):
   - Freeze backbone weights (`requires_grad = False`).
   - Optimizer: `AdamW(classifier.parameters(), lr=1e-3, weight_decay=1e-2)`.
   - Train custom embedding and classification head.
3. Stage 2 (Epochs 6–20):
   - Unfreeze top convolutional blocks of backbone.
   - Optimizer with discriminative learning rates:
     - Backbone: `lr=5e-5`
     - Custom Head: `lr=5e-4`
   - Scheduler: `CosineAnnealingLR(optimizer, T_max=15, eta_min=1e-6)`.
4. Validation & Early Stopping:
   - Evaluate validation loss and validation F1-score at the end of every epoch.
   - Save best checkpoint if `val_f1` improves: `torch.save(checkpoint, "ml/models/visual_cnn_best.pt")`.
   - Early stopping trigger: If `val_f1` does not improve for 5 consecutive epochs, terminate training.
5. Record training/validation loss and F1 history to `ml/reports/dl_training_history.json`.

**Acceptance Criteria:**
- Completes 2-stage training; saves best checkpoint with optimal validation F1-score (TC-DL-01).

---

### CHIP DL-05 — Deep Learning Evaluation & ROC-AUC Benchmark

**Objective:** Benchmark the trained visual model on the held-out test set, evaluating Accuracy, Precision, Recall, F1-Score, ROC-AUC, and verifying the target performance threshold of $\ge 90\%$ (FR-DL-05, NFR-01).

**Why:** Formally validates that the deep learning vision model surpasses the 85% baseline threshold, meeting the major project target specification.

**Dependencies:** CHIP DL-04.

**Files to create:**
- `ml/scripts/evaluate_visual_cnn.py`

**Implementation:**
1. Load `visual_cnn_best.pt` in `eval()` mode.
2. Iterate through `test_loader` without gradient computation (`torch.no_grad()`).
3. Compute predictions: `probs = torch.sigmoid(logits).cpu().numpy()`, `preds = (probs >= 0.50).astype(int)`.
4. Calculate metrics:
   - Test Accuracy
   - Test Precision
   - Test Recall
   - Test F1-Score
   - ROC-AUC Score
5. Check target assertion:
   ```python
   assert test_f1 >= 0.90, f"Visual model F1 {test_f1} is below 0.90 specification"
   assert test_accuracy >= 0.90, f"Visual model accuracy {test_accuracy} is below 0.90 specification"
   ```
6. Generate and save visualizations:
   - `ml/reports/dl_confusion_matrix.png`
   - `ml/reports/dl_roc_curve.png`
   - `ml/reports/dl_metrics.json`

**Acceptance Criteria:**
- Test set performance satisfies Accuracy $\ge 90\%$ and F1-Score $\ge 0.90$ (TC-DL-02).

---

### CHIP DL-06 — Visual Feature Embedding Extractor

**Objective:** Implement dedicated module to extract the 512-dimensional visual embedding vector from the penultimate layer of the CNN for any certificate image (FR-DL-03).

**Why:** These embeddings capture abstract visual and texture features (borders, stamps, paper grain, font style). They are directly concatenated with textual embeddings in Phase 11 to form the multimodal representation.

**Dependencies:** CHIP DL-01, CHIP DL-04.

**Files to create:**
- `backend/app/modules/visual_model/embedding_extractor.py`

**Implementation:**
1. Implement `VisualEmbeddingExtractor`:
   ```python
   class VisualEmbeddingExtractor:
       def __init__(self, model: CertificateVisualCNN, device: torch.device):
           self.model = model
           self.device = device

       def extract(self, image_tensor: torch.Tensor) -> np.ndarray:
           # Input tensor: (1, 3, 512, 512)
           self.model.eval()
           with torch.no_grad():
               image_tensor = image_tensor.to(self.device)
               _, embedding = self.model(image_tensor)
               # L2-normalize embedding vector:
               embedding = F.normalize(embedding, p=2, dim=1)
               return embedding.cpu().numpy().squeeze(0)  # Shape (512,)
   ```
2. Ensure embedding vector is normalized ($\|v\|_2 = 1.0$) for cosine similarity comparison.

**Inputs:** Preprocessed certificate image.

**Outputs:** 512-dimensional float32 NumPy array.

**Acceptance Criteria:**
- Consistently outputs normalized 512-dimensional embedding vector (TC-DL-03).

---

### CHIP DL-07 — Grad-CAM Visual Explainability Generator

**Objective:** Implement Gradient-weighted Class Activation Mapping (Grad-CAM) to highlight the exact spatial pixel regions that influenced the CNN’s classification of a certificate as forged (FR-DL-04).

**Why:** Neural networks are traditionally "black boxes". Grad-CAM provides visual justification by visualizing which specific parts of the image (e.g. an altered date, a pasted seal, or an anomalous border) triggered the fraud prediction.

**Dependencies:** CHIP DL-01, CHIP DL-04.

**Files to create:**
- `backend/app/modules/visual_model/gradcam.py`

**Implementation:**
1. Implement `GradCAMExplainer`:
   - Target layer: Final convolutional layer of backbone (e.g. `backbone.features[-1]` for EfficientNet, or `backbone.layer4[-1]` for ResNet).
   - Register forward hook to capture activations $A^k$.
   - Register backward hook to capture gradients $\frac{\partial Y^c}{\partial A^k}$.
2. Forward pass input image through model to obtain prediction score for target class (Manipulated).
3. Backward pass score through target convolutional layer.
4. Compute importance weights: $\alpha_k^c = \frac{1}{Z} \sum_i \sum_j \frac{\partial Y^c}{\partial A_{i, j}^k}$.
5. Compute weighted combination of activation maps:
   $$L_{\text{Grad-CAM}}^c = \text{ReLU}\left(\sum_k \alpha_k^c A^k\right)$$
6. Upsample heatmap to original image resolution $(W, H)$ via bilinear interpolation.
7. Normalize heatmap to $[0.0, 1.0]$ and overlay using OpenCV `cv2.COLORMAP_JET`:
   ```python
   overlay = cv2.addWeighted(raw_bgr, 0.65, cam_colored, 0.35, 0)
   ```
8. Save annotated visual heatmap to `storage/reports/{uuid}_gradcam_overlay.png`.

**Inputs:** Raw image and model checkpoint.

**Outputs:** Visual Grad-CAM heatmap array, saved PNG overlay path.

**Testing:** Test on synthetic certificate with manipulated student name; verify Grad-CAM attention peak focuses on the name region (TC-DL-04).

**Acceptance Criteria:**
- Successfully renders Grad-CAM heatmap highlighting salient tampering regions.

---

### CHIP DL-08 — Model Optimization, TorchScript Export & CPU Quantization

**Objective:** Export the trained PyTorch model to TorchScript (`torch.jit.trace`) and apply dynamic INT8 quantization to accelerate CPU inference latency to $< 300$ms (NFR-03).

**Why:** Most production deployment servers and developer laptops run on CPU. Full FP32 PyTorch models can take 600–900ms per inference. Dynamic INT8 quantization cuts latency by 60% with $< 0.5\%$ loss in accuracy.

**Dependencies:** CHIP DL-04.

**Files to create:**
- `ml/scripts/export_visual_model.py`

**Implementation:**
1. Load FP32 model checkpoint.
2. Trace model with dummy input:
   ```python
   dummy_input = torch.randn(1, 3, 512, 512)
   traced_model = torch.jit.trace(model, dummy_input)
   traced_model.save("ml/models/visual_cnn_traced.pt")
   ```
3. Apply PyTorch dynamic quantization for CPU:
   ```python
   quantized_model = torch.quantization.quantize_dynamic(
       model, {nn.Linear}, dtype=torch.qint8
   )
   torch.save(quantized_model.state_dict(), "ml/models/visual_cnn_quantized.pt")
   ```
4. Benchmark latency: Run 50 inferences on CPU and record mean milliseconds.

**Acceptance Criteria:**
- Traced model reduces file size by ~40% and achieves CPU inference latency $< 300$ms (TC-DL-05).

---

### CHIP DL-09 — Production Visual CNN Inference Service

**Objective:** Implement the production `VisualCNNService` singleton managing model loading, batch inference, embedding generation, and Grad-CAM creation in the backend.

**Why:** Provides a single, thread-safe service interface for the verification pipeline and populates the `ml_prediction` database entity with visual scores.

**Dependencies:** CHIP DL-01 through CHIP DL-08.

**Files to create:**
- `backend/app/modules/visual_model/service.py`

**Implementation:**
1. Implement `VisualCNNService`:
   ```python
   class VisualCNNService:
       def __init__(self, model_path: Path, device: str = "cpu"):
           self.device = torch.device(device)
           self.model = self._load_model(model_path)
           self.transforms = get_inference_transforms(image_size=512)
           self.embedding_extractor = VisualEmbeddingExtractor(self.model, self.device)
           self.gradcam = GradCAMExplainer(self.model)

       def predict(self, image_path: Path, certificate_id: UUID) -> VisualPredictionResult:
           # 1. Load image and apply transforms
           # 2. Run inference: logits, embedding = self.model(tensor)
           # 3. fake_prob = torch.sigmoid(logits).item()
           # 4. If fake_prob >= 0.50, generate Grad-CAM heatmap overlay
           # 5. Return VisualPredictionResult(
           #        fake_probability=fake_prob,
           #        predicted_label="MANIPULATED" if fake_prob >= 0.50 else "GENUINE",
           #        visual_embedding=embedding,
           #        gradcam_image_path=gradcam_path
           #    )
   ```

**Acceptance Criteria:**
- Executes prediction, embedding extraction, and Grad-CAM generation within 500ms total.

---

### CHIP DL-10 — Visual Model CLI Diagnostics & Inference Script

**Objective:** Build a CLI tool to run the visual model and Grad-CAM on any image file and display prediction probabilities and activation heatmaps.

**Dependencies:** CHIP DL-09.

**Files to create:**
- `backend/scripts/run_visual_model.py`

**Acceptance Criteria:**
- Accepts `--image <path>` and prints prediction probabilities and saves Grad-CAM image.

---

### CHIP DL-11 — Unit Tests: CNN Training and Evaluation Metrics

**Objective:** Test visual CNN model training loop, checkpoint saving, and verify test evaluation metrics meet the $\ge 90\%$ accuracy and F1 threshold (TC-DL-01, TC-DL-02).

**Dependencies:** CHIP DL-01, CHIP DL-04, CHIP DL-05.

**Files to create:**
- `backend/tests/unit/test_visual_network.py`

**Implementation:**
1. Test `test_visual_cnn_forward_pass()`: Pass dummy input tensor `(2, 3, 512, 512)`; verify output shapes `(2,)` for logits and `(2, 512)` for embeddings (TC-DL-01).
2. Test `test_evaluation_metrics_exceed_90_percent()`: Verify test set evaluation metrics satisfy Accuracy $\ge 0.90$ and F1 $\ge 0.90$ (TC-DL-02, NFR-01).

**Acceptance Criteria:**
- Confirms deep learning visual model meets all target accuracy specifications.

---

### CHIP DL-12 — Unit Tests: Embeddings, Grad-CAM and Latency

**Objective:** Test visual embedding normalization, Grad-CAM heatmap generation, and verify inference latency is $< 500$ms on CPU (TC-DL-03, TC-DL-04, TC-DL-05).

**Dependencies:** CHIP DL-06, CHIP DL-07, CHIP DL-08, CHIP DL-09.

**Files to create:**
- `backend/tests/unit/test_embedding_extractor.py`
- `backend/tests/unit/test_gradcam.py`
- `backend/tests/unit/test_visual_service.py`

**Implementation:**
1. Test `test_visual_embedding_extraction()`: Verify returned vector has shape `(512,)` and L2 norm is $1.0 \pm 1e-4$ (TC-DL-03).
2. Test `test_gradcam_overlay_generation()`: Verify Grad-CAM generates valid PNG image with non-zero heat activation (TC-DL-04).
3. Test `test_inference_latency_benchmark()`: Assert average inference latency on CPU is $< 500$ms (TC-DL-05, NFR-03).

**Acceptance Criteria:**
- 100% test pass rate across deep learning test cases.

---

## 9. Implementation Order and Dependencies

```
CHIP DL-01 (Visual CNN Architecture & Head)
    ↓
CHIP DL-02 (Transforms & Augmentation)
    ↓
CHIP DL-03 (Dataset Loader & Sampler)
    ↓
CHIP DL-04 (Two-Stage Transfer Learning)
    ↓
CHIP DL-05 (Evaluation & Metrics Benchmark) ──┐
    ↓                                        │
CHIP DL-06 (Visual Embedding Extractor)      │
    ↓                                        │
CHIP DL-07 (Grad-CAM Visualizer)             │
    ↓                                        │
CHIP DL-08 (TorchScript & INT8 Quantization) ◄┘
    ↓
CHIP DL-09 (Production Inference Service)
    ↓
CHIP DL-10 (CLI Tool)
    ↓
CHIP DL-11 & CHIP DL-12 (Unit Tests & Latency Benchmarks)
```

---

## 10. Phase Completion Checklist

- [ ] EfficientNet-B0 / ResNet-50 backbone fine-tuned using transfer learning with custom 512D head.
- [ ] Augmentation pipeline applies realistic physical scanning and capture distortions.
- [ ] Balanced DataLoader prevents majority-class bias during training.
- [ ] Test set evaluation satisfies Accuracy $\ge 90\%$ and F1-Score $\ge 0.90$ (FR-DL-05, NFR-01).
- [ ] Penultimate layer extracts L2-normalized 512-dimensional visual feature embeddings.
- [ ] Grad-CAM visualizer produces high-resolution heatmaps highlighting salient tampering regions.
- [ ] Model optimized with TorchScript / dynamic quantization achieving CPU latency $< 300$ms.
- [ ] Production service handles end-to-end inference and Grad-CAM generation within 500ms.
- [ ] Test cases TC-DL-01 through TC-DL-05 passing with 100% success rate.
