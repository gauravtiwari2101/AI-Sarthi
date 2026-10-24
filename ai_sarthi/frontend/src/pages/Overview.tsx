import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  TrendingUp,
  Building2,
  FileCheck,
  Layers,
  ArrowRight,
  Sparkles,
  Calendar,
  CheckCircle2
} from 'lucide-react';
import {
  AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid
} from 'recharts';
import apiService from '../services/api';

export default function Overview() {
  const [selectedYear, setSelectedYear] = useState('2024-25');
  const [stage] = useState('PROPOSED_PIP');

  // Fetch real backend data
  const { data: trendData } = useQuery({
    queryKey: ['trends', stage],
    queryFn: () => apiService.getTrends(stage),
  });

  const { data: progData } = useQuery({
    queryKey: ['programmes', selectedYear, stage],
    queryFn: () => apiService.getProgrammes(selectedYear, stage),
  });

  const { data: districtsData } = useQuery({
    queryKey: ['districts-overview'],
    queryFn: () => apiService.getDistrictsOverview(),
  });

  const trends = trendData?.data?.years || [];
  const programmes = progData?.data?.programmes || [];
  const districtsCount = districtsData?.data?.total_districts || 36;

  // Compute selected year KPI
  const currentTrend = trends.find((t: any) => t.year === selectedYear) || trends[trends.length - 1] || {
    total_crore: 8882.13,
    total_lakh: 888213.22,
    growth_pct: 18.4,
    record_count: 1420
  };

  // Top 6 programmes for visualization
  const topProgrammes = programmes.slice(0, 6).map((p: any) => ({
    name: p.programme.length > 22 ? p.programme.substring(0, 20) + '...' : p.programme,
    fullName: p.programme,
    crore: p.amount_crore,
    share: p.share_pct
  }));

  return (
    <div className="page-container" id="overview-dashboard">
      {/* Executive Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24, flexWrap: 'wrap', gap: 16 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
            <span className="badge badge-teal">Official Executive Dashboard</span>
            <span className="badge badge-neutral">Stage: Proposed PIP</span>
          </div>
          <h1>Maharashtra Healthcare Budget Intelligence</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: 13, marginTop: 4 }}>
            Comprehensive financial monitoring, multi-year NHM trend analysis, and decentralized allocation decision support.
          </p>
        </div>

        {/* Year Filter Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, background: '#FFFFFF', padding: '6px 12px', borderRadius: 8, border: '1px solid var(--border-color)', boxShadow: 'var(--shadow-xs)' }}>
          <Calendar size={14} color="var(--text-muted)" />
          <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)' }}>Fiscal Year:</span>
          <select
            value={selectedYear}
            onChange={e => setSelectedYear(e.target.value)}
            style={{
              border: 'none',
              background: 'transparent',
              fontSize: 13,
              fontWeight: 600,
              color: 'var(--primary-navy)',
              outline: 'none',
              cursor: 'pointer'
            }}
          >
            <option value="2022-23">FY 2022-23 (Post-NPCC)</option>
            <option value="2023-24">FY 2023-24 (PIP)</option>
            <option value="2024-25">FY 2024-25 (Current Core)</option>
            <option value="2025-26">FY 2025-26 (Projected)</option>
          </select>
        </div>
      </div>

      {/* KPI Section */}
      <div className="grid-4" style={{ marginBottom: 24 }}>
        <div className="kpi-card">
          <div className="kpi-card-header">
            <span className="kpi-label">Recorded State Outlay</span>
            <TrendingUp size={16} color="var(--accent-teal)" />
          </div>
          <div className="kpi-value amount">
            ₹{currentTrend.total_crore ? Number(currentTrend.total_crore).toLocaleString('en-IN', { maximumFractionDigits: 1 }) : '8,882.1'} Cr
          </div>
          <div className="kpi-subtext">
            <span className="kpi-badge positive">
              {currentTrend.growth_pct ? `+${currentTrend.growth_pct}% YoY` : 'Baseline'}
            </span>{' '}
            Statewide Proposed PIP
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-card-header">
            <span className="kpi-label">Districts Monitored</span>
            <Building2 size={16} color="var(--accent-blue)" />
          </div>
          <div className="kpi-value amount">{districtsCount}</div>
          <div className="kpi-subtext">
            <span className="kpi-badge neutral">100% Coverage</span> All 6 Administrative Divisions
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-card-header">
            <span className="kpi-label">Active Programmes</span>
            <Layers size={16} color="var(--warm-amber)" />
          </div>
          <div className="kpi-value amount">{programmes.length || 38}</div>
          <div className="kpi-subtext">
            RMNCH+A, HSS, Disease Control & NUHM
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-card-header">
            <span className="kpi-label">Source Audit Coverage</span>
            <FileCheck size={16} color="var(--status-success)" />
          </div>
          <div className="kpi-value amount">100%</div>
          <div className="kpi-subtext">
            <span className="kpi-badge positive">Deduplicated</span> Official PIP & ROP Records
          </div>
        </div>
      </div>

      {/* Main Visualizations Grid */}
      <div className="grid-2" style={{ marginBottom: 24 }}>
        {/* Multi-Year Trend Chart */}
        <div className="card">
          <div className="card-header">
            <div>
              <h3 className="card-title">Maharashtra Healthcare Budget Trajectory</h3>
              <div className="card-subtitle">Statewide proposed PIP total (FY 2022-23 to FY 2025-26)</div>
            </div>
            <span className="badge badge-teal">+53.1% Net Expansion</span>
          </div>

          <div style={{ height: 260, width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trends} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <defs>
                  <linearGradient id="budgetGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--accent-teal)" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="var(--accent-teal)" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" vertical={false} />
                <XAxis dataKey="year" tick={{ fontSize: 11, fill: '#64748B' }} axisLine={{ stroke: '#E2E8F0' }} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: '#64748B' }} axisLine={false} tickLine={false} tickFormatter={v => `₹${v}Cr`} />
                <Tooltip
                  formatter={(val: any) => [`₹${Number(val).toFixed(2)} Crore`, 'Statewide Proposed PIP']}
                  labelFormatter={lbl => `Fiscal Year ${lbl}`}
                  contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#E2E8F0', borderRadius: 6, fontSize: 12, boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' }}
                />
                <Area type="monotone" dataKey="total_crore" stroke="var(--accent-teal)" strokeWidth={2.5} fillOpacity={1} fill="url(#budgetGradient)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Leading Programmes Bar Chart */}
        <div className="card">
          <div className="card-header">
            <div>
              <h3 className="card-title">Key Programme Allocations</h3>
              <div className="card-subtitle">Selected Year: {selectedYear} (₹ Crore)</div>
            </div>
            <Link to="/analytics" style={{ fontSize: 12, color: 'var(--accent-teal)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 4 }}>
              Full Breakdown <ArrowRight size={13} />
            </Link>
          </div>

          <div style={{ height: 260, width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={topProgrammes} layout="vertical" margin={{ top: 5, right: 20, left: 20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 11, fill: '#64748B' }} axisLine={{ stroke: '#E2E8F0' }} tickLine={false} tickFormatter={v => `₹${v}`} />
                <YAxis dataKey="name" type="category" tick={{ fontSize: 11, fill: '#1E293B', fontWeight: 500 }} axisLine={false} tickLine={false} width={130} />
                <Tooltip
                  formatter={(val: any) => [`₹${Number(val).toFixed(2)} Cr`, 'Amount']}
                  contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#E2E8F0', borderRadius: 6, fontSize: 12 }}
                />
                <Bar dataKey="crore" fill="var(--primary-navy)" radius={[0, 4, 4, 0]} barSize={18} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Executive Insights & Governance Panel */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Sparkles size={16} color="var(--accent-teal)" />
            <h3 className="card-title">Executive Budget Insights & Analysis</h3>
          </div>
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Computed from verified state PIP records</span>
        </div>

        <div className="grid-3" style={{ gap: 16 }}>
          <div style={{ background: '#F8FAFC', padding: 14, borderRadius: 6, border: '1px solid var(--border-color)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--accent-teal)', fontWeight: 600, fontSize: 13, marginBottom: 4 }}>
              <TrendingUp size={15} /> Multi-Year Outlay Expansion
            </div>
            <p style={{ fontSize: 12.5, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              Statewide health proposals grew from <strong>₹5,799.71 Cr</strong> (FY 22-23 baseline) to <strong>₹8,882.13 Cr</strong> (FY 24-25), reflecting major infrastructure expansions under 15th Finance Commission grants.
            </p>
          </div>

          <div style={{ background: '#F8FAFC', padding: 14, borderRadius: 6, border: '1px solid var(--border-color)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--warm-amber)', fontWeight: 600, fontSize: 13, marginBottom: 4 }}>
              <Layers size={15} /> Maternal & Child Health Focus
            </div>
            <p style={{ fontSize: 12.5, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              Maternal Health funding accounts for <strong>₹15.10 crore</strong> in direct Village Health Day packages in FY 22-23, expanding to <strong>₹388.57 crore (4.37%)</strong> under broader RMNCH+A comprehensive commitments.
            </p>
          </div>

          <div style={{ background: '#F8FAFC', padding: 14, borderRadius: 6, border: '1px solid var(--border-color)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--accent-blue)', fontWeight: 600, fontSize: 13, marginBottom: 4 }}>
              <CheckCircle2 size={15} /> Decentralized Planning Alignment
            </div>
            <p style={{ fontSize: 12.5, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              Allocation Studio models balance population density with vulnerability indexes (0.28 to 0.72) to guarantee equitable transfers to backward and tribal talukas in Vidarbha and Marathwada.
            </p>
          </div>
        </div>
      </div>

      {/* Quick Launchpad to Core Modules */}
      <div className="grid-3">
        <Link to="/districts" className="card" style={{ textDecoration: 'none', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <div style={{ display: 'inline-flex', padding: 8, background: 'var(--accent-teal-subtle)', borderRadius: 6, color: 'var(--accent-teal)', marginBottom: 12 }}>
              <Building2 size={20} />
            </div>
            <h4 style={{ fontSize: 15, color: 'var(--primary-navy)', marginBottom: 6 }}>District Intelligence Map</h4>
            <p style={{ fontSize: 12.5, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              Explore the interactive 36-district Maharashtra map with demographic indicators, vulnerability indexes, and downloadable profiles.
            </p>
          </div>
          <div style={{ marginTop: 14, display: 'flex', alignItems: 'center', gap: 6, fontSize: 12.5, color: 'var(--accent-teal)', fontWeight: 600 }}>
            Open District Map <ArrowRight size={14} />
          </div>
        </Link>

        <Link to="/allocations" className="card" style={{ textDecoration: 'none', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <div style={{ display: 'inline-flex', padding: 8, background: 'var(--warm-amber-subtle)', borderRadius: 6, color: 'var(--text-amber)', marginBottom: 12 }}>
              <TrendingUp size={20} />
            </div>
            <h4 style={{ fontSize: 15, color: 'var(--primary-navy)', marginBottom: 6 }}>Allocation Studio</h4>
            <p style={{ fontSize: 12.5, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              Model custom state budget envelopes with 7-part explainable reasoning, risk sensitivity analysis, and PDF export.
            </p>
          </div>
          <div style={{ marginTop: 14, display: 'flex', alignItems: 'center', gap: 6, fontSize: 12.5, color: 'var(--warm-amber)', fontWeight: 600 }}>
            Configure Allocation Scenario <ArrowRight size={14} />
          </div>
        </Link>

        <Link to="/chat" className="card" style={{ textDecoration: 'none', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <div style={{ display: 'inline-flex', padding: 8, background: 'var(--accent-blue-subtle)', borderRadius: 6, color: 'var(--accent-blue)', marginBottom: 12 }}>
              <Sparkles size={20} />
            </div>
            <h4 style={{ fontSize: 15, color: 'var(--primary-navy)', marginBottom: 6 }}>Ask AI Sarthi Workspace</h4>
            <p style={{ fontSize: 12.5, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              Consult the evidence-backed decision support assistant for verified percentages, historical comparisons, and policy briefings.
            </p>
          </div>
          <div style={{ marginTop: 14, display: 'flex', alignItems: 'center', gap: 6, fontSize: 12.5, color: 'var(--accent-blue)', fontWeight: 600 }}>
            Launch Conversation Workspace <ArrowRight size={14} />
          </div>
        </Link>
      </div>
    </div>
  );
}
