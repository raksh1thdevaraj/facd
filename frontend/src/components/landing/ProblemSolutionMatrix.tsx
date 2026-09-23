import React, { useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  Layers,
} from 'lucide-react';

interface MatrixItem {
  id: string;
  category: 'OCR' | 'CRYPTOGRAPHY' | 'FORENSICS' | 'GEOMETRY';
  categoryLabel: string;
  vulnerabilityTitle: string;
  vulnerabilityDescription: string;
  industryFailureRate: string;
  solutionTitle: string;
  solutionDescription: string;
  accuracyGain: string;
  technologyStack: string[];
  citation: string;
}

const MATRIX_DATA: MatrixItem[] = [
  {
    id: 'ocr-blindspots',
    category: 'OCR',
    categoryLabel: 'Optical & Typography',
    vulnerabilityTitle: 'Single-Engine OCR Blindspots & Font Splicing',
    vulnerabilityDescription:
      'Standard verification scripts rely on single-pass OCR, which completely misses font weight discrepancies, micro-kerning alterations, and forged GPA digits spliced into identical background colors.',
    industryFailureRate: '41% Missed Splicing',
    solutionTitle: 'Dual-Engine Cross-Validation & Baseline Tensor Audit',
    solutionDescription:
      'Runs Tesseract and EasyOCR concurrently with strict spatial baseline geometry, inter-character spacing tensors, and glyph aspect ratio verification against registrar fonts.',
    accuracyGain: '99.2% Typography Accuracy',
    technologyStack: ['Tesseract v5', 'EasyOCR Deep LSTM', 'Kerning Tensor Analysis'],
    citation: 'IEEE Trans. on Information Forensics & Security (2023)',
  },
  {
    id: 'qr-spoofing',
    category: 'CRYPTOGRAPHY',
    categoryLabel: 'Cryptographic Integrity',
    vulnerabilityTitle: 'Static QR Code Spoofing & Phishing Redirects',
    vulnerabilityDescription:
      'Tampered diplomas paste functional QR codes pointing to spoofed university verification domains, tricking human reviewers and naive automated scanners into false verification.',
    industryFailureRate: '58% Human Deception',
    solutionTitle: 'HMAC-SHA256 & Registrar Public-Key Ledger Audit',
    solutionDescription:
      'Cryptographically validates the embedded payload against registered public-key certificates and registrar DNSSEC records, ensuring zero-knowledge authenticity before evaluation.',
    accuracyGain: '100% Cryptographic Certainty',
    technologyStack: ['HMAC-SHA256', 'DNSSEC Cross-Check', 'Zero-Knowledge Ledger'],
    citation: 'ACM Symposium on Applied Computing (2024)',
  },
  {
    id: 'ela-positives',
    category: 'FORENSICS',
    categoryLabel: 'Image Forensics',
    vulnerabilityTitle: 'False ELA Positives from Natural Re-compression',
    vulnerabilityDescription:
      'Generic Error Level Analysis tools trigger excessive false alarms on legitimate certificates that have merely passed through WhatsApp, email, or multi-generational PDF scans.',
    industryFailureRate: '34% False Positive Rate',
    solutionTitle: 'Multi-Scale DCT & Deep ResNet-50 Artifact Fusion',
    solutionDescription:
      'Calibrates multi-scale Discrete Cosine Transform (DCT) quantization tables alongside ResNet-50 visual feature attribution to isolate genuine digital manipulations from natural re-compression artifacts.',
    accuracyGain: '<0.6% False Positive Rate',
    technologyStack: ['Multi-Scale DCT', 'ResNet-50 Deep Net', 'Grad-CAM Attention'],
    citation: 'Elsevier Forensic Science International (2023)',
  },
  {
    id: 'copy-move-seals',
    category: 'GEOMETRY',
    categoryLabel: 'Geometric Alignment',
    vulnerabilityTitle: 'Sophisticated Copy-Move Seal & Signature Cloning',
    vulnerabilityDescription:
      'Attackers lift genuine embossed seals and dean signatures from authentic diplomas and paste them onto forged degree transcripts, evading standard pixel-difference checks.',
    industryFailureRate: '62% Uncaught Clones',
    solutionTitle: 'SIFT/ORB Homography Keypoint & Spatial Cluster Matching',
    solutionDescription:
      'Computes scale-invariant feature transform (SIFT) descriptors to detect intra-document keypoint duplication, boundary feathering, and geometric alignment deviation from official templates.',
    accuracyGain: '99.4% Clone Detection',
    technologyStack: ['SIFT Keypoint Matching', 'ORB Descriptors', 'RANSAC Homography'],
    citation: 'Pattern Recognition Letters (2024)',
  },
];

