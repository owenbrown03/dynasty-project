import './Navbar.css';
import { useAppState } from '@/hooks/app/useAppState';

export const Navbar = ({ onSleeperAuthClick }: { onSleeperAuthClick: () => void }) => {
  const app = useAppState();

  return (
    <nav className="navbar">
      <div className="navbar-left">Dynasty App</div>

      <div className="navbar-middle">
        {app.state === 'anonymous' && (
          <span>Not logged in</span>
        )}

        {app.state === 'authenticated-no-sleeper' && (
          <span>
            Logged in — no Sleeper linked
          </span>
        )}

        {app.state === 'sleeper-linked-read-only' && (
          <span>
            Read-only: {app.sleeperUsername}
            <button onClick={onSleeperAuthClick}>
              Enable Write Access
            </button>
          </span>
        )}

        {app.state === 'sleeper-linked-write' && (
          <span>
            Write access: {app.sleeperUsername}
          </span>
        )}
      </div>

      <div className="navbar-right">
        {app.isLoggedIn ? (
          <button onClick={app.logout}>Log out</button>
        ) : (
          <button onClick={app.openAuth}>Login</button>
        )}
      </div>
    </nav>
  );
};