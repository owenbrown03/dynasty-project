import { AppRoutes } from './Routes';
import { Sidebar } from './layouts/Sidebar.tsx';
import { UserProvider } from './context/UserContext.tsx';
import { ApiProvider } from './context/ApiContext.tsx';

export function App() {
  return (
    <UserProvider>
      <ApiProvider>
        <div className="app-container">
          <nav className="sidebar-container">
            <Sidebar />
          </nav>
          
          <main>
            <AppRoutes />
          </main>
        </div>  
      </ApiProvider>
    </UserProvider>
  );

}