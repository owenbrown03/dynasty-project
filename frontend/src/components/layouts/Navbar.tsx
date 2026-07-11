import './Navbar.css';
import { Link } from 'react-router';
import { useAuth } from '@/hooks/useAuth';
import { useAuthContext } from '@/context/useAuthContext'
import { useSleeperAuthContext } from '@/context/useSleeperAuthContext';
import { useSleeperConnection } from '@/hooks/sleeper/useConnection';
import { useTheme } from '@/context/useTheme';
import brandLogo from '@/assets/logo.png';

export const Navbar = () => {
  const auth = useAuth();
  const authContext = useAuthContext();
  const sleeperContext = useSleeperAuthContext();
  const connection = useSleeperConnection();
  const theme = useTheme();

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
        <div className="navbar-account-cluster">
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

          {auth.isLoggedIn ? (
            <button
              className="button-primary"
              onClick={auth.logout}
            >
              Logout
            </button>
          ) : (
            <button
              className="button-primary"
              onClick={authContext.open}
            >
              Login
            </button>
          )}
        </div>
      </div>
    </nav>
  );
};
