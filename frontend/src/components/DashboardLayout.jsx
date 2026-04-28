import Sidebar from './Sidebar'
import Topbar from './Topbar'

export default function DashboardLayout({ children }) {
  return (
    <div className="min-h-screen bg-[var(--color-surface)] flex">
      <Sidebar />
      <div className="flex-1 ml-[240px] flex flex-col transition-all duration-300">
        <Topbar />
        <main className="flex-1 p-6 overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  )
}
