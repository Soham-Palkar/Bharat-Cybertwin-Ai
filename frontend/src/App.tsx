import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/shared/Navbar';
import DashboardPage from './pages/DashboardPage';
import CyberTwinPage from './pages/CyberTwinPage';
import ContainmentPage from './pages/ContainmentPage';
import { FloatingCopilot } from './components/CyberTwin/FloatingCopilot';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-bg">
        <Navbar />
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/cybertwin" element={<CyberTwinPage />} />
          <Route path="/containment" element={<ContainmentPage />} />
        </Routes>
        <FloatingCopilot />
      </div>
    </Router>
  );
}

export default App;
