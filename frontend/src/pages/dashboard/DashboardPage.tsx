import { Outlet } from 'react-router';

import './DashboardPage.css'

export const DashboardPage = () => {
  return (      
      <main className="dashboard-content">
        <Outlet /> 
      </main>
  );
};