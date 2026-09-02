import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { assessmentsApi } from '../../api/endpoints';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import './Assessments.css';

export default function AssessmentsList() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [topic, setTopic] = useState('');
  const [difficulty, setDifficulty] = useState('beginner');
  const [startLoading, setStartLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      const res = await assessmentsApi.getHistory();
      setHistory(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleStart = async (e) => {
    e.preventDefault();
    if (!topic.trim()) return;
    
    setStartLoading(true);
    setError('');
    
    try {
      const res = await assessmentsApi.start(topic.trim(), difficulty);
      navigate(`/student/assessments/${res.data.id}/take`, { state: { session: res.data } });
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start assessment. Ensure enough questions exist.');
    } finally {
      setStartLoading(false);
    }
  };

  return (
    <div className="assessments-list page-container">
      <div className="page-header">
        <div>
          <h1>Skill Assessments</h1>
          <p>Test your knowledge and prove your skills</p>
        </div>
        <Button variant="primary" onClick={() => setShowModal(true)}>
          Take New Assessment
        </Button>
      </div>

      {loading ? (
        <div>Loading history...</div>
      ) : history.length === 0 ? (
        <Card className="empty-state">
          <h3>No Assessments Yet</h3>
          <p>Take an assessment to validate your skills and update your Skill Profile.</p>
        </Card>
      ) : (
        <div className="history-grid">
          {history.map((session) => (
            <Card key={session.id} className="history-card">
              <div className="history-header">
                <h3>{session.topic.toUpperCase()}</h3>
                <span className={`difficulty-badge ${session.difficulty}`}>
                  {session.difficulty}
                </span>
              </div>
              <div className="history-score">
                <span className="score-value">{Math.round(session.score)}%</span>
              </div>
              <div className="history-meta">
                <span>{new Date(session.started_at).toLocaleDateString()}</span>
                <span className={`status ${session.status}`}>{session.status.replace('_', ' ')}</span>
              </div>
              {session.status === 'in_progress' && (
                <Button 
                  variant="outline" 
                  onClick={() => navigate(`/student/assessments/${session.id}/take`)}
                >
                  Resume
                </Button>
              )}
            </Card>
          ))}
        </div>
      )}

      {showModal && (
        <div className="modal-overlay">
          <div className="modal-content assessment-modal">
            <h2>Start New Assessment</h2>
            {error && <div className="error-alert">{error}</div>}
            
            <form onSubmit={handleStart}>
              <div className="form-group">
                <label>Skill Topic</label>
                <input 
                  type="text" 
                  placeholder="e.g., Python, React, SQL"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label>Difficulty</label>
                <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
                  <option value="beginner">Beginner</option>
                  <option value="intermediate">Intermediate</option>
                  <option value="advanced">Advanced</option>
                </select>
              </div>
              <div className="modal-actions">
                <Button variant="ghost" type="button" onClick={() => setShowModal(false)}>
                  Cancel
                </Button>
                <Button variant="primary" type="submit" disabled={startLoading || !topic}>
                  {startLoading ? 'Preparing...' : 'Start Assessment'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
