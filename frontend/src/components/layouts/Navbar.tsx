import './Navbar.css';

interface NavbarProps {
  onLoginClick: () => void;
  isLoggedIn: boolean;
  onLogoutClick: () => void | Promise<void>;
  sleeperUsername: string | undefined;
}

export const Navbar = ({ onLoginClick, isLoggedIn, onLogoutClick, sleeperUsername }: NavbarProps) => {
  return (
    <nav className="navbar" aria-label="Primary Navigation">
      <div className="navbar-left">
        Dynasty App
      </div>
      <div className="navbar-middle">
        {isLoggedIn && sleeperUsername ? (
          <span>{sleeperUsername}</span>
        ) : (
          <span>Sleeper not linked</span>
        )}
      </div>
      <div className="navbar-right">
        {isLoggedIn ? (
          <button 
            className="login-button" 
            onClick={onLogoutClick}
            aria-label="Log out"
          >
            Log out
          </button>
        ) : (
          <button 
            className="login-button" 
            onClick={onLoginClick}
            aria-label="Open Login or Register"
          >
            Login / Register
          </button>
        )}
      </div>
    </nav>
  );
};