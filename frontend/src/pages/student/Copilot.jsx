/**
 * AI Career Copilot — full-height chat interface with conversation history.
 * Connects to the real Copilot API when mocks are disabled.
 */

import { useState, useRef, useEffect } from 'react';
import { copilotApi } from '../../api/endpoints';

// ─── Suggested Prompts ──────────────────────────────────────────────
const SUGGESTED_PROMPTS = [
  'What are my strongest skills based on my profile?',
  'Which companies should I target based on my skill score?',
  'Help me write a cover letter for a Data Analyst role',
  'What Python projects can I add to my resume?',
  'How do I prepare for a Google SWE interview?',
  'Explain my top skill gap and how to fix it',
  'What drives am I eligible for right now?',
  'Compare my profile to peer benchmarks',
];

// ─── Markdown-lite renderer ─────────────────────────────────────────
function MessageContent({ content }) {
  const lines = content.split('\n');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      {lines.map((line, i) => {
        if (line.startsWith('**') && line.endsWith('**')) {
          return (
            <div
              key={i}
              style={{
                fontWeight: 700,
                marginTop: i > 0 ? 8 : 0
              }}
            >
              {line.replace(/\*\*/g, '')}
            </div>
          );
        }

        const parts = line.split(/\*\*(.*?)\*\*/g);

        return (
          <div key={i} style={{ lineHeight: 1.6 }}>
            {parts.map((p, j) =>
              j % 2 === 1
                ? <strong key={j}>{p}</strong>
                : p
            )}
          </div>
        );
      })}
    </div>
  );
}

// ─── Message Bubble ─────────────────────────────────────────────────
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
          width: 32,
          height: 32,
          borderRadius: '50%',
          background: 'var(--gradient-primary)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '1rem',
          flexShrink: 0,
          marginTop: 2,
        }}>
          🤖
        </div>
      )}

      <div style={{
        maxWidth: '72%',
        padding: 'var(--space-3) var(--space-4)',
        borderRadius: isUser
          ? '16px 16px 4px 16px'
          : '16px 16px 16px 4px',
        background: isUser
          ? 'var(--accent-primary)'
          : 'var(--bg-card)',
        border: isUser
          ? 'none'
          : '1px solid var(--border-color)',
        color: isUser
          ? 'white'
          : 'var(--text-primary)',
        fontSize: 'var(--font-size-sm)',
        boxShadow: isUser
          ? '0 2px 8px rgba(99,102,241,0.3)'
          : 'var(--shadow-sm)',
      }}>
        <ScorecardRenderer content={msg.content || ''} />

        <div style={{
          fontSize: 10,
          opacity: 0.6,
          marginTop: 6,
          textAlign: isUser ? 'right' : 'left'
        }}>
          {msg.ts || ''}
        </div>
      </div>
    </div>
  );
}

// ─── Scorecard Renderer ─────────────────────────────────────────────
function ScorecardRenderer({ content }) {
  // If the content is purely a JSON block of a final scorecard, render it nicely.
  const jsonMatch = content.match(/```json\n([\s\S]*?)\n```/);
  
  if (jsonMatch) {
    let parsedData = null;
    try {
      parsedData = JSON.parse(jsonMatch[1]);
    } catch(e) {}
    
    if (parsedData && parsedData["Technical Knowledge"]) {
      return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 15, padding: 5 }}>
          <h3 style={{ margin: 0, color: 'var(--accent-primary)', fontSize: '1.1rem' }}>🏆 Interview Scorecard</h3>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            <div style={{ background: 'var(--bg-secondary)', padding: 10, borderRadius: 8 }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Technical Knowledge</div>
              <div style={{ fontWeight: 600 }}>{parsedData["Technical Knowledge"]}</div>
            </div>
            <div style={{ background: 'var(--bg-secondary)', padding: 10, borderRadius: 8 }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Communication</div>
              <div style={{ fontWeight: 600 }}>{parsedData["Communication"]}</div>
            </div>
            <div style={{ background: 'var(--bg-secondary)', padding: 10, borderRadius: 8 }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Problem Solving</div>
              <div style={{ fontWeight: 600 }}>{parsedData["Problem Solving"]}</div>
            </div>
            <div style={{ background: 'var(--bg-secondary)', padding: 10, borderRadius: 8, background: 'rgba(34,197,94,0.1)', color: '#16a34a' }}>
              <div style={{ fontSize: '0.75rem' }}>Overall Readiness</div>
              <div style={{ fontWeight: 600 }}>{parsedData["Overall Readiness"]}</div>
            </div>
          </div>
          
          <div>
            <div style={{ fontWeight: 600, color: '#16a34a', marginBottom: 4 }}>📈 Key Strengths</div>
            <ul style={{ margin: 0, paddingLeft: 20 }}>
              {parsedData["Key Strengths"]?.map((s, i) => <li key={i}>{s}</li>)}
            </ul>
          </div>
          
          <div>
            <div style={{ fontWeight: 600, color: '#d97706', marginBottom: 4 }}>🎯 Areas to Improve</div>
            <ul style={{ margin: 0, paddingLeft: 20 }}>
              {parsedData["Areas to Improve"]?.map((s, i) => <li key={i}>{s}</li>)}
            </ul>
          </div>
          
          <div style={{ marginTop: 5 }}>
            <div style={{ fontWeight: 600, marginBottom: 4 }}>📚 Recommended Resources</div>
            <ul style={{ margin: 0, paddingLeft: 20 }}>
              {parsedData["Recommended Resources"]?.map((s, i) => <li key={i}>{s}</li>)}
            </ul>
          </div>
        </div>
      );
    }
  }

  // Fallback to markdown renderer
  return <MessageContent content={content} />;
}

