import './Sidebar.css';
import { useState } from 'react';
import { Link } from 'react-router';
import { useUsername } from '../context/usernameContext';

const Sidebar = () => {
  const [isOpen, setIsOpen] = useState(false);
  const { username } = useUsername();
  const userPrefix = username ? `/${encodeURIComponent(username)}` : '';

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
          <Link to="/" className="sidebar-link">
            <div>home</div>
          </Link>
          <Link to={`${userPrefix}/rosters`} className="sidebar-link">
            <div>rosters</div>
          </Link>
          <Link to={`${userPrefix}/trades`} className="sidebar-link">
            <div>trades</div>
          </Link>
        </div>
      }
    </div>


  );
};

export default Sidebar;
