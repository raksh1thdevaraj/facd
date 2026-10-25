/**
 * High-fidelity synthetic institutional marks card raster/SVG generator for VTU test samples.
 */

export function createSampleMarksCardSvg(
  sampleType: 'authentic' | 'altered_sgpa' | 'spliced_usn'
): string {
  const isAlteredSgpa = sampleType === 'altered_sgpa';
  const isSplicedUsn = sampleType === 'spliced_usn';

  const studentName = isAlteredSgpa ? 'RAHUL S SHARMA' : isSplicedUsn ? 'KARTHIK M NAIR' : 'ANANYA RAO';
  const usn = isAlteredSgpa ? '1RV20EC045' : isSplicedUsn ? '1PE19CS999' : '1MS21CS045';
  const college = isAlteredSgpa
    ? 'R.V. COLLEGE OF ENGINEERING, BENGALURU [1RV]'
    : isSplicedUsn
    ? 'PES INSTITUTE OF TECHNOLOGY, BENGALURU [1PE]'
    : 'M.S. RAMAIAH INSTITUTE OF TECHNOLOGY, BENGALURU [1MS]';
  const semester = 'IV SEMESTER B.E. (CBCS 2021 SCHEME)';
  const exam = 'JULY / AUGUST 2024';

  const printedSgpa = isAlteredSgpa ? '8.85' : '8.50';

  // SVG representation resembling official VTU engineering grade card
  const svg = `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 1080" width="800" height="1080" style="background:#ffffff; font-family:'Inter', sans-serif;">
  <!-- Border and Guilloche Watermark effect -->
  <rect x="20" y="20" width="760" height="1040" fill="#fafafa" stroke="#1e3a8a" stroke-width="2.5" rx="4"/>
  <rect x="28" y="28" width="744" height="1024" fill="#ffffff" stroke="#e2e8f0" stroke-width="1"/>
  
  <!-- Faint Institutional Watermark in background -->
  <text x="400" y="540" font-size="64" font-weight="bold" fill="#f1f5f9" text-anchor="middle" transform="rotate(-30 400 540)" letter-spacing="8">
    VTU BELAGAVI OFFICIAL
  </text>

  <!-- University Header -->
  <g transform="translate(50, 48)">
    <!-- University Crest Emblem -->
    <circle cx="50" cy="50" r="38" fill="#1e3a8a" opacity="0.95"/>
    <polygon points="50,22 59,38 77,41 64,54 67,72 50,63 33,72 36,54 23,41 41,38" fill="#fbbf24"/>
    <circle cx="50" cy="50" r="14" fill="#ffffff"/>
    <text x="50" y="54" font-size="11" font-weight="900" fill="#1e3a8a" text-anchor="middle">VTU</text>

    <!-- University Title -->
    <text x="110" y="32" font-size="17" font-weight="800" fill="#0f172a" letter-spacing="0.5">VISVESVARAYA TECHNOLOGICAL UNIVERSITY</text>
    <text x="110" y="50" font-size="11" font-weight="600" fill="#475569">"Jnana Sangama", Belagavi - 590 018, Karnataka, India</text>
    <text x="110" y="68" font-size="13" font-weight="700" fill="#1e3a8a">PROVISIONAL GRADE CARD - BACHELOR OF ENGINEERING</text>
  </g>

  <!-- Divider Line -->
  <line x1="50" y1="140" x2="750" y2="140" stroke="#1e3a8a" stroke-width="1.5"/>

  <!-- Student Metadata Box -->
  <g transform="translate(50, 155)">
    <rect x="0" y="0" width="700" height="95" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1" rx="4"/>
    
    <text x="15" y="25" font-size="10" font-weight="600" fill="#64748b">CANDIDATE NAME:</text>
    <text x="135" y="25" font-size="11" font-weight="700" fill="#0f172a">${studentName}</text>
    
    <text x="440" y="25" font-size="10" font-weight="600" fill="#64748b">UNIVERSITY SEAT NO (USN):</text>
    <text x="595" y="25" font-size="${isSplicedUsn ? '12.5' : '12'}" font-weight="800" font-family="${isSplicedUsn ? 'Courier, monospace' : 'monospace'}" fill="${isSplicedUsn ? '#b91c1c' : '#1e3a8a'}">${usn}</text>
    
    <text x="15" y="55" font-size="10" font-weight="600" fill="#64748b">INSTITUTION:</text>
    <text x="135" y="55" font-size="10.5" font-weight="600" fill="#0f172a">${college}</text>
    
    <text x="15" y="80" font-size="10" font-weight="600" fill="#64748b">SEMESTER / SCHEME:</text>
    <text x="135" y="80" font-size="10.5" font-weight="600" fill="#0f172a">${semester}</text>
    
    <text x="440" y="80" font-size="10" font-weight="600" fill="#64748b">EXAMINATION CYCLE:</text>
    <text x="560" y="80" font-size="10" font-weight="600" fill="#0f172a">${exam}</text>
  </g>

  <!-- Subject Ledger Table -->
  <g transform="translate(50, 275)">
    <!-- Header -->
    <rect x="0" y="0" width="700" height="28" fill="#1e3a8a" rx="2"/>
    <text x="15" y="18" font-size="10" font-weight="700" fill="#ffffff">COURSE CODE</text>
    <text x="120" y="18" font-size="10" font-weight="700" fill="#ffffff">COURSE TITLE</text>
    <text x="420" y="18" font-size="10" font-weight="700" fill="#ffffff" text-anchor="middle">CREDITS (Ci)</text>
    <text x="500" y="18" font-size="10" font-weight="700" fill="#ffffff" text-anchor="middle">GRADE</text>
    <text x="580" y="18" font-size="10" font-weight="700" fill="#ffffff" text-anchor="middle">POINTS (Gi)</text>
    <text x="665" y="18" font-size="10" font-weight="700" fill="#ffffff" text-anchor="middle">Ci × Gi</text>

    <!-- Row 1 -->
    <rect x="0" y="28" width="700" height="34" fill="#ffffff" stroke="#e2e8f0" stroke-width="0.5"/>
    <text x="15" y="50" font-size="10.5" font-weight="700" font-family="monospace" fill="#0f172a">21CS41</text>
    <text x="120" y="50" font-size="10" font-weight="500" fill="#334155">Mathematical Foundations for Computing</text>
    <text x="420" y="50" font-size="10" font-weight="600" fill="#0f172a" text-anchor="middle">3.0</text>
    <text x="500" y="50" font-size="11" font-weight="700" fill="#059669" text-anchor="middle">A+</text>
    <text x="580" y="50" font-size="10" font-weight="600" fill="#0f172a" text-anchor="middle">9</text>
    <text x="665" y="50" font-size="10.5" font-weight="700" fill="#0f172a" text-anchor="middle">27.0</text>

    <!-- Row 2 -->
    <rect x="0" y="62" width="700" height="34" fill="#f8fafc" stroke="#e2e8f0" stroke-width="0.5"/>
    <text x="15" y="84" font-size="10.5" font-weight="700" font-family="monospace" fill="#0f172a">21CS42</text>
    <text x="120" y="84" font-size="10" font-weight="500" fill="#334155">Design and Analysis of Algorithms</text>
    <text x="420" y="84" font-size="10" font-weight="600" fill="#0f172a" text-anchor="middle">4.0</text>
    <text x="500" y="84" font-size="11" font-weight="700" fill="#059669" text-anchor="middle">${isAlteredSgpa ? 'B+' : 'A+'}</text>
    <text x="580" y="84" font-size="10" font-weight="600" fill="#0f172a" text-anchor="middle">${isAlteredSgpa ? '7' : '9'}</text>
    <text x="665" y="84" font-size="10.5" font-weight="700" fill="#0f172a" text-anchor="middle">${isAlteredSgpa ? '28.0' : '36.0'}</text>

    <!-- Row 3 -->
    <rect x="0" y="96" width="700" height="34" fill="#ffffff" stroke="#e2e8f0" stroke-width="0.5"/>
    <text x="15" y="118" font-size="10.5" font-weight="700" font-family="monospace" fill="#0f172a">21CS43</text>
    <text x="120" y="118" font-size="10" font-weight="500" fill="#334155">Microcontrollers and Embedded Systems</text>
    <text x="420" y="118" font-size="10" font-weight="600" fill="#0f172a" text-anchor="middle">3.0</text>
    <text x="500" y="118" font-size="11" font-weight="700" fill="#059669" text-anchor="middle">${isAlteredSgpa ? 'B' : 'A'}</text>
    <text x="580" y="118" font-size="10" font-weight="600" fill="#0f172a" text-anchor="middle">${isAlteredSgpa ? '6' : '8'}</text>
    <text x="665" y="118" font-size="10.5" font-weight="700" fill="#0f172a" text-anchor="middle">${isAlteredSgpa ? '18.0' : '24.0'}</text>

    <!-- Row 4 -->
    <rect x="0" y="130" width="700" height="34" fill="#f8fafc" stroke="#e2e8f0" stroke-width="0.5"/>
    <text x="15" y="152" font-size="10.5" font-weight="700" font-family="monospace" fill="#0f172a">21CS44</text>
    <text x="120" y="152" font-size="10" font-weight="500" fill="#334155">Operating Systems and System Software</text>
    <text x="420" y="152" font-size="10" font-weight="600" fill="#0f172a" text-anchor="middle">3.0</text>
    <text x="500" y="152" font-size="11" font-weight="700" fill="#059669" text-anchor="middle">A</text>
    <text x="580" y="152" font-size="10" font-weight="600" fill="#0f172a" text-anchor="middle">8</text>
    <text x="665" y="152" font-size="10.5" font-weight="700" fill="#0f172a" text-anchor="middle">24.0</text>

    <!-- Row 5 -->
    <rect x="0" y="164" width="700" height="34" fill="#ffffff" stroke="#e2e8f0" stroke-width="0.5"/>
    <text x="15" y="186" font-size="10.5" font-weight="700" font-family="monospace" fill="#0f172a">21CSL46</text>
    <text x="120" y="186" font-size="10" font-weight="500" fill="#334155">Design and Analysis of Algorithms Lab</text>
    <text x="420" y="186" font-size="10" font-weight="600" fill="#0f172a" text-anchor="middle">1.5</text>
    <text x="500" y="186" font-size="11" font-weight="700" fill="#059669" text-anchor="middle">O</text>
    <text x="580" y="186" font-size="10" font-weight="600" fill="#0f172a" text-anchor="middle">10</text>
    <text x="665" y="186" font-size="10.5" font-weight="700" fill="#0f172a" text-anchor="middle">15.0</text>

    <!-- Row 6 -->
    <rect x="0" y="198" width="700" height="34" fill="#f8fafc" stroke="#e2e8f0" stroke-width="0.5"/>
    <text x="15" y="220" font-size="10.5" font-weight="700" font-family="monospace" fill="#0f172a">21CSL47</text>
    <text x="120" y="220" font-size="10" font-weight="500" fill="#334155">Microcontrollers Laboratory</text>
    <text x="420" y="220" font-size="10" font-weight="600" fill="#0f172a" text-anchor="middle">1.5</text>
    <text x="500" y="220" font-size="11" font-weight="700" fill="#059669" text-anchor="middle">A+</text>
    <text x="580" y="220" font-size="10" font-weight="600" fill="#0f172a" text-anchor="middle">9</text>
    <text x="665" y="220" font-size="10.5" font-weight="700" fill="#0f172a" text-anchor="middle">13.5</text>

    <!-- Row 7 -->
    <rect x="0" y="232" width="700" height="34" fill="#ffffff" stroke="#e2e8f0" stroke-width="0.5"/>
    <text x="15" y="254" font-size="10.5" font-weight="700" font-family="monospace" fill="#0f172a">21UH49</text>
    <text x="120" y="254" font-size="10" font-weight="500" fill="#334155">Universal Human Values</text>
    <text x="420" y="254" font-size="10" font-weight="600" fill="#0f172a" text-anchor="middle">1.0</text>
    <text x="500" y="254" font-size="11" font-weight="700" fill="#059669" text-anchor="middle">A</text>
    <text x="580" y="254" font-size="10" font-weight="600" fill="#0f172a" text-anchor="middle">8</text>
    <text x="665" y="254" font-size="10.5" font-weight="700" fill="#0f172a" text-anchor="middle">8.0</text>

    <!-- Row 8 -->
    <rect x="0" y="266" width="700" height="34" fill="#f8fafc" stroke="#e2e8f0" stroke-width="0.5"/>
    <text x="15" y="288" font-size="10.5" font-weight="700" font-family="monospace" fill="#0f172a">21CIP48</text>
    <text x="120" y="288" font-size="10" font-weight="500" fill="#334155">Constitution of India &amp; Professional Ethics</text>
    <text x="420" y="288" font-size="10" font-weight="600" fill="#0f172a" text-anchor="middle">1.0</text>
    <text x="500" y="288" font-size="11" font-weight="700" fill="#059669" text-anchor="middle">A+</text>
    <text x="580" y="288" font-size="10" font-weight="600" fill="#0f172a" text-anchor="middle">9</text>
    <text x="665" y="288" font-size="10.5" font-weight="700" fill="#0f172a" text-anchor="middle">9.0</text>

    <!-- Summary Total Line -->
    <rect x="0" y="300" width="700" height="30" fill="#f1f5f9" stroke="#cbd5e1" stroke-width="1"/>
    <text x="120" y="320" font-size="10.5" font-weight="700" fill="#0f172a">TOTAL SEMESTER CREDITS &amp; QUALITY POINTS:</text>
    <text x="420" y="320" font-size="11" font-weight="800" fill="#0f172a" text-anchor="middle">18.0</text>
    <text x="665" y="320" font-size="11" font-weight="800" fill="#1e3a8a" text-anchor="middle">${isAlteredSgpa ? '130.5' : '153.0'}</text>
  </g>

  <!-- SGPA & Institutional Seal Box -->
  <g transform="translate(50, 630)">
    <rect x="0" y="0" width="700" height="90" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1" rx="4"/>
    
    <text x="25" y="32" font-size="11" font-weight="700" fill="#475569">SEMESTER GRADE POINT AVERAGE (SGPA):</text>
    <rect x="25" y="42" width="120" height="36" fill="#ffffff" stroke="${isAlteredSgpa ? '#e11d48' : '#1e3a8a'}" stroke-width="${isAlteredSgpa ? '2' : '1.5'}" rx="4"/>
    <text x="85" y="66" font-size="18" font-weight="900" font-family="monospace" fill="${isAlteredSgpa ? '#e11d48' : '#1e3a8a'}" text-anchor="middle">${printedSgpa}</text>
    
    <text x="220" y="32" font-size="11" font-weight="700" fill="#475569">CUMULATIVE GRADE POINT (CGPA):</text>
    <rect x="220" y="42" width="120" height="36" fill="#ffffff" stroke="#cbd5e1" stroke-width="1" rx="4"/>
    <text x="280" y="66" font-size="17" font-weight="800" font-family="monospace" fill="#0f172a" text-anchor="middle">${isAlteredSgpa ? '8.40' : '8.38'}</text>

    <!-- Registrar Signature and Seal -->
    <g transform="translate(490, 15)">
      <!-- Seal Circle -->
      <circle cx="140" cy="30" r="28" fill="none" stroke="#1e3a8a" stroke-width="1.5" stroke-dasharray="2 1"/>
      <text x="140" y="27" font-size="7" font-weight="bold" fill="#1e3a8a" text-anchor="middle">VTU EXAM</text>
      <text x="140" y="38" font-size="6.5" font-weight="bold" fill="#1e3a8a" text-anchor="middle">BELAGAVI</text>

      <!-- Signature scribble -->
      <path d="M40,32 Q60,10 80,30 T120,25" fill="none" stroke="#1e3a8a" stroke-width="1.5"/>
      <text x="80" y="52" font-size="9" font-weight="700" fill="#334155" text-anchor="middle">Registrar (Evaluation)</text>
      <text x="80" y="64" font-size="8" font-weight="500" fill="#64748b" text-anchor="middle">Visvesvaraya Technological University</text>
    </g>
  </g>

  <!-- Security Verification Barcode & QR Code representation -->
  <g transform="translate(50, 740)">
    <rect x="0" y="0" width="700" height="60" fill="#ffffff" stroke="#e2e8f0" stroke-width="1" rx="4"/>
    <!-- Simulated 2D Barcode lines -->
    <g transform="translate(20, 15)">
      <line x1="0" y1="0" x2="0" y2="30" stroke="#000" stroke-width="2"/>
      <line x1="4" y1="0" x2="4" y2="30" stroke="#000" stroke-width="1"/>
      <line x1="8" y1="0" x2="8" y2="30" stroke="#000" stroke-width="3"/>
      <line x1="14" y1="0" x2="14" y2="30" stroke="#000" stroke-width="1"/>
      <line x1="18" y1="0" x2="18" y2="30" stroke="#000" stroke-width="2"/>
      <line x1="24" y1="0" x2="24" y2="30" stroke="#000" stroke-width="1.5"/>
      <line x1="30" y1="0" x2="30" y2="30" stroke="#000" stroke-width="3"/>
      <line x1="38" y1="0" x2="38" y2="30" stroke="#000" stroke-width="1"/>
      <line x1="44" y1="0" x2="44" y2="30" stroke="#000" stroke-width="2.5"/>
      <line x1="52" y1="0" x2="52" y2="30" stroke="#000" stroke-width="1"/>
      <line x1="58" y1="0" x2="58" y2="30" stroke="#000" stroke-width="2"/>
      <text x="0" y="38" font-size="7" font-family="monospace" fill="#64748b">VTU-VERIFY-${usn}</text>
    </g>

    <text x="180" y="28" font-size="10" font-weight="700" fill="#0f172a">CRYPTOGRAPHIC INTEGRITY NOTE:</text>
    <text x="180" y="44" font-size="9" font-weight="500" fill="#64748b">
      Marks card subject to continuous algorithmic cross-verification against university master database.
    </text>
  </g>

  <!-- Footer security advisory -->
  <text x="400" y="830" font-size="8.5" font-weight="500" fill="#94a3b8" text-anchor="middle">
    Generated in compliance with VTU CBCS Ordinance Clause 18OB 6.1 • Any erasure, alteration or mathematical discrepancy invalidates this document.
  </text>
</svg>
`;

  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;
}
