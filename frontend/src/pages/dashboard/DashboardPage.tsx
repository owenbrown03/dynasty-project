import { Outlet } from 'react-router';

export const DashboardPage = () => {
  return (      
      <main className="dashboard-content">
        <Outlet /> 
      </main>
  );
};