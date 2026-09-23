import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { ShieldCheck, Scan, Layers } from 'lucide-react';

export const Hero3DCanvas: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isWebGLAvailable, setIsWebGLAvailable] = useState<boolean>(true);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // Check WebGL support
    try {
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
      if (!gl) {
        setIsWebGLAvailable(false);
        return;
      }
    } catch {
      setIsWebGLAvailable(false);
      return;
    }

    // Three.js Scene Setup
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x0b0f19, 0.12);

    const width = container.clientWidth || 500;
    const height = container.clientHeight || 500;

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(0, 0, 4.2);

    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance',
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;
    container.appendChild(renderer.domElement);

    // --- PROCEDURAL CERTIFICATE TEXTURE ---
    const canvas = document.createElement('canvas');
    canvas.width = 1024;
    canvas.height = 1448; // Standard A4 aspect ratio
    const ctx = canvas.getContext('2d');
    if (ctx) {
      // Dark luxurious parchment background
      const bgGrad = ctx.createLinearGradient(0, 0, 1024, 1448);
      bgGrad.addColorStop(0, '#0f172a');
      bgGrad.addColorStop(0.5, '#131d36');
      bgGrad.addColorStop(1, '#0b1120');
      ctx.fillStyle = bgGrad;
      ctx.fillRect(0, 0, 1024, 1448);

      // Guilloche ornate double border
      ctx.strokeStyle = 'rgba(16, 185, 129, 0.6)';
      ctx.lineWidth = 6;
      ctx.strokeRect(36, 36, 952, 1376);

      ctx.strokeStyle = 'rgba(6, 182, 212, 0.4)';
      ctx.lineWidth = 2;
      ctx.strokeRect(52, 52, 920, 1344);

      // Micro-pattern security corner accents
      const drawCorner = (x: number, y: number, angle: number) => {
        ctx.save();
        ctx.translate(x, y);
        ctx.rotate(angle);
        ctx.strokeStyle = '#10B981';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(40, 0);
        ctx.lineTo(40, 40);
        ctx.stroke();
        ctx.restore();
      };
      drawCorner(70, 70, 0);
      drawCorner(954, 70, Math.PI / 2);
      drawCorner(954, 1378, Math.PI);
      drawCorner(70, 1378, -Math.PI / 2);

      // University Seal Emblem (Center-Top)
      ctx.save();
      ctx.translate(512, 220);
      ctx.beginPath();
      ctx.arc(0, 0, 70, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(16, 185, 129, 0.15)';
      ctx.fill();
      ctx.strokeStyle = 'rgba(16, 185, 129, 0.8)';
      ctx.lineWidth = 4;
      ctx.stroke();

      // Inner seal star
      ctx.strokeStyle = 'rgba(6, 182, 212, 0.7)';
      ctx.lineWidth = 2;
      for (let i = 0; i < 8; i++) {
        ctx.rotate(Math.PI / 4);
        ctx.strokeRect(-25, -25, 50, 50);
      }
      ctx.restore();

      // Certificate Typography
      ctx.textAlign = 'center';
      ctx.fillStyle = 'rgba(241, 245, 249, 0.9)';
      ctx.font = 'bold 36px sans-serif';
      ctx.fillText('UNIVERSITY OF ADVANCED SCIENCES', 512, 360);

      ctx.fillStyle = 'rgba(148, 163, 184, 0.8)';
      ctx.font = '20px monospace';
      ctx.fillText('OFFICIAL ACCREDITED DIPLOMA OF EXCELLENCE', 512, 410);

      ctx.fillStyle = 'rgba(16, 185, 129, 0.9)';
      ctx.font = 'italic 26px serif';
      ctx.fillText('This is to certify that', 512, 490);

      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 44px sans-serif';
      ctx.fillText('ALEXANDRA V. MERCER', 512, 570);

      ctx.fillStyle = 'rgba(148, 163, 184, 0.85)';
      ctx.font = '22px sans-serif';
      ctx.fillText('has fulfilled all requirements for the degree of', 512, 640);

      ctx.fillStyle = 'rgba(6, 182, 212, 0.95)';
      ctx.font = 'bold 32px sans-serif';
      ctx.fillText('MASTER OF SCIENCE IN ARTIFICIAL INTELLIGENCE', 512, 700);

      ctx.fillStyle = 'rgba(148, 163, 184, 0.75)';
      ctx.font = '18px monospace';
      ctx.fillText('CUM LAUDE • HONORS IN NEURAL SYSTEMS • GPA: 3.96', 512, 750);

      // Cryptographic Hash & QR Code Simulation
      ctx.strokeStyle = 'rgba(16, 185, 129, 0.5)';
      ctx.strokeRect(120, 850, 784, 120);
      ctx.fillStyle = 'rgba(16, 185, 129, 0.08)';
      ctx.fillRect(120, 850, 784, 120);

      ctx.textAlign = 'left';
      ctx.fillStyle = 'rgba(16, 185, 129, 0.9)';
      ctx.font = '14px monospace';
      ctx.fillText('BLOCKCHAIN HASH: 0x9f83a2b7c4d1e8902bca47102e3b8f1d7a6e5c9b', 140, 890);
      ctx.fillText('HMAC SIGNATURE : a72f10b3e58914c6d29871fa01cb74ef62d981ba', 140, 920);
      ctx.fillText('REGISTRY STATUS: VERIFIED BY NATIONAL HIGHER ED LEDGER', 140, 950);

      // Signatures
      ctx.textAlign = 'center';
      ctx.strokeStyle = 'rgba(148, 163, 184, 0.5)';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(180, 1180);
      ctx.lineTo(400, 1180);
      ctx.moveTo(624, 1180);
      ctx.lineTo(844, 1180);
      ctx.stroke();

      ctx.fillStyle = 'rgba(203, 213, 225, 0.8)';
      ctx.font = 'italic 22px cursive';
      ctx.fillText('Arthur Pendelton, Ph.D.', 290, 1160);
      ctx.fillText('Victoria Sterling, Dean', 734, 1160);

      ctx.font = '14px monospace';
      ctx.fillStyle = 'rgba(100, 116, 139, 0.9)';
      ctx.fillText('University Registrar', 290, 1210);
      ctx.fillText('President of Academic Board', 734, 1210);

      // Watermark Stamp
      ctx.save();
      ctx.translate(512, 1080);
      ctx.rotate(-Math.PI / 12);
      ctx.strokeStyle = 'rgba(16, 185, 129, 0.35)';
      ctx.lineWidth = 4;
      ctx.strokeRect(-160, -40, 320, 80);
      ctx.fillStyle = 'rgba(16, 185, 129, 0.4)';
      ctx.font = 'bold 24px monospace';
      ctx.fillText('FORENSIC INTEGRITY: 99.4%', 0, 8);
      ctx.restore();
    }

    const certificateTexture = new THREE.CanvasTexture(canvas);
    certificateTexture.minFilter = THREE.LinearMipmapLinearFilter;
    certificateTexture.magFilter = THREE.LinearFilter;

    // --- CERTIFICATE 3D MESH ---
    const certWidth = 2.0;
    const certHeight = 2.82; // 1 : 1.414 ratio
    const certGeometry = new THREE.BoxGeometry(certWidth, certHeight, 0.02);

    // Front: Certificate Texture, Back/Sides: Dark Sleek Slate
    const sideMaterial = new THREE.MeshStandardMaterial({
      color: 0x0f172a,
      roughness: 0.5,
      metalness: 0.8,
    });
    const frontMaterial = new THREE.MeshStandardMaterial({
      map: certificateTexture,
      roughness: 0.3,
      metalness: 0.2,
      emissive: 0x064e3b,
      emissiveIntensity: 0.05,
    });

    const materials = [
      sideMaterial, // right
      sideMaterial, // left
      sideMaterial, // top
      sideMaterial, // bottom
      frontMaterial, // front
      sideMaterial, // back
    ];

    const certificateMesh = new THREE.Mesh(certGeometry, materials);
    certificateMesh.castShadow = true;
    certificateMesh.receiveShadow = true;

    // Outer Glowing Frame / Shield Ring
    const frameGeometry = new THREE.RingGeometry(1.65, 1.68, 64);
    const frameMaterial = new THREE.MeshBasicMaterial({
      color: 0x06b6d4,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.35,
    });
    const outerRing = new THREE.Mesh(frameGeometry, frameMaterial);
    outerRing.position.z = -0.05;

    // --- SCANNING LASER PLANE ---
    const laserGeometry = new THREE.PlaneGeometry(certWidth * 1.15, 0.08);
    const laserMaterial = new THREE.MeshBasicMaterial({
      color: 0x10b981,
      transparent: true,
      opacity: 0.9,
      blending: THREE.AdditiveBlending,
      side: THREE.DoubleSide,
    });
    const laserBeam = new THREE.Mesh(laserGeometry, laserMaterial);
    laserBeam.position.z = 0.03;

    // Laser glow aura
    const auraGeometry = new THREE.PlaneGeometry(certWidth * 1.15, 0.4);
    const auraMaterial = new THREE.MeshBasicMaterial({
      color: 0x06b6d4,
      transparent: true,
      opacity: 0.3,
      blending: THREE.AdditiveBlending,
      side: THREE.DoubleSide,
    });
    const laserAura = new THREE.Mesh(auraGeometry, auraMaterial);
    laserAura.position.z = 0.025;

    const laserGroup = new THREE.Group();
    laserGroup.add(laserBeam);
    laserGroup.add(laserAura);

    // --- POINT CLOUD FORENSIC VERTICES ---
    const particleCount = 280;
    const particleGeometry = new THREE.BufferGeometry();
    const particlePositions = new Float32Array(particleCount * 3);
    const particleColors = new Float32Array(particleCount * 3);

    const emerald = new THREE.Color(0x10b981);
    const cyan = new THREE.Color(0x06b6d4);
    const amber = new THREE.Color(0xf59e0b);

    for (let i = 0; i < particleCount; i++) {
      // Points distributed across certificate bounds representing OCR tokens and ELA anchors
      particlePositions[i * 3] = (Math.random() - 0.5) * (certWidth * 0.95);
      particlePositions[i * 3 + 1] = (Math.random() - 0.5) * (certHeight * 0.95);
      particlePositions[i * 3 + 2] = 0.03 + Math.random() * 0.08;

      const col = Math.random() > 0.3 ? emerald : Math.random() > 0.5 ? cyan : amber;
      particleColors[i * 3] = col.r;
      particleColors[i * 3 + 1] = col.g;
      particleColors[i * 3 + 2] = col.b;
    }

    particleGeometry.setAttribute('position', new THREE.BufferAttribute(particlePositions, 3));
    particleGeometry.setAttribute('color', new THREE.BufferAttribute(particleColors, 3));

    const particleMaterial = new THREE.PointsMaterial({
      size: 0.035,
      vertexColors: true,
      transparent: true,
      opacity: 0.85,
      blending: THREE.AdditiveBlending,
    });

    const particles = new THREE.Points(particleGeometry, particleMaterial);

    // Master Diploma Group
    const diplomaGroup = new THREE.Group();
    diplomaGroup.add(certificateMesh);
    diplomaGroup.add(outerRing);
    diplomaGroup.add(laserGroup);
    diplomaGroup.add(particles);
    diplomaGroup.rotation.y = -0.15;
    diplomaGroup.rotation.x = 0.1;
    scene.add(diplomaGroup);

    // Background floating ambient cyber nodes
    const ambientCount = 120;
    const ambientGeometry = new THREE.BufferGeometry();
    const ambientPositions = new Float32Array(ambientCount * 3);

    for (let i = 0; i < ambientCount; i++) {
      ambientPositions[i * 3] = (Math.random() - 0.5) * 10;
      ambientPositions[i * 3 + 1] = (Math.random() - 0.5) * 8;
      ambientPositions[i * 3 + 2] = -1 - Math.random() * 4;
    }
    ambientGeometry.setAttribute('position', new THREE.BufferAttribute(ambientPositions, 3));
    const ambientParticles = new THREE.Points(
      ambientGeometry,
      new THREE.PointsMaterial({
        color: 0x334155,
        size: 0.025,
        transparent: true,
        opacity: 0.5,
      })
    );
    scene.add(ambientParticles);

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
    scene.add(ambientLight);

    const pointLight = new THREE.PointLight(0x10b981, 2.5, 8);
    pointLight.position.set(1.5, 2, 2);
    scene.add(pointLight);

    const cyanLight = new THREE.PointLight(0x06b6d4, 2, 8);
    cyanLight.position.set(-1.5, -1.5, 2);
    scene.add(cyanLight);

    // Mouse Interaction Parallax with Lerp
    let targetRotationX = 0.08;
    let targetRotationY = -0.12;
    let currentRotationX = 0.08;
    let currentRotationY = -0.12;

    const handleMouseMove = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      const y = -(((e.clientY - rect.top) / rect.height) * 2 - 1);

      targetRotationY = x * 0.35;
      targetRotationX = -y * 0.25;
    };

    const handleMouseEnter = () => {};
    const handleMouseLeave = () => {
      targetRotationX = 0.08;
      targetRotationY = -0.12;
    };

    container.addEventListener('mousemove', handleMouseMove);
    container.addEventListener('mouseenter', handleMouseEnter);
    container.addEventListener('mouseleave', handleMouseLeave);

    // Animation Loop
    let animationFrameId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);

      const elapsedTime = clock.getElapsedTime();

      // Lerp mouse parallax smoothing
      currentRotationX += (targetRotationX - currentRotationX) * 0.06;
      currentRotationY += (targetRotationY - currentRotationY) * 0.06;

      diplomaGroup.rotation.x = currentRotationX;
      diplomaGroup.rotation.y = currentRotationY;

      // Gentle floating levitation
      diplomaGroup.position.y = Math.sin(elapsedTime * 1.8) * 0.08;

      // Scanning Laser Movement (sweeping up and down)
      const laserY = Math.sin(elapsedTime * 2.2) * (certHeight * 0.45);
      laserGroup.position.y = laserY;

      // Rotate outer holographic ring
      outerRing.rotation.z = elapsedTime * 0.15;

      // Particle vertex pulse
      particleMaterial.size = 0.032 + Math.sin(elapsedTime * 3) * 0.008;

      renderer.render(scene, camera);
    };

    animate();

    // Resize Handler
    const handleResize = () => {
      if (!container) return;
      const newWidth = container.clientWidth;
      const newHeight = container.clientHeight;
      camera.aspect = newWidth / newHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(newWidth, newHeight);
    };

    window.addEventListener('resize', handleResize);

    // Cleanup
    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', handleResize);
      container.removeEventListener('mousemove', handleMouseMove);
      container.removeEventListener('mouseenter', handleMouseEnter);
      container.removeEventListener('mouseleave', handleMouseLeave);

      renderer.dispose();
      certGeometry.dispose();
      frameGeometry.dispose();
      laserGeometry.dispose();
      auraGeometry.dispose();
      particleGeometry.dispose();
      ambientGeometry.dispose();

      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, []);

  return (
    <div className="relative w-full h-[420px] sm:h-[500px] lg:h-[560px] flex items-center justify-center">
      {/* Three.js canvas container */}
      <div
        ref={containerRef}
        className="w-full h-full cursor-grab active:cursor-grabbing relative z-10"
        title="Interactive 3D Diploma: Move mouse to tilt parallax, inspect laser scanner"
      />

      {/* Floating HUD status cards */}
      <div className="absolute top-4 left-4 z-20 pointer-events-none hidden sm:flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-slate-900/80 border border-slate-700/60 backdrop-blur-md text-[11px] font-mono text-emerald-400">
        <Scan className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
        <span>LASER OCR SWEEP: ACTIVE</span>
      </div>

      <div className="absolute bottom-6 right-4 z-20 pointer-events-none hidden sm:flex flex-col space-y-1 p-3 rounded-2xl bg-slate-900/85 border border-slate-700/60 backdrop-blur-md text-[10px] font-mono text-slate-300 shadow-xl">
        <div className="flex items-center space-x-1.5 text-cyan-400 font-semibold">
          <Layers className="w-3.5 h-3.5" />
          <span>Point-Cloud Feature Mesh</span>
        </div>
        <div className="text-slate-400 flex justify-between gap-4">
          <span>OCR Bounding Vertices</span>
          <span className="text-emerald-400 font-bold">280 nodes</span>
        </div>
        <div className="text-slate-400 flex justify-between gap-4">
          <span>ELA Difference Map</span>
          <span className="text-cyan-400 font-bold">Multi-Scale DCT</span>
        </div>
        <div className="text-slate-400 flex justify-between gap-4">
          <span>Homography Alignment</span>
          <span className="text-emerald-400 font-bold">SIFT / ORB</span>
        </div>
      </div>

      {/* Non-WebGL Fallback */}
      {!isWebGLAvailable && (
        <div className="absolute inset-0 flex flex-col items-center justify-center p-6 text-center bg-slate-900/80 rounded-3xl border border-slate-800 backdrop-blur-md">
          <ShieldCheck className="w-16 h-16 text-emerald-400 mb-3" />
          <h3 className="text-lg font-bold text-slate-100">3D Neural Visualizer</h3>
          <p className="text-xs text-slate-400 max-w-xs mt-1">
            Real-time interactive diploma mesh with laser OCR sweeping and point-cloud feature extraction.
          </p>
        </div>
      )}
    </div>
  );
};
