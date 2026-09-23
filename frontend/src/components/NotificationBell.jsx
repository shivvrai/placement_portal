import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useWebSocket } from '../../hooks/useWebSocket';
import { api } from '../../api/client';

const fetchUnreadCount = async () => {
  try {
    const res = await api.get('/notifications/unread-count');
    return res.data?.count || 0;
  } catch { return 0; }
};
const fetchNotifications = async () => {
  try {
    const res = await api.get('/notifications', { params: { page_size: 10 } });
    return res.data?.data || [];
  } catch { return []; }
};
const markAllRead = async () => {
  try { await api.post('/notifications/read-all'); } catch {}
};
const markRead = async (id) => {
  try { await api.post(`/notifications/${id}/read`); } catch {}
};

export default function NotificationBell() {
  const [count, setCount] = useState(0);
  const [notifications, setNotifications] = useState([]);
  const [open, setOpen] = useState(false);
  const [tab, setTab] = useState('All');
  const [shake, setShake] = useState(false);
  const navigate = useNavigate();
  const dropdownRef = useRef(null);

  useEffect(() => {
    fetchUnreadCount().then(setCount);
  }, []);

  useEffect(() => {
    if (open) {
      fetchNotifications().then(setNotifications);
    }
  }, [open]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [dropdownRef]);

  const onMessage = (payload) => {
    setCount(prev => prev + 1);
    setShake(true);
    setTimeout(() => setShake(false), 500);
    if (open) {
      setNotifications(prev => [{ ...payload, is_new: true }, ...prev]);
    }
  };

  useWebSocket(onMessage);

  const handleMarkAllRead = async () => {
    try {
      setCount(0);
      setNotifications(prev => prev.map(n => ({...n, is_read: true})));
      await markAllRead();
    } catch(e) {}
  };

  const handleItemClick = async (notif) => {
    if (!notif.is_read) {
        setCount(prev => Math.max(0, prev - 1));
        setNotifications(prev => prev.map(n => n.id === notif.id ? {...n, is_read: true} : n));
        await markRead(notif.id);
    }
    setOpen(false);
    if (notif.link) {
        navigate(notif.link);
    }
  };

  const filtered = tab === 'Unread' ? notifications.filter(n => !n.is_read) : notifications;

  return (
    <div className="notification-bell-wrapper" style={{ position: 'relative' }} ref={dropdownRef}>
      <button 
        style={{ background: 'none', border: 'none', cursor: 'pointer', position: 'relative', fontSize: '1.5rem', animation: shake ? 'shake 0.5s' : 'none' }} 
        onClick={() => setOpen(!open)}
      >
        🔔
        {count > 0 && (
          <span style={{
            position: 'absolute', top: '-5px', right: '-5px', background: 'red', color: 'white',
            borderRadius: '50%', padding: '2px 6px', fontSize: '0.75rem', fontWeight: 'bold'
          }}>
            {count}
          </span>
        )}
      </button>

      {open && (
        <div style={{
          position: 'absolute', top: '100%', right: '0', width: '320px', maxHeight: '480px',
          background: 'var(--bg-secondary, #fff)', border: '1px solid var(--border-color, #ccc)',
          borderRadius: '8px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)', zIndex: 1000,
          display: 'flex', flexDirection: 'column', overflow: 'hidden'
        }}>
          <div style={{ padding: '1rem', borderBottom: '1px solid var(--border-color, #eee)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', gap: '1rem' }}>
              <span style={{ cursor: 'pointer', fontWeight: tab==='All' ? 'bold': 'normal'}} onClick={() => setTab('All')}>All</span>
              <span style={{ cursor: 'pointer', fontWeight: tab==='Unread' ? 'bold': 'normal'}} onClick={() => setTab('Unread')}>Unread ({count})</span>
            </div>
            <button onClick={handleMarkAllRead} style={{ fontSize: '0.8rem', background: 'none', border: 'none', color: 'blue', cursor: 'pointer' }}>Mark all read</button>
          </div>
          
          <div style={{ overflowY: 'auto', flex: 1 }}>
            {filtered.length === 0 ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: '#888' }}>🔕 All caught up!</div>
            ) : (
              filtered.map(n => (
                <div key={n.id} onClick={() => handleItemClick(n)} style={{
                  padding: '1rem', borderBottom: '1px solid #eee', cursor: 'pointer',
                  background: n.is_read ? 'transparent' : '#f0f8ff',
                  borderLeft: `4px solid ${n.priority === 'critical' ? 'red' : n.priority === 'high' ? 'orange' : 'green'}`
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <div style={{ fontWeight: 'bold' }}>{n.type === 'APPLICATION_STATUS'? '📄': '🔔'} {n.title}</div>
                    {n.is_new && <span style={{ color: 'blue', fontSize: '0.7rem' }}>● NEW</span>}
                  </div>
                  <div style={{ fontSize: '0.85rem', color: '#555', marginTop: '0.5rem', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                    {n.message}
                  </div>
                </div>
              ))
            )}
          </div>
          <div style={{ padding: '0.5rem', textAlign: 'center', borderTop: '1px solid #eee', background: '#f9f9f9', cursor: 'pointer' }} onClick={() => { setOpen(false); navigate('/student/notifications'); }}>
            View all →
          </div>
        </div>
      )}
      <style>{`
        @keyframes shake {
          0% { transform: rotate(0deg); }
          25% { transform: rotate(15deg); }
          50% { transform: rotate(-15deg); }
          75% { transform: rotate(10deg); }
          100% { transform: rotate(0deg); }
        }
      `}</style>
    </div>
  );
}
