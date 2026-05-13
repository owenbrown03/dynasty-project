import AppRoutes from './Routes';
import Sidebar from './components/Sidebar';
import { usernameLookup } from './hooks/usernameHandler.ts';

function App() {
  const { username, loading, handleUserSubmit } = usernameLookup(); 

  return (
    <div className="app-container">
      <nav className="sidebar-container">
        <Sidebar />
      </nav>
      
      <main>
        <AppRoutes 
          handleUserSubmit={handleUserSubmit}
          loading={loading}
          username={username}
        />
      </main>
    </div>
  );

}
export default App;