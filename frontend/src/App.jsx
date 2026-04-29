import { useState } from 'react'
import DashboardLayout from './components/DashboardLayout'
import Dashboard from './components/Dashboard'
import JobsTable from './components/JobsTable'
import TechniciansPage from './components/TechniciansPage'
import FeedbackReportsPage from './components/FeedbackReportsPage'

function App() {
  const [activePage, setActivePage] = useState('Dashboard')

  const renderPage = () => {
    switch (activePage) {
      case 'Jobs':
        return <JobsTable />
      case 'Technicians':
        return <TechniciansPage />
      case 'Feedback':
        return <FeedbackReportsPage />
      case 'Dashboard':
      default:
        return <Dashboard onNavigate={setActivePage} />
    }
  }

  return (
    <DashboardLayout activePage={activePage} onNavigate={setActivePage}>
      {renderPage()}
    </DashboardLayout>
  )
}

export default App
