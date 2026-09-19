/**
 * BI Studio — Unified Apache Superset + Power BI integration hub.
 *
 * Three tabs:
 *   1. Superset Dashboards — embedded via guest token iframe
 *   2. Power BI Connector — OData feed URLs + connection guide
 *   3. Data Export — CSV downloads for offline BI analysis
 */

import { useState, useEffect, useCallback } from 'react';
import { biApi } from '../../api/endpoints';

/* ─── Palette & Constants ─────────────────────────────────────────────────── */

const TABS = [
  { key: 'superset', label: 'Superset Dashboards', icon: '🔮' },
  { key: 'powerbi', label: 'Power BI Connector', icon: '📊' },
  { key: 'export', label: 'Data Export', icon: '📥' },
];

const ENTITY_META = {
  students:    { label: 'Students',        icon: '🎓', desc: 'Student records with department, CGPA, semester' },
  placements:  { label: 'Placements',      icon: '✅', desc: 'Placement outcomes — company, role, CTC, year' },
  drives:      { label: 'Placement Drives', icon: '🏢', desc: 'Drive records — company, dates, salary, status' },
  skills:      { label: 'Skills Taxonomy',  icon: '🧠', desc: 'Skills master list with categories and domains' },
  departments: { label: 'Departments',      icon: '🏛️', desc: 'Department master data' },
};

const POWERBI_STEPS = [
  { step: 1, title: 'Open Power BI Desktop', desc: 'Launch Power BI Desktop (free download from Microsoft)' },
  { step: 2, title: 'Get Data → OData Feed', desc: 'Click "Get Data" → search for "OData Feed" → click Connect' },
  { step: 3, title: 'Paste the OData URL', desc: 'Copy any entity URL below and paste it in the URL field' },
  { step: 4, title: 'Authenticate', desc: 'Select "Organizational account" and enter your portal credentials' },
  { step: 5, title: 'Select Tables & Load', desc: 'Pick the tables you need → Transform & Load → build your dashboards!' },
];

/* ─── Component ───────────────────────────────────────────────────────────── */

