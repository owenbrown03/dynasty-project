import './Navbar.css';
import {
  useEffect,
  useRef,
  useState,
} from 'react';
import { Link } from 'react-router';
import { useAuth } from '@/hooks/useAuth';
import { useAuthContext } from '@/context/useAuthContext'
import { useSleeperAuthContext } from '@/context/useSleeperAuthContext';
import { useSettingsContext } from '@/context/useSettingsContext';
import { useSleeperConnection } from '@/hooks/sleeper/useConnection';
import { useTheme } from '@/context/useTheme';
import { useValuePreference } from '@/context/useValuePreference';
import { getValueBasisOptions } from '@/pages/waivers/waiver.constants';
import type { AccentColor, ValueBasis } from '@/types';
import brandLogo from '@/assets/logo.png';

const ACCENT_OPTIONS: Array<{
  value: AccentColor;
  label: string;
  light: string;
  dark: string;
}> = [
  { value: 'blue', label: 'Blue', light: '#1f6feb', dark: '#79a7ff' },
  { value: 'green', label: 'Green', light: '#1f7a3f', dark: '#5ec27a' },
  { value: 'purple', label: 'Purple', light: '#7c3aed', dark: '#a78bfa' },
  { value: 'red', label: 'Red', light: '#b33a2b', dark: '#f18a7d' },
  { value: 'orange', label: 'Orange', light: '#c2410c', dark: '#fb923c' },
  { value: 'teal', label: 'Teal', light: '#0d9488', dark: '#5eead4' },
  { value: 'pink', label: 'Pink', light: '#db2777', dark: '#f472b6' },
];

export const Navbar = () => {
  const [accountMenuOpen, setAccountMenuOpen] = useState(false);
  const accountMenuRef = useRef<HTMLDivElement | null>(null);
  const auth = useAuth();
  const authContext = useAuthContext();
  const sleeperContext = useSleeperAuthContext();
  const settingsContext = useSettingsContext();
  const connection = useSleeperConnection();
  const theme = useTheme();
  const valuePreference = useValuePreference();

  useEffect(() => {
    const handleClick = (event: MouseEvent) => {
      if (
        accountMenuRef.current
        && !accountMenuRef.current.contains(
          event.target as Node,
        )
      ) {
        setAccountMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClick);
    return () => {
      document.removeEventListener('mousedown', handleClick);
    };
  }, []);

  const accountLabel = auth.siteUser?.email
    ?? connection.username
    ?? 'Guest';

  return (
    <nav className="navbar">
      <Link to="/" className="navbar-left navbar-brand-link">
        <div className="navbar-brand-mark">
          <img src={brandLogo} alt="Dynasty Base logo" />
        </div>

        <div className="navbar-brand-copy">
          <span className="navbar-kicker">
            Dynasty Base
          </span>
        </div>
      </Link>

      <div className="navbar-middle">
        {!connection.canRead ? (
          <div className="navbar-status">
            <span className="status-label">
              Sleeper
            </span>

            <strong className="status-value">
              Not linked
            </strong>
          </div>
        ) : !auth.isLoggedIn ? (
          <div className="navbar-status">
            <span className="status-label">
              Read access
            </span>

            <strong className="status-value">
              {connection.username}
            </strong>

            <button
              className="button-secondary navbar-inline-button"
              onClick={authContext.open}
            >
              Log in to link
            </button>
          </div>
        ) : !connection.canWrite ? (
          <div className="navbar-status">
            <span className="status-label">
              Read access
            </span>

            <strong className="status-value">
              {connection.username}
            </strong>

            <button
              className="button-secondary navbar-inline-button"
              onClick={sleeperContext.open}
            >
              Enable write access
            </button>
          </div>
        ) : (
          <div className="navbar-status">
            <span className="status-label">
              Write access
            </span>

            <strong className="status-value">
              {connection.username}
            </strong>
          </div>
        )}
      </div>

      <div className="navbar-right">
        <div
          className="navbar-account-cluster"
          ref={accountMenuRef}
        >
          <button
            type="button"
            className="navbar-account-trigger"
            onClick={() => {
              setAccountMenuOpen((current) => !current);
            }}
            aria-expanded={accountMenuOpen}
            aria-haspopup="menu"
            title={accountLabel}
          >
            <svg
              className="navbar-account-icon"
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
          </button>

          {
            accountMenuOpen
              ? (
                <div className="navbar-account-menu">
                  <label className="navbar-theme-control">
                    <span>
                      Theme
                    </span>

                    <select
                      value={theme.preference}
                      onChange={(e) => {
                        void theme.setPreference(
                          e.target.value as
                            | 'light'
                            | 'dark'
                            | 'system',
                        );
                      }}
                      disabled={theme.isSaving}
                    >
                      <option value="light">
                        Light
                      </option>

                      <option value="dark">
                        Dark
                      </option>

                      <option value="system">
                        System
                      </option>
                    </select>
                  </label>

                  <div className="navbar-theme-control">
                    <span>
                      Accent
                    </span>

                    <div className="navbar-accent-row">
                      {ACCENT_OPTIONS.map((option) => (
                        <button
                          key={option.value}
                          type="button"
                          className={`navbar-accent-dot ${theme.accentColor === option.value ? 'navbar-accent-dot--active' : ''}`}
                          style={{
                            background: theme.resolvedTheme === 'dark'
                              ? option.dark
                              : option.light,
                          }}
                          disabled={theme.isSavingAccent}
                          title={option.label}
                          onClick={() => {
                            void theme.setAccentColor(option.value);
                          }}
                        />
                      ))}
                    </div>
                  </div>

                  <label className="navbar-theme-control">
                    <span>
                      Default value
                    </span>

                    <select
                      value={valuePreference.preference}
                      onChange={(e) => {
                        void valuePreference.setPreference(
                          e.target.value as ValueBasis,
                        );
                      }}
                      disabled={valuePreference.isSaving}
                    >
                      {
                        getValueBasisOptions(auth.isLoggedIn).map((option) => (
                          <option
                            key={option.value}
                            value={option.value}
                          >
                            {option.label}
                          </option>
                        ))
                      }
                    </select>
                  </label>

                  <button
                    type="button"
                    className="button-secondary navbar-settings-link"
                    onClick={() => {
                      setAccountMenuOpen(false);
                      settingsContext.open();
                    }}
                  >
                    Open settings
                  </button>

                  {auth.isLoggedIn ? (
                    <button
                      className="button-primary"
                      onClick={() => {
                        setAccountMenuOpen(false);
                        void auth.logout();
                      }}
                    >
                      Logout
                    </button>
                  ) : (
                    <button
                      className="button-primary"
                      onClick={() => {
                        setAccountMenuOpen(false);
                        authContext.open();
                      }}
                    >
                      Login
                    </button>
                  )}
                </div>
              )
              : null
          }
        </div>
      </div>
    </nav>
  );
};
