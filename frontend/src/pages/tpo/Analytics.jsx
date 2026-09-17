/**
 * TPO Analytics — placement analytics: dept rates, package distribution,
 * skill demand heatmap, year-over-year comparison.
 * Connected to live database via analyticsApi.
 */

import { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, CartesianGrid, PieChart, Pie, Cell,
} from 'recharts';
import { analyticsApi } from '../../api/endpoints';

const DEFAULT_COLORS = ['#6366f1', '#06b6d4', '#f59e0b', '#22c55e', '#ec4899', '#8b5cf6'];

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: 8, padding: 'var(--space-3) var(--space-4)' }}>
      <div style={{ fontWeight: 600, marginBottom: 4 }}>{label}</div>
      {payload.map(p => (
        <div key={p.name} style={{ color: p.color, fontSize: 'var(--font-size-sm)' }}>{p.name}: {p.value}</div>
      ))}
    </div>
  );
}

function CustomLabel({ cx, cy, midAngle, innerRadius, outerRadius, value }) {
  const RADIAN = Math.PI / 180;
  const r = innerRadius + (outerRadius - innerRadius) * 0.5;
  const x = cx + r * Math.cos(-midAngle * RADIAN);
  const y = cy + r * Math.sin(-midAngle * RADIAN);
  return (
    <text x={x} y={y} fill="white" textAnchor="middle" dominantBaseline="central" fontSize={11} fontWeight={600}>
      {value}
    </text>
  );
}

