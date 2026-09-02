/**
 * AI Career Copilot — full-height chat interface with conversation history.
 * Sends mock responses. Ready to wire to copilotApi when backend is live.
 */

import { useState, useRef, useEffect } from 'react';

// ─── Mock Data ────────────────────────────────────────────────────
const INITIAL_CONVERSATIONS = [
  {
    id: 'c1', title: 'Resume review for Data Analyst',
    created_at: '2026-08-29',
    messages: [
      { role: 'user', content: 'Can you review my resume for a Data Analyst role?', ts: '09:12' },
      { role: 'assistant', content: 'I\'ve analyzed your profile. Your resume is strong in Python and SQL, but you should add 2–3 data projects with measurable outcomes. Also include any Kaggle or Tableau Public links. Shall I suggest specific project ideas based on your skill gaps?', ts: '09:12' },
      { role: 'user', content: 'Yes, suggest some projects.', ts: '09:13' },
      { role: 'assistant', content: 'Based on your current skill set, here are 3 project ideas:\n\n**1. Sales Dashboard (Tableau + SQL)**\nAnalyse a public retail dataset. Build an interactive Tableau dashboard. Estimated time: 2 weeks.\n\n**2. Customer Churn Prediction (Python + scikit-learn)**\nUse the Telco Customer Churn dataset on Kaggle. Target 80%+ AUC. Estimated time: 3 weeks.\n\n**3. SQL Case Study (StrataScratch)**\nSolve 20 medium/hard SQL problems. Document solutions on GitHub. Estimated time: 1 week.\n\nWant me to create a roadmap for any of these?', ts: '09:13' },
    ],
  },
  {
    id: 'c2', title: 'Interview prep for Amazon',
    created_at: '2026-08-27',
    messages: [
      { role: 'user', content: 'I have an interview at Amazon for Data Engineer. What should I prepare?', ts: '14:30' },
      { role: 'assistant', content: 'For Amazon Data Engineer, focus on:\n\n**Technical:** Python (advanced), SQL (window functions, CTEs), Apache Spark, AWS services (S3, Glue, Redshift), System Design for data systems.\n\n**Behavioural:** Amazon uses Leadership Principles. Prepare STAR format stories for: "Customer Obsession", "Dive Deep", "Deliver Results".\n\nYour current gap: Spark and AWS. I recommend 2–3 hours on Spark basics before the interview. Want me to create a 1-week prep plan?', ts: '14:30' },
    ],
  },
];

const SUGGESTED_PROMPTS = [
  'What are my strongest skills based on my profile?',
  'Which companies should I target based on my skill score?',
  'Help me write a cover letter for a Data Analyst role',
  'What Python projects can I add to my resume?',
  'How do I prepare for a Google SWE interview?',
  'Explain my top skill gap and how to fix it',
];

const MOCK_RESPONSES = [
  'Based on your profile, I recommend focusing on strengthening your Statistics fundamentals — it\'s the largest gap for most analytics roles. Start with Khan Academy Statistics this week.',
  'Your Python skills are solid at 75/100. To reach the 85+ level required by top companies, practice pandas data manipulation problems on StrataScratch for 1 hour/day.',
  'For your target role, the most in-demand skills right now are: SQL (window functions), Python (pandas/numpy), and data visualisation. Your roadmap already covers these.',
  'I\'ve identified 3 upcoming placement drives that match your profile well: Google (84% match), Freshworks (79% match), and Infosys (91% match). Apply to all three before the deadlines.',
  'Great question! Here\'s a study plan for this week:\n\n**Monday–Tuesday:** SQL joins and window functions (4h)\n**Wednesday–Thursday:** Python pandas — GroupBy, merge, pivot (4h)\n**Friday:** Mock interview on Pramp (2h)\n**Weekend:** Build a mini project combining SQL + Python (6h)',
];

let responseIdx = 0;
const getMockResponse = () => {
  const r = MOCK_RESPONSES[responseIdx % MOCK_RESPONSES.length];
  responseIdx++;
  return r;
};

// ─── Markdown-lite renderer ────────────────────────────────────────
function MessageContent({ content }) {
  const lines = content.split('\n');
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      {lines.map((line, i) => {
        if (line.startsWith('**') && line.endsWith('**')) {
          return <div key={i} style={{ fontWeight: 700, marginTop: i > 0 ? 8 : 0 }}>{line.replace(/\*\*/g, '')}</div>;
        }
        const parts = line.split(/\*\*(.*?)\*\*/g);
        return (
          <div key={i} style={{ lineHeight: 1.6 }}>
            {parts.map((p, j) => j % 2 === 1 ? <strong key={j}>{p}</strong> : p)}
          </div>
        );
      })}
    </div>
  );
}

