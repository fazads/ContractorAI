import { Navigate, Route, Routes } from 'react-router-dom';
import NavBar from './components/NavBar';
import DashboardPage from './pages/DashboardPage';
import HelpPage from './pages/HelpPage';

export default function App() {
  return (
    <div className="app-shell">
      <NavBar />
      <main className="app-main">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/help" element={<HelpPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}
