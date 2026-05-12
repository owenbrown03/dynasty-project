import AppRoutes from './Routes';
import Sidebar from './components/Sidebar';
import usernameLookup from './hooks/usernameLookup.ts';

function App() {
  const { transactions, username, loading, handleUserSubmit } = usernameLookup(); 

  return (
    <div className="app-container">
      <nav className="sidebar-container">
        <Sidebar />
      </nav>
      
      <main>
        <AppRoutes 
          handleUserSubmit={handleUserSubmit}
          transactions={transactions}
          loading={loading}
          username={username}
        />
      </main>
    </div>
  );

}
export default App;