import { useState, useEffect } from 'react'
import { Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom'
import DashboardLayout from './components/DashboardLayout'
import Dashboard from './components/Dashboard'
import JobsTable from './components/JobsTable'
import TechniciansPage from './components/TechniciansPage'
import FeedbackReportsPage from './components/FeedbackReportsPage'
import LiveChatPage from './components/LiveChatPage'
import Login from './components/Login'

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('access_token'))
  const navigate = useNavigate()
  const location = useLocation()

  // Helper to map paths to the sidebar active label
  const getActivePage = () => {
    if (location.pathname === '/jobs') return 'Jobs'
    if (location.pathname === '/technicians') return 'Technicians'
    if (location.pathname === '/chat') return 'Live Chat'
    if (location.pathname === '/feedback') return 'Feedback'
    return 'Dashboard'
  }

  const handleNavigate = (label) => {
    switch (label) {
      case 'Jobs': navigate('/jobs'); break;
      case 'Technicians': navigate('/technicians'); break;
      case 'Live Chat': navigate('/chat'); break;
      case 'Feedback': navigate('/feedback'); break;
      case 'Dashboard':
      default: navigate('/'); break;
    }
  }

  if (!isAuthenticated) {
    return <Login onLoginSuccess={() => setIsAuthenticated(true)} />
  }

  return (
    <DashboardLayout activePage={getActivePage()} onNavigate={handleNavigate}>
      <Routes>
        <Route path="/" element={<Dashboard onNavigate={handleNavigate} />} />
        <Route path="/jobs" element={<JobsTable />} />
        <Route path="/technicians" element={<TechniciansPage />} />
        <Route path="/chat" element={<LiveChatPage />} />
        <Route path="/feedback" element={<FeedbackReportsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </DashboardLayout>
  )
}

export default App
