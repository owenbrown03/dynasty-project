import { Outlet } from 'react-router';

import './DashboardLayout.css'
import { Navbar } from './Navbar';
import { Sidebar } from './Sidebar';
import { AuthModal } from '../auth/AuthModal';
import { SleeperAuthModal } from '../sleeper/SleeperAuthModal';

export const DashboardLayout = () => {
  return (
    <div className="app-container">
      <Navbar />
      <div className="main-wrapper">
        <Sidebar />
        <main className="content">
          <Outlet />
        </main>
      </div>
      <AuthModal />
      <SleeperAuthModal />
    </div>
  );
};