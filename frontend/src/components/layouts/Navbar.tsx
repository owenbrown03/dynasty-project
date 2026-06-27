import './Navbar.css';
import { useAuth } from '@/hooks/useAuth';
import { useAuthContext } from '@/context/AuthContext'
import { useSleeperAuthContext } from '@/context/SleeperAuthContext';
import { useSleeperConnection } from '@/hooks/sleeper/useConnection';

export const Navbar = () => {
  const auth = useAuth();
  const authContext = useAuthContext();
  const sleeperContext = useSleeperAuthContext();
  const connection = useSleeperConnection();

  return (
    <nav className="navbar">
      {/* LEFT */}
      <div className="navbar-left">
        Sleeper App
      </div>

      {/* MIDDLE */}
      <div className="navbar-middle">
        {!connection.canRead ? (
          <span>Sleeper not linked</span>
        ) : !auth.isLoggedIn ? (
          <span>
            Read access: {connection.username}
            <button className="login-button" onClick={authContext.open}>
            Log in to link
            </button>
          </span>
        ) : !connection.canWrite ? (
          <span>
            Read access: {connection.username}
            <button className="login-button" onClick={sleeperContext.open}>
              Enable write access
            </button>
          </span>
        ) : (
          <span>
            Write access: {connection.username}
          </span>
        )}
      </div>

      {/* RIGHT */}
      <div className="navbar-right">
        {auth.isLoggedIn ? (
          <button className="login-button" onClick={auth.logout}>
            Logout
          </button>
        ) : (
          <button className="login-button" onClick={authContext.open}>
            Login
          </button>
        )}
      </div>
    </nav>
  );
};