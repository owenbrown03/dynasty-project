import './Sidebar.css';
import { useState } from 'react';
import { Link } from 'react-router';

const Sidebar = () => {
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
          <Link to="/" className="sidebar-link">
            <div>home</div>
          </Link>
          <Link to="/leagues" className="sidebar-link">
            <div>leagues</div>
          </Link>
          <Link to="/trades" className="sidebar-link">
            <div>trades</div>
          </Link>
        </div>
      }
    </div>


  );
};

export default Sidebar;
