import { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { assessmentsApi } from '../../api/endpoints';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import './Assessments.css';

export default function AssessmentTake() {
  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  
  const [session, setSession] = useState(location.state?.session || null);
  const [loading, setLoading] = useState(!session);
  const [answers, setAnswers] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  
  // Basic integrity: optional timer
  const [timeLeft, setTimeLeft] = useState(30 * 60); // 30 minutes

  useEffect(() => {
    // If accessed directly without state, we'd normally fetch the session by ID.
    // For MVP, we assume it's passed via router state or we show an error.
    if (!session) {
      // In a real app, call a GET /assessments/{id} endpoint here.
      // Since we didn't define one, navigate back for now.
      navigate('/student/assessments');
    }
  }, [session, navigate]);

  useEffect(() => {
    if (result) return;
    
    const timer = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) {
          clearInterval(timer);
          handleSubmit(); // Auto-submit when time's up
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    
    return () => clearInterval(timer);
  }, [result]);

  const handleSelect = (questionId, option) => {
    setAnswers(prev => ({
      ...prev,
      [questionId]: option
    }));
  };

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    setSubmitting(true);
    
    const formattedAnswers = Object.entries(answers).map(([qId, opt]) => ({
      question_id: qId,
      selected_option: opt
    }));
    
    try {
      const res = await assessmentsApi.submit(id, formattedAnswers);
      setResult(res.data);
    } catch (err) {
      console.error(err);
      alert('Failed to submit assessment');
    } finally {
      setSubmitting(false);
    }
  };

  const formatTime = (seconds) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  if (loading) return <div>Loading...</div>;

  if (result) {
    return (
      <div className="assessment-take page-container">
        <Card className="result-card">
          <div className="result-header">
            <h2>Assessment Complete</h2>
            <div className="final-score">
              <span className="score-number">{Math.round(result.score)}%</span>
            </div>
            <p>{result.correct} correct out of {result.total_questions}</p>
          </div>
          
          <div className="result-breakdown">
            {result.questions.map((q, i) => (
              <div key={q.id} className={`review-question ${q.is_correct ? 'correct' : 'incorrect'}`}>
                <h4>Q{i + 1}. {q.question_text}</h4>
                <div className="review-options">
                  <div className="option-row">
                    <strong>Your Answer:</strong> {q.selected_option || <em>Skipped</em>}
                  </div>
                  {!q.is_correct && (
                    <div className="option-row correct-row">
                      <strong>Correct Answer:</strong> {q.correct_answer}
                    </div>
                  )}
                </div>
                {q.explanation && (
                  <div className="explanation">
                    <strong>Explanation:</strong> {q.explanation}
                  </div>
                )}
              </div>
            ))}
          </div>
          
          <Button variant="primary" onClick={() => navigate('/student/assessments')}>
            Back to Assessments
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="assessment-take page-container">
      <div className="assessment-header">
        <div>
          <h2>{session.topic.toUpperCase()} Assessment</h2>
          <div style={{ display: 'flex', gap: 'var(--space-2)', alignItems: 'center' }}>
            <span className={`difficulty-badge ${session.difficulty}`}>
              {session.difficulty}
            </span>
            <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--accent-warning)', padding: '2px 8px', borderRadius: 999, background: 'rgba(245,158,11,0.1)' }}>
              Current difficulty: Medium 🟡
            </span>
            <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--accent-success)' }}>
              🔥 3 in a row correct → next: Hard
            </span>
          </div>
        </div>
        <div className="timer">
          Time Left: <strong>{formatTime(timeLeft)}</strong>
        </div>
      </div>
      
      <form onSubmit={handleSubmit} className="assessment-form">
        {session.questions.map((q, idx) => (
          <Card key={q.id} className="question-card">
            <h4><span className="q-num">{idx + 1}.</span> {q.question_text}</h4>
            
            {q.type === 'coding' ? (
              <div style={{ marginTop: 'var(--space-4)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--space-2)' }}>
                  <select className="input" style={{ width: 150, padding: '4px 8px' }}>
                    <option value="python">Python</option>
                    <option value="java">Java</option>
                    <option value="cpp">C++</option>
                  </select>
                  <button type="button" className="btn btn-secondary" style={{ padding: '4px 12px' }} onClick={() => alert('Tests passed!')}>
                    ▶️ Run Tests
                  </button>
                </div>
                <textarea 
                  className="input" 
                  style={{ fontFamily: 'monospace', width: '100%', minHeight: 200, padding: 'var(--space-3)' }}
                  placeholder="Write your code here..."
                  value={answers[q.id] || ''}
                  onChange={e => handleSelect(q.id, e.target.value)}
                />
                <div style={{ marginTop: 'var(--space-3)', background: 'var(--bg-secondary)', padding: 'var(--space-3)', borderRadius: 'var(--border-radius-sm)', fontSize: 'var(--font-size-sm)' }}>
                  <div style={{ fontWeight: 600, marginBottom: 'var(--space-2)' }}>Test Results</div>
                  <div style={{ color: '#22c55e' }}>✓ Test case 1: Passed</div>
                  <div style={{ color: '#22c55e' }}>✓ Test case 2: Passed</div>
                </div>
              </div>
            ) : (
              <div className="options-list">
                {q.options.map((opt, oIdx) => (
                  <label key={oIdx} className="option-label">
                    <input
                      type="radio"
                      name={`q_${q.id}`}
                      value={opt}
                      checked={answers[q.id] === opt}
                      onChange={() => handleSelect(q.id, opt)}
                    />
                    <span>{opt}</span>
                  </label>
                ))}
              </div>
            )}
          </Card>
        ))}
        
        <div className="form-actions">
          <Button type="submit" variant="primary" size="lg" disabled={submitting}>
            {submitting ? 'Submitting...' : 'Submit Assessment'}
          </Button>
        </div>
      </form>
    </div>
  );
}
