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
import { useSleeperConnection } from '@/hooks/sleeper/useConnection';
import { useTheme } from '@/context/useTheme';
import { useValuePreference } from '@/context/useValuePreference';
import { VALUE_BASIS_OPTIONS } from '@/pages/waivers/waiver.constants';
import type { ValueBasis } from '@/types';
import brandLogo from '@/assets/logo.png';

export const Navbar = () => {
  const [accountMenuOpen, setAccountMenuOpen] = useState(false);
  const accountMenuRef = useRef<HTMLDivElement | null>(null);
  const auth = useAuth();
  const authContext = useAuthContext();
  const sleeperContext = useSleeperAuthContext();
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
            className="button-secondary navbar-account-trigger"
            onClick={() => {
              setAccountMenuOpen((current) => !current);
            }}
            aria-expanded={accountMenuOpen}
            aria-haspopup="menu"
          >
            <span className="navbar-account-trigger-copy">
              <span className="status-label">
                Account
              </span>
              <strong className="status-value">
                {accountLabel}
              </strong>
            </span>
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
                            'light'
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
                        VALUE_BASIS_OPTIONS.map((option) => (
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
