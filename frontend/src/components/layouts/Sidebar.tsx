import { useState } from 'react';
import { NavLink } from 'react-router';
import {
  LayoutDashboard,
  Trophy,
  Briefcase,
  User,
  HandCoins,
  Wallet,
  Layers3,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';

import './Sidebar.css';
import { useSleeperConnection } from '@/hooks/sleeper/useConnection';

export const Sidebar = () => {
  const connection = useSleeperConnection();
  const [isOpen, setIsOpen] = useState(false);
  const commissionerPath = connection.username
    ? `/commissioner/${encodeURIComponent(connection.username)}`
    : '/commissioner';
  const menuItems = [
    {
      to: '/dashboard',
      label: 'Dashboard',
      icon: <LayoutDashboard size={20} />,
    },
    {
      to: '/leagues',
      label: 'Leagues',
      icon: <Trophy size={20} />,
    },
    {
      to: '/trades',
      label: 'Trades',
      icon: <Briefcase size={20} />,
    },
    {
      to: '/waivers',
      label: 'Waivers',
      icon: <HandCoins size={20} />,
    },
    {
      to: '/tiers',
      label: 'Tiers',
      icon: <Layers3 size={20} />,
    },
    {
      to: '/finance',
      label: 'Finance',
      icon: <Wallet size={20} />,
    },
    {
      to: commissionerPath,
      label: 'Commissioner',
      icon: <User size={20} />,
    },
  ];

  return (
    <nav className={`sidebar ${isOpen ? 'expanded' : 'collapsed'}`}>
      <button
        className="button-secondary sidebar-toggle"
        onClick={() => setIsOpen(!isOpen)}
        aria-label={
          isOpen
            ? 'Collapse sidebar'
            : 'Expand sidebar'
        }
      >
        {isOpen ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
      </button>

      <div id="sidebar-menu">
        {isOpen && (
          <span className="sidebar-section-label">
            Navigation
          </span>
        )}

        {menuItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `sidebar-link ${isActive ? 'active' : ''}`
            }
          >
            <div className="tooltip-container sidebar-icon-slot">
              {item.icon}
              {!isOpen && <span className="tooltip">{item.label}</span>}
            </div>
            {isOpen && <span className="link-text">{item.label}</span>}
          </NavLink>
        ))}
      </div>
    </nav>
  );
};
