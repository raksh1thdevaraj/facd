# Forensics & Algorithm Specification

**Document ID:** SPEC-03  
**Status:** Approved / Authoritative  
**Domain:** Computer Vision, Digital Forensics, Heuristics, and Score Fusion  

---

## 1. Purpose

This document provides the mathematical equations, algorithms, tuning parameters, and classification thresholds for the forensic inspection modules and score fusion engine. AI developers must implement these exact formulations rather than inventing arbitrary or placeholder heuristics.

---

## 2. Module A: Error Level Analysis (ELA)

### 2.1 Principle
JPEG compression divides images into $8 \times 8$ pixel blocks and quantizes frequency coefficients. When an image is spliced or manipulated, modified regions typically undergo different compression cycles, resulting in distinct error rates when recompressed at a fixed quality factor.

### 2.2 Algorithm & Mathematical Formulation
1. **Input Image:** $I_{\text{orig}}$ (in RGB, dimensions $W \times H$).
2. **Re-compression:** Save $I_{\text{orig}}$ into memory buffer as a JPEG with quality factor $Q = 90$, then decode back to RGB as $I_{\text{resaved}}$.
3. **Difference Calculation:**
   $$\Delta(x, y) = |I_{\text{orig}}(x, y) - I_{\text{resaved}}(x, y)|$$
4. **Scale Amplification:**
   $$E(x, y) = \min\left(255, \; \Delta(x, y) \times \alpha\right), \quad \text{where } \alpha = 10$$
5. **Local Variance & Energy:**
   Compute the local root-mean-square error (RMSE) within $16 \times 16$ sliding windows:
   $$\text{RMSE}_k = \sqrt{\frac{1}{256} \sum_{(x,y) \in W_k} \|\Delta(x, y)\|^2}$$
6. **ELA Anomaly Score:**
   Let $\mu_{\text{RMSE}}$ and $\sigma_{\text{RMSE}}$ be the global mean and standard deviation of block RMSE values. A block $W_k$ is flagged if:
   $$\text{RMSE}_k > \mu_{\text{RMSE}} + 2.5 \cdot \sigma_{\text{RMSE}}$$
7. **Normalized ELA Score ($S_{\text{ELA}} \in [0.0, 1.0]$):**
   $$S_{\text{ELA}} = \text{clip}\left(\frac{\text{count}(\text{flagged blocks})}{\text{total blocks} \times 0.05}, \; 0.0, \; 1.0\right)$$

---

## 3. Module B: Copy-Move / Splicing Detection

### 3.1 Algorithm
1. **Feature Extraction:** Convert preprocessed image to grayscale. Use **ORB (Oriented FAST and Rotated BRIEF)** with `n_features = 2000`, `scaleFactor = 1.2`, `nlevels = 8`.
2. **Feature Matching:** Match keypoint descriptors against each other using FLANN or Brute-Force Matcher with Hamming distance.
3. **Self-Match Elimination:** Remove identity matches where keypoint index $i = j$.
4. **Spatial Distance Filtering:** Exclude matches that are too close (natural text kerning/repeated letters):
   $$D_{\text{spatial}}(p_i, p_j) = \sqrt{(x_i - x_j)^2 + (y_i - y_j)^2} < 35 \text{ pixels} \implies \text{DISCARD}$$
5. **Lowe's Ratio Test:** Discard ambiguous matches where $\frac{d_1}{d_2} > 0.75$.
6. **DBSCAN Clustering:** Cluster remaining matched vector pairs $[\vec{v} = p_j - p_i]$ with `eps = 15` and `min_samples = 4`.
7. **Copy-Move Score ($S_{\text{CM}} \in [0.0, 1.0]$):**
   - If valid clusters $\ge 1$, then $S_{\text{CM}} = \min(1.0, 0.4 + 0.15 \times \text{cluster\_count})$.
   - If no valid clusters, $S_{\text{CM}} = 0.0$.

---

## 4. Module C: Font & Baseline Alignment Heuristic

### 4.1 Principle
In authentic certificates, printed text across a line shares an identical baseline and font metrics. Forged insertions typically show baseline tilting, uneven line-height, or character bounding-box anomalies.

### 4.2 Algorithm
1. From OCR token coordinates, group tokens into horizontal text lines where:
   $$|y_{c, i} - y_{c, j}| \le 0.5 \times \text{height}_i$$
