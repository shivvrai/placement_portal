/**
 * DriveCalendar - Monthly & Weekly calendar view for placement drives.
 * Features: Drive pills, conflict alerts, reschedule modal, week view toggle.
 * Route: /tpo/calendar
 */

import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { calendarApi } from '../../api/endpoints';

const STATUS_COLORS = {
  upcoming: '#6366f1',
  open: '#22c55e',
  in_progress: '#f59e0b',
  completed: '#6b7280',
  cancelled: '#ef4444',
};

const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
];
const DAY_NAMES = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

export default function DriveCalendar() {
  const navigate = useNavigate();
  const today = new Date();

  const [currentYear, setCurrentYear] = useState(today.getFullYear());
  const [currentMonth, setCurrentMonth] = useState(today.getMonth());
  const [viewMode, setViewMode] = useState('month');
  const [drives, setDrives] = useState([]);
  const [conflicts, setConflicts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDrive, setSelectedDrive] = useState(null);
  const [rescheduleModal, setRescheduleModal] = useState(null);
  const [rescheduleForm, setRescheduleForm] = useState({ drive_date: '', registration_deadline: '' });
  const [rescheduleLoading, setRescheduleLoading] = useState(false);
  const [toast, setToast] = useState(null);
  const [weekOffset, setWeekOffset] = useState(0);

  const loadData = async () => {
    try {
      setLoading(true);
      const [drivesRes, conflictsRes] = await Promise.all([
        calendarApi.getDrives(),
        calendarApi.getConflicts(),
      ]);
      setDrives(Array.isArray(drivesRes.data) ? drivesRes.data : []);
      setConflicts(Array.isArray(conflictsRes.data) ? conflictsRes.data : []);
    } catch (err) {
      console.error('Calendar load failed:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3500);
  };

  const calendarDays = useMemo(() => {
    const firstDay = new Date(currentYear, currentMonth, 1).getDay();
    const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
    const days = [];
    for (let i = 0; i < firstDay; i++) days.push(null);
    for (let d = 1; d <= daysInMonth; d++) days.push(d);
    return days;
  }, [currentYear, currentMonth]);

  const drivesForDay = (day) => {
    if (!day) return [];
    const dateStr = `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    return drives.filter(d => d.drive_date === dateStr);
  };

  const weekDays = useMemo(() => {
    const start = new Date(today);
    start.setDate(today.getDate() - today.getDay() + weekOffset * 7);
    return Array.from({ length: 7 }, (_, i) => {
      const d = new Date(start);
      d.setDate(start.getDate() + i);
      return d;
    });
  }, [weekOffset]);

  const drivesForDate = (dateObj) => {
    const dateStr = dateObj.toISOString().split('T')[0];
    return drives.filter(d => d.drive_date === dateStr);
  };

  const prevMonth = () => {
    if (currentMonth === 0) {
      setCurrentYear(y => y - 1);
      setCurrentMonth(11);
    } else {
      setCurrentMonth(m => m - 1);
    }
  };

  const nextMonth = () => {
    if (currentMonth === 11) {
      setCurrentYear(y => y + 1);
      setCurrentMonth(0);
    } else {
      setCurrentMonth(m => m + 1);
    }
  };

  const handleReschedule = async () => {
    if (!rescheduleModal) return;
    setRescheduleLoading(true);
    try {
      await calendarApi.rescheduleDrive(rescheduleModal.id, rescheduleForm);
      showToast('Drive rescheduled and students notified!');
      setRescheduleModal(null);
      await loadData();
    } catch (err) {
      showToast('Failed to reschedule drive', 'error');
    } finally {
      setRescheduleLoading(false);
    }
  };

  const isToday = (day) => {
    return day && currentYear === today.getFullYear() &&
      currentMonth === today.getMonth() && day === today.getDate();
  };

  if (loading) {
    return <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>Loading calendar...</div>;
  }

  return (
    <div style={{ padding: 'var(--space-6)', display: 'flex', gap: 20, minHeight: '100vh' }}>
      {toast && (
        <div style={{
          position: 'fixed', top: 20, right: 20, zIndex: 9999,
          padding: '12px 20px', borderRadius: 10,
          background: toast.type === 'error' ? '#ef4444' : '#22c55e',
          color: '#fff', fontWeight: 600, boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
        }}>
          {toast.msg}
        </div>
      )}

      {/* Main Calendar Area */}
      <div style={{ flex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
          <h1 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 700 }}>📅 Drive Calendar & Scheduler</h1>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            <div style={{ display: 'flex', border: '1px solid var(--border-color)', borderRadius: 8, overflow: 'hidden' }}>
              {['month', 'week'].map(v => (
                <button
                  key={v}
                  onClick={() => setViewMode(v)}
                  style={{
                    padding: '6px 16px', border: 'none', cursor: 'pointer', fontWeight: 600, fontSize: '0.85rem',
                    background: viewMode === v ? 'var(--primary)' : 'var(--bg-secondary)',
                    color: viewMode === v ? '#fff' : 'var(--text-secondary)',
                  }}
                >
                  {v.charAt(0).toUpperCase() + v.slice(1)}
                </button>
              ))}
            </div>
            <button className="btn btn-primary" onClick={() => navigate('/tpo/drives')}>
              + New Drive
            </button>
          </div>
        </div>

        {viewMode === 'month' && (
          <>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 16 }}>
              <button className="btn btn-ghost" onClick={prevMonth}>◀</button>
              <h2 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 700 }}>
                {MONTH_NAMES[currentMonth]} {currentYear}
              </h2>
              <button className="btn btn-ghost" onClick={nextMonth}>▶</button>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 2, marginBottom: 2 }}>
              {DAY_NAMES.map(d => (
                <div key={d} style={{ textAlign: 'center', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', padding: '6px 0' }}>{d}</div>
              ))}
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 2 }}>
              {calendarDays.map((day, idx) => {
                const dayDrives = drivesForDay(day);
                return (
                  <div
                    key={idx}
                    style={{
                      minHeight: 90, padding: '6px', borderRadius: 8,
                      background: day ? 'var(--bg-secondary)' : 'transparent',
                      border: isToday(day) ? '2px solid var(--primary)' : '1px solid var(--border-color)',
                      cursor: day ? 'pointer' : 'default',
                      position: 'relative',
                    }}
                    onClick={() => {
                      if (!day) return;
                      if (dayDrives.length > 0) setSelectedDrive(dayDrives[0]);
                    }}
                  >
                    {day && (
                      <div style={{ fontSize: '0.8rem', fontWeight: isToday(day) ? 700 : 400, color: isToday(day) ? 'var(--primary)' : 'var(--text-secondary)', marginBottom: 4 }}>{day}</div>
                    )}
                    {dayDrives.slice(0, 2).map(drive => (
                      <div
                        key={drive.id}
                        onClick={(e) => { e.stopPropagation(); setSelectedDrive(drive); }}
                        style={{
                          background: STATUS_COLORS[drive.status] || '#6366f1',
                          color: '#fff', borderRadius: 4, padding: '2px 6px',
                          fontSize: '0.68rem', fontWeight: 600, marginBottom: 2,
                          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                          cursor: 'pointer',
                          outline: drive.has_conflict ? '2px solid #ef4444' : 'none',
                        }}
                        title={`${drive.company_name} - ${drive.title}`}
                      >
                        {drive.has_conflict ? '⚠️ ' : ''}{drive.company_name}
                      </div>
                    ))}
                    {dayDrives.length > 2 && (
                      <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>+{dayDrives.length - 2} more</div>
                    )}
                  </div>
                );
              })}
            </div>
          </>
        )}

        {viewMode === 'week' && (
          <>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 16 }}>
              <button className="btn btn-ghost" onClick={() => setWeekOffset(w => w - 1)}>◀ Prev Week</button>
              <span style={{ fontWeight: 700 }}>
                {weekDays[0].toLocaleDateString()} - {weekDays[6].toLocaleDateString()}
              </span>
              <button className="btn btn-ghost" onClick={() => setWeekOffset(w => w + 1)}>Next Week ▶</button>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 8 }}>
              {weekDays.map((dateObj, i) => {
                const dayDrives = drivesForDate(dateObj);
                const isT = dateObj.toDateString() === today.toDateString();
                return (
                  <div
                    key={i}
                    style={{
                      minHeight: 200, background: 'var(--bg-secondary)', borderRadius: 10,
                      border: isT ? '2px solid var(--primary)' : '1px solid var(--border-color)', padding: 10,
                    }}
                  >
                    <div style={{ fontWeight: 700, fontSize: '0.85rem', color: isT ? 'var(--primary)' : 'var(--text-secondary)', marginBottom: 8 }}>
                      {DAY_NAMES[i]} {dateObj.getDate()}
                    </div>
                    {dayDrives.map(drive => (
                      <div
                        key={drive.id}
                        onClick={() => setSelectedDrive(drive)}
                        style={{
                          background: STATUS_COLORS[drive.status] || '#6366f1',
                          color: '#fff', borderRadius: 6, padding: '6px 8px',
                          fontSize: '0.75rem', fontWeight: 600, marginBottom: 6, cursor: 'pointer',
                        }}
                      >
                        {drive.company_name}<br />
                        <span style={{ opacity: 0.85, fontWeight: 400 }}>{drive.title}</span>
                      </div>
                    ))}
                    {dayDrives.length === 0 && (
                      <div style={{ color: 'var(--text-muted)', fontSize: '0.72rem', marginTop: 8 }}>No drives</div>
                    )}
                  </div>
                );
              })}
            </div>
          </>
        )}
      </div>

      {/* Right Sidebar */}
      <div style={{ width: 280, flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div className="card" style={{ padding: 16 }}>
          <div style={{ fontWeight: 700, marginBottom: 10, fontSize: '0.9rem' }}>Status Legend</div>
          {Object.entries(STATUS_COLORS).map(([s, c]) => (
            <div key={s} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
              <div style={{ width: 12, height: 12, borderRadius: 3, background: c }} />
              <span style={{ fontSize: '0.8rem', textTransform: 'capitalize' }}>{s.replace('_', ' ')}</span>
            </div>
          ))}
        </div>

        {/* Conflicts */}
        <div className="card" style={{ padding: 16 }}>
          <div style={{ fontWeight: 700, marginBottom: 10, fontSize: '0.9rem' }}>
            ⚠️ Conflicts ({conflicts.length})
          </div>
          {conflicts.length === 0 && (
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>No scheduling conflicts detected ✓</div>
          )}
          {conflicts.map((c, i) => (
            <div
              key={i}
              style={{
                padding: '10px', borderRadius: 8, marginBottom: 8,
                background: c.severity === 'critical' ? 'rgba(239,68,68,0.1)' : 'rgba(245,158,11,0.1)',
                border: `1px solid ${c.severity === 'critical' ? '#ef444440' : '#f59e0b40'}`,
              }}
            >
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: c.severity === 'critical' ? '#ef4444' : '#f59e0b', marginBottom: 4 }}>
                {c.severity === 'critical' ? '🔴 CRITICAL' : '⚠️ WARNING'} - {c.conflict_type.replace('_', ' ')}
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginBottom: 6 }}>
                {c.drive_a_company} &amp; {c.drive_b_company}<br />
                Dept: {c.shared_departments?.join(', ')} · {c.days_apart === 0 ? 'Same day' : `${c.days_apart} day(s) apart`}
              </div>
              <button
                className="btn btn-ghost"
                style={{ fontSize: '0.7rem', height: 24, padding: '0 8px' }}
                onClick={() => {
                  const drive = drives.find(d => d.id === c.drive_b_id);
                  if (drive) {
                    setRescheduleModal(drive);
                    setRescheduleForm({ drive_date: drive.drive_date || '', registration_deadline: '' });
                  }
                }}
              >
                Reschedule →
              </button>
            </div>
          ))}
        </div>

        {/* Selected Drive Details */}
        {selectedDrive && (
          <div className="card" style={{ padding: 16, border: '1px solid var(--primary)40' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
              <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>Drive Details</div>
              <span style={{ cursor: 'pointer' }} onClick={() => setSelectedDrive(null)}>✕</span>
            </div>
            <div style={{ display: 'inline-block', padding: '3px 10px', borderRadius: 99, background: STATUS_COLORS[selectedDrive.status] || '#6366f1', color: '#fff', fontSize: '0.7rem', fontWeight: 700, marginBottom: 8 }}>
              {selectedDrive.status?.replace('_', ' ').toUpperCase()}
            </div>
            <div style={{ fontWeight: 700, marginBottom: 4 }}>{selectedDrive.title}</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 4 }}>🏢 {selectedDrive.company_name}</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 4 }}>📅 {selectedDrive.drive_date || 'Date TBD'}</div>
            {selectedDrive.eligible_departments?.length > 0 && (
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: 12 }}>🎓 {selectedDrive.eligible_departments.join(', ')}</div>
            )}
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                className="btn btn-primary"
                style={{ flex: 1, fontSize: '0.8rem', padding: '6px 0' }}
                onClick={() => navigate('/tpo/drives')}
              >
                View Drives
              </button>
              <button
                className="btn btn-secondary"
                style={{ flex: 1, fontSize: '0.8rem', padding: '6px 0' }}
                onClick={() => {
                  setRescheduleModal(selectedDrive);
                  setRescheduleForm({ drive_date: selectedDrive.drive_date || '', registration_deadline: '' });
                }}
              >
                Reschedule
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Reschedule Modal */}
      {rescheduleModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ background: 'var(--bg-secondary)', borderRadius: 16, padding: 32, width: 420 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 20 }}>
              <h2 style={{ margin: 0, fontSize: '1.2rem' }}>📅 Reschedule Drive</h2>
              <span style={{ cursor: 'pointer' }} onClick={() => setRescheduleModal(null)}>✕</span>
            </div>
            <div style={{ marginBottom: 8, fontWeight: 600 }}>{rescheduleModal.title}</div>
            <div style={{ marginBottom: 16, fontSize: '0.85rem', color: 'var(--text-secondary)' }}>🏢 {rescheduleModal.company_name}</div>
            <div style={{ marginBottom: 14 }}>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: 6 }}>New Drive Date</label>
              <input
                type="date"
                value={rescheduleForm.drive_date}
                onChange={e => setRescheduleForm(f => ({ ...f, drive_date: e.target.value }))}
                style={{ width: '100%', padding: '8px 12px', borderRadius: 8, border: '1px solid var(--border-color)', background: 'var(--bg-primary)', color: 'var(--text-primary)' }}
              />
            </div>
            <div style={{ marginBottom: 20 }}>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: 6 }}>New Registration Deadline</label>
              <input
                type="datetime-local"
                value={rescheduleForm.registration_deadline}
                onChange={e => setRescheduleForm(f => ({ ...f, registration_deadline: e.target.value }))}
                style={{ width: '100%', padding: '8px 12px', borderRadius: 8, border: '1px solid var(--border-color)', background: 'var(--bg-primary)', color: 'var(--text-primary)' }}
              />
            </div>
            <div style={{ display: 'flex', gap: 10 }}>
              <button className="btn btn-secondary" onClick={() => setRescheduleModal(null)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleReschedule} disabled={rescheduleLoading} style={{ flex: 1 }}>
                {rescheduleLoading ? 'Saving...' : 'Confirm Reschedule'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
