import { AppRoutes } from './Routes';
import { Sidebar } from './layouts/Sidebar.tsx';
import { UserProvider } from './context/UserContext.tsx';

export function App() {
  return (
    <UserProvider>
      <div className="app-container">
        <nav className="sidebar-container">
          <Sidebar />
        </nav>
        
        <main>
          <AppRoutes />
        </main>
      </div>
    </UserProvider>
  );

}