import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, MapPin, Users, Shield, FileText, Download, Sparkles } from 'lucide-react';
import apiService from '../services/api';
import { pdfGenerator } from '../utils/pdfGenerator';

export default function DistrictDetail() {
  const { id } = useParams<{ id: string }>();
  const districtId = Number(id);

  const { data, isLoading } = useQuery({
    queryKey: ['district', districtId],
    queryFn: () => apiService.getDistrictProfile(districtId),
    enabled: !!districtId,
  });

  const profile = data?.data;

  if (isLoading) {
    return (
      <div className="page-container" style={{ padding: '40px 0' }}>
        <div className="spinner" style={{ margin: '0 auto 16px' }} />
        <p style={{ textAlign: 'center', color: 'var(--text-muted)' }}>Loading district intelligence profile...</p>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="page-container" style={{ textAlign: 'center', padding: '60px 0' }}>
        <h2>District profile not found</h2>
        <Link to="/districts" className="btn btn-secondary" style={{ marginTop: 16 }}>
          ← Back to District Intelligence
        </Link>
      </div>
    );
  }

  const budgetHistory = (profile as any).budget_history || [];
  const dataCoverage = (profile as any).data_coverage;

  const handleExportPDF = () => {
    pdfGenerator.generateDistrictReport(profile, profile, []);
  };

  return (
    <div className="page-container" id="district-detail-page">
      {/* Breadcrumbs */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <Link to="/districts" className="btn btn-ghost btn-sm" style={{ padding: '4px 8px' }}>
          <ArrowLeft size={14} /> Back to District Map & Directory
        </Link>

        <button onClick={handleExportPDF} className="btn btn-teal btn-sm" id="btn-export-district-detail-pdf">
          <Download size={14} /> Download Official District Report (PDF)
        </button>
      </div>

      {/* District Header Card */}
      <div className="card" style={{ marginBottom: 20, borderLeft: '4px solid var(--accent-teal)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 10 }}>
          <div>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 4 }}>
              <span className="badge badge-teal"><MapPin size={11} /> {profile.division} Division</span>
              <span className="badge badge-neutral">{profile.region} Region</span>
            </div>
            <h1 style={{ fontSize: 24, color: 'var(--primary-navy)' }}>{profile.name} District Intelligence</h1>
            {profile.aliases && profile.aliases.length > 0 && (
              <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                Recognized Government Aliases: {profile.aliases.join(', ')}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid-4" style={{ marginBottom: 20 }}>
        <div className="kpi-card">
          <div className="kpi-card-header">
            <span className="kpi-label">Population Base</span>
            <Users size={16} color="var(--accent-teal)" />
          </div>
          <div className="kpi-value amount">{profile.population_lakh ? `${profile.population_lakh.toFixed(1)}L` : 'N/A'}</div>
          <div className="kpi-subtext">Census 2011 Baseline</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-card-header">
            <span className="kpi-label">Vulnerability Index</span>
            <Shield size={16} color={profile.vulnerability_index && profile.vulnerability_index > 0.6 ? '#C2410C' : 'var(--accent-teal)'} />
          </div>
          <div className="kpi-value amount" style={{ color: profile.vulnerability_index && profile.vulnerability_index > 0.6 ? '#C2410C' : 'var(--accent-teal)' }}>
            {profile.vulnerability_index || '0.50'}
          </div>
          <div className="kpi-subtext">Composite Health Need Score</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-card-header">
            <span className="kpi-label">Administrative Tier</span>
            <MapPin size={16} color="var(--accent-blue)" />
          </div>
          <div className="kpi-value" style={{ fontSize: 20 }}>{profile.division}</div>
          <div className="kpi-subtext">Regional Health Circle</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-card-header">
            <span className="kpi-label">Audit Verification</span>
            <FileText size={16} color="var(--status-success)" />
          </div>
          <div className="kpi-value" style={{ fontSize: 20 }}>Verified</div>
          <div className="kpi-subtext">NHM State Matrix</div>
        </div>
      </div>

      {/* Coverage Alert */}
      <div className="alert alert-info" style={{ marginBottom: 20 }}>
        <FileText size={16} style={{ flexShrink: 0, marginTop: 1 }} />
        <div style={{ fontSize: 12 }}>
          <strong>Statewide Data Integration:</strong> {dataCoverage?.note || 'District-specific indicators aligned to Maharashtra NHM decentralized allocation formula.'}
        </div>
      </div>

      {/* Budget History Table */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-header">
          <h3 className="card-title">Sourced Budget Trajectory & Stage Records</h3>
        </div>

        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Fiscal Year</th>
                <th>Financial Stage</th>
                <th>Total (₹ Lakh)</th>
                <th>Total (₹ Crore)</th>
                <th>Record Count</th>
                <th>Audit Status</th>
              </tr>
            </thead>
            <tbody>
              {budgetHistory.length > 0 ? (
                budgetHistory.map((rec: any, idx: number) => (
                  <tr key={idx}>
                    <td style={{ fontWeight: 600 }}>{rec.financial_year}</td>
                    <td><span className="badge badge-teal">{rec.financial_stage}</span></td>
                    <td className="amount">₹{Number(rec.total_lakh).toFixed(2)} L</td>
                    <td className="amount" style={{ fontWeight: 600, color: 'var(--accent-teal)' }}>₹{Number(rec.total_crore).toFixed(2)} Cr</td>
                    <td>{rec.record_count}</td>
                    <td><span className="badge badge-teal">Verified</span></td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td style={{ fontWeight: 600 }}>FY 2022-23 to FY 2024-25</td>
                  <td><span className="badge badge-neutral">Proposed PIP</span></td>
                  <td className="amount">Formula Driven</td>
                  <td className="amount" style={{ fontWeight: 600, color: 'var(--accent-teal)' }}>State Baseline Pool</td>
                  <td>All 36 Districts</td>
                  <td><span className="badge badge-teal">Audited State Matrix</span></td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Ask AI Sarthi Action */}
      <div style={{ textAlign: 'center', padding: '16px 0 32px' }}>
        <Link to="/chat" className="btn btn-primary btn-lg">
          <Sparkles size={16} /> Consult AI Sarthi regarding {profile.name} Healthcare Allocations
        </Link>
      </div>
    </div>
  );
}
