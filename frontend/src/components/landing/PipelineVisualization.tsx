import React, { useState } from 'react';
import {
  FileText,
  Scan,
  Type,
  Activity,
  Copy,
  LayoutGrid,
  FileSearch,
  Cpu,
  ShieldCheck,
  Award,
  ChevronRight,
  Sparkles,
  CheckCircle2,
  Terminal,
} from 'lucide-react';

interface StageDetail {
  step: string;
  title: string;
  category: string;
  icon: React.ElementType;
  description: string;
  algorithm: string;
  inputs: string;
  outputs: string;
  confidenceWeight: string;
  latency: string;
}

const PIPELINE_STAGES: StageDetail[] = [
  {
    step: '01',
    title: 'Document Intake & Optical Normalization',
    category: 'PREPROCESSING',
    icon: FileText,
    description:
      'High-throughput intake supporting PDF, TIFF, JPEG, and PNG. Executes automatic bilateral filter denoising, 4-point perspective warp correction, and orientation rectification.',
    algorithm: 'Canny Edge + Probabilistic Hough Transform + Bilateral Filter',
    inputs: 'Raw Document Image / Multi-page PDF (up to 20MB)',
    outputs: 'Rectified 300 DPI Normalized Tensor [H, W, 3]',
    confidenceWeight: 'Prerequisite (Normalization Pass)',
    latency: '110ms',
  },
  {
    step: '02',
    title: 'Dual-Engine OCR & Spatial Typography',
    category: 'OCR EXTRACTION',
    icon: Scan,
    description:
      'Runs Tesseract v5 (LSTM line recognizer) and EasyOCR concurrently to extract all text tokens, confidence scores, and bounding boxes across Latin, Cyrillic, and Asian scripts.',
    algorithm: 'Dual-Engine Ensemble (Tesseract 5.3 + EasyOCR PyTorch)',
    inputs: 'Normalized Grayscale & Binarized Tensors',
    outputs: 'Token Bounding Boxes [X, Y, W, H], Text Streams, OCR Confidences',
    confidenceWeight: '15% of Composite Score',
    latency: '240ms',
  },
  {
    step: '03',
    title: 'Font Kerning & Spatial Baseline Audit',
    category: 'TYPOGRAPHY INTEGRITY',
    icon: Type,
    description:
      'Measures inter-character kerning consistency, glyph aspect ratios, and baseline drift across student names, degree titles, and GPAs to uncover digital splicing.',
    algorithm: 'Horizontal Projection Profiling & Kerning Variance Tensors',
    inputs: 'Token Spatial Coordinates & Bounding Box Baselines',
    outputs: 'Kerning Variance Index & Baseline Deviation Metric',
    confidenceWeight: '10% of Composite Score',
    latency: '60ms',
  },
  {
    step: '04',
    title: 'Multi-Scale Error Level Analysis (ELA)',
    category: 'DIGITAL FORENSICS',
    icon: Activity,
    description:
      'Re-compresses the image at predetermined JPEG quality levels (90%, 95%) and computes pixel-level error difference maps to highlight regions edited in different sessions.',
    algorithm: 'JPEG Re-Compression Divergence Matrix & Multi-Scale DCT',
    inputs: 'Full Color Normalized Document Tensor',
    outputs: 'Error Level Heatmap (256-level RGB) & High-Frequency Anomaly Ratio',
    confidenceWeight: '15% of Composite Score',
    latency: '95ms',
  },
  {
    step: '05',
    title: 'Copy-Move Forgery & Clone Detection',
    category: 'FEATURE CLUSTERING',
    icon: Copy,
    description:
      'Identifies cloned university seals, forged signatures, and duplicated graduation honors using keypoint descriptor spatial clustering.',
    algorithm: 'SIFT + 2-Nearest Neighbor Euclidean Ratio + DBSCAN Clustering',
    inputs: 'High-Contrast Feature Keypoints',
    outputs: 'Duplicate Cluster Pairs, Transform Vectors, Tamper Mask',
    confidenceWeight: '12% of Composite Score',
    latency: '180ms',
  },
  {
    step: '06',
    title: 'SIFT/ORB Homography Template Matching',
    category: 'GEOMETRIC ALIGNMENT',
    icon: LayoutGrid,
    description:
      'Matches the uploaded certificate against the official accredited university template baseline to verify coat-of-arms positioning, margins, and watermarks.',
    algorithm: 'RANSAC Homography Estimation & Inlier Ratio Quantification',
    inputs: 'Uploaded Keypoints vs University Master Template Catalog',
    outputs: 'Homography Matrix H (3x3), Inlier Score, Structural Divergence',
    confidenceWeight: '12% of Composite Score',
    latency: '140ms',
  },
  {
    step: '07',
    title: 'Metadata, EXIF & Software Signature Audit',
    category: 'METADATA FORENSICS',
    icon: FileSearch,
    description:
      'Scrutinizes PDF trailers, XMP metadata, embedded font tables, and camera/scanner EXIF tags for telltale indicators of Adobe Photoshop or Canva export signatures.',
    algorithm: 'Heuristic Stream Parsing & XMP Signature Cross-Validation',
    inputs: 'Raw Binary File Stream & PDF Object Streams',
    outputs: 'Creation Toolchain Signature, Revision Count, Timestamp Anomaly',
    confidenceWeight: '8% of Composite Score',
    latency: '35ms',
  },
  {
    step: '08',
    title: 'ResNet-50 Visual Deep Feature Classifier',
    category: 'DEEP LEARNING',
    icon: Cpu,
    description:
      'Extracts dense deep convolutional representations trained on 20,000+ authentic and synthetic forged diplomas. Generates Grad-CAM visual heatmaps for explainable tamper localization.',
    algorithm: 'Custom Fine-Tuned ResNet-50 + Grad-CAM Visual Attention Layer',
    inputs: 'Normalized 224x224 RGB Batch Tensors',
    outputs: 'Forged Probability [0.0 - 1.0] & Spatial Grad-CAM Activation Map',
    confidenceWeight: '18% of Composite Score',
    latency: '190ms',
  },
  {
    step: '09',
    title: 'Cryptographic Registry & QR Cross-Audit',
    category: 'REGISTRY LEDGER',
    icon: ShieldCheck,
    description:
      'Decodes embedded QR codes or barcodes, verifies digital signatures against registrar public keys, and audits registrar DNSSEC/TLS verification endpoints.',
    algorithm: 'Ed25519 / RSA-PSS Signature Verification & DNSSEC Lookup',
    inputs: 'QR Code Payload & University Public Key Registry',
    outputs: 'Ledger Confirmation Status & Registrar Identity Assertion',
    confidenceWeight: '10% of Composite Score',
    latency: '160ms',
  },
  {
    step: '10',
    title: 'Dempster-Shafer Evidential Fusion & Dossier',
    category: 'DECISION FUSION',
    icon: Award,
    description:
      'Combines probabilities from all 9 prior forensic stages using Dempster-Shafer rule of combination under uncertainty. Synthesizes an explainable HMAC-SHA256 signed audit dossier.',
    algorithm: 'Dempster-Shafer Belief Theory & HMAC-SHA256 Verifiable Dossier',
    inputs: 'Multi-Stage Probability Vectors & Evidence Confidence Weights',
    outputs: 'Composite Verdict (AUTHENTIC / SUSPICIOUS / FORGED) + Signed PDF',
    confidenceWeight: 'Final Synthesized Verdict (100%)',
    latency: '80ms',
  },
];

