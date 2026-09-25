/**
 * OfferPipeline - Full offer letter management page for TPO.
 * Shows: Pending Upload, Accepted offers, CSV export, upload modal.
 * Route: /tpo/offers
 */

import { useState, useEffect } from 'react';
import { offerLetterApi } from '../../api/endpoints';

export default function OfferPipeline() {
  const [activeTab, setActiveTab] = useState('pending');
  const [pendingList, setPendingList] = useState([]);
  const [acceptedList, setAcceptedList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploadModal, setUploadModal] = useState(null);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [toast, setToast] = useState(null);

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3500);
  };

  const loadData = async () => {
    try {
      setLoading(true);
      const [pendingRes, acceptedRes] = await Promise.all([
        offerLetterApi.listPending(),
        offerLetterApi.listAccepted(),
      ]);
      setPendingList(Array.isArray(pendingRes.data) ? pendingRes.data : []);
      setAcceptedList(Array.isArray(acceptedRes.data) ? acceptedRes.data : []);
    } catch (err) {
      console.error('Offer pipeline load failed:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleUpload = async () => {
    if (!uploadFile || !uploadModal) return;
    setUploadLoading(true);
    try {
      await offerLetterApi.upload(uploadModal.application_id, uploadFile);
      setUploadSuccess(true);
      showToast('Offer letter uploaded! Student notified.');
      await loadData();
    } catch (err) {
      showToast('Upload failed: ' + (err.response?.data?.detail || 'Error'), 'error');
    } finally {
      setUploadLoading(false);
    }
  };

  const exportCsv = () => {
    const headers = ['Name', 'Company', 'Drive', 'CTC (LPA)', 'Designation', 'Accepted At', 'Joining Confirmed', 'Joining Date'];
    const rows = acceptedList.map(a => [
      `${a.first_name || ''} ${a.last_name || ''}`.trim(),
      a.company_name || '',
      a.drive_title || '',
      a.offer_ctc_lpa || '',
      a.offer_designation || '',
      a.offer_accepted_at ? new Date(a.offer_accepted_at).toLocaleDateString() : '',
      a.offer_joining_confirmed ? 'Yes' : 'No',
      a.offer_joining_date_confirmed || '',
    ]);
    const csv = [headers.join(','), ...rows.map(r => r.map(f => `"${f}"`).join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'accepted_offers.csv';
    a.click();
  };

  const stats = {
    selected: pendingList.length + acceptedList.length,
    pending: pendingList.length,
    accepted: acceptedList.length,
  };

  const TABS = [
    { key: 'pending', label: `📋 Pending Upload (${stats.pending})` },
    { key: 'accepted', label: `✅ Accepted (${stats.accepted})` },
  ];

  if (loading) {
    return <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>Loading offer pipeline...</div>;
  }

  return (
    <div style={{ padding: 'var(--space-6)', maxWidth: 1200, margin: '0 auto' }}>
      {toast && (
        <div style={{
          position: 'fixed', top: 20, right: 20, zIndex: 9999, padding: '12px 20px',
          borderRadius: 10, background: toast.type === 'error' ? '#ef4444' : '#22c55e',
          color: '#fff', fontWeight: 600, boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
        }}>{toast.msg}</div>
      )}

      <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: 24 }}>📄 Offer Letter Pipeline</h1>

      {/* Summary Stat Row */}
      <div style={{ display: 'flex', gap: 16, marginBottom: 28 }}>
        {[
          { label: 'Total Tracked', value: stats.selected, color: '#6366f1' },
          { label: 'Pending Upload', value: stats.pending, color: '#f59e0b' },
          { label: 'Offer Accepted', value: stats.accepted, color: '#22c55e' },
        ].map(s => (
          <div key={s.label} style={{
            flex: 1, padding: '16px 20px', borderRadius: 12, background: 'var(--bg-secondary)',
            border: `1px solid ${s.color}30`, textAlign: 'center',
          }}>
            <div style={{ fontSize: '2rem', fontWeight: 700, color: s.color }}>{s.value}</div>
            <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 2, borderBottom: '2px solid var(--border-color)', marginBottom: 24 }}>
        {TABS.map(t => (
          <button
            key={t.key}
            onClick={() => setActiveTab(t.key)}
            style={{
              padding: '10px 20px', border: 'none', background: 'none', cursor: 'pointer',
              fontWeight: activeTab === t.key ? 700 : 400,
              color: activeTab === t.key ? 'var(--primary)' : 'var(--text-secondary)',
              borderBottom: activeTab === t.key ? '2px solid var(--primary)' : '2px solid transparent',
              marginBottom: -2, fontSize: '0.9rem',
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Pending Upload Tab */}
      {activeTab === 'pending' && (
        <div>
          {pendingList.length === 0 && (
            <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
              ✅ No pending offer letters - all selected candidates have received their letters!
            </div>
          )}
          {pendingList.map(app => (
            <div key={app.application_id} className="card" style={{ padding: '16px 20px', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 16 }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 700, fontSize: '1rem' }}>{app.first_name} {app.last_name}</div>
                <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: 2 }}>
                  🏢 {app.company_name} - {app.drive_title} · Dept: {app.department}
                  {app.offer_ctc_lpa && ` · ₹${app.offer_ctc_lpa} LPA`}
                  {app.offer_designation && ` (${app.offer_designation})`}
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 4 }}>
                  Selected: {app.selected_at ? new Date(app.selected_at).toLocaleDateString() : 'N/A'}
                </div>
              </div>
              <button
                className="btn btn-primary"
                style={{ fontSize: '0.82rem' }}
                onClick={() => {
                  setUploadModal(app);
                  setUploadFile(null);
                  setUploadSuccess(false);
                }}
              >
                ⬆ Upload Offer Letter
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Accepted Tab */}
      {activeTab === 'accepted' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
            <button className="btn btn-secondary" onClick={exportCsv} disabled={acceptedList.length === 0}>
              ⬇ Export Accepted CSV
            </button>
          </div>
          {acceptedList.length === 0 && (
            <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
              No accepted offers yet.
            </div>
          )}
          {acceptedList.map(app => (
            <div key={app.application_id} className="card" style={{ padding: '16px 20px', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 16 }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 700, fontSize: '1rem' }}>{app.first_name} {app.last_name}</div>
                <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: 2 }}>
                  🏢 {app.company_name} - {app.drive_title} · Dept: {app.department}
                  {app.offer_ctc_lpa && ` · ₹${app.offer_ctc_lpa} LPA`}
                  {app.offer_designation && ` (${app.offer_designation})`}
                </div>
                <div style={{ fontSize: '0.78rem', color: '#22c55e', marginTop: 4 }}>
                  ✅ Accepted: {app.offer_accepted_at ? new Date(app.offer_accepted_at).toLocaleDateString() : 'N/A'}
                  {app.offer_joining_confirmed && ` · 📅 Confirmed Joining: ${app.offer_joining_date_confirmed}`}
                </div>
              </div>
              <div style={{
                padding: '4px 12px', borderRadius: 99, background: 'rgba(34,197,94,0.12)',
                color: '#22c55e', fontWeight: 700, fontSize: '0.8rem',
              }}>
                Accepted ✓
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Upload Modal */}
      {uploadModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ background: 'var(--bg-secondary)', borderRadius: 16, padding: 32, width: 460 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 20 }}>
              <h2 style={{ margin: 0, fontSize: '1.1rem' }}>Upload Official Offer Letter</h2>
              <span style={{ cursor: 'pointer' }} onClick={() => setUploadModal(null)}>✕</span>
            </div>
            <div style={{ fontWeight: 600, marginBottom: 4 }}>{uploadModal.first_name} {uploadModal.last_name}</div>
            <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: 20 }}>
              {uploadModal.company_name} - {uploadModal.drive_title}
            </div>
            {uploadSuccess ? (
              <div style={{ textAlign: 'center', padding: 20, color: '#22c55e', fontWeight: 700, fontSize: '1.1rem' }}>
                ✅ Offer letter uploaded!<br />
                <span style={{ fontWeight: 400, fontSize: '0.85rem' }}>Student has been notified in-app.</span>
              </div>
            ) : (
              <>
                <div
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={(e) => {
                    e.preventDefault();
                    const f = e.dataTransfer.files[0];
                    if (f && (f.type === 'application/pdf' || f.name.toLowerCase().endsWith('.pdf'))) setUploadFile(f);
                  }}
                  style={{ border: '2px dashed var(--border-color)', borderRadius: 10, padding: '28px 20px', textAlign: 'center', marginBottom: 16, cursor: 'pointer' }}
                  onClick={() => document.getElementById('pipeline-pdf').click()}
                >
                  <input
                    id="pipeline-pdf"
                    type="file"
                    accept=".pdf"
                    style={{ display: 'none' }}
                    onChange={e => {
                      if (e.target.files?.[0]) setUploadFile(e.target.files[0]);
                    }}
                  />
                  {uploadFile ? (
                    <div style={{ fontWeight: 600 }}>📄 {uploadFile.name} ({(uploadFile.size / 1024).toFixed(0)} KB)</div>
                  ) : (
                    <div style={{ color: 'var(--text-muted)' }}>Drag &amp; drop PDF or click to browse</div>
                  )}
                </div>
                {uploadLoading && (
                  <div style={{ height: 6, background: 'var(--bg-tertiary)', borderRadius: 3, overflow: 'hidden', marginBottom: 12 }}>
                    <div style={{ height: '100%', width: '70%', background: 'var(--primary)', borderRadius: 3 }} />
                  </div>
                )}
                <div style={{ display: 'flex', gap: 10 }}>
                  <button className="btn btn-secondary" onClick={() => setUploadModal(null)}>Cancel</button>
                  <button className="btn btn-primary" style={{ flex: 1 }} onClick={handleUpload} disabled={!uploadFile || uploadLoading}>
                    {uploadLoading ? 'Uploading...' : '⬆ Upload & Notify Student'}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