// ─── Message Bubble ────────────────────────────────────────────────
function Message({ msg }) {
  const isUser = msg.role === 'user';
  return (
    <div style={{
      display: 'flex',
      justifyContent: isUser ? 'flex-end' : 'flex-start',
      gap: 'var(--space-3)',
      marginBottom: 'var(--space-4)',
    }}>
      {!isUser && (
        <div style={{
          width: 32, height: 32, borderRadius: '50%',
          background: 'var(--gradient-primary)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '1rem', flexShrink: 0, marginTop: 2,
        }}>
          🤖
        </div>
      )}
      <div style={{
        maxWidth: '72%',
        padding: 'var(--space-3) var(--space-4)',
        borderRadius: isUser ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
        background: isUser ? 'var(--accent-primary)' : 'var(--bg-card)',
        border: isUser ? 'none' : '1px solid var(--border-color)',
        color: isUser ? 'white' : 'var(--text-primary)',
        fontSize: 'var(--font-size-sm)',
        boxShadow: isUser ? '0 2px 8px rgba(99,102,241,0.3)' : 'var(--shadow-sm)',
      }}>
        <MessageContent content={msg.content} />
        <div style={{ fontSize: 10, opacity: 0.6, marginTop: 6, textAlign: isUser ? 'right' : 'left' }}>
          {msg.ts}
        </div>
      </div>
    </div>
  );
}

// ─── Typing Indicator ──────────────────────────────────────────────
function TypingIndicator() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', marginBottom: 'var(--space-4)' }}>
      <div style={{
        width: 32, height: 32, borderRadius: '50%', background: 'var(--gradient-primary)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
      }}>🤖</div>
      <div style={{
        padding: 'var(--space-3) var(--space-4)',
        background: 'var(--bg-card)', border: '1px solid var(--border-color)',
        borderRadius: '16px 16px 16px 4px',
        display: 'flex', gap: 5, alignItems: 'center',
      }}>
        {[0, 1, 2].map(i => (
          <div key={i} style={{
            width: 8, height: 8, borderRadius: '50%', background: 'var(--accent-primary)',
            animation: `bounce 1.2s ${i * 0.2}s ease-in-out infinite`,
          }} />
        ))}
      </div>
      <style>{`
        @keyframes bounce {
          0%, 100% { transform: translateY(0); opacity: 0.4; }
          50% { transform: translateY(-6px); opacity: 1; }
        }
      `}</style>
    </div>
  );
}

