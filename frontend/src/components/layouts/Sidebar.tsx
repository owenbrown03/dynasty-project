import { useState } from 'react';
import { Link } from 'react-router';
import { LayoutDashboard, Trophy, Briefcase, User, ChevronLeft, ChevronRight } from 'lucide-react';

import './Sidebar.css';

const menuItems = [
  { to: '/dashboard', label: 'Dashboard', icon: <LayoutDashboard size={20} /> },
  { to: '/leagues', label: 'Leagues', icon: <Trophy size={20} /> },
  { to: '/trades', label: 'Trades', icon: <Briefcase size={20} /> },
  { to: '/orphans', label: 'Orphans', icon: <User size={20} /> },
];

export const Sidebar = () => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <nav className={`sidebar ${isOpen ? 'expanded' : 'collapsed'}`}>
      <button className='button-secondary' onClick={() => setIsOpen(!isOpen)}>
        {isOpen ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
      </button>

      <div id="sidebar-menu">
        {menuItems.map((item) => (
          <Link key={item.to} to={item.to} className="sidebar-link">
            <div className="tooltip-container">
              {item.icon}
              {!isOpen && <span className="tooltip">{item.label}</span>}
            </div>
            {isOpen && <span className="link-text">{item.label}</span>}
          </Link>
        ))}
      </div>
    </nav>
  );
};