2. For each text line $L$, fit an ordinary least squares (OLS) linear regression on token baseline centers:
   $$\hat{y} = m \cdot x + c$$
3. Compute baseline residuals for each token: $r_i = |y_i - (m \cdot x_i + c)|$.
4. If $\max(r_i) > 2.5 \cdot \text{std}(r)$ and $\max(r_i) > 4 \text{ pixels}$, flag the token as suspicious.
5. Compute character aspect-ratio variance:
   $$V_{\text{ratio}} = \frac{\text{Var}(\text{width} / \text{height})}{\text{Mean}(\text{width} / \text{height})}$$
6. **Font Anomaly Score ($S_{\text{font}} \in [0.0, 1.0]$):**
   $$S_{\text{font}} = \min\left(1.0, \; \frac{\text{flagged tokens}}{\text{total tokens}} \times 5.0\right)$$

---

## 5. Module D: Text Consistency Rules

Each check evaluates to `PASSED (0.0)`, `WARNING (0.5)`, or `FAILED (1.0)`.

| Rule ID | Name | Evaluation Logic | Weight |
| :--- | :--- | :--- | :--- |
| `RULE_DATE_LOGIC` | Date Sanity & Chronology | Admission date < Passing date < Issue date; Issue date $\le$ Current date. | 25% |
| `RULE_GRADE_FORMAT` | Marks/CGPA Syntax | CGPA $\in [0.0, 10.0]$ or Marks $\le \text{Max Marks}$. | 25% |
| `RULE_REG_PATTERN` | Register Number Check | Matches institutional alphanumeric regex (e.g. `^[0-9]{2}[A-Z]{3}[0-9]{4}$`). | 20% |
| `RULE_INST_NAME` | Institution Entity Match | Fuzzy string matching (Levenshtein ratio $\ge 0.85$) against known list. | 15% |
| `RULE_CERT_NUMBER` | Certificate Number Sanity | Non-empty, alphanumeric, minimum 6 characters, no illegal symbols. | 15% |

$$\text{Consistency Risk Score} = \sum (\text{Rule Status Value} \times \text{Weight}) \times 100$$

---

## 6. Module E: Score Fusion Mathematics

### 6.1 Weighted Combination
The global authenticity risk score $R \in [0.0, 100.0]$ is computed using a weighted linear combination:

$$R_{\text{raw}} = w_1 \cdot S_{\text{forensics}} + w_2 \cdot S_{\text{consistency}} + w_3 \cdot S_{\text{ml}} + w_4 \cdot S_{\text{ocr\_penalty}} + w_5 \cdot S_{\text{template}}$$

### 6.2 Default Base Weights

| Component | Variable | Default Weight | Condition |
| :--- | :--- | :--- | :--- |
| Image Forensics | $w_1$ | 0.35 | Always active |
| Text Consistency | $w_2$ | 0.25 | Always active |
| ML Classifier Prob | $w_3$ | 0.25 | Always active |
| OCR Low-Confidence Penalty | $w_4$ | 0.05 | Always active |
| Template / Record Match | $w_5$ | 0.10 | If template available (otherwise redistributed) |

*Dynamic Redistribution:* If no registered institutional template exists, $w_5$ is set to $0$, and its weight is proportionally split: $+0.05$ to $w_1$ and $+0.05$ to $w_3$.

### 6.3 Critical Override Rules (Tamper Short-Circuiting)
Regardless of the weighted sum:
1. **Definite Copy-Move:** If $S_{\text{CM}} \ge 0.85 \implies R = \max(R, 80.0)$ (Immediate High Risk).
2. **Date Logic Violation:** If passing date is after issue date by $>1$ year $\implies R = \max(R, 75.0)$.
3. **Database Record Mismatch:** If an institutional record exists for this registration number but student name does not match $\implies R = 95.0$ (High Risk).

### 6.4 Risk Band Mapping

| Risk Band | Range | System Verdict Description |
| :--- | :--- | :--- |
| **LOW** | $0.0 \le R < 30.0$ | No significant anomalies detected. Standard authentic structure. |
| **MEDIUM** | $30.0 \le R < 70.0$ | Discrepancies detected. Manual inspection recommended. |
| **HIGH** | $70.0 \le R \le 100.0$ | Strong evidence of digital alteration or logical inconsistency. |
