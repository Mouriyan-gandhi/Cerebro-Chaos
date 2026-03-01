import React from 'react';
import { BrowserRouter as Router, Routes, Route, Outlet } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import HomePage from './pages/HomePage';
import Dashboard from './pages/Dashboard';
import AnalyzePage from './pages/AnalyzePage';
import RiskMapPage from './pages/RiskMapPage';
import ChaosPage from './pages/ChaosPage';
import FixesPage from './pages/FixesPage';

function AppLayout() {
  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}

export default function App() {
  return (
    <Router>
      <Routes>
        {/* Landing Page — no sidebar */}
        <Route path="/" element={<HomePage />} />

        {/* App Pages — with sidebar */}
        <Route path="/app" element={<AppLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="analyze" element={<AnalyzePage />} />
          <Route path="risks" element={<RiskMapPage />} />
          <Route path="chaos" element={<ChaosPage />} />
          <Route path="fixes" element={<FixesPage />} />
        </Route>
      </Routes>
    </Router>
  );
}