// ─── Typing Indicator ───────────────────────────────────────────────
function TypingIndicator() {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: 'var(--space-3)',
      marginBottom: 'var(--space-4)'
    }}>
      <div style={{
        width: 32,
        height: 32,
        borderRadius: '50%',
        background: 'var(--gradient-primary)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexShrink: 0,
      }}>
        🤖
      </div>

      <div style={{
        padding: 'var(--space-3) var(--space-4)',
        background: 'var(--bg-card)',
        border: '1px solid var(--border-color)',
        borderRadius: '16px 16px 16px 4px',
        display: 'flex',
        gap: 5,
        alignItems: 'center',
      }}>
        {[0, 1, 2].map(i => (
          <div
            key={i}
            style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              background: 'var(--accent-primary)',
              animation: `bounce 1.2s ${i * 0.2}s ease-in-out infinite`,
            }}
          />
        ))}
      </div>

      <style>{`
        @keyframes bounce {
          0%, 100% {
            transform: translateY(0);
            opacity: 0.4;
          }
          50% {
            transform: translateY(-6px);
            opacity: 1;
          }
        }
      `}</style>
    </div>
  );
}

// ─── Main ───────────────────────────────────────────────────────────
export default function Copilot() {
  const [conversations, setConversations] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [input, setInput] = useState('');
  const [typing, setTyping] = useState(false);
  const [loading, setLoading] = useState(true);
  const [mode, setMode] = useState('qa'); // 'qa' | 'mock'
  
  // Mock Interview Setup State
  const [miRole, setMiRole] = useState('Software Engineer');
  const [miDifficulty, setMiDifficulty] = useState('Junior SDE');
  const [miQuestions, setMiQuestions] = useState(4);

  // V3: Suggestions & Context Inspector
  const [suggestions, setSuggestions] = useState([]);
  const [contextData, setContextData] = useState(null);
  const [showContext, setShowContext] = useState(false);

  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  const activeConv = conversations.find(
    c => c.id === activeId
  );

  useEffect(() => {
    bottomRef.current?.scrollIntoView({
      behavior: 'smooth'
    });
  }, [activeConv?.messages, typing]);

  const now = () =>
    new Date().toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    });

  // ─── Load conversations ───────────────────────────────────────────
  useEffect(() => {
    const loadConversations = async () => {
      try {
        const response = await copilotApi.getConversations();
        const data = response.data || [];

        setConversations(data);

        if (data.length > 0) {
          setActiveId(data[0].id);
        }
      } catch (error) {
        console.error('Failed to load conversations:', error);
      } finally {
        setLoading(false);
      }
    };

    loadConversations();
  }, []);

  // ─── V3: Load proactive suggestions ───────────────────────────────
  useEffect(() => {
    copilotApi.getSuggestions()
      .then(res => setSuggestions(res.data || []))
      .catch(() => {});
  }, []);

  // ─── V3: Load context inspector ───────────────────────────────────
  const loadContext = async () => {
    if (contextData) { setShowContext(!showContext); return; }
    try {
      // Use any conversation ID to get context (it's student-level)
      const convId = activeId || 'any';
      const res = await copilotApi.getContext(convId);
      setContextData(res.data);
      setShowContext(true);
    } catch {
      setShowContext(false);
    }
  };

  // ─── Load conversation history ───────────────────────────────────
  const loadHistory = async (conversationId) => {
    try {
      const response =
        await copilotApi.getHistory(conversationId);

      const conversation = response.data;

      setConversations(prev =>
        prev.map(c =>
          c.id === conversationId
            ? {
                ...c,
                ...conversation,
                messages: conversation.messages || []
              }
            : c
        )
      );
    } catch (error) {
      console.error('Failed to load conversation history:', error);
    }
  };

  // ─── Select conversation ─────────────────────────────────────────
  const handleSelectConversation = (conversationId) => {
    setActiveId(conversationId);
    loadHistory(conversationId);
  };

  // ─── Send message ────────────────────────────────────────────────
  const sendMessage = async (text) => {
    if (!text.trim() || typing) return;

    let conversationId = activeId;

    try {
      // Create a conversation if none exists
      if (!conversationId) {
        const response =
          await copilotApi.createConversation();

        const newConversation = response.data;

        conversationId = newConversation.id;

        setConversations(prev => [
          newConversation,
          ...prev
        ]);

        setActiveId(conversationId);
      }

      const userText = text.trim();

      const userMsg = {
        role: 'user',
        content: userText,
        ts: now()
      };

      setConversations(prev =>
        prev.map(c =>
          c.id === conversationId
            ? {
                ...c,
                messages: [
                  ...(c.messages || []),
                  userMsg
                ]
              }
            : c
        )
      );

      setInput('');
      setTyping(true);

      // Add assistant placeholder
      const tempReply = {
        role: 'assistant',
        content: '',
        ts: now()
      };

      setConversations(prev =>
        prev.map(c =>
          c.id === conversationId
            ? {
                ...c,
                messages: [
                  ...(c.messages || []),
                  tempReply
                ]
              }
            : c
        )
      );

      const token = localStorage.getItem('token');
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      
      const isMockInterview = activeConv?.messages?.[0]?.mock_interview;
      
      const endpointDetails = isMockInterview
        ? {
            url: `${baseUrl}/api/v1/copilot/mock-interview/${conversationId}/respond`,
            body: { content: userText }
          }
        : {
            url: `${baseUrl}/api/v1/copilot/conversations/${conversationId}/messages`,
            body: { content: userText } // Fast API schema looks for content too
          };

      const response = await fetch(endpointDetails.url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(endpointDetails.body)
      });

      if (!response.ok) {
        throw new Error('API Error');
      }

      setTyping(false);

      // Handle streaming response
      const reader = response.body?.getReader();

      if (!reader) {
        const data = await response.json();

        const content =
          data.content ||
          data.message ||
          '';

        setConversations(prev =>
          prev.map(c => {
            if (c.id !== conversationId) return c;

            const messages = [...(c.messages || [])];

            messages[messages.length - 1] = {
              ...messages[messages.length - 1],
              content
            };

            return {
              ...c,
              messages
            };
          })
        );

        return;
      }

      const decoder = new TextDecoder();
      let fullText = '';

      while (true) {
        const { value, done } = await reader.read();

        if (done) break;

        const chunk = decoder.decode(value, {
          stream: true
        });

        fullText += chunk;

        setConversations(prev =>
          prev.map(c => {
            if (c.id !== conversationId) return c;

            const messages = [...(c.messages || [])];

            messages[messages.length - 1] = {
              ...messages[messages.length - 1],
              content: fullText
            };

            return {
              ...c,
              messages
            };
          })
        );
      }
    } catch (error) {
      console.error(error);
      setTyping(false);

      setConversations(prev =>
        prev.map(c => {
          if (c.id !== conversationId) return c;

          const messages = [...(c.messages || [])];

          if (messages.length > 0) {
            messages[messages.length - 1] = {
              role: 'assistant',
              content:
                '**Error**: Could not connect to AI Copilot.',
              ts: now()
            };
          }

          return {
            ...c,
            messages
          };
        })
      );
    } finally {
      if (activeConv?.messages?.[0]?.mock_interview) {
        // Scroll once more for scorecard expansion
        setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 500); 
      }
      setTyping(false);
    }
  };

  const startMockInterview = async () => {
    try {
      setTyping(true);
      const token = localStorage.getItem('token');
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      
      const payload = {
        role: miRole,
        difficulty: miDifficulty,
        total_questions: miQuestions
      };
      
      const response = await fetch(`${baseUrl}/api/v1/copilot/mock-interview/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });
      
      if (!response.ok) throw new Error("Failed to start mock interview");
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullText = '';
      let isFirstChunk = true;
      let newConvId = activeId;
      
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        let chunk = decoder.decode(value, { stream: true });
        
        if (isFirstChunk && chunk.includes(':::CONV_ID:')) {
            const parts = chunk.split(':::');
            newConvId = parts[1].replace('CONV_ID:', '').trim();
            chunk = parts[2] || '';
            isFirstChunk = false;
            
            // Push an empty shell conversation temporarily
            const newConv = {
                id: newConvId,
                title: `[Mock Interview] ${miRole}`,
                messages: [
                    { role: 'system', content: 'Interview Config', mock_interview: payload },
                    { role: 'assistant', content: chunk, ts: now() }
                ]
            };
            setConversations(prev => [newConv, ...prev]);
            setActiveId(newConvId);
        }
        
        fullText += chunk;
        setConversations(prev =>
            prev.map(c => {
                if (c.id !== newConvId) return c;
                const m = [...c.messages];
                m[m.length - 1] = { ...m[m.length - 1], content: fullText };
                return { ...c, messages: m };
            })
        );
      }
    } catch(err) {
      console.error(err);
    } finally {
      setTyping(false);
    }
  };

  // ─── New conversation ────────────────────────────────────────────
  const newConversation = async () => {
    try {
      const response =
        await copilotApi.createConversation();

      const conversation = response.data;

      setConversations(prev => [
        conversation,
        ...prev
      ]);

      setActiveId(conversation.id);
    } catch (error) {
      console.error(
        'Failed to create conversation:',
        error
      );
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  if (loading) {
    return (
      <div>
        <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1>AI Career Copilot</h1>
            <p>Your personal AI advisor for career planning, interview prep, and skill guidance</p>
          </div>
        </div>

        <div className="page-body">
          <p>Loading conversations...</p>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      display: 'flex',
      height: 'calc(100vh - var(--header-height, 0px))',
      flexDirection: 'column'
    }}>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1>AI Career Copilot</h1>
          <p>Your personal AI advisor for career planning, interview prep, and skill guidance</p>
        </div>
        
        <div style={{ display: 'flex', background: 'var(--bg-secondary)', borderRadius: 8, padding: 4, border: '1px solid var(--border-color)' }}>
          <button 
            className={`btn ${mode === 'qa' ? 'btn-primary' : ''}`}
            onClick={() => { setMode('qa'); setActiveId(null); }}
            style={{ borderRadius: 6, fontSize: '0.8rem', padding: '6px 12px', background: mode === 'qa' ? 'var(--accent-primary)' : 'transparent', color: mode === 'qa' ? 'white' : 'var(--text-primary)' }}
          >
            💬 Career Q&A
          </button>
          <button 
            className={`btn ${mode === 'mock' ? 'btn-primary' : ''}`}
            onClick={() => { setMode('mock'); setActiveId(null); }}
            style={{ borderRadius: 6, fontSize: '0.8rem', padding: '6px 12px', background: mode === 'mock' ? 'var(--accent-primary)' : 'transparent', color: mode === 'mock' ? 'white' : 'var(--text-primary)' }}
          >
            🎯 Mock Interview
          </button>
          <button 
            onClick={loadContext}
            style={{ borderRadius: 6, fontSize: '0.8rem', padding: '6px 12px', background: showContext ? 'var(--accent-primary)' : 'transparent', color: showContext ? 'white' : 'var(--text-primary)', marginLeft: 4 }}
          >
            🔍 AI Context
          </button>
        </div>
      </div>

      {/* V3: Proactive Suggestions */}
      {suggestions.length > 0 && !activeConv?.messages?.length && (
        <div style={{ display: 'flex', gap: 10, padding: '0 var(--space-4) var(--space-3)', overflowX: 'auto' }}>
          {suggestions.map((s, i) => (
            <div key={i} style={{
              minWidth: 220, padding: '14px 16px', borderRadius: 12,
              background: 'var(--bg-card)', border: '1px solid var(--border-color)',
              cursor: 'pointer', transition: 'all 0.2s', flexShrink: 0,
            }}
              onClick={() => { if (s.action_link) window.location.href = s.action_link; }}
              onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--accent-primary)'}
              onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border-color)'}
            >
              <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>{s.title}</div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.4, marginBottom: 8 }}>{s.message}</div>
              <span style={{ fontSize: 11, color: 'var(--accent-primary)', fontWeight: 600 }}>{s.action_label} →</span>
            </div>
          ))}
        </div>
      )}

      {/* V3: Context Inspector Panel */}
      {showContext && contextData && (
        <div style={{
          padding: 'var(--space-3) var(--space-4)', background: 'var(--bg-secondary)',
          borderBottom: '1px solid var(--border-color)', maxHeight: 200, overflowY: 'auto',
        }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)', marginBottom: 8 }}>
            🧠 What the AI knows about you ({contextData.token_estimate || 0} tokens)
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {(contextData.context_items || []).map((item, i) => (
              <div key={i} style={{
                padding: '4px 10px', borderRadius: 6, background: 'var(--bg-card)',
                border: '1px solid var(--border-color)', fontSize: 11,
              }}>
                <span style={{ fontWeight: 700, color: 'var(--accent-primary)' }}>{item.category}: </span>
                <span style={{ color: 'var(--text-primary)' }}>{item.data}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div style={{
        display: 'flex',
        flex: 1,
        overflow: 'hidden'
      }}>

        {/* Sidebar: conversation history */}
        <div style={{
          width: 260,
          background: 'var(--bg-secondary)',
          borderRight: '1px solid var(--border-color)',
          display: 'flex',
          flexDirection: 'column',
          flexShrink: 0,
        }}>
          <div style={{
            padding: 'var(--space-4)'
          }}>
            <button
              className="btn btn-primary"
              style={{
                width: '100%',
                height: 36
              }}
              onClick={newConversation}
            >
              + New Chat
            </button>
          </div>

          <div style={{
            flex: 1,
            overflowY: 'auto',
            padding: '0 var(--space-2)'
          }}>
            {conversations.map(c => (
              <div
                key={c.id}
                onClick={() =>
                  handleSelectConversation(c.id)
                }
                style={{
                  padding:
                    'var(--space-3) var(--space-4)',
                  borderRadius:
                    'var(--border-radius-sm)',
                  cursor: 'pointer',
                  marginBottom: 2,
                  background:
                    c.id === activeId
                      ? 'var(--accent-primary-subtle)'
                      : 'transparent',
                  color:
                    c.id === activeId
                      ? 'var(--accent-primary)'
                      : 'var(--text-secondary)',
                  transition:
                    'all var(--transition-fast)',
                }}
              >
                <div style={{
                  fontSize: 'var(--font-size-sm)',
                  fontWeight: 500,
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis'
                }}>
                  💬 {c.title || 'Conversation'}
                </div>

                <div style={{
                  fontSize: 'var(--font-size-xs)',
                  color: 'var(--text-muted)',
                  marginTop: 2
                }}>
                  {c.created_at || ''}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Chat area */}
        <div style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden'
        }}>

          {/* Messages */}
          <div style={{
            flex: 1,
            overflowY: 'auto',
            padding: 'var(--space-6) var(--space-8)'
          }}>
            {activeConv?.messages && activeConv.messages.length > 0 ? (
              <>
                {activeConv.messages.map((msg, i) => {
                  if (msg.role === 'system') return null;
                  return <Message key={i} msg={msg} />;
                })}

                {typing && <TypingIndicator />}
                <div ref={bottomRef} />
              </>
            ) : mode === 'qa' ? (
              /* Empty state Q&A */
              <div style={{
                display: 'flex', flexDirection: 'column', alignItems: 'center',
                justifyContent: 'center', height: '100%', gap: 'var(--space-6)'
              }}>
                <div style={{ fontSize: '3rem' }}>🤖</div>
                <div style={{ textAlign: 'center' }}>
                  <h2 style={{ fontWeight: 700, marginBottom: 'var(--space-2)' }}>How can I help you today?</h2>
                  <p style={{ color: 'var(--text-muted)', fontSize: 'var(--font-size-sm)' }}>
                    Ask me anything about your career, skills, or placement preparation.
                  </p>
                </div>

                <div style={{
                  display: 'grid', gridTemplateColumns: '1fr 1fr',
                  gap: 'var(--space-3)', width: '100%', maxWidth: 600
                }}>
                  {SUGGESTED_PROMPTS.map(p => (
                    <button
                      key={p} onClick={() => sendMessage(p)}
                      style={{
                        padding: 'var(--space-3) var(--space-4)', background: 'var(--bg-card)',
                        border: '1px solid var(--border-color)', borderRadius: 'var(--border-radius)',
                        cursor: 'pointer', fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)',
                        textAlign: 'left', transition: 'all var(--transition-fast)', lineHeight: 1.4,
                      }}
                      onMouseOver={e => {
                        e.currentTarget.style.background = 'var(--bg-card-hover)';
                        e.currentTarget.style.borderColor = 'var(--accent-primary)';
                        e.currentTarget.style.color = 'var(--text-primary)';
                      }}
                      onMouseOut={e => {
                        e.currentTarget.style.background = 'var(--bg-card)';
                        e.currentTarget.style.borderColor = 'var(--border-color)';
                        e.currentTarget.style.color = 'var(--text-secondary)';
                      }}
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              /* Empty state Mock Interview Setup */
              <div style={{
                display: 'flex', flexDirection: 'column',
                justifyContent: 'center', height: '100%', gap: 'var(--space-6)', maxWidth: 600, margin: '0 auto'
              }}>
                <div style={{ textAlign: 'left', borderBottom: '1px solid var(--border-color)', paddingBottom: 15 }}>
                  <h2 style={{ fontWeight: 700 }}>🎯 Setup Mock Interview</h2>
                  <p style={{ color: 'var(--text-muted)' }}>Configure your automated technical interview session.</p>
                </div>
                
                <div className="form-group">
                  <label>Target Role</label>
                  <input type="text" className="form-control" value={miRole} onChange={e => setMiRole(e.target.value)} placeholder="e.g. Data Analyst, MLE" />
                </div>
                
                <div className="form-group">
                  <label>Difficulty</label>
                  <select className="form-control" value={miDifficulty} onChange={e => setMiDifficulty(e.target.value)}>
                    <option value="Intern">Intern</option>
                    <option value="Junior SDE">Junior SDE</option>
                    <option value="Mid-Level SDE">Mid-Level SDE</option>
                  </select>
                </div>
                
                <div className="form-group">
                  <label>Questions: {miQuestions}</label>
                  <input type="range" min="3" max="6" value={miQuestions} onChange={e => setMiQuestions(Number(e.target.value))} style={{ width: '100%' }} />
                </div>
                
                <button 
                  className="btn btn-primary" 
                  disabled={typing}
                  style={{ width: '100%', padding: 12, fontSize: '1rem', marginTop: 10 }}
                  onClick={startMockInterview}
                >
                  🚀 Begin Mock Interview
                </button>
              </div>
            )}
          </div>

          {/* Input bar */}
          {(activeConv || mode === 'qa') && (
            <div style={{
              padding: 'var(--space-4) var(--space-6)',
              borderTop: '1px solid var(--border-color)',
              background: 'var(--bg-secondary)',
            }}>
              <div style={{
                display: 'flex',
                gap: 'var(--space-3)',
                alignItems: 'flex-end'
              }}>
              <textarea
                ref={inputRef}
                value={input}
                onChange={e =>
                  setInput(e.target.value)
                }
                onKeyDown={handleKeyDown}
                placeholder="Ask about your career, skills, or interview prep... (Enter to send)"
                rows={1}
                style={{
                  flex: 1,
                  padding:
                    'var(--space-3) var(--space-4)',
                  background:
                    'var(--bg-input)',
                  border:
                    '1px solid var(--border-color)',
                  borderRadius:
                    'var(--border-radius)',
                  color:
                    'var(--text-primary)',
                  fontFamily:
                    'var(--font-family)',
                  fontSize:
                    'var(--font-size-sm)',
                  resize: 'none',
                  lineHeight: 1.5,
                  outline: 'none',
                  transition:
                    'border-color var(--transition-fast)',
                }}
                onFocus={e =>
                  e.target.style.borderColor =
                    'var(--accent-primary)'
                }
                onBlur={e =>
                  e.target.style.borderColor =
                    'var(--border-color)'
                }
              />

              <button
                className="btn btn-primary"
                disabled={!input.trim() || typing}
                onClick={() => sendMessage(input)}
                style={{
                  height: 44,
                  width: 44,
                  padding: 0,
                  flexShrink: 0,
                  fontSize: '1.2rem'
                }}
              >
                ↑
              </button>
            </div>

            <div style={{
              fontSize: 10,
              color: 'var(--text-muted)',
              marginTop: 'var(--space-2)',
              paddingLeft: 4
            }}>
              Shift+Enter for new line · Enter to send · Powered by Gemini
            </div>
          </div>
          )}
        </div>
      </div>
    </div>
  );
}