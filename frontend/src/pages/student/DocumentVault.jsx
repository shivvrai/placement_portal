/**
 * DocumentVault — Secure student document management system.
 * Upload, organize, and share documents (offer letters, certificates, ID proofs).
 *
 * Sprint 3 — Anjula
 */

import { useState } from 'react';

const DOC_TYPES = [
  { key: 'all', label: 'All Documents', icon: '📁' },
  { key: 'offer_letter', label: 'Offer Letters', icon: '📨' },
  { key: 'certificate', label: 'Certificates', icon: '🏅' },
  { key: 'transcript', label: 'Transcripts', icon: '📜' },
  { key: 'id_proof', label: 'ID Proofs', icon: '🪪' },
  { key: 'resume', label: 'Resumes', icon: '📄' },
  { key: 'recommendation', label: 'Recommendations', icon: '✉️' },
];

const MOCK_DOCS = [
  { id: '1', document_type: 'offer_letter', title: 'TCS Offer Letter', file_name: 'tcs_offer_letter.pdf', file_size_bytes: 256000, mime_type: 'application/pdf', is_verified: true, is_shared_with_tpo: true, tags: ['TCS', '2025'], created_at: '2025-09-25' },
  { id: '2', document_type: 'certificate', title: 'AWS Cloud Practitioner', file_name: 'aws_cert.pdf', file_size_bytes: 189000, mime_type: 'application/pdf', is_verified: true, is_shared_with_tpo: false, tags: ['AWS', 'Cloud'], created_at: '2025-08-10' },
  { id: '3', document_type: 'transcript', title: 'Semester 6 Marksheet', file_name: 'sem6_marksheet.pdf', file_size_bytes: 312000, mime_type: 'application/pdf', is_verified: false, is_shared_with_tpo: true, tags: ['Academic', 'Sem-6'], created_at: '2025-07-15' },
  { id: '4', document_type: 'id_proof', title: 'Aadhaar Card', file_name: 'aadhaar.pdf', file_size_bytes: 145000, mime_type: 'application/pdf', is_verified: true, is_shared_with_tpo: false, tags: ['ID', 'Government'], created_at: '2025-06-01' },
  { id: '5', document_type: 'resume', title: 'Latest Resume (Oct 2025)', file_name: 'resume_oct25.pdf', file_size_bytes: 98000, mime_type: 'application/pdf', is_verified: false, is_shared_with_tpo: true, tags: ['Resume', 'Latest'], created_at: '2025-10-01' },
];

