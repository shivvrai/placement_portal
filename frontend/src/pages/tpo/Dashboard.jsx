/**
 * TPO Dashboard — KPI overview, placement trend chart, top recruiters, upcoming drives.
 */

import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid,
} from 'recharts';

// ─── Mock Data ────────────────────────────────────────────────────
const STATS = {
  total_students: 348,
  placed: 214,
  placement_pct: 61.5,
  avg_package: 8.4,
  median_package: 6.5,
  highest_package: 80,
  companies_visited: 42,
  offers_released: 248,
};

const TREND_DATA = [
  { month: 'Jan', placed: 12, offers: 15 },
  { month: 'Feb', placed: 18, offers: 22 },
  { month: 'Mar', placed: 28, offers: 34 },
  { month: 'Apr', placed: 42, offers: 50 },
  { month: 'May', placed: 55, offers: 63 },
  { month: 'Jun', placed: 70, offers: 82 },
  { month: 'Jul', placed: 88, offers: 96 },
  { month: 'Aug', placed: 105, offers: 118 },
];

const TOP_RECRUITERS = [
  { company: 'Google',    offers: 6,  avg_ctc: 48.5, sector: 'Product' },
  { company: 'Amazon',    offers: 12, avg_ctc: 25.0, sector: 'Product' },
  { company: 'Infosys',   offers: 38, avg_ctc: 3.6,  sector: 'Service' },
  { company: 'TCS',       offers: 32, avg_ctc: 7.0,  sector: 'Service' },
  { company: 'Deloitte',  offers: 14, avg_ctc: 7.5,  sector: 'Consulting' },
  { company: 'Freshworks',offers: 8,  avg_ctc: 10.0, sector: 'Product' },
  { company: 'Wipro',     offers: 26, avg_ctc: 3.5,  sector: 'Service' },
  { company: 'Accenture', offers: 18, avg_ctc: 4.5,  sector: 'Consulting' },
];

const DEPT_STATS = [
  { dept: 'CS', placed: 82, total: 110 },
  { dept: 'IT', placed: 65, total: 90 },
  { dept: 'ECE', placed: 38, total: 68 },
  { dept: 'ME', placed: 18, total: 48 },
  { dept: 'EEE', placed: 11, total: 32 },
];

const UPCOMING_DRIVES = [
  { id: 1, company: 'Google', role: 'SWE Intern', deadline: '2026-09-10', registered: 48, shortlisted: 0, status: 'open' },
  { id: 2, company: 'Amazon', role: 'Data Engineer', deadline: '2026-09-15', registered: 62, shortlisted: 18, status: 'in_progress' },
  { id: 3, company: 'Deloitte', role: 'Technology Analyst', deadline: '2026-10-05', registered: 31, shortlisted: 0, status: 'open' },
];

const SECTOR_COLORS = { Product: '#6366f1', Service: '#06b6d4', Consulting: '#f59e0b' };

function Tooltip2({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: 8, padding: 'var(--space-3) var(--space-4)' }}>
      <div style={{ fontWeight: 600, marginBottom: 4 }}>{label}</div>
      {payload.map(p => (
        <div key={p.name} style={{ color: p.color, fontSize: 'var(--font-size-sm)' }}>
          {p.name}: {p.value}
        </div>
      ))}
    </div>
  );
}

