/**
 * OfferModal — Record official placement offer & CTC breakdown.
 * Triggered from DriveApplicantReviewer when selecting or recording candidate offers.
 */

import { useState, useEffect } from 'react';
import { placementApi, offerLetterApi } from '../../api/endpoints';

export default function OfferModal({ driveId, application, onClose, onSuccess }) {
  const studentName = application
    ? `${application.first_name || ''} ${application.last_name || ''}`.trim() || 'Student'
    : 'Candidate';

  const [form, setForm] = useState({
    designation: application?.offer_designation || '',
    totalCtc: application?.offer_ctc_lpa ?? '',
    fixedCtc: application?.offer_fixed_lpa ?? '',
    variableCtc: application?.offer_variable_lpa ?? 0,
    joiningDate: application?.offer_joining_date || '',
    referenceNumber: application?.offer_reference_number || '',
  });

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [offerFile, setOfferFile] = useState(null);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);

  const handleUploadLetter = async () => {
    if (!offerFile || !application?.application_id) return;
    setUploadLoading(true);
    setError(null);
    try {
      await offerLetterApi.upload(application.application_id, offerFile);
      setUploadSuccess(true);
      setOfferFile(null);
    } catch (err) {
      console.error('Upload failed:', err);
      setError(err.response?.data?.detail || 'Failed to upload offer letter.');
    } finally {
      setUploadLoading(false);
    }
  };

  // Auto-fill defaults if empty
  useEffect(() => {
    if (application) {
      setForm({
        designation: application.offer_designation || 'Associate Software Engineer',
        totalCtc: application.offer_ctc_lpa ?? '',
        fixedCtc: application.offer_fixed_lpa ?? '',
        variableCtc: application.offer_variable_lpa ?? 0,
        joiningDate: application.offer_joining_date || '',
        referenceNumber: application.offer_reference_number || '',
      });
    }
  }, [application]);

  if (!application) return null;

  const total = parseFloat(form.totalCtc) || 0;
  const fixed = parseFloat(form.fixedCtc) || 0;
  const variable = parseFloat(form.variableCtc) || 0;

  // Breakdown percentages
  const fixedPct = total > 0 ? Math.min(100, Math.max(0, Math.round((fixed / total) * 100))) : 0;
  const variablePct = total > 0 ? Math.min(100 - fixedPct, Math.max(0, Math.round((variable / total) * 100))) : 0;
  const discrepancy = total > 0 && Math.abs(fixed + variable - total) > 0.05 * total;

  const handleChange = (k) => (e) => {
    const val = e.target.value;
    setForm(prev => {
      const updated = { ...prev, [k]: val };
      // When total is changed and fixed is empty, suggest 80% fixed
      if (k === 'totalCtc' && val && !prev.fixedCtc) {
        const t = parseFloat(val);
        if (!isNaN(t) && t > 0) {
          updated.fixedCtc = (t * 0.85).toFixed(1);
          updated.variableCtc = (t * 0.15).toFixed(1);
        }
      }
      return updated;
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.designation.trim()) {
      setError('Designation is required.');
      return;
    }
    if (total <= 0) {
      setError('Total CTC must be greater than 0.');
      return;
    }
    if (fixed <= 0) {
      setError('Fixed CTC must be greater than 0.');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      const payload = {
        offer_ctc_lpa: total,
        offer_fixed_lpa: fixed,
        offer_variable_lpa: variable,
        offer_designation: form.designation.trim(),
        offer_joining_date: form.joiningDate || null,
        offer_reference_number: form.referenceNumber.trim() || null,
      };

      const res = await placementApi.recordOffer(driveId, application.application_id, payload);
      onSuccess(res.data || payload);
      onClose();
    } catch (err) {
      console.error('Failed to record offer:', err);
      setError(err.response?.data?.detail || 'Failed to record official offer. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      style={{
        position: 'fixed', inset: 0,
        background: 'rgba(5, 8, 18, 0.75)',
        backdropFilter: 'blur(8px)',
        zIndex: 1200, display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: 'var(--space-6)',
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: 'var(--bg-card)',
          border: '1px solid rgba(99, 102, 241, 0.25)',
          borderRadius: 'var(--border-radius-lg)',
          boxShadow: '0 20px 50px rgba(0,0,0,0.6)',
          padding: 'var(--space-8)',
          width: '100%', maxWidth: 580,
          maxHeight: '90vh', overflowY: 'auto',
        }}
        onClick={e => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--space-5)' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontSize: '1.4rem' }}>📝</span>
              <h2 style={{ fontWeight: 700, fontSize: 'var(--font-size-xl)', color: 'var(--text-primary)', margin: 0 }}>
                Record Official Offer
              </h2>
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-size-sm)', marginTop: 4 }}>
              Candidate: <strong style={{ color: 'var(--accent-primary-hover)' }}>{studentName}</strong> ({application.roll_number})
            </p>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none', border: 'none', cursor: 'pointer',
              color: 'var(--text-muted)', fontSize: '1.5rem', lineHeight: 1,
            }}
          >
            ×
          </button>
        </div>

        {error && (
          <div style={{
            padding: '10px 14px', background: 'rgba(239, 68, 68, 0.12)',
            border: '1px solid rgba(239, 68, 68, 0.3)', color: '#ef4444',
            borderRadius: 'var(--border-radius-sm)', marginBottom: 'var(--space-4)',
            fontSize: 'var(--font-size-xs)',
          }}>
            ⚠️ {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          {/* Designation */}
          <div className="input-group">
            <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600 }}>Designation / Job Role *</label>
            <input
              className="input"
              required
              placeholder="e.g. Associate Software Engineer"
              value={form.designation}
              onChange={handleChange('designation')}
            />
          </div>

          {/* CTC Inputs */}
          <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr 1fr', gap: 'var(--space-3)' }}>
            <div className="input-group">
              <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600 }}>Total CTC (LPA) *</label>
              <input
                className="input"
                type="number"
                step="0.1"
                min="0.5"
                max="200"
                required
                placeholder="e.g. 24.0"
                value={form.totalCtc}
                onChange={handleChange('totalCtc')}
              />
            </div>
            <div className="input-group">
              <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600 }}>Fixed (LPA) *</label>
              <input
                className="input"
                type="number"
                step="0.1"
                min="0.1"
                required
                placeholder="e.g. 20.0"
                value={form.fixedCtc}
                onChange={handleChange('fixedCtc')}
              />
            </div>
            <div className="input-group">
              <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600 }}>Variable (LPA)</label>
              <input
                className="input"
                type="number"
                step="0.1"
                min="0"
                placeholder="e.g. 4.0"
                value={form.variableCtc}
                onChange={handleChange('variableCtc')}
              />
            </div>
          </div>

          {/* Real-time CTC Breakdown Bar */}
          <div style={{
            background: 'var(--bg-tertiary)',
            padding: '12px 16px',
            borderRadius: 'var(--border-radius)',
            border: '1px solid var(--border-color)',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--font-size-xs)', marginBottom: 8 }}>
              <span style={{ color: 'var(--text-muted)' }}>CTC Breakdown Preview</span>
              <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                Fixed: <span style={{ color: '#22c55e' }}>{fixedPct}%</span> | Variable: <span style={{ color: '#6366f1' }}>{variablePct}%</span>
              </span>
            </div>

            {/* Visual Bar */}
            <div style={{
              height: 10,
              background: 'rgba(255,255,255,0.06)',
              borderRadius: 5,
              overflow: 'hidden',
              display: 'flex',
            }}>
              <div
                style={{
                  width: `${fixedPct}%`,
                  background: 'linear-gradient(90deg, #22c55e, #10b981)',
                  transition: 'width 0.25s ease',
                }}
                title={`Fixed: ₹${fixed} LPA (${fixedPct}%)`}
              />
              <div
                style={{
                  width: `${variablePct}%`,
                  background: 'linear-gradient(90deg, #6366f1, #06b6d4)',
                  transition: 'width 0.25s ease',
                }}
                title={`Variable: ₹${variable} LPA (${variablePct}%)`}
              />
            </div>

            {discrepancy && (
              <div style={{ fontSize: '0.72rem', color: '#f59e0b', marginTop: 6, display: 'flex', alignItems: 'center', gap: 4 }}>
                <span>⚠️ Note: Fixed (₹{fixed}) + Variable (₹{variable}) = ₹{(fixed + variable).toFixed(1)} LPA, which differs from Total CTC (₹{total} LPA).</span>
              </div>
            )}
          </div>

          {/* Joining Date & Reference */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3)' }}>
            <div className="input-group">
              <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600 }}>Tentative Joining Date</label>
              <input
                className="input"
                type="date"
                value={form.joiningDate}
                onChange={handleChange('joiningDate')}
              />
            </div>
            <div className="input-group">
              <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600 }}>Offer Reference #</label>
              <input
                className="input"
                placeholder="e.g. AMZ/2026/OFFER/423"
                value={form.referenceNumber}
                onChange={handleChange('referenceNumber')}
              />
            </div>
          </div>

          {/* PDF Offer Letter Upload */}
          <div style={{ marginTop: 24, padding: 16, borderRadius: 10, border: '1px dashed var(--border-color)', background: 'var(--bg-tertiary)' }}>
            <div style={{ fontWeight: 600, marginBottom: 10, fontSize: '0.9rem' }}>📄 Upload Official Offer Letter PDF</div>
            {uploadSuccess ? (
              <div style={{ color: '#22c55e', fontWeight: 600, textAlign: 'center', padding: 12 }}>
                ✅ Offer letter uploaded successfully! Student has been notified.
              </div>
            ) : (
              <>
                <div
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={(e) => {
                    e.preventDefault();
                    const f = e.dataTransfer.files[0];
                    if (f && (f.type === 'application/pdf' || f.name.toLowerCase().endsWith('.pdf'))) {
                      setOfferFile(f);
                    }
                  }}
                  style={{
                    border: '2px dashed var(--border-color)',
                    borderRadius: 8,
                    padding: '16px',
                    textAlign: 'center',
                    cursor: 'pointer',
                    marginBottom: 10,
                  }}
                  onClick={() => document.getElementById('offer-pdf-input').click()}
                >
                  <input
                    id="offer-pdf-input"
                    type="file"
                    accept=".pdf"
                    style={{ display: 'none' }}
                    onChange={e => {
                      if (e.target.files?.[0]) setOfferFile(e.target.files[0]);
                    }}
                  />
                  {offerFile ? (
                    <div style={{ color: 'var(--text-primary)', fontWeight: 600 }}>
                      📄 {offerFile.name} ({(offerFile.size / 1024).toFixed(1)} KB)
                    </div>
                  ) : (
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                      Drag &amp; drop PDF offer letter here or click to browse
                    </div>
                  )}
                </div>
                {offerFile && (
                  <button
                    type="button"
                    className="btn btn-secondary"
                    style={{ width: '100%', borderColor: 'var(--primary)', color: 'var(--primary)' }}
                    onClick={handleUploadLetter}
                    disabled={uploadLoading}
                  >
                    {uploadLoading ? 'Uploading PDF...' : '⬆ Upload Offer Letter PDF'}
                  </button>
                )}
              </>
            )}
          </div>

          {/* Actions */}
          <div style={{ display: 'flex', gap: 'var(--space-3)', marginTop: 'var(--space-4)' }}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onClose}
              disabled={submitting}
              style={{ flex: 1 }}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={submitting || total <= 0}
              style={{ flex: 1.5 }}
            >
              {submitting ? 'Recording Offer...' : '✓ Confirm & Record Offer'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