// ─── Main ─────────────────────────────────────────────────────────
export default function Copilot() {
  const [conversations, setConversations] = useState(INITIAL_CONVERSATIONS);
  const [activeId, setActiveId] = useState('c1');
  const [input, setInput] = useState('');
  const [typing, setTyping] = useState(false);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  const activeConv = conversations.find(c => c.id === activeId);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [activeConv?.messages, typing]);

  const now = () => new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: false });

  const sendMessage = async (text) => {
    if (!text.trim()) return;
    const userMsg = { role: 'user', content: text.trim(), ts: now() };

    setConversations(prev => prev.map(c =>
      c.id === activeId ? { ...c, messages: [...c.messages, userMsg] } : c
    ));
    setInput('');
    setTyping(true);

    const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true';

    if (USE_MOCKS) {
      await new Promise(r => setTimeout(r, 1000 + Math.random() * 800));
      const reply = { role: 'assistant', content: getMockResponse(), ts: now() };
      setTyping(false);
      setConversations(prev => prev.map(c =>
        c.id === activeId ? { ...c, messages: [...c.messages, reply] } : c
      ));
    } else {
      // Create empty assistant message placeholder
      const tempReply = { role: 'assistant', content: '', ts: now() };
      setConversations(prev => prev.map(c =>
        c.id === activeId ? { ...c, messages: [...c.messages, tempReply] } : c
      ));
      
      try {
        const token = localStorage.getItem('token');
        const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
        
        const response = await fetch(`${baseUrl}/api/v1/copilot/conversations/${activeId}/messages`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ content: text.trim() })
        });

        if (!response.ok) throw new Error('API Error');

        setTyping(false);
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullText = '';

        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          
          const chunk = decoder.decode(value, { stream: true });
          fullText += chunk;
          
          // Update the last message in real-time
          setConversations(prev => prev.map(c => {
            if (c.id === activeId) {
              const msgs = [...c.messages];
              msgs[msgs.length - 1] = { ...msgs[msgs.length - 1], content: fullText };
              return { ...c, messages: msgs };
            }
            return c;
          }));
        }
      } catch (err) {
        console.error(err);
        setTyping(false);
        const errorReply = { role: 'assistant', content: '**Error**: Could not connect to AI Copilot.', ts: now() };
        setConversations(prev => prev.map(c => {
          if (c.id === activeId) {
            const msgs = [...c.messages];
            msgs[msgs.length - 1] = errorReply;
            return { ...c, messages: msgs };
          }
          return c;
        }));
      }
    }
  };

  const newConversation = () => {
    const id = `c${Date.now()}`;
    const conv = { id, title: 'New conversation', created_at: new Date().toISOString().slice(0, 10), messages: [] };
    setConversations(prev => [conv, ...prev]);
    setActiveId(id);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - var(--header-height, 0px))', flexDirection: 'column' }}>
      <div className="page-header">
        <h1>AI Career Copilot</h1>
        <p>Your personal AI advisor for career planning, interview prep, and skill guidance</p>
      </div>

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>

        {/* Sidebar: conversation history */}
        <div style={{
          width: 260, background: 'var(--bg-secondary)',
          borderRight: '1px solid var(--border-color)',
          display: 'flex', flexDirection: 'column',
          flexShrink: 0,
        }}>
          <div style={{ padding: 'var(--space-4)' }}>
            <button className="btn btn-primary" style={{ width: '100%', height: 36 }} onClick={newConversation}>
              + New Chat
            </button>
          </div>
          <div style={{ flex: 1, overflowY: 'auto', padding: '0 var(--space-2)' }}>
            {conversations.map(c => (
              <div
                key={c.id}
                onClick={() => setActiveId(c.id)}
                style={{
                  padding: 'var(--space-3) var(--space-4)',
                  borderRadius: 'var(--border-radius-sm)',
                  cursor: 'pointer',
                  marginBottom: 2,
                  background: c.id === activeId ? 'var(--accent-primary-subtle)' : 'transparent',
                  color: c.id === activeId ? 'var(--accent-primary)' : 'var(--text-secondary)',
                  transition: 'all var(--transition-fast)',
                }}
              >
                <div style={{ fontSize: 'var(--font-size-sm)', fontWeight: 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  💬 {c.title}
                </div>
                <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginTop: 2 }}>
                  {c.created_at}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Chat area */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>

          {/* Messages */}
          <div style={{ flex: 1, overflowY: 'auto', padding: 'var(--space-6) var(--space-8)' }}>
            {activeConv?.messages.length === 0 ? (
              /* Empty state */
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: 'var(--space-6)' }}>
                <div style={{ fontSize: '3rem' }}>🤖</div>
                <div style={{ textAlign: 'center' }}>
                  <h2 style={{ fontWeight: 700, marginBottom: 'var(--space-2)' }}>How can I help you today?</h2>
                  <p style={{ color: 'var(--text-muted)', fontSize: 'var(--font-size-sm)' }}>
                    Ask me anything about your career, skills, or placement preparation.
                  </p>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3)', width: '100%', maxWidth: 600 }}>
                  {SUGGESTED_PROMPTS.map(p => (
                    <button
                      key={p}
                      onClick={() => sendMessage(p)}
                      style={{
                        padding: 'var(--space-3) var(--space-4)',
                        background: 'var(--bg-card)', border: '1px solid var(--border-color)',
                        borderRadius: 'var(--border-radius)', cursor: 'pointer',
                        fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)',
                        textAlign: 'left', transition: 'all var(--transition-fast)',
                        lineHeight: 1.4,
                      }}
                      onMouseOver={e => { e.currentTarget.style.background = 'var(--bg-card-hover)'; e.currentTarget.style.borderColor = 'var(--accent-primary)'; e.currentTarget.style.color = 'var(--text-primary)'; }}
                      onMouseOut={e => { e.currentTarget.style.background = 'var(--bg-card)'; e.currentTarget.style.borderColor = 'var(--border-color)'; e.currentTarget.style.color = 'var(--text-secondary)'; }}
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <>
                {activeConv.messages.map((msg, i) => <Message key={i} msg={msg} />)}
                {typing && <TypingIndicator />}
                <div ref={bottomRef} />
              </>
            )}
          </div>

          {/* Input bar */}
          <div style={{
            padding: 'var(--space-4) var(--space-6)',
            borderTop: '1px solid var(--border-color)',
            background: 'var(--bg-secondary)',
          }}>
            <div style={{ display: 'flex', gap: 'var(--space-3)', alignItems: 'flex-end' }}>
              <textarea
                ref={inputRef}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about your career, skills, or interview prep... (Enter to send)"
                rows={1}
                style={{
                  flex: 1, padding: 'var(--space-3) var(--space-4)',
                  background: 'var(--bg-input)', border: '1px solid var(--border-color)',
                  borderRadius: 'var(--border-radius)',
                  color: 'var(--text-primary)', fontFamily: 'var(--font-family)',
                  fontSize: 'var(--font-size-sm)', resize: 'none',
                  lineHeight: 1.5, outline: 'none',
                  transition: 'border-color var(--transition-fast)',
                }}
                onFocus={e => e.target.style.borderColor = 'var(--accent-primary)'}
                onBlur={e => e.target.style.borderColor = 'var(--border-color)'}
              />
              <button
                className="btn btn-primary"
                disabled={!input.trim() || typing}
                onClick={() => sendMessage(input)}
                style={{ height: 44, width: 44, padding: 0, flexShrink: 0, fontSize: '1.2rem' }}
              >
                ↑
              </button>
            </div>
            <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 'var(--space-2)', paddingLeft: 4 }}>
              Shift+Enter for new line · Enter to send · Powered by Gemini
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
