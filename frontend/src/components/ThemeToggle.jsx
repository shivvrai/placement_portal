/**
 * ThemeToggle — animated sun/moon button for switching between light and dark modes.
 * Uses CSS transitions for a smooth, organic feel.
 */

import { useTheme } from '../context/ThemeContext';

export default function ThemeToggle({ compact = false }) {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <button
      onClick={toggleTheme}
      className="theme-toggle"
      aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`}
      title={`Switch to ${isDark ? 'light' : 'dark'} mode`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: compact ? 0 : 8,
        padding: compact ? '8px' : '8px 14px',
        borderRadius: 'var(--border-radius-sm)',
        border: '1px solid var(--border-color)',
        background: 'var(--bg-tertiary)',
        color: 'var(--text-secondary)',
        cursor: 'pointer',
        fontSize: '0.82rem',
        fontWeight: 500,
        fontFamily: 'var(--font-family)',
        transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
        position: 'relative',
        overflow: 'hidden',
        minWidth: compact ? 36 : 'auto',
        height: compact ? 36 : 34,
      }}
    >
      <span
        style={{
          display: 'inline-flex',
          transition: 'transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)',
          transform: isDark ? 'rotate(0deg)' : 'rotate(360deg)',
          fontSize: compact ? '1rem' : '0.9rem',
        }}
      >
        {isDark ? '🌙' : '☀️'}
      </span>
      {!compact && (
        <span style={{ transition: 'opacity 0.2s ease' }}>
          {isDark ? 'Dark' : 'Light'}
        </span>
      )}
    </button>
  );
}
