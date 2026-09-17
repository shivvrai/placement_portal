/**
 * TPO Dashboard — KPI overview, placement trend chart, top recruiters, upcoming drives.
 * Connected to live database via analyticsApi and placementApi.
 */

import { useState, useEffect } from 'react';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid,
} from 'recharts';
import { analyticsApi, placementApi, systemApi } from '../../api/endpoints';

const SECTOR_COLORS = {
  Product: '#6366f1',
  Technology: '#6366f1',
  Service: '#06b6d4',
  'IT Services': '#06b6d4',
  Consulting: '#f59e0b',
  Finance: '#10b981',
  Fintech: '#10b981',
  Other: '#8b5cf6',
};

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
  const [stats, setStats] = useState(null);
  const [deptStats, setDeptStats] = useState([]);
  const [upcomingDrives, setUpcomingDrives] = useState([]);
  const [trendData, setTrendData] = useState([]);
  const [topRecruiters, setTopRecruiters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Audit drawer state
  const [auditOpen, setAuditOpen] = useState(false);
  const [auditLogs, setAuditLogs] = useState([]);
  const [auditLoading, setAuditLoading] = useState(false);
  const [auditFilter, setAuditFilter] = useState('');
  const [auditPage, setAuditPage] = useState(1);
  const [auditTotal, setAuditTotal] = useState(0);
  const [expandedLog, setExpandedLog] = useState(null);

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      setError(null);
      const [statsRes, deptRes, drivesRes, trendsRes, recsRes] = await Promise.all([
        analyticsApi.getPlacementStats(),
        analyticsApi.getDeptPlacement(),
        placementApi.getDrives({ status: 'upcoming' }),
        analyticsApi.getPlacementTrends(),
        analyticsApi.getTopRecruiters(),
      ]);

      setStats(statsRes.data);
      setDeptStats(deptRes.data || []);
      setUpcomingDrives(drivesRes.data?.data || drivesRes.data || []);
      setTrendData(trendsRes.data || []);
      setTopRecruiters(recsRes.data || []);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
      setError('Failed to load dashboard data from server.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  // ─── Audit helpers ───────────────────────────────────────────────
  const EVENT_COLORS = {
    DRIVE_CREATE: '#22c55e',
    DRIVE_UPDATE: '#f59e0b',
    DRIVE_CANCEL: '#ef4444',
    APPLICATION_STATUS_CHANGE: '#ef4444',
    OFFER_RECORDED: '#22c55e',
    UMS_SYNC_TRIGGERED: '#06b6d4',
    SKILL_VERIFIED: '#22c55e',
    STUDENT_PROFILE_UPDATE: '#f59e0b',
    SHORTLIST_GENERATED: '#6366f1',
    ACCREDITATION_REPORT_EXPORTED: '#8b5cf6',
  };

  function timeAgo(isoDate) {
    if (!isoDate) return '';
    const diff = (Date.now() - new Date(isoDate).getTime()) / 1000;
    if (diff < 60) return `${Math.floor(diff)}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)} min ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)} hours ago`;
    if (diff < 172800) return 'Yesterday';
    return new Date(isoDate).toLocaleDateString();
  }

  const fetchAuditLogs = async (page = 1, eventType = '') => {
    try {
      setAuditLoading(true);
      const params = { page, page_size: 20 };
      if (eventType) params.event_type = eventType;
      const res = await systemApi.getAuditLogs(params);
      const body = res.data;
      setAuditLogs(body.data || []);
      setAuditTotal(body.meta?.total || 0);
      setAuditPage(page);
    } catch (err) {
      console.error('Audit fetch failed:', err);
    } finally {
      setAuditLoading(false);
    }
  };

  const openAuditDrawer = () => {
    setAuditOpen(true);
    fetchAuditLogs(1, auditFilter);
  };

  const deptChartData = deptStats.map(d => ({
    dept: d.department_code,
    total: d.total,
    placed: d.placed,
    rate: d.placement_pct,
  }));

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1>TPO Dashboard</h1>
          <p>Placement intelligence for Academic Year {stats?.academic_year || '2025–26'}</p>
        </div>
        <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
          <button
            id="audit-trail-btn"
            className="btn btn-secondary"
            onClick={openAuditDrawer}
            style={{ fontSize: 'var(--font-size-xs)' }}
          >
            📋 Activity &amp; Audit Trail
          </button>
          <button
            className="btn btn-secondary"
            onClick={fetchDashboard}
            disabled={loading}
            style={{ fontSize: 'var(--font-size-xs)' }}
          >
            {loading ? 'Refreshing...' : '🔄 Refresh Data'}
          </button>
        </div>
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
          <button className="btn btn-primary" onClick={fetchDashboard} style={{ height: 28, fontSize: 'var(--font-size-xs)' }}>
            Retry
          </button>
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: 'center', padding: 'var(--space-12)', color: 'var(--text-muted)' }}>
          <div style={{ fontSize: '1.5rem', marginBottom: 'var(--space-2)' }}>⏳ Loading live dashboard metrics...</div>
          <p>Connecting to backend database...</p>
        </div>
      ) : (
        <div className="page-body" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-8)' }}>

          {/* KPI cards */}
          <div className="stat-grid">
            {[
              { label: 'Total Students', value: stats?.total_students ?? '—', unit: '', icon: '🎓' },
              { label: 'Placed', value: stats?.placed ?? '—', unit: '', icon: '✅' },
              { label: 'Placement %', value: stats?.placement_pct ?? '—', unit: '%', icon: '📈' },
              { label: 'Avg Package', value: stats?.avg_package ? `₹${stats.avg_package}L` : '—', unit: '', icon: '💰' },
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

          {/* Two-col: trend + dept breakdown */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-6)' }}>

            {/* Placement trend */}
            <div className="card">
              <div style={{ fontWeight: 600, marginBottom: 'var(--space-4)' }}>Placement Trend ({stats?.academic_year || '2025–26'})</div>
              {trendData.length > 0 ? (
                <>
                  <ResponsiveContainer width="100%" height={230}>
                    <LineChart data={trendData} margin={{ left: 0, right: 8, top: 4, bottom: 4 }}>
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
                </>
              ) : (
                <div style={{ textAlign: 'center', padding: 'var(--space-8)', color: 'var(--text-muted)' }}>
                  No placement trend data recorded yet.
                </div>
              )}
            </div>

            {/* Dept bar chart */}
            <div className="card">
              <div style={{ fontWeight: 600, marginBottom: 'var(--space-4)' }}>Placement by Department</div>
              {deptChartData.length > 0 ? (
                <ResponsiveContainer width="100%" height={230}>
                  <BarChart data={deptChartData} margin={{ left: 0, right: 8, top: 4, bottom: 4 }}>
                    <XAxis dataKey="dept" tick={{ fill: 'var(--text-muted)', fontSize: 12 }} />
                    <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
                    <Tooltip content={<Tooltip2 />} />
                    <Bar dataKey="total" fill="rgba(99,102,241,0.2)" radius={[4, 4, 0, 0]} name="Total" />
                    <Bar dataKey="placed" fill="#6366f1" radius={[4, 4, 0, 0]} name="Placed" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div style={{ textAlign: 'center', padding: 'var(--space-8)', color: 'var(--text-muted)' }}>
                  No department placement data available.
                </div>
              )}
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
                    {topRecruiters.length > 0 ? (
                      topRecruiters.map(r => {
                        const compName = r.company || r.company_name;
                        const sectorName = r.sector || 'Product';
                        const color = SECTOR_COLORS[sectorName] || '#6366f1';
                        return (
                          <tr key={compName}>
                            <td style={{ fontWeight: 600 }}>{compName}</td>
                            <td>
                              <span style={{
                                padding: '2px 8px', borderRadius: 999,
                                fontSize: 'var(--font-size-xs)', fontWeight: 500,
                                background: `${color}18`,
                                color: color,
                              }}>
                                {sectorName}
                              </span>
                            </td>
                            <td style={{ textAlign: 'right', fontWeight: 600 }}>{r.offers}</td>
                            <td style={{ textAlign: 'right', color: 'var(--accent-success)', fontWeight: 600 }}>
                              {r.avg_ctc ? `₹${r.avg_ctc}L` : '—'}
                            </td>
                          </tr>
                        );
                      })
                    ) : (
                      <tr>
                        <td colSpan={4} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 'var(--space-4)' }}>
                          No recruiter placements recorded yet.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Upcoming drives */}
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)' }}>
                <div style={{ fontWeight: 600 }}>Upcoming Drives</div>
                <span className="badge badge-primary">{upcomingDrives.length} drives</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                {upcomingDrives.length > 0 ? (
                  upcomingDrives.map(d => {
                    const compName = d.company?.name || d.company || 'Unknown Company';
                    const roleName = (d.roles_offered && d.roles_offered[0]) || d.title || d.role || 'Role';
                    const deadlineStr = d.registration_deadline
                      ? new Date(d.registration_deadline).toLocaleDateString()
                      : (d.drive_date ? new Date(d.drive_date).toLocaleDateString() : 'TBD');
                    const registeredCount = d.registered_count ?? d.registered ?? 0;
                    const shortlistedCount = d.shortlisted_count ?? d.shortlisted ?? 0;

                    return (
                      <div key={d.id} style={{
                        padding: 'var(--space-4)',
                        background: 'var(--bg-tertiary)', borderRadius: 'var(--border-radius-sm)',
                        borderLeft: `3px solid ${d.status === 'in_progress' ? '#f59e0b' : 'var(--accent-primary)'}`,
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <div style={{ fontWeight: 600 }}>{compName}</div>
                          <span className={`badge ${d.status === 'in_progress' ? 'badge-warning' : 'badge-primary'}`}>
                            {d.status === 'in_progress' ? '◎ In Progress' : '● Upcoming'}
                          </span>
                        </div>
                        <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginTop: 4 }}>
                          {roleName} · Date/Deadline: {deadlineStr}
                        </div>
                        <div style={{ display: 'flex', gap: 'var(--space-4)', marginTop: 'var(--space-2)', fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)' }}>
                          <span>👥 {registeredCount} registered</span>
                          {shortlistedCount > 0 && <span>✓ {shortlistedCount} shortlisted</span>}
                          {d.salary_ctc && <span>💰 ₹{d.salary_ctc}L</span>}
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <div style={{ textAlign: 'center', padding: 'var(--space-6)', color: 'var(--text-muted)' }}>
                    No upcoming recruitment drives found.
                  </div>
                )}
              </div>

              {/* Summary metrics */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 'var(--space-3)', marginTop: 'var(--space-5)', paddingTop: 'var(--space-5)', borderTop: '1px solid var(--border-color)' }}>
                {[
                  { label: 'Highest Pkg', value: stats?.highest_package ? `₹${stats.highest_package}L` : '—', color: '#22c55e' },
                  { label: 'Offers', value: stats?.offers_released ?? (stats?.placed ?? '—'), color: '#6366f1' },
                  { label: 'Companies', value: stats?.companies_visited ?? '—', color: '#06b6d4' },
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
      )}

      {/* ─── Audit Trail Drawer ──────────────────────────────────────────── */}
      {auditOpen && (
        <>
          {/* Dark overlay */}
          <div
            onClick={() => setAuditOpen(false)}
            style={{
              position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)',
              zIndex: 200, cursor: 'pointer',
            }}
          />

          {/* Drawer panel */}
          <div style={{
            position: 'fixed', top: 0, right: 0, bottom: 0, width: 500,
            background: 'var(--bg-secondary)', borderLeft: '1px solid var(--border-color)',
            zIndex: 201, display: 'flex', flexDirection: 'column',
            boxShadow: '-8px 0 32px rgba(0,0,0,0.4)',
            animation: 'slideInRight 0.25s ease',
          }}>
            {/* Drawer header */}
            <div style={{
              padding: 'var(--space-5) var(--space-5) var(--space-4)',
              borderBottom: '1px solid var(--border-color)',
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            }}>
              <div>
                <div style={{ fontWeight: 700, fontSize: 'var(--font-size-lg)' }}>📋 Activity &amp; Audit Trail</div>
                <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginTop: 2 }}>
                  {auditTotal} events recorded
                </div>
              </div>
              <button
                onClick={() => setAuditOpen(false)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '1.2rem', cursor: 'pointer' }}
              >✕</button>
            </div>

            {/* Filter bar */}
            <div style={{ padding: 'var(--space-3) var(--space-5)', borderBottom: '1px solid var(--border-color)' }}>
              <select
                id="audit-event-type-filter"
                value={auditFilter}
                onChange={e => {
                  setAuditFilter(e.target.value);
                  fetchAuditLogs(1, e.target.value);
                }}
                style={{
                  width: '100%', background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)',
                  color: 'var(--text-primary)', borderRadius: 'var(--border-radius-sm)',
                  padding: '7px 12px', fontSize: 'var(--font-size-sm)',
                }}
              >
                <option value="">All Event Types</option>
                {['DRIVE_CREATE','DRIVE_UPDATE','DRIVE_CANCEL','APPLICATION_STATUS_CHANGE','OFFER_RECORDED','UMS_SYNC_TRIGGERED','ACCREDITATION_REPORT_EXPORTED','SHORTLIST_GENERATED'].map(e => (
                  <option key={e} value={e}>{e.replace(/_/g, ' ')}</option>
                ))}
              </select>
            </div>

            {/* Log list */}
            <div style={{ flex: 1, overflowY: 'auto', padding: 'var(--space-3) var(--space-5)' }}>
              {auditLoading ? (
                <div style={{ textAlign: 'center', padding: 'var(--space-8)', color: 'var(--text-muted)' }}>
                  ⏳ Loading audit logs...
                </div>
              ) : auditLogs.length === 0 ? (
                <div style={{ textAlign: 'center', padding: 'var(--space-8)', color: 'var(--text-muted)' }}>
                  No audit events recorded yet. Events are logged when TPOs create drives, sync students, or export reports.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
                  {auditLogs.map(log => {
                    const color = EVENT_COLORS[log.event_type] || '#6366f1';
                    const isExpanded = expandedLog === log.id;
                    return (
                      <div key={log.id} style={{
                        padding: 'var(--space-3) var(--space-4)',
                        background: 'var(--bg-tertiary)',
                        borderRadius: 8,
                        borderLeft: `4px solid ${color}`,
                        cursor: 'pointer',
                      }} onClick={() => setExpandedLog(isExpanded ? null : log.id)}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                          <span style={{
                            fontSize: 'var(--font-size-xs)', fontWeight: 700,
                            background: `${color}22`, color: color,
                            padding: '2px 8px', borderRadius: 999,
                          }}>
                            {log.event_type}
                          </span>
                          <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
                            {timeAgo(log.created_at)}
                          </span>
                        </div>
                        <div style={{ fontSize: 'var(--font-size-sm)', marginTop: 4 }}>
                          {log.resource_type} <span style={{ color: 'var(--text-muted)' }}>#{log.resource_id?.slice(0, 8)}</span>
                        </div>
                        {log.ip_address && (
                          <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginTop: 2 }}>
                            IP: {log.ip_address}
                          </div>
                        )}
                        {isExpanded && (
                          <pre style={{
                            marginTop: 'var(--space-2)', fontSize: 11, lineHeight: 1.5,
                            background: 'var(--bg-primary)', borderRadius: 4,
                            padding: 'var(--space-2)', color: 'var(--text-secondary)',
                            overflowX: 'auto', whiteSpace: 'pre-wrap', wordBreak: 'break-all',
                          }}>
                            {JSON.stringify(log.details, null, 2)}
                          </pre>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Load more */}
              {!auditLoading && auditLogs.length > 0 && auditTotal > auditPage * 20 && (
                <div style={{ textAlign: 'center', marginTop: 'var(--space-4)' }}>
                  <button
                    className="btn btn-secondary"
                    onClick={() => fetchAuditLogs(auditPage + 1, auditFilter)}
                    style={{ fontSize: 'var(--font-size-xs)' }}
                  >
                    Load More ({auditTotal - auditPage * 20} remaining)
                  </button>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
