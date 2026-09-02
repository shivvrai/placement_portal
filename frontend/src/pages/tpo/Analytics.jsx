/**
 * TPO Analytics — placement analytics: dept rates, package distribution,
 * skill demand heatmap, year-over-year comparison.
 */

import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, CartesianGrid, PieChart, Pie, Cell, Legend,
} from 'recharts';

// ─── Mock Data ────────────────────────────────────────────────────
const DEPT_PLACEMENT = [
  { dept: 'CS',  placed: 82, total: 110, pct: 74.5 },
  { dept: 'IT',  placed: 65, total: 90,  pct: 72.2 },
  { dept: 'ECE', placed: 38, total: 68,  pct: 55.9 },
  { dept: 'ME',  placed: 18, total: 48,  pct: 37.5 },
  { dept: 'EEE', placed: 11, total: 32,  pct: 34.4 },
];

const YOY_DATA = [
  { year: '2021–22', placed: 148, rate: 52.3, avg_pkg: 5.8 },
  { year: '2022–23', placed: 175, rate: 57.9, avg_pkg: 6.4 },
  { year: '2023–24', placed: 198, rate: 60.2, avg_pkg: 7.1 },
  { year: '2024–25', placed: 214, rate: 61.5, avg_pkg: 8.4 },
];

const PACKAGE_DISTRIBUTION = [
  { range: '< 4L',   count: 38, color: '#94a3b8' },
  { range: '4–7L',   count: 72, color: '#6366f1' },
  { range: '7–12L',  count: 54, color: '#8b5cf6' },
  { range: '12–20L', count: 32, color: '#06b6d4' },
  { range: '20–40L', count: 12, color: '#22c55e' },
  { range: '> 40L',  count: 6,  color: '#f59e0b' },
];

const SECTOR_PIE = [
  { name: 'Product',    value: 62,  color: '#6366f1' },
  { name: 'Service',    value: 112, color: '#06b6d4' },
  { name: 'Consulting', value: 40,  color: '#f59e0b' },
];

const SKILL_DEMAND = [
  { skill: 'Python',      demand: 92, supply: 75, gap: 17 },
  { skill: 'SQL',         demand: 88, supply: 70, gap: 18 },
  { skill: 'React',       demand: 78, supply: 55, gap: 23 },
  { skill: 'Docker',      demand: 75, supply: 28, gap: 47 },
  { skill: 'Statistics',  demand: 82, supply: 48, gap: 34 },
  { skill: 'ML / AI',     demand: 85, supply: 52, gap: 33 },
  { skill: 'TypeScript',  demand: 72, supply: 30, gap: 42 },
  { skill: 'System Design', demand: 80, supply: 42, gap: 38 },
];

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

