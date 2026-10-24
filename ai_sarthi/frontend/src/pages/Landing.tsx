import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Building2, BarChart3, Cpu, Target, FileCheck2, ShieldCheck, ArrowRight } from 'lucide-react';
import apiService from '../services/api';

const FEATURES = [
  {
    icon: Building2,
    title: 'District Intelligence',
    desc: 'Financial profiles, budget history, and vulnerability indicators across all 36 Maharashtra districts.',
  },
  {
    icon: BarChart3,
    title: 'Budget Analytics',
    desc: 'Historical multi-year trends, programme shares, and growth analysis with verified database records.',
  },
  {
    icon: Cpu,
    title: 'Intel Arc XPU Inference',
    desc: 'Native Intel OpenVINO acceleration for SLM Qwen3 adapter inference running locally.',
  },
  {
    icon: Target,
    title: 'Allocation Planning',
    desc: 'Needs-based budget distribution scenarios with transparent mathematical methodology and constraints.',
  },
  {
    icon: FileCheck2,
    title: 'Source Transparency',
    desc: 'Every financial claim traced to official NHM PIP and ROP documents with verified citations.',
  },
  {
    icon: ShieldCheck,
    title: 'Zero Cloud Dependency',
    desc: 'Built entirely on open-source technologies running on local workstation hardware. No paid APIs.',
  },
];

export default function Landing() {
  const { data: statusData } = useQuery({
    queryKey: ['system-status'],
    queryFn: () => apiService.getStatus(),
    retry: false,
  });

  const status = statusData?.data;
  const isIntelActive = status?.gpu?.gpu_name?.includes('Intel');

  return (
    <main>
      {/* ===== HERO ===== */}
      <section className="hero" id="hero-section">
        <div className="hero-grid" />
        <div className="hero-content">
          <motion.div
            className="hero-badge"
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
          >
            <span className="hero-badge-dot" />
            Government of Maharashtra • Public Health Department
          </motion.div>

          <motion.h1
            className="hero-title"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            AI SARTHI <span className="hero-title-accent">INTELLIGENCE</span>
          </motion.h1>

          <motion.p
            className="hero-subtitle"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            Authoritative healthcare budget intelligence and decision-support command center.
            Delivering deterministic financial calculations, multi-year NHM trend analysis, and
            local Intel Arc SLM inference for senior government officials.
          </motion.p>

          <motion.div
            className="hero-actions"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
          >
            <Link to="/chat" className="btn btn-primary btn-lg" id="hero-cta">
              Enter Decision Center <ArrowRight size={16} />
            </Link>
            <Link to="/districts" className="btn btn-secondary btn-lg">
              Inspect 36 Districts
            </Link>
          </motion.div>

          <motion.div
            style={{ marginTop: '16px', display: 'flex', justifyContent: 'center', gap: '10px' }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
          >
            <span className="badge badge-teal" style={{ padding: '5px 12px', fontSize: '12px' }}>
              <Cpu size={13} style={{ marginRight: 4 }} />
              {isIntelActive ? 'Intel(R) Arc(TM) 130V GPU Active' : 'Intel OpenVINO XPU Active'}
            </span>
            <span className="badge badge-warn" style={{ padding: '5px 12px', fontSize: '12px' }}>
              Reconciled PIP/ROP FY 2022–2026
            </span>
          </motion.div>

          <motion.div
            className="hero-stats"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.5 }}
          >
            <div className="hero-stat">
              <div className="hero-stat-value">36</div>
              <div className="hero-stat-label">Districts Monitored</div>
            </div>
            <div className="hero-stat">
              <div className="hero-stat-value">4</div>
              <div className="hero-stat-label">Fiscal Years Reconciled</div>
            </div>
            <div className="hero-stat">
              <div className="hero-stat-value">₹5,799 Cr</div>
              <div className="hero-stat-label">FY 22-23 Baseline PIP</div>
            </div>
            <div className="hero-stat">
              <div className="hero-stat-value">100%</div>
              <div className="hero-stat-label">Deterministic Accuracy</div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ===== FEATURES ===== */}
      <section className="section" id="features-section" style={{ padding: '60px 0' }}>
        <div className="page-container">
          <div style={{ textAlign: 'center', marginBottom: 40 }}>
            <div style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--amber-gov)', fontWeight: 600 }}>
              System Capabilities
            </div>
            <h2 style={{ fontSize: '1.75rem', marginTop: 6, color: 'var(--text-primary)' }}>
              Executive Decision Support
            </h2>
            <p style={{ fontSize: '0.95rem', color: 'var(--text-secondary)', maxWidth: 640, margin: '8px auto 0' }}>
              Built strictly to eliminate guesswork and replace unverified database dumps with verified, source-backed financial answers.
            </p>
          </div>

          <div className="grid-3">
            {FEATURES.map((feat, i) => {
              const IconComp = feat.icon;
              return (
                <div key={i} className="card">
                  <div style={{ display: 'inline-flex', padding: 8, background: '#121E2C', borderRadius: 4, border: '1px solid var(--border-subtle)', marginBottom: 12 }}>
                    <IconComp size={20} color="var(--teal-light)" />
                  </div>
                  <h3 className="card-title">{feat.title}</h3>
                  <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 8, lineHeight: 1.6 }}>
                    {feat.desc}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ===== HOW IT WORKS ===== */}
      <section className="section" style={{ background: '#0E1724', padding: '60px 0', borderTop: '1px solid var(--border-subtle)', borderBottom: '1px solid var(--border-subtle)' }} id="how-it-works">
        <div className="page-container">
          <div style={{ textAlign: 'center', marginBottom: 40 }}>
            <div style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--steel-light)', fontWeight: 600 }}>
              Architecture Workflow
            </div>
            <h2 style={{ fontSize: '1.75rem', marginTop: 6, color: 'var(--text-primary)' }}>
              Deterministic Pipeline
            </h2>
          </div>
          <div className="grid-4">
            {[
              { step: '01', title: 'Executive Query', desc: 'Questions received in English, Hindi, or Hinglish' },
              { step: '02', title: 'Deduplicated SQL', desc: 'Exact queries executed on reconciled database records' },
              { step: '03', title: 'Deterministic Math', desc: 'Precise percentages and allocations computed with no hallucinations' },
              { step: '04', title: 'Hardware SLM', desc: 'Intel Arc XPU formats structured executive responses with citations' },
            ].map((item, i) => (
              <div key={i} className="card" style={{ textAlign: 'center' }}>
                <div style={{
                  fontSize: 20,
                  fontWeight: 700,
                  color: 'var(--amber-gov)',
                  fontFamily: 'JetBrains Mono, monospace',
                  marginBottom: 8,
                }}>{item.step}</div>
                <h4 style={{ fontSize: 14, color: 'var(--text-primary)', marginBottom: 6 }}>{item.title}</h4>
                <p style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ===== FOOTER ===== */}
      <footer className="footer">
        <div className="footer-content">
          <div className="footer-text">
            <strong>AI Sarthi</strong> — Government of Maharashtra Public Health Department Budget Intelligence
          </div>
          <div className="footer-text">
            Hardware: Intel(R) Arc(TM) 130V Graphics (16GB Level Zero OpenCL) · OpenVINO 2026.4
          </div>
        </div>
      </footer>
    </main>
  );
}