export const PipelineVisualization: React.FC = () => {
  const [activeStageIndex, setActiveStageIndex] = useState<number>(0);
  const activeStage = PIPELINE_STAGES[activeStageIndex];
  const Icon = activeStage.icon;

  return (
    <section id="pipeline" className="space-y-8 py-8">
      {/* Header */}
      <div className="text-center space-y-3 max-w-3xl mx-auto">
        <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-emerald-950/60 border border-emerald-500/30 text-emerald-300 text-xs font-mono font-medium">
          <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
          <span>MULTI-MODAL FORENSIC ARCHITECTURE</span>
        </div>

        <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
          The 10-Stage Academic Integrity Pipeline
        </h2>

        <p className="text-sm text-slate-400 leading-relaxed">
          From high-resolution optical intake to evidential Dempster-Shafer score fusion. Click any stage to inspect algorithm specifications, tensor flows, and latency budgets.
        </p>
      </div>

      {/* Horizontal Stage Stepper (Scrollable) */}
      <div className="flex items-center gap-2 overflow-x-auto pb-4 pt-2 no-scrollbar">
        {PIPELINE_STAGES.map((s, idx) => {
          const isCurrent = idx === activeStageIndex;
          const StageIcon = s.icon;
          return (
            <button
              key={s.step}
              onClick={() => setActiveStageIndex(idx)}
              className={`flex-shrink-0 flex items-center space-x-2.5 px-3.5 py-2.5 rounded-2xl border transition-all ${
                isCurrent
                  ? 'bg-emerald-950/80 border-emerald-500 text-slate-100 ring-2 ring-emerald-500/40 shadow-lg shadow-emerald-950/50'
                  : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-800/80 hover:border-slate-700'
              }`}
            >
              <div
                className={`p-1.5 rounded-lg text-xs font-mono font-bold flex items-center space-x-1 ${
                  isCurrent
                    ? 'bg-emerald-500 text-slate-950'
                    : 'bg-slate-800 text-slate-400'
                }`}
              >
                <StageIcon className="w-3 h-3" />
                <span>{s.step}</span>
              </div>
              <span className="text-xs font-semibold whitespace-nowrap">{s.title.split(' ')[0]}</span>
              {isCurrent && (
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              )}
            </button>
          );
        })}
      </div>

      {/* Active Stage Detailed Breakdown Panel */}
      <div className="glass-card rounded-3xl p-6 sm:p-8 border border-slate-800 relative overflow-hidden shadow-2xl">
        {/* Background Radial Glow */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-bl from-emerald-500/10 via-cyan-500/5 to-transparent rounded-full blur-3xl pointer-events-none" />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start relative z-10">
          {/* Left Column: Stage Summary */}
          <div className="lg:col-span-2 space-y-6">
            <div className="flex items-center space-x-3">
              <div className="p-3 rounded-2xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                <Icon className="w-7 h-7" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-mono font-bold text-emerald-400 bg-emerald-950/80 px-2 py-0.5 rounded border border-emerald-500/30">
                    STAGE {activeStage.step} • {activeStage.category}
                  </span>
                  <span className="text-xs font-mono text-slate-400">
                    LATENCY: {activeStage.latency}
                  </span>
                </div>
                <h3 className="text-xl sm:text-2xl font-extrabold text-white mt-1">
                  {activeStage.title}
                </h3>
              </div>
            </div>

            <p className="text-sm sm:text-base text-slate-300 leading-relaxed">
              {activeStage.description}
            </p>

            {/* Algorithmic Details */}
            <div className="space-y-3 pt-2">
              <div className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-1.5">
                <div className="flex items-center space-x-2 text-xs font-mono text-emerald-400">
                  <Terminal className="w-3.5 h-3.5" />
                  <span>CORE ALGORITHM & MODEL ENGINE</span>
                </div>
                <p className="text-xs sm:text-sm font-mono text-slate-200">
                  {activeStage.algorithm}
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
                  <span className="text-[10px] font-mono text-slate-400">INPUT DATA CONTRACT</span>
                  <p className="text-xs text-slate-300 font-mono">{activeStage.inputs}</p>
                </div>
                <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
                  <span className="text-[10px] font-mono text-slate-400">OUTPUT ARTIFACTS</span>
                  <p className="text-xs text-emerald-300 font-mono">{activeStage.outputs}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Key Metric Card */}
          <div className="p-6 rounded-3xl bg-slate-900/90 border border-slate-800 space-y-6 flex flex-col justify-between">
            <div className="space-y-4">
              <span className="text-xs font-mono text-slate-400 uppercase tracking-wider block">
                Evidence Quantification
              </span>

              <div className="space-y-1">
                <span className="text-3xl font-extrabold text-white font-mono">
                  {activeStage.confidenceWeight.split(' ')[0]}
                </span>
                <p className="text-xs text-slate-400">
                  {activeStage.confidenceWeight}
                </p>
              </div>

              <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-emerald-500 to-cyan-400 rounded-full transition-all duration-500"
                  style={{
                    width: `${Math.min(
                      100,
                      parseInt(activeStage.confidenceWeight) || (activeStageIndex + 1) * 10
                    )}%`,
                  }}
                />
              </div>

              <div className="pt-2 text-xs text-slate-400 space-y-2">
                <div className="flex justify-between">
                  <span>Execution Order:</span>
                  <span className="text-slate-200 font-mono">Step {activeStageIndex + 1} of 10</span>
                </div>
                <div className="flex justify-between">
                  <span>Inference Hardware:</span>
                  <span className="text-slate-200 font-mono">CPU / Torch CUDA</span>
                </div>
                <div className="flex justify-between">
                  <span>Standard Error Budget:</span>
                  <span className="text-emerald-400 font-mono">&lt; 0.002 FPR</span>
                </div>
              </div>
            </div>

            {/* Quick Next Stage Switcher */}
            <button
              onClick={() =>
                setActiveStageIndex((prev) => (prev + 1) % PIPELINE_STAGES.length)
              }
              className="w-full inline-flex items-center justify-center space-x-2 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white text-xs font-semibold border border-slate-700 transition-colors"
            >
              <span>Inspect Next Stage ({PIPELINE_STAGES[(activeStageIndex + 1) % PIPELINE_STAGES.length].step})</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </section>
  );
};