export default function BIStudio() {
  const [activeTab, setActiveTab] = useState('superset');
  const [biConfig, setBiConfig] = useState(null);
  const [dashboards, setDashboards] = useState([]);
  const [counts, setCounts] = useState(null);
  const [embedToken, setEmbedToken] = useState(null);
  const [selectedDashboard, setSelectedDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState({});
  const [copiedUrl, setCopiedUrl] = useState(null);

  /* ─── Initial Fetch ─────────────────────────────────────────────────────── */

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const [configRes, countRes] = await Promise.all([
          biApi.getConfig().catch(() => ({ data: null })),
          biApi.getCounts().catch(() => ({ data: null })),
        ]);
        setBiConfig(configRes.data);
        setCounts(countRes.data);

        // Try to load dashboards
        try {
          const dashRes = await biApi.getDashboards();
          setDashboards(dashRes.data?.dashboards || []);
        } catch {
          setDashboards([]);
        }
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  /* ─── Superset Embed ────────────────────────────────────────────────────── */

  const handleEmbedDashboard = useCallback(async (dashboardId) => {
    setSelectedDashboard(dashboardId);
    try {
      const res = await biApi.getEmbedToken(dashboardId);
      setEmbedToken(res.data);
    } catch {
      setEmbedToken(null);
    }
  }, []);

  /* ─── Copy URL ──────────────────────────────────────────────────────────── */

  const copyToClipboard = useCallback((text, key) => {
    navigator.clipboard.writeText(text);
    setCopiedUrl(key);
    setTimeout(() => setCopiedUrl(null), 2000);
  }, []);

  /* ─── Export CSV ────────────────────────────────────────────────────────── */

  const handleExport = useCallback(async (entity) => {
    try {
      setExporting(prev => ({ ...prev, [entity]: true }));
      const res = await biApi.exportData(entity);
      const blob = new Blob([res.data], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `ccip_${entity}_${new Date().toISOString().split('T')[0]}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      alert(`Failed to export ${entity}`);
    } finally {
      setExporting(prev => ({ ...prev, [entity]: false }));
    }
  }, []);

  /* ─── Helpers ───────────────────────────────────────────────────────────── */

  const getODataUrl = (entity) => {
    const base = window.location.origin;
    return `${base}/api/v1/bi/odata/${entity}`;
  };

  const supersetUrl = biConfig?.superset?.url || 'http://localhost:8088';
  const supersetOnline = biConfig?.superset?.online || false;

  /* ─── Render ────────────────────────────────────────────────────────────── */

  return (
    <div>
      {/* ─── Page Header ──────────────────────────────────────────────────── */}
      <div className="page-header">
        <div>
          <h1>BI Studio</h1>
          <p>Apache Superset dashboards · Power BI data connector · bulk data export</p>
        </div>
      </div>

      {/* ─── Tab Bar ──────────────────────────────────────────────────────── */}
      <div style={{
        display: 'flex', gap: 'var(--space-2)', marginBottom: 'var(--space-6)',
        background: 'var(--bg-secondary)', borderRadius: 'var(--border-radius)',
        padding: 'var(--space-1)', border: '1px solid var(--border-color)',
      }}>
        {TABS.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            style={{
              flex: 1, padding: 'var(--space-3) var(--space-4)',
              borderRadius: 'calc(var(--border-radius) - 2px)',
              border: 'none', cursor: 'pointer', fontWeight: 600,
              fontSize: 'var(--font-size-sm)',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 'var(--space-2)',
              background: activeTab === tab.key ? 'var(--bg-card)' : 'transparent',
              color: activeTab === tab.key ? 'var(--text-primary)' : 'var(--text-muted)',
              boxShadow: activeTab === tab.key ? '0 1px 3px rgba(0,0,0,0.15)' : 'none',
              transition: 'all 0.2s ease',
            }}
          >
            <span style={{ fontSize: '1.1rem' }}>{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 'var(--space-12)', color: 'var(--text-muted)' }}>
          <div style={{ fontSize: '1.5rem', marginBottom: 'var(--space-2)' }}>⏳ Loading BI Studio...</div>
          <p>Connecting to Superset and checking data sources...</p>
        </div>
      ) : (
        <div className="page-body" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>

          {/* ═══════════════════════════════════════════════════════════════ */}
          {/*  TAB 1: SUPERSET DASHBOARDS                                   */}
          {/* ═══════════════════════════════════════════════════════════════ */}
          {activeTab === 'superset' && (
            <>
              {/* Status banner */}
              <div style={{
                display: 'flex', alignItems: 'center', gap: 'var(--space-3)',
                padding: 'var(--space-3) var(--space-4)',
                borderRadius: 'var(--border-radius)',
                background: supersetOnline ? 'rgba(34,197,94,0.08)' : 'rgba(239,68,68,0.08)',
                border: `1px solid ${supersetOnline ? 'rgba(34,197,94,0.3)' : 'rgba(239,68,68,0.3)'}`,
              }}>
                <span style={{
                  width: 10, height: 10, borderRadius: '50%',
                  background: supersetOnline ? '#22c55e' : '#ef4444',
                  display: 'inline-block',
                }} />
                <span style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: supersetOnline ? '#22c55e' : '#ef4444' }}>
                  {supersetOnline ? 'Superset is running' : 'Superset is offline'}
                </span>
                <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
                  {supersetOnline
                    ? `at ${supersetUrl}`
                    : 'Start with: docker compose up superset'}
                </span>
                {supersetOnline && (
                  <a
                    href={biConfig?.superset?.sql_lab_url || `${supersetUrl}/sqllab/`}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      marginLeft: 'auto', fontSize: 'var(--font-size-xs)',
                      color: 'var(--accent-primary)', textDecoration: 'none', fontWeight: 600,
                    }}
                  >
                    Open SQL Lab →
                  </a>
                )}
              </div>

              {/* Dashboard selector + embed */}
              {dashboards.length > 0 ? (
                <div className="card">
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)', marginBottom: 'var(--space-4)' }}>
                    <div style={{ fontWeight: 700, fontSize: 'var(--font-size-base)' }}>📊 Embedded Dashboard</div>
                    <select
                      value={selectedDashboard || ''}
                      onChange={e => handleEmbedDashboard(e.target.value)}
                      style={{
                        background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)',
                        color: 'var(--text-primary)', borderRadius: 'var(--border-radius-sm)',
                        padding: '6px 12px', fontSize: 'var(--font-size-sm)', cursor: 'pointer',
                      }}
                    >
                      <option value="">Select a dashboard...</option>
                      {dashboards.map(d => (
                        <option key={d.id} value={d.id}>{d.title}</option>
                      ))}
                    </select>
                  </div>

                  {selectedDashboard && embedToken?.guest_token ? (
                    <iframe
                      src={`${supersetUrl}/superset/dashboard/${selectedDashboard}/?standalone=1&guest_token=${embedToken.guest_token}`}
                      title="Superset Dashboard"
                      style={{
                        width: '100%', height: 600, border: '1px solid var(--border-color)',
                        borderRadius: 'var(--border-radius)', background: '#fff',
                      }}
                    />
                  ) : selectedDashboard ? (
                    <div style={{ textAlign: 'center', padding: 'var(--space-8)', color: 'var(--text-muted)' }}>
                      Loading dashboard embed...
                    </div>
                  ) : (
                    <div style={{
                      textAlign: 'center', padding: 'var(--space-10)',
                      color: 'var(--text-muted)', borderRadius: 'var(--border-radius)',
                      background: 'var(--bg-tertiary)', border: '1px dashed var(--border-color)',
                    }}>
                      <div style={{ fontSize: '2rem', marginBottom: 'var(--space-3)' }}>📊</div>
                      <div style={{ fontWeight: 600, marginBottom: 'var(--space-2)' }}>Select a dashboard to embed</div>
                      <div style={{ fontSize: 'var(--font-size-xs)' }}>Choose from the dropdown above to view a Superset dashboard inline</div>
                    </div>
                  )}
                </div>
              ) : (
                /* Setup guide when no dashboards exist */
                <div className="card" style={{ borderTop: '3px solid #6366f1' }}>
                  <div style={{ fontWeight: 700, fontSize: 'var(--font-size-lg)', marginBottom: 'var(--space-4)' }}>
                    🚀 Get Started with Superset
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 'var(--space-4)' }}>
                    {[
                      { step: 1, title: 'Start Superset', desc: 'Run docker compose up superset to start the BI server on port 8088', icon: '🐳' },
                      { step: 2, title: 'Create Dashboards', desc: `Login at ${supersetUrl} (admin/admin) → Build charts from CCIP data → Save as dashboard`, icon: '📈' },
                      { step: 3, title: 'Embed Here', desc: 'Dashboards auto-appear in the dropdown above for inline embedding', icon: '🖥️' },
                    ].map(s => (
                      <div key={s.step} style={{
                        padding: 'var(--space-5)', borderRadius: 'var(--border-radius)',
                        background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)',
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-3)' }}>
                          <span style={{
                            width: 28, height: 28, borderRadius: '50%', background: '#6366f1',
                            color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center',
                            fontSize: 'var(--font-size-xs)', fontWeight: 700,
                          }}>{s.step}</span>
                          <span style={{ fontWeight: 700, fontSize: 'var(--font-size-sm)' }}>{s.title}</span>
                        </div>
                        <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                          {s.desc}
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* SQL Views info */}
                  <div style={{
                    marginTop: 'var(--space-5)', padding: 'var(--space-4)',
                    borderRadius: 'var(--border-radius)', background: 'rgba(99,102,241,0.06)',
                    border: '1px solid rgba(99,102,241,0.15)',
                  }}>
                    <div style={{ fontWeight: 600, fontSize: 'var(--font-size-sm)', marginBottom: 'var(--space-2)' }}>
                      📋 Pre-built Analytics Views (available in SQL Lab)
                    </div>
                    <div style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
                      {['v_placement_summary', 'v_dept_performance', 'v_skill_demand_matrix', 'v_student_risk_score'].map(v => (
                        <code key={v} style={{
                          padding: '3px 10px', borderRadius: 4, fontSize: 'var(--font-size-xs)',
                          background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)',
                          fontFamily: 'monospace', color: 'var(--accent-primary)',
                        }}>{v}</code>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </>
          )}

          {/* ═══════════════════════════════════════════════════════════════ */}
          {/*  TAB 2: POWER BI CONNECTOR                                    */}
          {/* ═══════════════════════════════════════════════════════════════ */}
          {activeTab === 'powerbi' && (
            <>
              {/* Power BI Embed (if configured) */}
              {biConfig?.powerbi?.configured && (
                <div className="card" style={{ borderTop: '3px solid #f59e0b' }}>
                  <div style={{ fontWeight: 700, marginBottom: 'var(--space-4)' }}>📊 Embedded Power BI Report</div>
                  <iframe
                    src={biConfig.powerbi.embed_url}
                    title="Power BI Report"
                    style={{
                      width: '100%', height: 500, border: '1px solid var(--border-color)',
                      borderRadius: 'var(--border-radius)', background: '#fff',
                    }}
                    allowFullScreen
                  />
                </div>
              )}

              {/* Connection Guide */}
              <div className="card" style={{ borderTop: '3px solid #06b6d4' }}>
                <div style={{ fontWeight: 700, fontSize: 'var(--font-size-lg)', marginBottom: 'var(--space-2)' }}>
                  🔗 Connect Power BI Desktop via OData Feed
                </div>
                <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginBottom: 'var(--space-5)' }}>
                  Also works with Tableau, Excel, Google Sheets, and any BI tool that supports OData v4
                </div>

                {/* Step-by-step guide */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)', marginBottom: 'var(--space-6)' }}>
                  {POWERBI_STEPS.map(s => (
                    <div key={s.step} style={{
                      display: 'flex', alignItems: 'flex-start', gap: 'var(--space-3)',
                      padding: 'var(--space-3) var(--space-4)',
                      borderRadius: 'var(--border-radius)',
                      background: 'var(--bg-tertiary)',
                    }}>
                      <span style={{
                        width: 26, height: 26, borderRadius: '50%', background: '#06b6d4',
                        color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: 'var(--font-size-xs)', fontWeight: 700, flexShrink: 0,
                      }}>{s.step}</span>
                      <div>
                        <div style={{ fontWeight: 600, fontSize: 'var(--font-size-sm)' }}>{s.title}</div>
                        <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)' }}>{s.desc}</div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* OData URLs */}
                <div style={{ fontWeight: 700, fontSize: 'var(--font-size-sm)', marginBottom: 'var(--space-3)' }}>
                  📡 OData Feed URLs
                </div>

                {/* Metadata URL */}
                <div style={{
                  display: 'flex', alignItems: 'center', gap: 'var(--space-3)',
                  padding: 'var(--space-3) var(--space-4)', marginBottom: 'var(--space-3)',
                  borderRadius: 'var(--border-radius)',
                  background: 'rgba(99,102,241,0.06)', border: '1px solid rgba(99,102,241,0.15)',
                }}>
                  <span style={{ fontWeight: 700, fontSize: 'var(--font-size-xs)', color: '#6366f1' }}>$metadata</span>
                  <code style={{
                    flex: 1, fontSize: 'var(--font-size-xs)', fontFamily: 'monospace',
                    color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis',
                  }}>{getODataUrl('$metadata')}</code>
                  <button
                    className="btn btn-secondary"
                    onClick={() => copyToClipboard(getODataUrl('$metadata'), 'metadata')}
                    style={{ height: 28, fontSize: 'var(--font-size-xs)', whiteSpace: 'nowrap' }}
                  >
                    {copiedUrl === 'metadata' ? '✓ Copied!' : '📋 Copy'}
                  </button>
                </div>

                {/* Entity URLs */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
                  {(biConfig?.odata?.entities || ['Students', 'Placements', 'Drives', 'Departments', 'Skills', 'StudentSkills']).map(entity => (
                    <div key={entity} style={{
                      display: 'flex', alignItems: 'center', gap: 'var(--space-3)',
                      padding: 'var(--space-2) var(--space-4)',
                      borderRadius: 'var(--border-radius-sm)',
                      background: 'var(--bg-tertiary)',
                    }}>
                      <span style={{ fontWeight: 600, fontSize: 'var(--font-size-xs)', minWidth: 110 }}>{entity}</span>
                      <code style={{
                        flex: 1, fontSize: 'var(--font-size-xs)', fontFamily: 'monospace',
                        color: 'var(--text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis',
                      }}>{getODataUrl(entity)}</code>
                      <button
                        className="btn btn-secondary"
                        onClick={() => copyToClipboard(getODataUrl(entity), entity)}
                        style={{ height: 26, fontSize: 11, whiteSpace: 'nowrap', padding: '0 10px' }}
                      >
                        {copiedUrl === entity ? '✓' : '📋'}
                      </button>
                    </div>
                  ))}
                </div>

                {/* Supported tools */}
                <div style={{
                  marginTop: 'var(--space-5)', padding: 'var(--space-3) var(--space-4)',
                  borderRadius: 'var(--border-radius)', background: 'var(--bg-tertiary)',
                  display: 'flex', alignItems: 'center', gap: 'var(--space-4)',
                  fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)',
                }}>
                  <span style={{ fontWeight: 600 }}>Compatible with:</span>
                  {['Power BI Desktop', 'Tableau', 'Excel', 'Google Sheets', 'Apache Superset'].map(tool => (
                    <span key={tool} style={{
                      padding: '2px 10px', borderRadius: 999,
                      background: 'var(--bg-card)', border: '1px solid var(--border-color)',
                      fontWeight: 500,
                    }}>{tool}</span>
                  ))}
                </div>
              </div>
            </>
          )}

          {/* ═══════════════════════════════════════════════════════════════ */}
          {/*  TAB 3: DATA EXPORT                                           */}
          {/* ═══════════════════════════════════════════════════════════════ */}
          {activeTab === 'export' && (
            <>
              <div style={{
                padding: 'var(--space-3) var(--space-4)',
                borderRadius: 'var(--border-radius)',
                background: 'rgba(99,102,241,0.06)', border: '1px solid rgba(99,102,241,0.15)',
                fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)',
                display: 'flex', alignItems: 'center', gap: 'var(--space-3)',
              }}>
                <span style={{ fontSize: '1.1rem' }}>💡</span>
                Download CSV files to import into Power BI Desktop, Superset, or any spreadsheet tool for custom analysis
              </div>

              {/* Entity cards */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 'var(--space-4)' }}>
                {Object.entries(ENTITY_META).map(([key, meta]) => (
                  <div key={key} className="card" style={{
                    display: 'flex', flexDirection: 'column', gap: 'var(--space-3)',
                    transition: 'transform 0.15s ease, box-shadow 0.15s ease',
                    cursor: 'default',
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-1)' }}>
                          <span style={{ fontSize: '1.3rem' }}>{meta.icon}</span>
                          <span style={{ fontWeight: 700, fontSize: 'var(--font-size-base)' }}>{meta.label}</span>
                        </div>
                        <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>{meta.desc}</div>
                      </div>
                      <div style={{
                        padding: '4px 10px', borderRadius: 'var(--border-radius-sm)',
                        background: 'rgba(99,102,241,0.08)', color: '#6366f1',
                        fontSize: 'var(--font-size-xs)', fontWeight: 700,
                      }}>
                        {counts?.[key] ?? '—'} records
                      </div>
                    </div>

                    <button
                      className="btn btn-primary"
                      onClick={() => handleExport(key)}
                      disabled={exporting[key]}
                      style={{ width: '100%', fontSize: 'var(--font-size-sm)', marginTop: 'auto' }}
                    >
                      {exporting[key] ? '⏳ Exporting...' : '📥 Download CSV'}
                    </button>
                  </div>
                ))}
              </div>

              {/* Total records */}
              {counts && (
                <div style={{
                  textAlign: 'center', padding: 'var(--space-3)',
                  fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)',
                }}>
                  Total records across all entities: <strong style={{ color: 'var(--text-primary)' }}>{counts.total_records?.toLocaleString()}</strong>
                  {counts.last_updated && (
                    <span> · Last refreshed: {new Date(counts.last_updated).toLocaleString()}</span>
                  )}
                </div>
              )}
            </>
          )}

        </div>
      )}
    </div>
  );
}
