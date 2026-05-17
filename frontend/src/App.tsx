import AppRoutes from './Routes';
import Sidebar from './components/Sidebar';
import { UsernameProvider } from './context/UsernameProvider';

function App() {
  return (
    <UsernameProvider>
      <div className="app-container">
        <nav className="sidebar-container">
          <Sidebar />
        </nav>

        <main>
          <AppRoutes />
        </main>
      </div>
    </UsernameProvider>
  );
}
export default App;
