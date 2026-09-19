import { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { assessmentsApi, intelligenceApi } from '../../api/endpoints';
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
  const [remediationInjected, setRemediationInjected] = useState(false);
  
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
      const submissionResult = res.data;
      setResult(submissionResult);

      const scoreNormalized = submissionResult.score / 100;
      const topic = session.topic;

      if (scoreNormalized < 0.70) {
        const resources = getRemediationResources(topic, submissionResult.weak_subtopics || []);
        
        await intelligenceApi.injectRemedialTask({
            title: `Remedial Practice: ${topic} (Score: ${Math.round(scoreNormalized * 100)}%)`,
            description: `Your ${topic} assessment revealed gaps in foundational concepts. Complete these targeted resources before your next attempt.`,
            assessment_topic: topic,
            assessment_score: scoreNormalized,
            hours_estimated: scoreNormalized < 0.4 ? 8.0 : 3.0,
            resources: resources,
            source: "quiz_remediation",
        });
        
        setRemediationInjected(true);
      }
    } catch (err) {
      console.error(err);
      alert('Failed to submit assessment');
    } finally {
      setSubmitting(false);
    }
  };

  const getRemediationResources = (topic, weakSubtopics) => {
    const RESOURCE_MAP = {
        "Data Structures": [
            { title: "Stacks & Queues — Visualized", url: "https://visualgo.net/en/list", type: "tool" },
            { title: "LeetCode DS Practice Set", url: "https://leetcode.com/tag/array/", type: "practice" },
        ],
        "Algorithms": [
            { title: "Sorting Algorithms Animated", url: "https://www.sorting.at/", type: "tool" },
        ],
        "Python": [
            { title: "Python OOP Crash Course", url: "https://realpython.com/python3-object-oriented-programming/", type: "article" },
        ]
    };
    return RESOURCE_MAP[topic] || [
        { title: `${topic} — Practice Problems`, url: `https://leetcode.com/search/?q=${encodeURIComponent(topic)}`, type: "practice" }
    ];
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
            <p>{result.correct} correct out of {result.total_questions || session.questions.length}</p>
          </div>
          
          {remediationInjected && (
            <div style={{
              margin: '20px 0', padding: '16px 20px', borderRadius: 'var(--border-radius)',
              background: 'rgba(56, 189, 248, 0.1)', border: '1px solid rgba(56, 189, 248, 0.3)',
              display: 'flex', flexDirection: 'column', gap: 10
            }}>
              <div style={{ fontWeight: 600, color: 'var(--accent-primary)', fontSize: '1.05rem' }}>
                🎯 Remediation tasks added to your Career Roadmap
              </div>
              <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                We've created focused practice tasks to help you improve on <strong>{session.topic}</strong>. 
                Visit your Roadmap to start working through them.
              </div>
              <div style={{ alignSelf: 'flex-start', marginTop: 5 }}>
                <Button variant="secondary" onClick={() => navigate('/student/roadmap')}>
                  → Go to Roadmap
                </Button>
              </div>
            </div>
          )}

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
          <span className={`difficulty-badge ${session.difficulty}`}>
            {session.difficulty}
          </span>
        </div>
        <div className="timer">
          Time Left: <strong>{formatTime(timeLeft)}</strong>
        </div>
      </div>
      
      <form onSubmit={handleSubmit} className="assessment-form">
        {session.questions.map((q, idx) => (
          <Card key={q.id} className="question-card">
            <h4><span className="q-num">{idx + 1}.</span> {q.question_text}</h4>
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
