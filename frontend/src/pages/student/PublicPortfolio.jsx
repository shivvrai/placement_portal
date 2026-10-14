import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { studentApi } from '../../api/endpoints';

function formatDate(dStr) {
  if (!dStr) return '';
  try {
    const d = new Date(dStr);
    if (isNaN(d.getTime())) return dStr;
    return d.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
  } catch {
    return dStr;
  }
}

export default function PublicPortfolio() {
  const { studentId } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    let isMounted = true;
    async function fetchPublicProfile() {
      try {
        setLoading(true);
        setError(null);
        const res = await studentApi.getPublicProfile(studentId);
        if (isMounted) {
          setData(res.data);
        }
      } catch (err) {
        if (isMounted) {
          if (err.response?.status === 403) {
            setError({
              title: 'Portfolio is Private',
              message: 'This student has chosen not to share their portfolio publicly.',
              icon: '🔒',
            });
          } else if (err.response?.status === 404) {
            setError({
              title: 'Student Not Found',
              message: 'The requested student profile could not be found. Please check the URL.',
              icon: '🔍',
            });
          } else {
            setError({
              title: 'Unable to Load Portfolio',
              message: err.response?.data?.detail || 'An unexpected error occurred while loading this portfolio.',
              icon: '⚠️',
            });
          }
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    fetchPublicProfile();
    return () => {
      isMounted = false;
    };
  }, [studentId]);

  const handleCopyLink = () => {
    navigator.clipboard.writeText(window.location.href);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handlePrint = () => {
    window.print();
  };

  if (loading) {
    return (
      <div
        style={{
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          background: '#f8fafc',
          color: '#334155',
          fontFamily: 'Inter, system-ui, sans-serif',
        }}
      >
        <div className="spinner" style={{ width: 36, height: 36, borderColor: '#6366f1', borderTopColor: 'transparent' }} />
        <p style={{ marginTop: 16, fontSize: 14, fontWeight: 500, color: '#64748b' }}>
          Loading verified student portfolio...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div
        style={{
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          background: '#f8fafc',
          padding: 24,
          fontFamily: 'Inter, system-ui, sans-serif',
        }}
      >
        <div
          style={{
            maxWidth: 480,
            width: '100%',
            background: '#ffffff',
            borderRadius: 16,
            padding: 32,
            boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.08), 0 8px 10px -6px rgba(0, 0, 0, 0.04)',
            textAlign: 'center',
            border: '1px solid #e2e8f0',
          }}
        >
          <div style={{ fontSize: '3rem', marginBottom: 16 }}>{error.icon}</div>
          <h2 style={{ fontSize: '1.35rem', fontWeight: 700, color: '#0f172a', marginBottom: 8 }}>
            {error.title}
          </h2>
          <p style={{ fontSize: 14, color: '#64748b', lineHeight: 1.6, marginBottom: 24 }}>
            {error.message}
          </p>
          <Link
            to="/login"
            style={{
              display: 'inline-block',
              padding: '10px 20px',
              borderRadius: 8,
              background: '#4f46e5',
              color: '#ffffff',
              fontWeight: 600,
              fontSize: 14,
              textDecoration: 'none',
              transition: 'background 0.15s ease',
            }}
          >
            Portal Sign In
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        background: '#f1f5f9',
        color: '#0f172a',
        fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        padding: '32px 16px 64px',
      }}
    >
      {/* Print Stylesheet */}
      <style>{`
        @media print {
          body { background: #ffffff !important; }
          .no-print { display: none !important; }
          .print-container {
            box-shadow: none !important;
            border: none !important;
            padding: 0 !important;
            max-width: 100% !important;
          }
          .page-break-inside-avoid {
            break-inside: avoid;
            page-break-inside: avoid;
          }
        }
      `}</style>

      {/* Floating Action Bar (hidden on print) */}
      <div
        className="no-print"
        style={{
          maxWidth: 820,
          margin: '0 auto 16px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 12,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 13, color: '#475569', fontWeight: 500 }}>
            Public Recruiter Showcase
          </span>
          <span
            style={{
              fontSize: 11,
              padding: '2px 8px',
              borderRadius: 9999,
              background: '#dcfce7',
              color: '#15803d',
              fontWeight: 700,
              display: 'inline-flex',
              alignItems: 'center',
              gap: 4,
            }}
          >
            ✓ Official Record
          </span>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            type="button"
            onClick={handleCopyLink}
            style={{
              padding: '6px 14px',
              borderRadius: 6,
              border: '1px solid #cbd5e1',
              background: '#ffffff',
              color: '#334155',
              fontSize: 13,
              fontWeight: 600,
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
              boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
            }}
          >
            {copied ? '✓ Link Copied!' : '🔗 Copy Shareable Link'}
          </button>
          <button
            type="button"
            onClick={handlePrint}
            style={{
              padding: '6px 14px',
              borderRadius: 6,
              border: 'none',
              background: '#4f46e5',
              color: '#ffffff',
              fontSize: 13,
              fontWeight: 600,
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
              boxShadow: '0 1px 3px rgba(79, 70, 229, 0.3)',
            }}
          >
            🖨️ Print / Save PDF
          </button>
        </div>
      </div>

      {/* Main Resume Sheet */}
      <div
        className="print-container"
        style={{
          maxWidth: 820,
          margin: '0 auto',
          background: '#ffffff',
          borderRadius: 16,
          padding: '48px 44px',
          boxShadow: '0 20px 25px -5px rgba(0,0,0,0.06), 0 8px 10px -6px rgba(0,0,0,0.04)',
          border: '1px solid #e2e8f0',
        }}
      >
        {/* Header Ribbon */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            borderBottom: '2px solid #f1f5f9',
            paddingBottom: 24,
            marginBottom: 28,
            flexWrap: 'wrap',
            gap: 16,
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
              <span
                style={{
                  background: 'linear-gradient(135deg, #4f46e5, #06b6d4)',
                  color: 'white',
                  fontWeight: 800,
                  fontSize: 16,
                  padding: '4px 10px',
                  borderRadius: 6,
                  letterSpacing: '0.05em',
                }}
              >
                CCIP
              </span>
              <span style={{ fontSize: 13, color: '#64748b', fontWeight: 600 }}>
                Campus Placement & Verified Portfolio
              </span>
            </div>
            <h1
              style={{
                fontSize: '2rem',
                fontWeight: 800,
                color: '#0f172a',
                margin: '0 0 6px 0',
                letterSpacing: '-0.02em',
              }}
            >
              {data.name}
            </h1>
            <div style={{ fontSize: 15, color: '#475569', fontWeight: 500 }}>
              🎓 {data.branch || data.department} · Class of {data.graduation_year}
            </div>
          </div>

          <div style={{ textAlign: 'right', minWidth: 180 }}>
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
                background: '#f8fafc',
                border: '1px solid #e2e8f0',
                padding: '6px 12px',
                borderRadius: 8,
                marginBottom: 10,
              }}
            >
              <span style={{ color: '#16a34a', fontSize: 14 }}>🛡️</span>
              <span style={{ fontSize: 12, fontWeight: 700, color: '#1e293b' }}>
                Verified University Record
              </span>
            </div>
            <div style={{ fontSize: 13, color: '#64748b' }}>
              Roll: <strong style={{ color: '#0f172a' }}>{data.roll_number}</strong>
            </div>
            {data.cgpa !== null && data.cgpa !== undefined && (
              <div style={{ fontSize: 13, color: '#64748b', marginTop: 4 }}>
                Cumulative GPA:{' '}
                <strong style={{ color: '#16a34a', fontSize: 14 }}>
                  {typeof data.cgpa === 'number' ? data.cgpa.toFixed(2) : data.cgpa} / 10.0
                </strong>
                <span style={{ color: '#16a34a', marginLeft: 4, fontWeight: 'bold' }}>✓</span>
              </div>
            )}
          </div>
        </div>

        {/* ─── SECTION 1: VERIFIED SKILLS ────────────────────────────── */}
        {data.verified_skills && data.verified_skills.length > 0 && (
          <div className="page-break-inside-avoid" style={{ marginBottom: 32 }}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                fontSize: 13,
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                color: '#475569',
                borderBottom: '1.5px solid #e2e8f0',
                paddingBottom: 8,
                marginBottom: 16,
              }}
            >
              <span>Verified Competencies & Skills</span>
              <span
                style={{
                  fontSize: 11,
                  background: '#e0e7ff',
                  color: '#4338ca',
                  padding: '2px 8px',
                  borderRadius: 9999,
                  fontWeight: 600,
                  textTransform: 'none',
                  letterSpacing: 'normal',
                }}
              >
                NLP Extracted & Confirmed
              </span>
            </div>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {data.verified_skills.map((skillName) => (
                <span
                  key={skillName}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 6,
                    padding: '6px 14px',
                    borderRadius: 8,
                    background: '#f8fafc',
                    border: '1px solid #cbd5e1',
                    color: '#1e293b',
                    fontSize: 13,
                    fontWeight: 600,
                  }}
                >
                  <span style={{ color: '#16a34a', fontSize: 12 }}>✓</span>
                  {skillName}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* ─── SECTION 2: PROJECTS ───────────────────────────────────── */}
        {data.projects && data.projects.length > 0 && (
          <div className="page-break-inside-avoid" style={{ marginBottom: 36 }}>
            <div
              style={{
                fontSize: 13,
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                color: '#475569',
                borderBottom: '1.5px solid #e2e8f0',
                paddingBottom: 8,
                marginBottom: 16,
              }}
            >
              Featured Projects
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              {data.projects.map((proj, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: 16,
                    borderRadius: 10,
                    border: '1px solid #f1f5f9',
                    background: proj.is_featured ? '#fafafa' : 'transparent',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'flex-start',
                      flexWrap: 'wrap',
                      gap: 8,
                      marginBottom: 6,
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{ fontSize: 16, fontWeight: 700, color: '#0f172a' }}>
                        {proj.title}
                      </span>
                      {proj.is_featured && (
                        <span
                          style={{
                            fontSize: 11,
                            padding: '2px 8px',
                            borderRadius: 9999,
                            background: '#fef3c7',
                            color: '#b45309',
                            fontWeight: 700,
                          }}
                        >
                          ⭐ Featured
                        </span>
                      )}
                    </div>

                    {(proj.start_date || proj.end_date) && (
                      <span style={{ fontSize: 12, color: '#64748b', fontWeight: 500 }}>
                        {formatDate(proj.start_date)}
                        {proj.start_date && (proj.end_date ? ` – ${formatDate(proj.end_date)}` : ' – Present')}
                      </span>
                    )}
                  </div>

                  {proj.technologies && proj.technologies.length > 0 && (
                    <div style={{ fontSize: 13, color: '#4f46e5', fontWeight: 600, marginBottom: 8 }}>
                      {proj.technologies.join(' · ')}
                    </div>
                  )}

                  <p style={{ fontSize: 13, color: '#334155', lineHeight: 1.6, margin: '0 0 10px 0' }}>
                    {proj.description}
                  </p>

                  <div style={{ display: 'flex', gap: 16, fontSize: 12 }}>
                    {proj.github_url && (
                      <a
                        href={proj.github_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ color: '#0f172a', textDecoration: 'none', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: 4 }}
                      >
                        <span>🐙</span> {proj.github_url.replace(/^https?:\/\//, '')}
                      </a>
                    )}
                    {proj.live_url && (
                      <a
                        href={proj.live_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ color: '#4f46e5', textDecoration: 'none', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: 4 }}
                      >
                        <span>🔗 Live Demo</span>
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ─── SECTION 3: WORK EXPERIENCE ────────────────────────────── */}
        {data.work_experience && data.work_experience.length > 0 && (
          <div className="page-break-inside-avoid" style={{ marginBottom: 36 }}>
            <div
              style={{
                fontSize: 13,
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                color: '#475569',
                borderBottom: '1.5px solid #e2e8f0',
                paddingBottom: 8,
                marginBottom: 16,
              }}
            >
              Work Experience & Internships
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
              {data.work_experience.map((exp, idx) => (
                <div key={idx} style={{ padding: '0 4px' }}>
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'baseline',
                      flexWrap: 'wrap',
                      gap: 8,
                      marginBottom: 4,
                    }}
                  >
                    <div>
                      <span style={{ fontSize: 15, fontWeight: 700, color: '#0f172a' }}>
                        {exp.role}
                      </span>
                      <span style={{ color: '#64748b', margin: '0 6px' }}>·</span>
                      <span style={{ fontSize: 14, fontWeight: 600, color: '#1e293b' }}>
                        {exp.company_name}
                      </span>
                      {exp.location && (
                        <span style={{ fontSize: 12, color: '#64748b', marginLeft: 6 }}>
                          ({exp.location})
                        </span>
                      )}
                    </div>

                    <span style={{ fontSize: 12, color: '#64748b', fontWeight: 500 }}>
                      {formatDate(exp.start_date)}
                      {exp.start_date && (exp.is_current ? ' – Present' : exp.end_date ? ` – ${formatDate(exp.end_date)}` : '')}
                    </span>
                  </div>

                  {exp.skills_used && exp.skills_used.length > 0 && (
                    <div style={{ fontSize: 12, color: '#64748b', marginBottom: 6 }}>
                      <strong style={{ color: '#475569' }}>Skills:</strong> {exp.skills_used.join(', ')}
                    </div>
                  )}

                  {exp.description && (
                    <p style={{ fontSize: 13, color: '#334155', lineHeight: 1.6, margin: 0 }}>
                      "{exp.description}"
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ─── SECTION 4: CERTIFICATIONS ─────────────────────────────── */}
        {data.certifications && data.certifications.length > 0 && (
          <div className="page-break-inside-avoid" style={{ marginBottom: 36 }}>
            <div
              style={{
                fontSize: 13,
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                color: '#475569',
                borderBottom: '1.5px solid #e2e8f0',
                paddingBottom: 8,
                marginBottom: 16,
              }}
            >
              Certifications & Credentials
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 14 }}>
              {data.certifications.map((cert, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: 14,
                    borderRadius: 8,
                    background: '#f8fafc',
                    border: '1px solid #e2e8f0',
                  }}
                >
                  <div style={{ fontSize: 14, fontWeight: 700, color: '#0f172a', marginBottom: 4 }}>
                    {cert.name}
                  </div>
                  <div style={{ fontSize: 12, color: '#475569', marginBottom: 6 }}>
                    {cert.issuing_organization} · Issued: {formatDate(cert.issue_date)}
                    {cert.expiration_date && ` · Expires: ${formatDate(cert.expiration_date)}`}
                  </div>
                  {cert.credential_id && (
                    <div style={{ fontSize: 11, color: '#64748b', marginBottom: 6 }}>
                      Credential ID: <code style={{ fontFamily: 'monospace' }}>{cert.credential_id}</code>
                    </div>
                  )}
                  {cert.credential_url && (
                    <a
                      href={cert.credential_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{
                        fontSize: 12,
                        color: '#4f46e5',
                        textDecoration: 'none',
                        fontWeight: 600,
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 4,
                      }}
                    >
                      🔗 Verify Credential
                    </a>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ─── UNIVERSITY VERIFICATION WATERMARK / FOOTER ─────────────── */}
        <div
          style={{
            marginTop: 40,
            paddingTop: 24,
            borderTop: '2px dashed #e2e8f0',
            textAlign: 'center',
            color: '#64748b',
          }}
        >
          <div style={{ fontSize: 13, fontWeight: 700, color: '#1e293b', marginBottom: 4 }}>
            🛡️ This profile is verified by {data.college_name || 'University Placement Cell'}
          </div>
          <div style={{ fontSize: 12 }}>
            Profile ID: <strong style={{ color: '#0f172a' }}>{data.roll_number}</strong>
            {data.last_updated && ` · Verified Record As Of: ${formatDate(data.last_updated)}`}
          </div>
        </div>
      </div>
    </div>
  );
}
