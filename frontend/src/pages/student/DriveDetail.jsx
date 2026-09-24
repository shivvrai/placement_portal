import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { placementApi, matchingApi } from '../../api/endpoints';

export default function DriveDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const [drive, setDrive] = useState(null);
  const [matchData, setMatchData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [skillToAdd, setSkillToAdd] = useState('');
  const [whatIfResult, setWhatIfResult] = useState(null);
  
  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        const [driveRes, matchRes] = await Promise.all([
          placementApi.getDrive(id),
          matchingApi.getDriveMatch(id)
        ]);
        setDrive(driveRes.data);
        setMatchData(matchRes.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [id]);

  const handleWhatIf = async () => {
    if (!skillToAdd) return;
    try {
      const res = await matchingApi.whatIf({ skill_to_add: skillToAdd, drive_id: id });
      setWhatIfResult(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) return <div className="page-body">Loading...</div>;
  if (!drive || !matchData) return <div className="page-body">Drive not found or error loading match data.</div>;

  const score = Math.round(matchData.match_score);
  const color = score >= 75 ? '#22c55e' : score >= 50 ? '#f59e0b' : '#ef4444';
  const bg = score >= 75 ? 'rgba(34,197,94,0.1)' : score >= 50 ? 'rgba(245,158,11,0.1)' : 'rgba(239,68,68,0.1)';

  return (
    <div>
      <div className="page-header">
        <h1>{drive.company} - {drive.roles_offered?.join(', ')}</h1>
        <p>Detailed Match Analysis</p>
      </div>
      <div className="page-body" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
        
        {/* Overall Score Bar */}
        <div className="card" style={{ background: bg, border: `1px solid ${color}` }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontWeight: 700, fontSize: 'var(--font-size-lg)', color }}>Overall Match Score</span>
            <span style={{ fontWeight: 800, fontSize: 'var(--font-size-2xl)', color }}>{score}%</span>
          </div>
          <div style={{ height: 8, background: 'var(--bg-secondary)', borderRadius: 4, marginTop: 'var(--space-2)', overflow: 'hidden' }}>
            <div style={{ width: `${score}%`, height: '100%', background: color, borderRadius: 4 }} />
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: 'var(--space-6)' }}>
          {/* Skill Breakdown */}
          <div className="card">
            <h3 style={{ marginBottom: 'var(--space-4)' }}>Skill Breakdown</h3>
            <table style={{ width: '100%', textAlign: 'left', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
                  <th style={{ paddingBottom: 'var(--space-2)' }}>Skill</th>
                  <th style={{ paddingBottom: 'var(--space-2)' }}>Status</th>
                  <th style={{ paddingBottom: 'var(--space-2)' }}>Your Level</th>
                </tr>
              </thead>
              <tbody>
                {matchData.skill_breakdown?.map(sb => {
                  const statusIcon = sb.status === 'strong' ? '✓ Strong' : sb.status === 'gap' ? '⚠️ Gap' : '✗ Missing';
                  const sColor = sb.status === 'strong' ? '#22c55e' : sb.status === 'gap' ? '#f59e0b' : '#ef4444';
                  return (
                    <tr key={sb.skill} style={{ borderBottom: '1px solid var(--bg-secondary)' }}>
                      <td style={{ padding: 'var(--space-3) 0', fontWeight: 500 }}>{sb.skill}</td>
                      <td style={{ padding: 'var(--space-3) 0', color: sColor, fontWeight: 600 }}>{statusIcon}</td>
                      <td style={{ padding: 'var(--space-3) 0' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                          <div style={{ flex: 1, height: 6, background: 'var(--bg-tertiary)', borderRadius: 3 }}>
                            <div style={{ width: `${sb.student_level}%`, height: '100%', background: 'var(--accent-primary)', borderRadius: 3 }} />
                          </div>
                          <span style={{ fontSize: 'var(--font-size-xs)' }}>{sb.student_level}</span>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
            {/* Rank Card */}
            <div className="card">
              <h3 style={{ marginBottom: 'var(--space-2)' }}>Your Rank</h3>
              <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)' }}>
                Among {matchData.total_applicants || 'N'} applicants
              </p>
              <div style={{ fontSize: 'var(--font-size-3xl)', fontWeight: 800, color: 'var(--accent-primary)', marginTop: 'var(--space-2)' }}>
                #{matchData.rank || '--'}
              </div>
            </div>

            {/* What-If Simulator */}
            <div className="card">
              <h3 style={{ marginBottom: 'var(--space-4)' }}>What-If Simulator</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                <input 
                  type="text" 
                  className="input" 
                  placeholder="Add a skill (e.g. AWS)" 
                  value={skillToAdd} 
                  onChange={e => setSkillToAdd(e.target.value)} 
                />
                <button className="btn btn-secondary" onClick={handleWhatIf}>Simulate</button>
                {whatIfResult && (
                  <div style={{ marginTop: 'var(--space-2)', padding: 'var(--space-2)', background: 'var(--bg-tertiary)', borderRadius: 'var(--border-radius-sm)', textAlign: 'center' }}>
                    <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)' }}>New Score</div>
                    <div style={{ fontWeight: 700, color: '#22c55e' }}>
                      {score}% → {whatIfResult.new_score}% <span style={{ fontSize: 'var(--font-size-xs)' }}>(↑{whatIfResult.delta}%)</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        <div style={{ textAlign: 'center', marginTop: 'var(--space-4)' }}>
          <button className="btn btn-primary" onClick={() => navigate('/student/roadmap')}>
            Get Ready →
          </button>
        </div>
      </div>
    </div>
  );
}
