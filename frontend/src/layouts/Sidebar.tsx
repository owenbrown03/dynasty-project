import { useState } from 'react';
import { Link } from 'react-router';

import './Sidebar.css';
import { useUserContext } from '../context/UserContext';

export const Sidebar = () => {
  const { username } = useUserContext();
  const [isOpen, setIsOpen] = useState(false);

  const toggleSidebar = () => {
    setIsOpen(!isOpen);
  };

  return (
    <div className={`sidebar ${isOpen ? 'expanded' : 'collapsed'}`}>
      <button onClick={toggleSidebar}>
        {isOpen ? 'Close' : 'Open'}
      </button>
      {isOpen &&
        <div className='sidebar'>
          <Link to={`/dashboard/${username}`} className="sidebar-link">            
            <div>home</div>
          </Link>
          <Link to={`/leagues/${username}`} className="sidebar-link">            
            <div>leagues</div>
          </Link>
          <Link to={`/trades/${username}`} className="sidebar-link">            
            <div>trades</div>
          </Link>
          <Link to={`/orphans/${username}`} className="sidebar-link">            
            <div>orphans</div>
          </Link>
        </div>
      }
    </div>
  );
};
