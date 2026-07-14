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
import { UserAvatar } from '@/components/users/UserAvatar';
import brandLogo from '@/assets/logo.png';

export const Navbar = () => {
  const [accountMenuOpen, setAccountMenuOpen] = useState(false);
  const accountMenuRef = useRef<HTMLDivElement | null>(null);
  const auth = useAuth();
  const authContext = useAuthContext();
  const sleeperContext = useSleeperAuthContext();
  const settingsContext = useSettingsContext();
  const connection = useSleeperConnection();

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
            <UserAvatar
              avatarId={connection.avatar}
              name={accountLabel}
              size="sm"
              className="navbar-account-avatar"
            />
          </button>

          {
            accountMenuOpen
              ? (
                <div className="navbar-account-menu">
                  <div className="navbar-account-info">
                    <span className="navbar-account-name">{accountLabel}</span>
                  </div>

                  <button
                    type="button"
                    className="button-secondary"
                    onClick={() => {
                      setAccountMenuOpen(false);
                      settingsContext.open();
                    }}
                  >
                    Settings
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
