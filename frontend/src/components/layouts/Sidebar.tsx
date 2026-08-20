import { NavLink } from 'react-router';
import { useEffect } from 'react';
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
  BadgeDollarSign,
  ChartNoAxesColumn,
} from 'lucide-react';

import './Sidebar.css';
import { useSleeperConnection } from '@/hooks/sleeper/useConnection';
import { useIsMobile } from '@/hooks/useIsMobile';
import { useMobileNav } from '@/hooks/useMobileNav';

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
  const isMobile = useIsMobile();
  const { open, close } = useMobileNav();

  useEffect(() => {
    if (isMobile && open) {
      document.body.style.overflow = 'hidden';
      return () => { document.body.style.overflow = ''; };
    }
    document.body.style.overflow = '';
    return () => { document.body.style.overflow = ''; };
  }, [isMobile, open]);

  const commissionerPath = connection.username
    ? `/commissioner/${encodeURIComponent(connection.username)}`
    : '/commissioner';

  const sections: SidebarSection[] = [
    {
      items: [
        { to: '/', label: 'Home', icon: <LayoutDashboard size={20} /> },
        { to: '/leagues', label: 'Leagues', icon: <Trophy size={20} /> },
      ],
    },
    {
      label: 'Analysis',
      items: [
        { to: '/trades', label: 'Trades', icon: <Briefcase size={20} /> },
        { to: '/waivers', label: 'Waivers', icon: <HandCoins size={20} /> },
        { to: '/tiers', label: 'Tiers', icon: <Layers3 size={20} /> },
        { to: '/adp', label: 'ADP', icon: <ChartNoAxesColumn size={20} /> },
        { to: '/my-values', label: 'My Values', icon: <Radar size={20} /> },
        { to: '/auction', label: 'Auction', icon: <BadgeDollarSign size={20} /> },
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

  if (isMobile) {
    return (
      <>
        {open && (
          <div className="sidebar-mobile-backdrop" onClick={close} />
        )}
        <nav className={`sidebar sidebar-mobile ${open ? 'sidebar-mobile-open' : ''}`}>
          <div className="sidebar-panel sidebar-panel-mobile">
            <div className="sidebar-menu">
              {sections.map((section, si) => (
                <div key={si} className="sidebar-section">
                  {section.label && (
                    <span className="sidebar-section-label sidebar-section-label-visible">
                      {section.label}
                    </span>
                  )}
                  {section.items.map((item) => (
                    <NavLink
                      key={item.to}
                      to={item.to}
                      end={item.to === '/'}
                      className={({ isActive }) =>
                        `sidebar-link ${isActive ? 'active' : ''}`
                      }
                      onClick={close}
                    >
                      <div className="sidebar-icon-slot">
                        {item.icon}
                      </div>
                      <span className="sidebar-link-label sidebar-link-label-visible">
                        {item.label}
                      </span>
                    </NavLink>
                  ))}
                </div>
              ))}
            </div>
          </div>
        </nav>
      </>
    );
  }

  return (
    <nav className="sidebar">
      <div className="sidebar-panel">
        <div className="sidebar-menu">
          {sections.map((section, si) => (
            <div key={si} className="sidebar-section">
              {section.label && (
                <span className="sidebar-section-label">{section.label}</span>
              )}
              {section.items.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === '/'}
                  className={({ isActive }) =>
                    `sidebar-link ${isActive ? 'active' : ''}`
                  }
                >
                  <div className="sidebar-icon-slot">
                    {item.icon}
                  </div>
                  <span className="sidebar-link-label">{item.label}</span>
                </NavLink>
              ))}
            </div>
          ))}
        </div>
      </div>
    </nav>
  );
};