function CustomLabel({ cx, cy, midAngle, innerRadius, outerRadius, name, value }) {
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
  return (
    <div>
      <div className="page-header">
        <h1>Analytics</h1>
        <p>Deep-dive into placement trends, skill demand, and department performance</p>
      </div>

      <div className="page-body" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-8)' }}>

        {/* KPI row */}
        <div className="stat-grid">
          {[
            { label: 'Placement Rate', value: '61.5', unit: '%', icon: '📈' },
            { label: 'Avg Package', value: '₹8.4L', unit: '', icon: '💰' },
            { label: 'Median Package', value: '₹6.5L', unit: '', icon: '📊' },
            { label: 'Highest Package', value: '₹80L', unit: '', icon: '🏆' },
          ].map(s => (
            <div key={s.label} className="stat-card">
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div className="stat-card-label">{s.label}</div>
                <span style={{ fontSize: '1.5rem' }}>{s.icon}</span>
              </div>
              <div className="stat-card-value">{s.value}<span style={{ fontSize: 'var(--font-size-lg)', WebkitTextFillColor: 'inherit' }}>{s.unit}</span></div>
            </div>
          ))}
        </div>

        {/* Dept placement rate + Year-over-year */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-6)' }}>

          {/* Dept bar */}
          <div className="card">
            <div style={{ fontWeight: 600, marginBottom: 'var(--space-4)' }}>Placement Rate by Department</div>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={DEPT_PLACEMENT} margin={{ left: 0, right: 8 }}>
                <XAxis dataKey="dept" tick={{ fill: 'var(--text-muted)', fontSize: 12 }} />
                <YAxis domain={[0, 100]} tick={{ fill: 'var(--text-muted)', fontSize: 11 }} unit="%" />
                <Tooltip content={<ChartTooltip />} />
                <Bar dataKey="pct" radius={[6, 6, 0, 0]} name="Rate %" fill="url(#barGrad)">
                  {DEPT_PLACEMENT.map((_, i) => (
                    <Cell key={i} fill={`hsl(${230 + i * 15}, 80%, ${55 + i * 4}%)`} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <div className="table-container" style={{ marginTop: 'var(--space-4)' }}>
              <table>
                <thead><tr><th>Dept</th><th style={{ textAlign: 'center' }}>Placed</th><th style={{ textAlign: 'center' }}>Total</th><th style={{ textAlign: 'right' }}>Rate</th></tr></thead>
                <tbody>
                  {DEPT_PLACEMENT.map(d => (
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
          </div>

          {/* YoY line */}
          <div className="card">
            <div style={{ fontWeight: 600, marginBottom: 'var(--space-4)' }}>Year-over-Year Comparison</div>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={YOY_DATA} margin={{ left: 0, right: 8 }}>
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
                  {YOY_DATA.map(y => (
                    <tr key={y.year}>
                      <td style={{ fontWeight: 500 }}>{y.year}</td>
                      <td style={{ textAlign: 'center' }}>{y.placed}</td>
                      <td style={{ textAlign: 'center', color: '#6366f1', fontWeight: 600 }}>{y.rate}%</td>
                      <td style={{ textAlign: 'right', color: '#22c55e', fontWeight: 600 }}>₹{y.avg_pkg}L</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Package distribution + sector pie */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-6)' }}>

          {/* Package histogram */}
          <div className="card">
            <div style={{ fontWeight: 600, marginBottom: 'var(--space-4)' }}>Package Distribution</div>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={PACKAGE_DISTRIBUTION} margin={{ left: 0, right: 8 }}>
                <XAxis dataKey="range" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
                <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
                <Tooltip content={<ChartTooltip />} />
                <Bar dataKey="count" name="Students" radius={[6, 6, 0, 0]}>
                  {PACKAGE_DISTRIBUTION.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Sector pie */}
          <div className="card">
            <div style={{ fontWeight: 600, marginBottom: 'var(--space-4)' }}>Placement by Sector</div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 'var(--space-6)' }}>
              <PieChart width={180} height={180}>
                <Pie data={SECTOR_PIE} cx={90} cy={90} outerRadius={80} dataKey="value" labelLine={false} label={<CustomLabel />}>
                  {SECTOR_PIE.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                </Pie>
              </PieChart>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
                {SECTOR_PIE.map(s => (
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
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
            {SKILL_DEMAND.sort((a, b) => b.gap - a.gap).map(s => (
              <div key={s.skill} style={{ display: 'grid', gridTemplateColumns: '140px 1fr 60px', gap: 'var(--space-4)', alignItems: 'center' }}>
                <div style={{ fontWeight: 500, fontSize: 'var(--font-size-sm)' }}>{s.skill}</div>
                <div style={{ position: 'relative', height: 20 }}>
                  {/* Supply bar */}
                  <div style={{ position: 'absolute', height: '100%', width: `${s.supply}%`, background: '#6366f1', borderRadius: 3, opacity: 0.8 }} />
                  {/* Demand marker */}
                  <div style={{
                    position: 'absolute', top: '50%', transform: 'translateY(-50%)',
                    left: `${s.demand}%`, width: 2, height: '130%',
                    background: s.gap > 30 ? '#ef4444' : '#f59e0b',
                  }} />
                  <div style={{
                    position: 'absolute', height: '100%', width: '100%',
                    background: 'var(--bg-tertiary)', borderRadius: 3, zIndex: -1,
                  }} />
                </div>
                <div style={{ textAlign: 'right', fontSize: 'var(--font-size-xs)', fontWeight: 700, color: s.gap > 30 ? '#ef4444' : s.gap > 15 ? '#f59e0b' : '#22c55e' }}>
                  −{s.gap}
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
        </div>

      </div>
    </div>
  );
}