function formatFileSize(bytes) {
  if (!bytes) return '—';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1048576).toFixed(1)} MB`;
}

export default function DocumentVault() {
  const [documents, setDocuments] = useState(MOCK_DOCS);
  const [typeFilter, setTypeFilter] = useState('all');
  const [search, setSearch] = useState('');
  const [showUpload, setShowUpload] = useState(false);
  const [uploadForm, setUploadForm] = useState({
    document_type: 'certificate', title: '', description: '', tags: '',
  });

  const filtered = documents.filter(d => {
    if (typeFilter !== 'all' && d.document_type !== typeFilter) return false;
    if (search && !d.title.toLowerCase().includes(search.toLowerCase()) &&
        !d.tags.some(t => t.toLowerCase().includes(search.toLowerCase()))) return false;
    return true;
  });

  const handleUpload = () => {
    const newDoc = {
      id: `d${Date.now()}`,
      document_type: uploadForm.document_type,
      title: uploadForm.title,
      file_name: `${uploadForm.title.toLowerCase().replace(/\s+/g, '_')}.pdf`,
      file_size_bytes: Math.floor(Math.random() * 500000) + 50000,
      mime_type: 'application/pdf',
      is_verified: false,
      is_shared_with_tpo: false,
      tags: uploadForm.tags.split(',').map(t => t.trim()).filter(Boolean),
      created_at: new Date().toISOString().split('T')[0],
    };
    setDocuments(prev => [newDoc, ...prev]);
    setShowUpload(false);
    setUploadForm({ document_type: 'certificate', title: '', description: '', tags: '' });
  };

  const handleDelete = (id) => {
    setDocuments(prev => prev.filter(d => d.id !== id));
  };

  const toggleShare = (id) => {
    setDocuments(prev => prev.map(d => d.id === id ? { ...d, is_shared_with_tpo: !d.is_shared_with_tpo } : d));
  };

  const stats = {
    total: documents.length,
    verified: documents.filter(d => d.is_verified).length,
    shared: documents.filter(d => d.is_shared_with_tpo).length,
  };

  return (
    <div style={{ padding: '2rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h1 style={{ fontSize: '1.8rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>🔒 Document Vault</h1>
          <p style={{ color: 'var(--text-secondary)', margin: '0.25rem 0 0' }}>Securely store and manage your placement documents.</p>
        </div>
        <button onClick={() => setShowUpload(true)} style={{
          padding: '0.6rem 1.2rem', borderRadius: '8px', border: 'none', cursor: 'pointer',
          background: 'var(--accent-primary)', color: '#fff', fontWeight: 600, fontSize: '0.9rem',
        }}>📤 Upload Document</button>
      </div>

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
        {[
          { label: 'Total Documents', value: stats.total, color: '#6366f1' },
          { label: 'Verified', value: stats.verified, color: '#22c55e' },
          { label: 'Shared with TPO', value: stats.shared, color: '#f59e0b' },
        ].map(s => (
          <div key={s.label} style={{ background: 'var(--bg-secondary)', borderRadius: '12px', padding: '1rem', border: '1px solid var(--border-primary)' }}>
            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: s.color }}>{s.value}</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* Type Filters */}
      <div style={{ display: 'flex', gap: '0.4rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
        {DOC_TYPES.map(dt => (
          <button key={dt.key} onClick={() => setTypeFilter(dt.key)} style={{
            padding: '0.4rem 0.75rem', borderRadius: '20px', border: 'none', cursor: 'pointer',
            background: typeFilter === dt.key ? 'var(--accent-primary)' : 'var(--bg-tertiary)',
            color: typeFilter === dt.key ? '#fff' : 'var(--text-secondary)',
            fontSize: '0.78rem', fontWeight: 500,
          }}>{dt.icon} {dt.label}</button>
        ))}
      </div>

      <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search documents..."
        style={{ width: '100%', padding: '0.6rem 1rem', borderRadius: '8px', border: '1px solid var(--border-primary)', background: 'var(--bg-secondary)', color: 'var(--text-primary)', marginBottom: '1.5rem' }} />

      {/* Document List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {filtered.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>No documents found. Upload your first document!</div>
        ) : filtered.map(doc => {
          const docType = DOC_TYPES.find(dt => dt.key === doc.document_type) || { icon: '📁' };
          return (
            <div key={doc.id} style={{
              background: 'var(--bg-secondary)', borderRadius: '10px', padding: '1rem 1.25rem',
              border: '1px solid var(--border-primary)', display: 'flex', alignItems: 'center', gap: '1rem',
            }}>
              <span style={{ fontSize: '1.5rem' }}>{docType.icon}</span>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>{doc.title}</h3>
                  {doc.is_verified && <span style={{ background: 'rgba(34,197,94,0.12)', color: '#22c55e', padding: '0.1rem 0.4rem', borderRadius: '4px', fontSize: '0.65rem', fontWeight: 600 }}>✅ Verified</span>}
                </div>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginTop: '0.2rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  <span>{doc.file_name}</span> · <span>{formatFileSize(doc.file_size_bytes)}</span> · <span>{doc.created_at}</span>
                </div>
                <div style={{ display: 'flex', gap: '0.25rem', marginTop: '0.3rem' }}>
                  {doc.tags.map(t => (
                    <span key={t} style={{ background: 'rgba(99,102,241,0.1)', color: '#6366f1', padding: '0.1rem 0.35rem', borderRadius: '4px', fontSize: '0.65rem' }}>{t}</span>
                  ))}
                </div>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                <button onClick={() => toggleShare(doc.id)} title={doc.is_shared_with_tpo ? 'Unshare with TPO' : 'Share with TPO'} style={{
                  padding: '0.35rem 0.7rem', borderRadius: '6px', border: '1px solid var(--border-primary)', cursor: 'pointer',
                  background: doc.is_shared_with_tpo ? 'rgba(245,158,11,0.12)' : 'transparent',
                  color: doc.is_shared_with_tpo ? '#f59e0b' : 'var(--text-muted)', fontSize: '0.72rem',
                }}>{doc.is_shared_with_tpo ? '🔗 Shared' : '🔗 Share'}</button>
                <button onClick={() => handleDelete(doc.id)} style={{
                  padding: '0.35rem 0.7rem', borderRadius: '6px', border: '1px solid rgba(239,68,68,0.3)', cursor: 'pointer',
                  background: 'transparent', color: '#ef4444', fontSize: '0.72rem',
                }}>🗑️</button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Upload Modal */}
      {showUpload && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}
             onClick={() => setShowUpload(false)}>
          <div style={{ background: 'var(--bg-primary)', borderRadius: '16px', padding: '2rem', width: '450px', maxWidth: '90vw' }}
               onClick={e => e.stopPropagation()}>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '1rem', color: 'var(--text-primary)' }}>📤 Upload Document</h2>
            <select value={uploadForm.document_type} onChange={e => setUploadForm(f => ({ ...f, document_type: e.target.value }))}
              style={{ width: '100%', padding: '0.6rem 1rem', borderRadius: '8px', border: '1px solid var(--border-primary)', background: 'var(--bg-secondary)', color: 'var(--text-primary)', marginBottom: '0.75rem' }}>
              {DOC_TYPES.filter(d => d.key !== 'all').map(d => <option key={d.key} value={d.key}>{d.icon} {d.label}</option>)}
            </select>
            <input value={uploadForm.title} onChange={e => setUploadForm(f => ({ ...f, title: e.target.value }))} placeholder="Document title"
              style={{ width: '100%', padding: '0.6rem 1rem', borderRadius: '8px', border: '1px solid var(--border-primary)', background: 'var(--bg-secondary)', color: 'var(--text-primary)', marginBottom: '0.75rem' }} />
            <textarea value={uploadForm.description} onChange={e => setUploadForm(f => ({ ...f, description: e.target.value }))} placeholder="Description (optional)"
              style={{ width: '100%', minHeight: '60px', padding: '0.6rem 1rem', borderRadius: '8px', border: '1px solid var(--border-primary)', background: 'var(--bg-secondary)', color: 'var(--text-primary)', marginBottom: '0.75rem', resize: 'vertical' }} />
            <input value={uploadForm.tags} onChange={e => setUploadForm(f => ({ ...f, tags: e.target.value }))} placeholder="Tags (comma-separated)"
              style={{ width: '100%', padding: '0.6rem 1rem', borderRadius: '8px', border: '1px solid var(--border-primary)', background: 'var(--bg-secondary)', color: 'var(--text-primary)', marginBottom: '1rem' }} />
            <div style={{
              border: '2px dashed var(--border-primary)', borderRadius: '12px', padding: '2rem',
              textAlign: 'center', marginBottom: '1rem', color: 'var(--text-muted)', cursor: 'pointer',
            }}>
              <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>📎</div>
              <div>Click or drag to upload file</div>
              <div style={{ fontSize: '0.75rem', marginTop: '0.25rem' }}>PDF, DOCX, JPG, PNG (max 10MB)</div>
            </div>
            <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
              <button onClick={() => setShowUpload(false)} style={{ padding: '0.5rem 1.2rem', borderRadius: '8px', border: '1px solid var(--border-primary)', background: 'transparent', color: 'var(--text-secondary)', cursor: 'pointer' }}>Cancel</button>
              <button onClick={handleUpload} disabled={!uploadForm.title} style={{ padding: '0.5rem 1.2rem', borderRadius: '8px', border: 'none', background: 'var(--accent-primary)', color: '#fff', fontWeight: 600, cursor: 'pointer', opacity: uploadForm.title ? 1 : 0.5 }}>Upload</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
