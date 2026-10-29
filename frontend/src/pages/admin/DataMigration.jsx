/**
 * Institutional Data Migration & Bulk Student Onboarding Console.
 * Allows Administrators to import existing student records from Excel (.xlsx, .xls) and CSV sheets.
 * Provides pre-upload schema guidance, downloadable sample templates, instant column-mapping preview,
 * automated email/password provisioning, flexible conflict resolution (skip vs replace), and an exportable credentials report.
 */

import React, { useState, useEffect } from 'react';
import { adminApi } from '../../api/endpoints';

export default function DataMigration() {
  const [schemaGuide, setSchemaGuide] = useState([]);
  const [file, setFile] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState(null);
  const [defaultPassword, setDefaultPassword] = useState('student123');
  const [conflictStrategy, setConflictStrategy] = useState('skip'); // 'skip' | 'update'
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('students');

  useEffect(() => {
    adminApi.getSchemaGuide()
      .then((res) => {
        if (res.data?.students) setSchemaGuide(res.data.students);
      })
      .catch((err) => console.error('Failed to load schema guide:', err));
  }, []);

  const handleFileChange = async (e) => {
    const selected = e.target.files?.[0];
    if (!selected) return;
    setFile(selected);
    setError('');
    setImportResult(null);
    setPreviewData(null);
    setConflictStrategy('skip');
    setLoadingPreview(true);

    const formData = new FormData();
    formData.append('file', selected);

    try {
      const res = await adminApi.previewStudents(formData);
      setPreviewData(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to parse file. Make sure it is a valid .xlsx or .csv.');
    } finally {
      setLoadingPreview(false);
    }
  };

  const handleDownloadTemplate = async (format) => {
    try {
      const res = await adminApi.downloadTemplate('students', format);
      const blob = new Blob([res.data], {
        type: format === 'xlsx'
          ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
          : 'text/csv'
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `ccip_student_roster_template.${format}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Download template failed:', err);
    }
  };

  const handleCommitMigration = async () => {
    if (!file) return;
    setImporting(true);
    setError('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await adminApi.commitStudents(formData, defaultPassword, conflictStrategy);
      setImportResult(res.data);
      setPreviewData(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to complete migration');
    } finally {
      setImporting(false);
    }
  };

  const downloadCredentialsCSV = () => {
    if (!importResult?.credentials?.length) return;
    const headers = ['Roll Number', 'Student Name', 'Email', 'Department', 'Temporary Password', 'Status / Action', 'Login Portal'];
    const rows = importResult.credentials.map(c => [
      `"${c.roll_number}"`,
      `"${c.name}"`,
      `"${c.email}"`,
      `"${c.department}"`,
      `"${c.temporary_password}"`,
      `"${c.status || 'Provisioned'}"`,
      `"${window.location.origin}/login"`
    ]);
    const csvContent = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ccip_provisioned_students_${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(a);
    a.click();
    a.remove();
  };

  return (
    <div style={{ padding: '28px', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Title */}
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '1.8rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '6px' }}>
          📦 Institutional Data Migration Hub
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
          Seamlessly migrate your institution&apos;s existing student population from legacy spreadsheets, ERP exports, or Excel records into CCIP.
        </p>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid var(--border-color)', marginBottom: '24px' }}>
        <button
          onClick={() => setActiveTab('students')}
          style={{
            padding: '10px 18px',
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'students' ? '2px solid var(--accent-primary)' : '2px solid transparent',
            color: activeTab === 'students' ? 'var(--accent-primary)' : 'var(--text-secondary)',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          🎓 Student Master Roster
        </button>
      </div>

      {/* ─── 1. Schema Guidance & Field Dictionary ─── */}
      <div
        style={{
          background: 'var(--bg-secondary)',
          border: '1px solid var(--border-color)',
          borderRadius: '12px',
          padding: '20px',
          marginBottom: '24px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>
              📋 Expected Spreadsheet Fields & Auto-Generation Rules
            </h2>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: '4px 0 0' }}>
              CCIP automatically detects flexible column headers (e.g. &ldquo;Reg No&rdquo;, &ldquo;Roll No&rdquo;, &ldquo;Branch&rdquo;) and generates missing credentials.
            </p>
          </div>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              onClick={() => handleDownloadTemplate('xlsx')}
              className="btn btn-secondary"
              style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem' }}
            >
              📥 Download Sample Excel (.xlsx)
            </button>
            <button
              onClick={() => handleDownloadTemplate('csv')}
              className="btn btn-secondary"
              style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem' }}
            >
              📄 Download Sample CSV (.csv)
            </button>
          </div>
        </div>

        {/* Schema Table */}
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-color)', textAlign: 'left', color: 'var(--text-muted)' }}>
                <th style={{ padding: '8px 12px' }}>Field</th>
                <th style={{ padding: '8px 12px' }}>Requirement</th>
                <th style={{ padding: '8px 12px' }}>Sample Value</th>
                <th style={{ padding: '8px 12px' }}>Header Aliases Recognized</th>
                <th style={{ padding: '8px 12px' }}>Fallback / Auto-Generation</th>
              </tr>
            </thead>
            <tbody>
              {schemaGuide.map((item) => (
                <tr key={item.field} style={{ borderBottom: '1px solid var(--border-color)' }}>
                  <td style={{ padding: '8px 12px', fontWeight: 600, color: 'var(--text-primary)' }}>{item.label}</td>
                  <td style={{ padding: '8px 12px' }}>
                    {item.required ? (
                      <span style={{ background: '#ef444422', color: '#ef4444', padding: '2px 8px', borderRadius: '4px', fontWeight: 600, fontSize: '0.75rem' }}>
                        Required
                      </span>
                    ) : item.fallback.includes('Auto-generated') ? (
                      <span style={{ background: '#3b82f622', color: '#60a5fa', padding: '2px 8px', borderRadius: '4px', fontWeight: 600, fontSize: '0.75rem' }}>
                        ⚡ Smart Auto-Fill
                      </span>
                    ) : (
                      <span style={{ background: '#10b98122', color: '#34d399', padding: '2px 8px', borderRadius: '4px', fontSize: '0.75rem' }}>
                        Optional
                      </span>
                    )}
                  </td>
                  <td style={{ padding: '8px 12px', fontFamily: 'monospace', color: 'var(--accent-primary)' }}>{item.sample}</td>
                  <td style={{ padding: '8px 12px', color: 'var(--text-secondary)' }}>{item.aliases}</td>
                  <td style={{ padding: '8px 12px', color: 'var(--text-muted)' }}>{item.fallback}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ─── 2. File Upload Box ─── */}
      <div
        style={{
          background: 'var(--bg-secondary)',
          border: '2px dashed var(--border-color)',
          borderRadius: '12px',
          padding: '32px',
          textAlign: 'center',
          marginBottom: '24px',
        }}
      >
        <div style={{ fontSize: '2.5rem', marginBottom: '8px' }}>📂</div>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '6px' }}>
          Upload Existing Student Spreadsheet
        </h3>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '16px' }}>
          Select or drag and drop your institution&apos;s student list in <strong>.xlsx</strong>, <strong>.xls</strong>, or <strong>.csv</strong> format.
        </p>

        <label className="btn btn-primary" style={{ cursor: 'pointer', display: 'inline-block' }}>
          Choose Spreadsheet File
          <input
            type="file"
            accept=".xlsx,.xls,.csv"
            onChange={handleFileChange}
            style={{ display: 'none' }}
          />
        </label>

        {file && (
          <div style={{ marginTop: '14px', fontSize: '0.9rem', color: 'var(--text-primary)' }}>
            Selected: <strong>{file.name}</strong> ({(file.size / 1024).toFixed(1)} KB)
          </div>
        )}

        {loadingPreview && (
          <div style={{ marginTop: '16px', color: 'var(--accent-primary)', fontSize: '0.9rem' }}>
            ⏳ Analyzing spreadsheet headers and validating records...
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div style={{ background: '#ef444422', border: '1px solid #ef4444', color: '#f87171', padding: '12px 16px', borderRadius: '8px', marginBottom: '20px' }}>
          ⚠️ {error}
        </div>
      )}

      {/* ─── 3. Preview & Validation Results ─── */}
      {previewData && (
        <div
          style={{
            background: 'var(--bg-secondary)',
            border: '1px solid var(--border-color)',
            borderRadius: '12px',
            padding: '24px',
            marginBottom: '24px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>
                🔍 Spreadsheet Verification & Auto-Mapping Preview
              </h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: '4px 0 0' }}>
                Review normalized student records before committing to the institutional database.
              </p>
            </div>

            {/* Default Password Setting */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Default Initial Password:</label>
              <input
                type="text"
                value={defaultPassword}
                onChange={(e) => setDefaultPassword(e.target.value)}
                className="input"
                style={{ width: '130px', padding: '4px 8px', fontSize: '0.85rem' }}
              />
            </div>
          </div>

          {/* Stat Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '14px', marginBottom: '20px' }}>
            <div style={{ background: 'var(--bg-primary)', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Total Rows Detected</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-primary)' }}>{previewData.total_rows_found}</div>
            </div>
            <div style={{ background: 'var(--bg-primary)', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>New Unique Records</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#10b981' }}>{previewData.valid_rows_count}</div>
            </div>
            <div style={{ background: 'var(--bg-primary)', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Existing / Conflicting Rows</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 700, color: previewData.duplicate_rows_count > 0 ? '#f59e0b' : 'var(--text-muted)' }}>
                {previewData.duplicate_rows_count}
              </div>
            </div>
          </div>

          {/* ── Conflict Resolution Strategy Selector (When Duplicates Exist) ── */}
          {previewData.duplicate_rows_count > 0 && (
            <div
              style={{
                background: conflictStrategy === 'update' ? '#3b82f612' : '#f59e0b12',
                border: `1.5px solid ${conflictStrategy === 'update' ? '#3b82f655' : '#f59e0b55'}`,
                borderRadius: '10px',
                padding: '16px 20px',
                marginBottom: '20px',
                transition: 'all 0.2s ease',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                <span style={{ fontSize: '1.3rem' }}>⚠️</span>
                <h4 style={{ margin: 0, fontSize: '0.98rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  Conflicting Records Detected ({previewData.duplicate_rows_count} student{previewData.duplicate_rows_count > 1 ? 's' : ''} already in database)
                </h4>
              </div>
              <p style={{ margin: '0 0 14px 0', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                Some roll numbers in your spreadsheet are already registered in the system. How would you like CCIP to handle these conflicting records?
              </p>
              
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '14px' }}>
                {/* Option 1: Skip Conflicts */}
                <label
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '10px',
                    cursor: 'pointer',
                    padding: '14px',
                    borderRadius: '8px',
                    background: conflictStrategy === 'skip' ? '#f59e0b22' : 'var(--bg-primary)',
                    border: `1.5px solid ${conflictStrategy === 'skip' ? '#f59e0b' : 'var(--border-color)'}`,
                    transition: 'all 0.15s ease',
                  }}
                >
                  <input
                    type="radio"
                    name="conflictStrategy"
                    value="skip"
                    checked={conflictStrategy === 'skip'}
                    onChange={() => setConflictStrategy('skip')}
                    style={{ marginTop: '3px' }}
                  />
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--text-primary)' }}>
                      🛡️ Skip Conflicting Data (Default)
                    </div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '3px', lineHeight: 1.4 }}>
                      Leaves existing student profiles and passwords completely unchanged. Only imports the <strong>{previewData.valid_rows_count}</strong> brand new student{previewData.valid_rows_count === 1 ? '' : 's'}.
                    </div>
                  </div>
                </label>

                {/* Option 2: Update / Overwrite Existing */}
                <label
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '10px',
                    cursor: 'pointer',
                    padding: '14px',
                    borderRadius: '8px',
                    background: conflictStrategy === 'update' ? '#3b82f622' : 'var(--bg-primary)',
                    border: `1.5px solid ${conflictStrategy === 'update' ? '#3b82f6' : 'var(--border-color)'}`,
                    transition: 'all 0.15s ease',
                  }}
                >
                  <input
                    type="radio"
                    name="conflictStrategy"
                    value="update"
                    checked={conflictStrategy === 'update'}
                    onChange={() => setConflictStrategy('update')}
                    style={{ marginTop: '3px' }}
                  />
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.9rem', color: '#60a5fa' }}>
                      🔄 Replace / Overwrite Existing Data
                    </div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '3px', lineHeight: 1.4 }}>
                      Updates existing profiles with latest CGPA, Semester, Department, and tags new skills from this sheet (login credentials remain intact).
                    </div>
                  </div>
                </label>
              </div>
            </div>
          )}

          {/* Missing Required Warning */}
          {previewData.missing_required_columns?.length > 0 && (
            <div style={{ background: '#ef444422', border: '1px solid #ef4444', color: '#f87171', padding: '12px 16px', borderRadius: '8px', marginBottom: '16px', fontSize: '0.9rem' }}>
              ❌ <strong>Missing Required Columns:</strong> {previewData.missing_required_columns.join(', ')}. Please update your spreadsheet or map these headers.
            </div>
          )}

          {/* Preview Table */}
          <div style={{ overflowX: 'auto', marginBottom: '20px' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)', textAlign: 'left', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '8px' }}>#</th>
                  <th style={{ padding: '8px' }}>Roll Number</th>
                  <th style={{ padding: '8px' }}>Student Name</th>
                  <th style={{ padding: '8px' }}>Assigned Email</th>
                  <th style={{ padding: '8px' }}>Department</th>
                  <th style={{ padding: '8px' }}>CGPA</th>
                  <th style={{ padding: '8px' }}>Action / Status</th>
                </tr>
              </thead>
              <tbody>
                {previewData.preview_sample.map((row) => (
                  <tr key={row.roll_number} style={{ borderBottom: '1px solid var(--border-color)' }}>
                    <td style={{ padding: '8px', color: 'var(--text-muted)' }}>{row.row_number}</td>
                    <td style={{ padding: '8px', fontWeight: 600, color: 'var(--accent-primary)' }}>{row.roll_number}</td>
                    <td style={{ padding: '8px', color: 'var(--text-primary)' }}>{row.name}</td>
                    <td style={{ padding: '8px', color: 'var(--text-secondary)' }}>
                      {row.email}
                      {row.auto_generated_email && (
                        <span style={{ marginLeft: '6px', fontSize: '0.7rem', color: '#60a5fa', background: '#3b82f622', padding: '1px 5px', borderRadius: '3px' }}>
                          ⚡ Auto
                        </span>
                      )}
                    </td>
                    <td style={{ padding: '8px' }}>{row.department}</td>
                    <td style={{ padding: '8px' }}>{row.cgpa ?? '—'}</td>
                    <td style={{ padding: '8px' }}>
                      {row.status === 'ready' ? (
                        <span style={{ color: '#10b981', background: '#10b98122', padding: '3px 8px', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 600 }}>
                          ✓ Ready to Import
                        </span>
                      ) : conflictStrategy === 'update' ? (
                        <span style={{ color: '#60a5fa', background: '#3b82f622', padding: '3px 8px', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 600 }} title="Will overwrite student data">
                          🔄 Will Replace (Overwrite)
                        </span>
                      ) : (
                        <span style={{ color: '#f59e0b', background: '#f59e0b22', padding: '3px 8px', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 600 }} title={row.conflict_reason}>
                          ⚠️ Conflict (Will Skip)
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Action Button & Context Note */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '14px', flexWrap: 'wrap' }}>
            <div style={{ fontSize: '0.85rem' }}>
              {conflictStrategy === 'skip' && (
                previewData.valid_rows_count > 0 ? (
                  <span style={{ color: 'var(--text-muted)' }}>
                    ℹ️ <strong>{previewData.valid_rows_count}</strong> new student{previewData.valid_rows_count === 1 ? '' : 's'} will be imported ({previewData.duplicate_rows_count} existing record{previewData.duplicate_rows_count === 1 ? '' : 's'} skipped).
                  </span>
                ) : (
                  <span style={{ color: '#f59e0b', display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                    <span>ℹ️ All {previewData.duplicate_rows_count} students in this file are already registered in the database.</span>
                    <button
                      type="button"
                      onClick={() => setConflictStrategy('update')}
                      className="btn btn-secondary"
                      style={{ padding: '4px 12px', fontSize: '0.8rem', color: '#60a5fa', borderColor: '#3b82f655' }}
                    >
                      🔄 Switch to Replace Mode
                    </button>
                  </span>
                )
              )}
              {conflictStrategy === 'update' && (
                <span style={{ color: '#60a5fa' }}>
                  ℹ️ {previewData.duplicate_rows_count > 0
                    ? `${previewData.duplicate_rows_count} existing record${previewData.duplicate_rows_count === 1 ? '' : 's'} will be updated with fresh spreadsheet data.`
                    : 'All records will be imported.'}
                </span>
              )}
            </div>

            {(() => {
              const hasMissingRequired = (previewData?.missing_required_columns?.length || 0) > 0;
              const canCommit = previewData && !hasMissingRequired && (
                conflictStrategy === 'update'
                  ? previewData.total_rows_found > 0
                  : previewData.valid_rows_count > 0
              );
              return (
                <button
                  onClick={handleCommitMigration}
                  disabled={importing || !canCommit}
                  className="btn btn-primary"
                  style={{
                    padding: '10px 24px',
                    fontSize: '0.95rem',
                    cursor: canCommit && !importing ? 'pointer' : 'not-allowed',
                    opacity: canCommit && !importing ? 1 : 0.6,
                  }}
                >
                  {importing
                    ? '⏳ Ingesting Data & Updating Records...'
                    : conflictStrategy === 'update'
                      ? previewData.valid_rows_count === 0
                        ? `🚀 Confirm & Overwrite All ${previewData.total_rows_found} Existing Records`
                        : `🚀 Confirm & Ingest All ${previewData.total_rows_found} Students (${previewData.valid_rows_count} New, ${previewData.duplicate_rows_count} Overwritten)`
                      : previewData.valid_rows_count > 0
                        ? `🚀 Confirm & Import ${previewData.valid_rows_count} New Students`
                        : `⚠️ No New Records to Import (Switch to Replace Above)`
                  }
                </button>
              );
            })()}
          </div>
        </div>
      )}

      {/* ─── 4. Success State & Download Credentials ─── */}
      {importResult && (
        <div
          style={{
            background: '#10b98115',
            border: '1px solid #10b98155',
            borderRadius: '12px',
            padding: '28px',
            textAlign: 'center',
            marginBottom: '24px',
          }}
        >
          <div style={{ fontSize: '2.5rem', marginBottom: '8px' }}>🎉</div>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 700, color: '#10b981', marginBottom: '6px' }}>
            Migration Completed Successfully!
          </h2>
          <div style={{ color: 'var(--text-primary)', fontSize: '0.95rem', marginBottom: '16px', lineHeight: 1.6 }}>
            {importResult.imported_count > 0 && (
              <div>✓ Successfully provisioned <strong>{importResult.imported_count}</strong> new student account{importResult.imported_count === 1 ? '' : 's'} with default password &ldquo;{importResult.default_password}&rdquo;.</div>
            )}
            {importResult.updated_count > 0 && (
              <div style={{ color: '#60a5fa', fontWeight: 600 }}>🔄 Updated <strong>{importResult.updated_count}</strong> existing student profile{importResult.updated_count === 1 ? '' : 's'} with latest spreadsheet data.</div>
            )}
            {importResult.skipped_count > 0 && (
              <div style={{ color: '#f59e0b', fontSize: '0.85rem' }}>⚠️ {importResult.skipped_count} conflicting row{importResult.skipped_count === 1 ? ' was' : 's were'} skipped based on selected strategy.</div>
            )}
          </div>

          <button
            onClick={downloadCredentialsCSV}
            className="btn btn-primary"
            style={{
              padding: '12px 28px',
              fontSize: '1rem',
              fontWeight: 600,
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              boxShadow: '0 4px 14px rgba(16, 185, 129, 0.4)',
            }}
          >
            📥 Download Student Credentials CSV
          </button>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '10px' }}>
            Distribute this CSV to students or send bulk welcome onboarding emails.
          </p>
        </div>
      )}
    </div>
  );
}