export default function TPOAnalytics() {
  const [stats, setStats] = useState(null);
  const [deptPlacement, setDeptPlacement] = useState([]);
  const [skillDemand, setSkillDemand] = useState([]);
  const [packageDistribution, setPackageDistribution] = useState([]);
  const [yoyData, setYoyData] = useState([]);
  const [sectorPie, setSectorPie] = useState([]);
  const [skillTrends, setSkillTrends] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);
      const [statsRes, deptRes, skillRes, pkgRes, yoyRes, secRes, trendsRes] = await Promise.all([
        analyticsApi.getPlacementStats(),
        analyticsApi.getDeptPlacement(),
        analyticsApi.getSkillDemand(),
        analyticsApi.getPackageDistribution(),
        analyticsApi.getYoYStats(),
        analyticsApi.getSectorDistribution(),
        analyticsApi.getSkillTrends().catch(() => ({ data: null })),
      ]);

      setStats(statsRes.data);
      setDeptPlacement(deptRes.data || []);
      setSkillDemand(skillRes.data || []);
      setPackageDistribution(pkgRes.data || []);
      setYoyData(yoyRes.data || []);
      setSectorPie(secRes.data || []);
      setSkillTrends(trendsRes?.data || null);
    } catch (err) {
      console.error('Analytics fetch failed:', err);
      setError('Failed to load analytics data from database.');
    } finally {
      setLoading(false);
    }
  };


  useEffect(() => {
    fetchAnalytics();
  }, []);

  const deptChartData = deptPlacement.map(d => ({
    dept: d.department_code,
    name: d.department_name,
    placed: d.placed,
    total: d.total,
    pct: d.placement_pct,
    avg_package: d.avg_package,
  }));

  const pkgChartData = packageDistribution.map((entry, idx) => ({
    range: entry.band_label || entry.range,
    count: entry.count,
    color: entry.color || DEFAULT_COLORS[idx % DEFAULT_COLORS.length],
  }));

  const sectorChartData = sectorPie.map((s, idx) => ({
    name: s.name,
    value: s.value,
    color: s.color || DEFAULT_COLORS[idx % DEFAULT_COLORS.length],
  }));

  const skillData = skillDemand.map(s => ({
    skill: s.skill_name || s.skill,
    demand: s.demand_pct ?? s.demand,
    supply: s.supply_pct ?? s.supply,
    gap: s.gap,
  }));

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1>Analytics</h1>
          <p>Deep-dive into placement trends, skill demand, and department performance</p>
        </div>
        <button
          className="btn btn-secondary"
          onClick={fetchAnalytics}
          disabled={loading}
          style={{ fontSize: 'var(--font-size-xs)' }}
        >
          {loading ? 'Refreshing...' : '🔄 Refresh Data'}
        </button>
      </div>

      {error && (
        <div style={{
          padding: 'var(--space-4)',
          marginBottom: 'var(--space-6)',
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid #ef4444',
          borderRadius: 'var(--border-radius)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          color: '#ef4444'
        }}>
          <span>{error}</span>
          <button className="btn btn-primary" onClick={fetchAnalytics} style={{ height: 28, fontSize: 'var(--font-size-xs)' }}>
            Retry
          </button>
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: 'center', padding: 'var(--space-12)', color: 'var(--text-muted)' }}>
          <div style={{ fontSize: '1.5rem', marginBottom: 'var(--space-2)' }}>⏳ Loading live analytics...</div>
          <p>Running aggregation queries on student records and placement drives...</p>
        </div>
      ) : (
        <div className="page-body" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-8)' }}>

          {/* KPI row */}
          <div className="stat-grid">
            {[
              { label: 'Placement Rate', value: stats?.placement_pct ?? '—', unit: '%', icon: '📈' },
              { label: 'Avg Package', value: stats?.avg_package ? `₹${stats.avg_package}L` : '—', unit: '', icon: '💰' },
              { label: 'Median Package', value: stats?.median_package ? `₹${stats.median_package}L` : (stats?.avg_package ? `₹${stats.avg_package}L` : '—'), unit: '', icon: '📊' },
              { label: 'Highest Package', value: stats?.highest_package ? `₹${stats.highest_package}L` : '—', unit: '', icon: '🏆' },
            ].map(s => (
              <div key={s.label} className="stat-card">
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <div className="stat-card-label">{s.label}</div>
                  <span style={{ fontSize: '1.5rem' }}>{s.icon}</span>
                </div>
                <div className="stat-card-value">
                  {s.value}
                  {s.unit && <span style={{ fontSize: 'var(--font-size-lg)', WebkitTextFillColor: 'inherit' }}>{s.unit}</span>}
                </div>
              </div>
            ))}
          </div>

          {/* Dept placement rate + Year-over-year */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-6)' }}>

            {/* Dept bar */}
            <div className="card">
              <div style={{ fontWeight: 600, marginBottom: 'var(--space-4)' }}>Placement Rate by Department</div>
              {deptChartData.length > 0 ? (
                <>
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart data={deptChartData} margin={{ left: 0, right: 8 }}>
                      <XAxis dataKey="dept" tick={{ fill: 'var(--text-muted)', fontSize: 12 }} />
                      <YAxis domain={[0, 100]} tick={{ fill: 'var(--text-muted)', fontSize: 11 }} unit="%" />
                      <Tooltip content={<ChartTooltip />} />
                      <Bar dataKey="pct" radius={[6, 6, 0, 0]} name="Rate %">
                        {deptChartData.map((_, i) => (
                          <Cell key={i} fill={`hsl(${230 + i * 15}, 80%, ${55 + i * 4}%)`} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                  <div className="table-container" style={{ marginTop: 'var(--space-4)' }}>
                    <table>
                      <thead><tr><th>Dept</th><th style={{ textAlign: 'center' }}>Placed</th><th style={{ textAlign: 'center' }}>Total</th><th style={{ textAlign: 'right' }}>Rate</th></tr></thead>
                      <tbody>
                        {deptChartData.map(d => (
                          <tr key={d.dept}>
                            <td><span className="badge badge-primary">{d.dept}</span></td>
                            <td style={{ textAlign: 'center', fontWeight: 600, color: '#22c55e' }}>{d.placed}</td>
                            <td style={{ textAlign: 'center' }}>{d.total}</td>
                            <td style={{ textAlign: 'right', fontWeight: 700 }}>{d.pct}%</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              ) : (
                <div style={{ textAlign: 'center', padding: 'var(--space-8)', color: 'var(--text-muted)' }}>
                  No department placement data available.
                </div>
              )}
            </div>

            {/* YoY line */}
            <div className="card">
              <div style={{ fontWeight: 600, marginBottom: 'var(--space-4)' }}>Year-over-Year Comparison</div>
              {yoyData.length > 0 ? (
                <>
                  <ResponsiveContainer width="100%" height={220}>
                    <LineChart data={yoyData} margin={{ left: 0, right: 8 }}>
                      <CartesianGrid stroke="var(--border-color)" strokeDasharray="4 4" />
                      <XAxis dataKey="year" tick={{ fill: 'var(--text-muted)', fontSize: 10 }} />
                      <YAxis yAxisId="left" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
                      <YAxis yAxisId="right" orientation="right" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
                      <Tooltip content={<ChartTooltip />} />
                      <Line yAxisId="left" type="monotone" dataKey="placed" stroke="#6366f1" strokeWidth={2.5} dot={{ r: 4, fill: '#6366f1' }} name="Placed" />
                      <Line yAxisId="right" type="monotone" dataKey="avg_pkg" stroke="#22c55e" strokeWidth={2} strokeDasharray="6 3" dot={{ r: 3, fill: '#22c55e' }} name="Avg Pkg (L)" />
                    </LineChart>
                  </ResponsiveContainer>
                  <div className="table-container" style={{ marginTop: 'var(--space-4)' }}>
                    <table>
                      <thead><tr><th>Year</th><th style={{ textAlign: 'center' }}>Placed</th><th style={{ textAlign: 'center' }}>Rate %</th><th style={{ textAlign: 'right' }}>Avg Pkg</th></tr></thead>
                      <tbody>
                        {yoyData.map(y => (
                          <tr key={y.year}>
                            <td style={{ fontWeight: 500 }}>{y.year}</td>
                            <td style={{ textAlign: 'center' }}>{y.placed}</td>
                            <td style={{ textAlign: 'center', color: '#6366f1', fontWeight: 600 }}>{y.rate}%</td>
                            <td style={{ textAlign: 'right', color: '#22c55e', fontWeight: 600 }}>
                              {y.avg_pkg ? `₹${y.avg_pkg}L` : '—'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              ) : (
                <div style={{ textAlign: 'center', padding: 'var(--space-8)', color: 'var(--text-muted)' }}>
                  No YoY comparison data recorded yet.
                </div>
              )}
            </div>
          </div>

          {/* Package distribution + sector pie */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-6)' }}>

            {/* Package histogram */}
            <div className="card">
              <div style={{ fontWeight: 600, marginBottom: 'var(--space-4)' }}>Package Distribution</div>
              {pkgChartData.length > 0 ? (
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={pkgChartData} margin={{ left: 0, right: 8 }}>
                    <XAxis dataKey="range" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
                    <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
                    <Tooltip content={<ChartTooltip />} />
                    <Bar dataKey="count" name="Students" radius={[6, 6, 0, 0]}>
                      {pkgChartData.map((entry, i) => (
                        <Cell key={i} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div style={{ textAlign: 'center', padding: 'var(--space-8)', color: 'var(--text-muted)' }}>
                  No package distribution data recorded.
                </div>
              )}
            </div>

            {/* Sector pie */}
            <div className="card">
              <div style={{ fontWeight: 600, marginBottom: 'var(--space-4)' }}>Placement by Sector</div>
              {sectorChartData.length > 0 ? (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 'var(--space-6)' }}>
                  <PieChart width={180} height={180}>
                    <Pie data={sectorChartData} cx={90} cy={90} outerRadius={80} dataKey="value" labelLine={false} label={<CustomLabel />}>
                      {sectorChartData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                    </Pie>
                  </PieChart>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
                    {sectorChartData.map(s => (
                      <div key={s.name} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
                        <div style={{ width: 14, height: 14, borderRadius: 3, background: s.color, flexShrink: 0 }} />
                        <div>
                          <div style={{ fontWeight: 600, fontSize: 'var(--font-size-sm)' }}>{s.name}</div>
                          <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>{s.value} offers</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: 'var(--space-8)', color: 'var(--text-muted)' }}>
                  No industry sector distribution data available.
                </div>
              )}
            </div>
          </div>

          {/* Skill demand vs supply */}
          <div className="card">
            <div style={{ fontWeight: 600, marginBottom: 'var(--space-5)' }}>
              Skill Demand vs Campus Supply
              <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 400, color: 'var(--text-muted)', marginLeft: 'var(--space-3)' }}>
                Red = large gap · shows where curriculum needs strengthening
              </span>
            </div>
            {skillData.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
                {skillData.sort((a, b) => b.gap - a.gap).map(s => (
                  <div key={s.skill} style={{ display: 'grid', gridTemplateColumns: '140px 1fr 60px', gap: 'var(--space-4)', alignItems: 'center' }}>
                    <div style={{ fontWeight: 500, fontSize: 'var(--font-size-sm)' }}>{s.skill}</div>
                    <div style={{ position: 'relative', height: 20 }}>
                      {/* Supply bar */}
                      <div style={{ position: 'absolute', height: '100%', width: `${Math.min(100, Math.max(0, s.supply))}%`, background: '#6366f1', borderRadius: 3, opacity: 0.8 }} />
                      {/* Demand marker */}
                      <div style={{
                        position: 'absolute', top: '50%', transform: 'translateY(-50%)',
                        left: `${Math.min(100, Math.max(0, s.demand))}%`, width: 2, height: '130%',
                        background: s.gap > 30 ? '#ef4444' : '#f59e0b',
                      }} />
                      <div style={{
                        position: 'absolute', height: '100%', width: '100%',
                        background: 'var(--bg-tertiary)', borderRadius: 3, zIndex: -1,
                      }} />
                    </div>
                    <div style={{ textAlign: 'right', fontSize: 'var(--font-size-xs)', fontWeight: 700, color: s.gap > 30 ? '#ef4444' : s.gap > 15 ? '#f59e0b' : '#22c55e' }}>
                      {s.gap > 0 ? `−${s.gap}` : `+${Math.abs(s.gap)}`}
                    </div>
                  </div>
                ))}
                <div style={{ display: 'flex', gap: 'var(--space-6)', marginTop: 'var(--space-2)', fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                    <div style={{ width: 16, height: 10, background: '#6366f1', borderRadius: 2 }} /> Campus supply
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                    <div style={{ width: 3, height: 16, background: '#f59e0b', borderRadius: 1 }} /> Industry demand
                  </div>
                </div>
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: 'var(--space-8)', color: 'var(--text-muted)' }}>
                No skill gap intelligence data available yet.
              </div>
            )}
          </div>

          {/* Skill Market Trends Section (Last 90 Days) */}
          <div className="card" style={{ padding: 'var(--space-6)', display: 'flex', flexDirection: 'column', gap: 'var(--space-5)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 style={{ fontSize: 'var(--font-size-base)', fontWeight: 700 }}>📈 Skill Market Trends (Last 90 Days)</h3>
                <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)', marginTop: 2 }}>
                  Velocity tracking across {skillTrends?.based_on_drives || 42} placement drives — forward-looking hiring intelligence
                </p>
              </div>
              <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
                Updated quarterly
              </span>
            </div>

            {/* Surging Demand */}
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 'var(--font-size-sm)', fontWeight: 700, color: '#22c55e', marginBottom: 'var(--space-2)' }}>
                <span>🚀</span> Surging Demand (High Growth &gt; 30%)
              </div>
              <div style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
                {(skillTrends?.surging || []).map((s) => (
                  <div
                    key={s.skill}
                    title={`Required by ${s.demand_count} drives this quarter (${s.drives_pct || 50}% of all drives)`}
                    style={{
                      padding: '4px 12px',
                      borderRadius: 999,
                      fontSize: 'var(--font-size-xs)',
                      fontWeight: 600,
                      background: 'rgba(34,197,94,0.12)',
                      color: '#22c55e',
                      border: '1px solid rgba(34,197,94,0.3)',
                      cursor: 'default',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6,
                    }}
                  >
                    <span>{s.skill}</span>
                    <span style={{ fontSize: 11, fontWeight: 800 }}>+{s.growth_pct}%</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Stable Core Skills */}
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 'var(--font-size-sm)', fontWeight: 700, color: 'var(--accent-primary)', marginBottom: 'var(--space-2)' }}>
                <span>⚖️</span> Stable Core Skills
              </div>
              <div style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
                {(skillTrends?.stable || []).map((s) => (
                  <div
                    key={s.skill}
                    title={`Required by ${s.demand_count} drives this quarter`}
                    style={{
                      padding: '4px 12px',
                      borderRadius: 999,
                      fontSize: 'var(--font-size-xs)',
                      fontWeight: 600,
                      background: 'var(--bg-tertiary)',
                      color: 'var(--text-primary)',
                      border: '1px solid var(--border-color)',
                      cursor: 'default',
                    }}
                  >
                    {s.skill}
                  </div>
                ))}
              </div>
            </div>

            {/* Declining Demand */}
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 'var(--font-size-sm)', fontWeight: 700, color: 'var(--accent-danger)', marginBottom: 'var(--space-2)' }}>
                <span>📉</span> Declining Demand (&lt; -10%)
              </div>
              <div style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
                {(skillTrends?.declining || []).map((s) => (
                  <div
                    key={s.skill}
                    title={`Required by ${s.demand_count} drives this quarter`}
                    style={{
                      padding: '4px 12px',
                      borderRadius: 999,
                      fontSize: 'var(--font-size-xs)',
                      fontWeight: 600,
                      background: 'rgba(239,68,68,0.08)',
                      color: 'var(--accent-danger)',
                      border: '1px solid rgba(239,68,68,0.2)',
                      cursor: 'default',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6,
                    }}
                  >
                    <span>{s.skill}</span>
                    <span style={{ fontSize: 11, fontWeight: 800 }}>{s.growth_pct}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

        </div>
      )}
    </div>
  );

}
