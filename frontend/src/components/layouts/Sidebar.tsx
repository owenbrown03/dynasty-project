import { useState } from 'react';
import { NavLink } from 'react-router';
import {
  LayoutDashboard,
  Trophy,
  Briefcase,
  User,
  HandCoins,
  Wallet,
  Bell,
  Radar,
  Layers3,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';

import './Sidebar.css';
import { useSleeperConnection } from '@/hooks/sleeper/useConnection';

interface SidebarItem {
  to: string;
  label: string;
  icon: React.ReactNode;
}

interface SidebarSection {
  label?: string;
  items: SidebarItem[];
}

export const Sidebar = () => {
  const connection = useSleeperConnection();
  const [isOpen, setIsOpen] = useState(false);
  const commissionerPath = connection.username
    ? `/commissioner/${encodeURIComponent(connection.username)}`
    : '/commissioner';

  const sections: SidebarSection[] = [
    {
      items: [
        { to: '/dashboard', label: 'Dashboard', icon: <LayoutDashboard size={20} /> },
        { to: '/leagues', label: 'Leagues', icon: <Trophy size={20} /> },
      ],
    },
    {
      label: 'Analysis',
      items: [
        { to: '/trades', label: 'Trades', icon: <Briefcase size={20} /> },
        { to: '/waivers', label: 'Waivers', icon: <HandCoins size={20} /> },
        { to: '/tiers', label: 'Tiers', icon: <Layers3 size={20} /> },
        { to: '/my-values', label: 'My Values', icon: <Radar size={20} /> },
      ],
    },
    {
      label: 'Tools',
      items: [
        { to: '/finance', label: 'Finance', icon: <Wallet size={20} /> },
        { to: '/reminders', label: 'Reminders', icon: <Bell size={20} /> },
        { to: commissionerPath, label: 'Commissioner', icon: <User size={20} /> },
      ],
    },
  ];

  return (
    <nav className={`sidebar ${isOpen ? 'expanded' : 'collapsed'}`}>
      <button
        className="button-secondary sidebar-toggle"
        onClick={() => setIsOpen(!isOpen)}
        aria-label={isOpen ? 'Collapse sidebar' : 'Expand sidebar'}
      >
        {isOpen ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
      </button>

      <div id="sidebar-menu">
        {sections.map((section, si) => (
          <div key={si} className="sidebar-section">
            {isOpen && section.label && (
              <span className="sidebar-section-label">{section.label}</span>
            )}
            {section.items.map((item) => (
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
            {isOpen && si < sections.length - 1 && (
              <div className="sidebar-divider" />
            )}
          </div>
        ))}
      </div>
    </nav>
  );
};