export default function TPODashboard() {
  return (
    <div>
      <div className="page-header">
        <h1>TPO Dashboard</h1>
        <p>Placement intelligence for Academic Year 2025–26</p>
      </div>

      <div className="page-body" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-8)' }}>

        {/* KPI cards */}
        <div className="stat-grid">
          {[
            { label: 'Total Students', value: STATS.total_students, unit: '', icon: '🎓' },
            { label: 'Placed', value: STATS.placed, unit: '', icon: '✅' },
            { label: 'Placement %', value: STATS.placement_pct, unit: '%', icon: '📈' },
            { label: 'Avg Package', value: `₹${STATS.avg_package}L`, unit: '', icon: '💰' },
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

        {/* Two-col: trend + dept breakdown */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-6)' }}>

          {/* Placement trend */}
          <div className="card">
            <div style={{ fontWeight: 600, marginBottom: 'var(--space-4)' }}>Placement Trend (2025–26)</div>
            <ResponsiveContainer width="100%" height={230}>
              <LineChart data={TREND_DATA} margin={{ left: 0, right: 8, top: 4, bottom: 4 }}>
                <CartesianGrid stroke="var(--border-color)" strokeDasharray="4 4" />
                <XAxis dataKey="month" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
                <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
                <Tooltip content={<Tooltip2 />} />
                <Line type="monotone" dataKey="placed" stroke="#6366f1" strokeWidth={2.5} dot={false} name="Placed" />
                <Line type="monotone" dataKey="offers" stroke="#06b6d4" strokeWidth={2} strokeDasharray="6 3" dot={false} name="Offers" />
              </LineChart>
            </ResponsiveContainer>
            <div style={{ display: 'flex', gap: 'var(--space-6)', marginTop: 'var(--space-2)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
                <div style={{ width: 16, height: 3, background: '#6366f1', borderRadius: 2 }} /> Placed
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
                <div style={{ width: 16, height: 3, background: '#06b6d4', borderRadius: 2 }} /> Offers
              </div>
            </div>
          </div>

          {/* Dept bar chart */}
          <div className="card">
            <div style={{ fontWeight: 600, marginBottom: 'var(--space-4)' }}>Placement by Department</div>
            <ResponsiveContainer width="100%" height={230}>
              <BarChart data={DEPT_STATS} margin={{ left: 0, right: 8, top: 4, bottom: 4 }}>
                <XAxis dataKey="dept" tick={{ fill: 'var(--text-muted)', fontSize: 12 }} />
                <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
                <Tooltip content={<Tooltip2 />} />
                <Bar dataKey="total" fill="rgba(99,102,241,0.2)" radius={[4, 4, 0, 0]} name="Total" />
                <Bar dataKey="placed" fill="#6366f1" radius={[4, 4, 0, 0]} name="Placed" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Two-col: top recruiters + upcoming drives */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-6)' }}>

          {/* Top recruiters */}
          <div className="card">
            <div style={{ fontWeight: 600, marginBottom: 'var(--space-4)' }}>Top Recruiters</div>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Company</th>
                    <th>Sector</th>
                    <th style={{ textAlign: 'right' }}>Offers</th>
                    <th style={{ textAlign: 'right' }}>Avg CTC</th>
                  </tr>
                </thead>
                <tbody>
                  {TOP_RECRUITERS.map(r => (
                    <tr key={r.company}>
                      <td style={{ fontWeight: 600 }}>{r.company}</td>
                      <td>
                        <span style={{
                          padding: '2px 8px', borderRadius: 999,
                          fontSize: 'var(--font-size-xs)', fontWeight: 500,
                          background: `${SECTOR_COLORS[r.sector]}18`,
                          color: SECTOR_COLORS[r.sector],
                        }}>
                          {r.sector}
                        </span>
                      </td>
                      <td style={{ textAlign: 'right', fontWeight: 600 }}>{r.offers}</td>
                      <td style={{ textAlign: 'right', color: 'var(--accent-success)', fontWeight: 600 }}>₹{r.avg_ctc}L</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Upcoming drives */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)' }}>
              <div style={{ fontWeight: 600 }}>Upcoming Drives</div>
              <button className="btn btn-primary" style={{ height: 32, fontSize: 'var(--font-size-xs)' }}>+ New Drive</button>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
              {UPCOMING_DRIVES.map(d => (
                <div key={d.id} style={{
                  padding: 'var(--space-4)',
                  background: 'var(--bg-tertiary)', borderRadius: 'var(--border-radius-sm)',
                  borderLeft: `3px solid ${d.status === 'in_progress' ? '#f59e0b' : 'var(--accent-primary)'}`,
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ fontWeight: 600 }}>{d.company}</div>
                    <span className={`badge ${d.status === 'in_progress' ? 'badge-warning' : 'badge-primary'}`}>
                      {d.status === 'in_progress' ? '◎ In Progress' : '● Open'}
                    </span>
                  </div>
                  <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginTop: 4 }}>
                    {d.role} · Deadline: {d.deadline}
                  </div>
                  <div style={{ display: 'flex', gap: 'var(--space-4)', marginTop: 'var(--space-2)', fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)' }}>
                    <span>👥 {d.registered} registered</span>
                    {d.shortlisted > 0 && <span>✓ {d.shortlisted} shortlisted</span>}
                  </div>
                </div>
              ))}
            </div>

            {/* Summary metrics */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 'var(--space-3)', marginTop: 'var(--space-5)', paddingTop: 'var(--space-5)', borderTop: '1px solid var(--border-color)' }}>
              {[
                { label: 'Highest Pkg', value: `₹${STATS.highest_package}L`, color: '#22c55e' },
                { label: 'Median Pkg', value: `₹${STATS.median_package}L`, color: '#6366f1' },
                { label: 'Companies', value: STATS.companies_visited, color: '#06b6d4' },
              ].map(m => (
                <div key={m.label} style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 'var(--font-size-xl)', fontWeight: 700, color: m.color }}>{m.value}</div>
                  <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>{m.label}</div>
                </div>
              ))}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