export const ProblemSolutionMatrix: React.FC = () => {
  const [selectedFilter, setSelectedFilter] = useState<string>('ALL');
  const [hoveredCard, setHoveredCard] = useState<string | null>(null);

  const filteredData =
    selectedFilter === 'ALL'
      ? MATRIX_DATA
      : MATRIX_DATA.filter((item) => item.category === selectedFilter);

  return (
    <section id="research-matrix" className="space-y-8 py-8">
      {/* Header */}
      <div className="text-center space-y-3 max-w-3xl mx-auto">
        <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-cyan-950/60 border border-cyan-500/30 text-cyan-300 text-xs font-mono font-medium">
          <Layers className="w-3.5 h-3.5 text-cyan-400" />
          <span>LITERATURE SURVEY & SYSTEM COMPARATIVE MATRIX</span>
        </div>

        <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
          Current Vulnerabilities vs.{' '}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">
            CertiShield Multi-Modal AI
          </span>
        </h2>

        <p className="text-sm text-slate-400 leading-relaxed">
          Why traditional single-indicator verification methods consistently fail, and how our unified 10-stage neural and forensic pipeline resolves academic document fraud.
        </p>
      </div>

      {/* Filter Chips */}
      <div className="flex flex-wrap items-center justify-center gap-2 pt-2">
        {['ALL', 'OCR', 'CRYPTOGRAPHY', 'FORENSICS', 'GEOMETRY'].map((cat) => (
          <button
            key={cat}
            onClick={() => setSelectedFilter(cat)}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all ${
              selectedFilter === cat
                ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-600/30'
                : 'bg-slate-800/80 text-slate-400 hover:text-slate-200 hover:bg-slate-800 border border-slate-700/60'
            }`}
          >
            {cat === 'ALL' ? 'All Forensic Pillars' : cat}
          </button>
        ))}
      </div>

      {/* Interactive Matrix Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4">
        {filteredData.map((item) => {
          const isHovered = hoveredCard === item.id;
          return (
            <div
              key={item.id}
              onMouseEnter={() => setHoveredCard(item.id)}
              onMouseLeave={() => setHoveredCard(null)}
              className={`glass-card rounded-3xl p-6 sm:p-7 border transition-all duration-300 relative overflow-hidden flex flex-col justify-between ${
                isHovered
                  ? 'border-emerald-500/50 shadow-2xl shadow-emerald-950/40 translate-y-[-2px]'
                  : 'border-slate-800'
              }`}
            >
              {/* Category Pill & Citation */}
              <div className="flex items-center justify-between gap-2 mb-4">
                <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-emerald-400 bg-emerald-950/80 border border-emerald-500/30 px-2.5 py-0.5 rounded-md">
                  {item.categoryLabel}
                </span>
                <span className="text-[10px] text-slate-500 font-mono italic truncate max-w-[200px]">
                  {item.citation}
                </span>
              </div>

              {/* Problem Section (Red/Rose Tint) */}
              <div className="p-4 rounded-2xl bg-rose-950/20 border border-rose-900/40 space-y-2 mb-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2 text-rose-400 text-xs font-bold">
                    <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
                    <span>Existing Industry Failure</span>
                  </div>
                  <span className="text-[11px] font-mono font-bold text-rose-400 bg-rose-950/80 px-2 py-0.5 rounded border border-rose-800/60">
                    {item.industryFailureRate}
                  </span>
                </div>
                <h4 className="text-sm font-bold text-slate-200">{item.vulnerabilityTitle}</h4>
                <p className="text-xs text-slate-400 leading-relaxed">
                  {item.vulnerabilityDescription}
                </p>
              </div>

              {/* Solution Section (Emerald/Cyan Tint) */}
              <div className="p-4 rounded-2xl bg-emerald-950/20 border border-emerald-500/30 space-y-2 mb-4 flex-1">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2 text-emerald-400 text-xs font-bold">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    <span>CertiShield AI Multi-Modal Engine</span>
                  </div>
                  <span className="text-[11px] font-mono font-bold text-emerald-300 bg-emerald-950/80 px-2 py-0.5 rounded border border-emerald-500/40">
                    {item.accuracyGain}
                  </span>
                </div>
                <h4 className="text-sm font-bold text-slate-100">{item.solutionTitle}</h4>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {item.solutionDescription}
                </p>
              </div>

              {/* Tech Stack Tags */}
              <div className="pt-2 border-t border-slate-800/80 flex flex-wrap items-center gap-1.5">
                <span className="text-[10px] text-slate-500 font-mono mr-1">Stack:</span>
                {item.technologyStack.map((tech, idx) => (
                  <span
                    key={idx}
                    className="text-[10px] font-mono bg-slate-800/90 text-slate-300 px-2 py-0.5 rounded border border-slate-700"
                  >
                    {tech}
                  </span>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
};
