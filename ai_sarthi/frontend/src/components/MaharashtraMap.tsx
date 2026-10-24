import { useState } from 'react';
import districtPaths from '../data/maharashtra_svg_paths.json';

export type MapMetric = 'vulnerability' | 'population' | 'allocation_share' | 'status';

interface MaharashtraMapProps {
  selectedDistrict: string | null;
  onSelectDistrict: (districtName: string) => void;
  metric: MapMetric;
  districtDataMap: Record<string, {
    population_lakh: number;
    vulnerability_index: number;
    share_pct?: number;
    division?: string;
  }>;
}

export default function MaharashtraMap({
  selectedDistrict,
  onSelectDistrict,
  metric,
  districtDataMap
}: MaharashtraMapProps) {
  const [hoveredDistrict, setHoveredDistrict] = useState<string | null>(null);

  // Choropleth color computation
  const getDistrictColor = (name: string, isSelected: boolean, isHovered: boolean) => {
    if (isSelected) return '#D49A35'; // Selected warm amber highlight
    if (isHovered) return '#0C9B92'; // Hover teal

    const data = districtDataMap[name] || {};

    if (metric === 'vulnerability') {
      const v = data.vulnerability_index || 0.5;
      if (v >= 0.65) return '#C2410C'; // Highest need / deep amber-orange
      if (v >= 0.55) return '#EA580C';
      if (v >= 0.45) return '#D97706';
      if (v >= 0.35) return '#0D9488';
      return '#2DD4BF'; // Lowest vulnerability
    }

    if (metric === 'population') {
      const p = data.population_lakh || 20;
      if (p >= 70) return '#14263D'; // Highly populated metro
      if (p >= 40) return '#26384A';
      if (p >= 25) return '#3476A8';
      if (p >= 15) return '#64748B';
      return '#94A3B8';
    }

    if (metric === 'allocation_share') {
      const s = data.share_pct || 2.5;
      if (s >= 4.0) return '#087F77';
      if (s >= 3.0) return '#0D9488';
      if (s >= 2.0) return '#14B8A6';
      return '#99F6E4';
    }

    // Default status: verified
    return '#087F77';
  };

  const hoveredData = hoveredDistrict ? districtDataMap[hoveredDistrict] : null;

  return (
    <div style={{ position: 'relative', width: '100%', background: '#FFFFFF', borderRadius: 8, border: '1px solid var(--border-color)', padding: 16 }}>
      {/* Map Legend */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12, flexWrap: 'wrap', gap: 10 }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--primary-navy)' }}>
          Maharashtra 36 Districts — Metric:{' '}
          <span style={{ color: 'var(--accent-teal)', textTransform: 'capitalize' }}>
            {metric.replace('_', ' ')}
          </span>
        </div>

        {/* Legend Scale */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: 'var(--text-muted)' }}>
          <span>Low</span>
          <div style={{ display: 'flex', gap: 2 }}>
            {metric === 'vulnerability' ? (
              <>
                <span style={{ width: 14, height: 10, background: '#2DD4BF', borderRadius: 2 }} />
                <span style={{ width: 14, height: 10, background: '#0D9488', borderRadius: 2 }} />
                <span style={{ width: 14, height: 10, background: '#D97706', borderRadius: 2 }} />
                <span style={{ width: 14, height: 10, background: '#EA580C', borderRadius: 2 }} />
                <span style={{ width: 14, height: 10, background: '#C2410C', borderRadius: 2 }} />
              </>
            ) : metric === 'population' ? (
              <>
                <span style={{ width: 14, height: 10, background: '#94A3B8', borderRadius: 2 }} />
                <span style={{ width: 14, height: 10, background: '#64748B', borderRadius: 2 }} />
                <span style={{ width: 14, height: 10, background: '#3476A8', borderRadius: 2 }} />
                <span style={{ width: 14, height: 10, background: '#26384A', borderRadius: 2 }} />
                <span style={{ width: 14, height: 10, background: '#14263D', borderRadius: 2 }} />
              </>
            ) : (
              <>
                <span style={{ width: 14, height: 10, background: '#99F6E4', borderRadius: 2 }} />
                <span style={{ width: 14, height: 10, background: '#14B8A6', borderRadius: 2 }} />
                <span style={{ width: 14, height: 10, background: '#0D9488', borderRadius: 2 }} />
                <span style={{ width: 14, height: 10, background: '#087F77', borderRadius: 2 }} />
              </>
            )}
          </div>
          <span>High Priority</span>
        </div>
      </div>

      {/* SVG Map Canvas */}
      <div style={{ width: '100%', height: 'auto', maxHeight: 520, display: 'flex', justifyContent: 'center' }}>
        <svg
          viewBox="0 0 800 640"
          style={{ width: '100%', height: 'auto', maxHeight: 520 }}
          onMouseLeave={() => setHoveredDistrict(null)}
        >
          {districtPaths.map((d: any) => {
            const isSelected = selectedDistrict?.toLowerCase() === d.name.toLowerCase();
            const isHovered = hoveredDistrict?.toLowerCase() === d.name.toLowerCase();
            const fill = getDistrictColor(d.name, isSelected, isHovered);

            return (
              <g key={d.id} id={`map-district-${d.id}`}>
                <path
                  d={d.path}
                  fill={fill}
                  stroke={isSelected ? '#14263D' : '#FFFFFF'}
                  strokeWidth={isSelected ? 2.5 : isHovered ? 1.8 : 0.8}
                  style={{
                    cursor: 'pointer',
                    transition: 'fill 0.15s ease, stroke 0.15s ease, stroke-width 0.15s ease'
                  }}
                  onMouseEnter={() => setHoveredDistrict(d.name)}
                  onClick={() => onSelectDistrict(d.name)}
                />
              </g>
            );
          })}
        </svg>
      </div>

      {/* District Hover Tooltip */}
      {hoveredDistrict && hoveredData && (
        <div style={{
          position: 'absolute',
          bottom: 24,
          left: 24,
          background: 'rgba(20, 38, 61, 0.95)',
          color: '#FFFFFF',
          padding: '8px 14px',
          borderRadius: 6,
          fontSize: 12,
          pointerEvents: 'none',
          boxShadow: 'var(--shadow-md)',
          zIndex: 10,
          backdropFilter: 'blur(4px)'
        }}>
          <div style={{ fontWeight: 700, fontSize: 13, color: '#D49A35', marginBottom: 2 }}>
            {hoveredDistrict} District
          </div>
          <div>Division: {hoveredData.division || 'Maharashtra'}</div>
          <div>Population: {hoveredData.population_lakh ? `${hoveredData.population_lakh} Lakh` : 'Sourced'}</div>
          <div>Vulnerability Index: {hoveredData.vulnerability_index || '0.50'}</div>
          {hoveredData.share_pct && (
            <div>Decentralized Share: {hoveredData.share_pct.toFixed(2)}%</div>
          )}
          <div style={{ fontSize: 10, color: '#94A3B8', marginTop: 4 }}>Click district for full profile</div>
        </div>
      )}
    </div>
  );
}
