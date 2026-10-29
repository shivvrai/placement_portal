/**
 * Global In-App Notification Center (Bell Dropdown).
 * Supports Real-time WebSockets, toast notifications, priority styling, filtering, and deep-linking.
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';

function formatTimeAgo(isoString) {
  if (!isoString) return '';
  const now = new Date();
  const date = new Date(isoString);
  const diffSec = Math.floor((now - date) / 1000);

  if (diffSec < 60) return 'Just now';
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHours = Math.floor(diffMin / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
}

export default function NotificationBell() {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [activeTab, setActiveTab] = useState('All');
  const [shake, setShake] = useState(false);
  const [loading, setLoading] = useState(false);
  const [toasts, setToasts] = useState([]);
  const dropdownRef = useRef(null);
  const navigate = useNavigate();

  const removeToast = (id) => {
    setToasts((prev) => prev.filter((t) => t.toastId !== id));
  };

  const fetchUnreadCount = async () => {
    try {
      const res = await api.get('/notifications/unread-count');
      if (typeof res.data?.count === 'number') {
        setUnreadCount(res.data.count);
      }
    } catch {
      // Fallback
      try {
        const res = await api.get('/notifications/mine', { params: { limit: 1 } });
        if (typeof res.data?.unread_count === 'number') {
          setUnreadCount(res.data.unread_count);
        }
      } catch {}
    }
  };

  const fetchNotifications = async () => {
    setLoading(true);
    try {
      const res = await api.get('/notifications', { params: { page_size: 15 } });
      if (res.data?.data) {
        setNotifications(res.data.data);
      } else {
        // Fallback to /notifications/mine
        const resMine = await api.get('/notifications/mine', { params: { limit: 15 } });
        setNotifications(resMine.data?.items || []);
        if (typeof resMine.data?.unread_count === 'number') {
          setUnreadCount(resMine.data.unread_count);
        }
      }
    } catch {
      try {
        const resMine = await api.get('/notifications/mine', { params: { limit: 15 } });
        setNotifications(resMine.data?.items || []);
      } catch (e) {
        console.error('Failed to load notifications:', e);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUnreadCount();
    const interval = setInterval(fetchUnreadCount, 60000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (isOpen) {
      fetchNotifications();
    }
  }, [isOpen]);

  // Click outside to close
  useEffect(() => {
    function handleClickOutside(e) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    }
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  // WebSocket message receiver
  const onWebSocketMessage = useCallback((payload) => {
    setUnreadCount((prev) => prev + 1);
    setShake(true);
    setTimeout(() => setShake(false), 600);
    setNotifications((prev) => [{ ...payload, is_new: true, is_read: false }, ...prev]);

    const toastId = Date.now() + Math.random();
    const newToast = { ...payload, toastId };
    setToasts((prev) => [newToast, ...prev].slice(0, 3));
    setTimeout(() => {
      removeToast(toastId);
    }, 5000);
  }, []);


  const handleMarkRead = async (notif) => {
    try {
      if (!notif.is_read) {
        setNotifications((prev) =>
          prev.map((n) => (n.id === notif.id ? { ...n, is_read: true } : n))
        );
        setUnreadCount((prev) => Math.max(0, prev - 1));
        await api.post(`/notifications/${notif.id}/read`).catch(() =>
          api.patch(`/notifications/${notif.id}/read`)
        );
      }
      if (notif.link) {
        setIsOpen(false);
        navigate(notif.link);
      }
    } catch (err) {
      console.error('Failed to mark read:', err);
      if (notif.link) {
        setIsOpen(false);
        navigate(notif.link);
      }
    }
  };

  const handleMarkAllRead = async () => {
    try {
      setUnreadCount(0);
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      await api.post('/notifications/read-all').catch(() =>
        api.patch('/notifications/read-all')
      );
    } catch (err) {
      console.error('Failed to mark all read:', err);
    }
  };

  const displayedNotifications =
    activeTab === 'Unread'
      ? notifications.filter((n) => !n.is_read)
      : notifications;

  return (
    <div
      ref={dropdownRef}
      className="notification-bell-wrapper"
      style={{ position: 'relative', display: 'inline-block' }}
    >
      <button
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Notifications"
        style={{
          background: isOpen ? 'var(--accent-primary-subtle, rgba(99,102,241,0.12))' : 'var(--bg-tertiary, #1f2937)',
          border: '1px solid var(--border-color, #374151)',
          borderRadius: '50%',
          width: 40,
          height: 40,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          position: 'relative',
          transition: 'all 0.2s ease',
          animation: shake ? 'bellShake 0.5s ease' : 'none',
        }}
      >
        <span style={{ fontSize: '1.2rem', lineHeight: 1 }}>🔔</span>

        {unreadCount > 0 && (
          <span
            style={{
              position: 'absolute',
              top: -3,
              right: -3,
              background: '#ef4444',
              color: '#ffffff',
              fontSize: '0.7rem',
              fontWeight: 700,
              minWidth: 18,
              height: 18,
              borderRadius: 9,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '0 4px',
              boxShadow: '0 0 8px rgba(239, 68, 68, 0.6)',
            }}
          >
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div
          style={{
            position: 'absolute',
            top: 48,
            right: 0,
            width: 360,
            maxWidth: '90vw',
            background: 'var(--bg-secondary, #111827)',
            border: '1px solid var(--border-color, #374151)',
            borderRadius: '12px',
            boxShadow: '0 12px 32px rgba(0,0,0,0.4)',
            zIndex: 1000,
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {/* Header */}
          <div
            style={{
              padding: '12px 16px',
              borderBottom: '1px solid var(--border-color, #374151)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              background: 'var(--bg-primary, #0f172a)',
            }}
          >
            <div style={{ display: 'flex', gap: 8 }}>
              {['All', 'Unread'].map((tab) => (
                <button
                  key={tab}
                  type="button"
                  onClick={() => setActiveTab(tab)}
                  style={{
                    background: activeTab === tab ? 'var(--accent-primary, #6366f1)' : 'transparent',
                    color: activeTab === tab ? '#ffffff' : 'var(--text-secondary, #9ca3af)',
                    border: 'none',
                    borderRadius: '6px',
                    padding: '4px 10px',
                    fontSize: '0.78rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  {tab === 'Unread' ? `Unread (${unreadCount})` : 'All'}
                </button>
              ))}
            </div>

            {unreadCount > 0 && (
              <button
                type="button"
                onClick={handleMarkAllRead}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--accent-primary, #6366f1)',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  padding: '2px 6px',
                }}
              >
                Mark all read
              </button>
            )}
          </div>

          {/* List */}
          <div style={{ maxHeight: 380, overflowY: 'auto' }}>
            {loading ? (
              <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted, #9ca3af)', fontSize: '0.85rem' }}>
                Loading...
              </div>
            ) : displayedNotifications.length === 0 ? (
              <div style={{ padding: '32px 16px', textAlign: 'center', color: 'var(--text-muted, #9ca3af)', fontSize: '0.85rem' }}>
                🔕 All caught up! No notifications.
              </div>
            ) : (
              displayedNotifications.map((n) => {
                const isCritical = n.priority === 'critical';
                const isHigh = n.priority === 'high';
                const borderLeftColor = isCritical ? '#ef4444' : isHigh ? '#f59e0b' : '#10b981';

                return (
                  <div
                    key={n.id}
                    onClick={() => handleMarkRead(n)}
                    style={{
                      padding: '12px 14px',
                      borderBottom: '1px solid var(--border-color, #1f2937)',
                      borderLeft: `4px solid ${borderLeftColor}`,
                      background: n.is_read ? 'transparent' : 'rgba(99, 102, 241, 0.06)',
                      cursor: 'pointer',
                      transition: 'background 0.15s ease',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = 'rgba(255,255,255,0.04)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = n.is_read
                        ? 'transparent'
                        : 'rgba(99, 102, 241, 0.06)';
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        marginBottom: 4,
                      }}
                    >
                      <div
                        style={{
                          fontWeight: n.is_read ? 500 : 700,
                          fontSize: '0.85rem',
                          color: 'var(--text-primary, #f9fafb)',
                          display: 'flex',
                          alignItems: 'center',
                          gap: 6,
                        }}
                      >
                        {n.type === 'APPLICATION_STATUS' ? '📄' : n.type === 'OFFER_RECEIVED' ? '🏆' : '🔔'}
                        <span>{n.title}</span>
                      </div>
                      {n.is_new && (
                        <span
                          style={{
                            color: '#60a5fa',
                            fontSize: '0.68rem',
                            fontWeight: 700,
                            letterSpacing: '0.04em',
                          }}
                        >
                          ● NEW
                        </span>
                      )}
                    </div>
                    <div
                      style={{
                        fontSize: '0.8rem',
                        color: 'var(--text-secondary, #d1d5db)',
                        lineHeight: 1.35,
                        display: '-webkit-box',
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: 'vertical',
                        overflow: 'hidden',
                      }}
                    >
                      {n.message}
                    </div>
                    <div
                      style={{
                        fontSize: '0.72rem',
                        color: 'var(--text-muted, #9ca3af)',
                        marginTop: 5,
                      }}
                    >
                      {formatTimeAgo(n.created_at)}
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* Footer View All */}
          <div
            onClick={() => {
              setIsOpen(false);
              navigate('/student/notifications');
            }}
            style={{
              padding: '10px',
              textAlign: 'center',
              borderTop: '1px solid var(--border-color, #374151)',
              background: 'var(--bg-primary, #0f172a)',
              color: 'var(--accent-primary, #6366f1)',
              fontSize: '0.82rem',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'background 0.15s ease',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'rgba(255,255,255,0.04)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'var(--bg-primary, #0f172a)';
            }}
          >
            View all notifications →
          </div>
        </div>
      )}

      {/* Toast Popups */}
      {toasts.length > 0 && (
        <div
          style={{
            position: 'fixed',
            bottom: '24px',
            right: '24px',
            zIndex: 9999,
            display: 'flex',
            flexDirection: 'column',
            gap: '10px',
            maxWidth: '360px',
          }}
        >
          {toasts.map((toast) => (
            <div
              key={toast.toastId}
              onClick={() => {
                handleMarkRead(toast);
                removeToast(toast.toastId);
              }}
              style={{
                background: '#1e293b',
                color: '#f1f5f9',
                border: '1px solid #334155',
                borderLeft: `5px solid ${toast.priority === 'critical' ? '#ef4444' : toast.priority === 'high' ? '#f59e0b' : '#10b981'}`,
                borderRadius: '8px',
                padding: '12px 16px',
                boxShadow: '0 8px 20px rgba(0,0,0,0.3)',
                cursor: 'pointer',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
                animation: 'slideIn 0.3s ease-out',
              }}
            >
              <div style={{ flex: 1, paddingRight: '8px' }}>
                <div style={{ fontWeight: 700, fontSize: '0.9rem', marginBottom: '4px' }}>
                  {toast.type === 'APPLICATION_STATUS' ? '📄' : toast.type === 'OFFER_RECEIVED' ? '🏆' : '🔔'} {toast.title}
                </div>
                <div style={{ fontSize: '0.8rem', color: '#94a3b8', lineHeight: 1.4 }}>
                  {toast.message}
                </div>
              </div>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  removeToast(toast.toastId);
                }}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#94a3b8',
                  cursor: 'pointer',
                  fontSize: '1rem',
                  lineHeight: 1,
                  padding: 0,
                }}
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}

      <style>{`
        @keyframes bellShake {
          0% { transform: rotate(0deg); }
          25% { transform: rotate(15deg); }
          50% { transform: rotate(-15deg); }
          75% { transform: rotate(10deg); }
          100% { transform: rotate(0deg); }
        }
        @keyframes slideIn {
          from { transform: translateX(100%); opacity: 0; }
          to { transform: translateX(0); opacity: 1; }
        }
      `}</style>
    </div>
  );
}
