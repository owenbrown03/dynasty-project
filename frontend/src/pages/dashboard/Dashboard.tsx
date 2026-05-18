import { Outlet } from 'react-router';

export const Dashboard = () => {
  return (      
      <main className="dashboard-content">
        <Outlet /> 
      </main>
  );
};