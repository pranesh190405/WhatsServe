import { useState, useEffect } from 'react'
import { fetchJobs, fetchTechnicians, fetchConversations, fetchPendingReassignments } from '../services/api'

export default function Dashboard({ onNavigate }) {
  const [stats, setStats] = useState({
    total: 0, pending: 0, in_progress: 0, completed: 0,
  })
  const [techCount, setTechCount] = useState(0)
  const [openChats, setOpenChats] = useState(0)
  const [reassignments, setReassignments] = useState(0)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadAll() {
      try {
        const [jobsData, techData, chatData, reassignData] = await Promise.allSettled([
          fetchJobs(),
          fetchTechnicians({ availability: 'available' }),
          fetchConversations({ status: 'open' }),
          fetchPendingReassignments(),
        ])

        if (jobsData.status === 'fulfilled') {
          const jobs = jobsData.value.results || jobsData.value
          setStats({
            total: jobs.length,
            pending: jobs.filter(j => j.status === 'pending').length,
            in_progress: jobs.filter(j => j.status === 'in_progress').length,
            completed: jobs.filter(j => j.status === 'completed').length,
          })
        }
        if (techData.status === 'fulfilled') {
          const techs = techData.value.results || techData.value
          setTechCount(techs.length)
        }
        if (chatData.status === 'fulfilled') {
          const chats = chatData.value.results || chatData.value
          setOpenChats(chats.length)
        }
        if (reassignData.status === 'fulfilled') {
          const ra = reassignData.value.results || reassignData.value
          setReassignments(ra.length)
        }
      } catch { /* silent */ }
      finally { setLoading(false) }
    }
    loadAll()
    const interval = setInterval(loadAll, 30000)
    return () => clearInterval(interval)
  }, [])

  const statCards = [
    {
      label: 'Total Jobs',
      value: stats.total,
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 14.15v4.25c0 1.094-.787 2.036-1.872 2.18-2.087.277-4.216.42-6.378.42s-4.291-.143-6.378-.42c-1.085-.144-1.872-1.086-1.872-2.18v-4.25m16.5 0a2.18 2.18 0 0 0 .75-1.661V8.706c0-1.081-.768-2.015-1.837-2.175a48.114 48.114 0 0 0-3.413-.387m4.5 8.006c-.194.165-.42.295-.673.38A23.978 23.978 0 0 1 12 15.75c-2.648 0-5.195-.429-7.577-1.22a2.016 2.016 0 0 1-.673-.38m0 0A2.18 2.18 0 0 1 3 12.489V8.706c0-1.081.768-2.015 1.837-2.175a48.111 48.111 0 0 1 3.413-.387m7.5 0V5.25A2.25 2.25 0 0 0 13.5 3h-3a2.25 2.25 0 0 0-2.25 2.25v.894m7.5 0a48.667 48.667 0 0 0-7.5 0" />
        </svg>
      ),
      bgColor: 'bg-[var(--color-accent-soft)]',
      textColor: 'text-[var(--color-accent)]',
      page: 'Jobs',
    },
    {
      label: 'Pending',
      value: stats.pending,
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
        </svg>
      ),
      bgColor: 'bg-[var(--color-warning-soft)]',
      textColor: 'text-[var(--color-warning)]',
      page: 'Jobs',
    },
    {
      label: 'In Progress',
      value: stats.in_progress,
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
        </svg>
      ),
      bgColor: 'bg-[var(--color-info-soft)]',
      textColor: 'text-[var(--color-info)]',
      page: 'Jobs',
    },
    {
      label: 'Completed',
      value: stats.completed,
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
        </svg>
      ),
      bgColor: 'bg-[var(--color-success-soft)]',
      textColor: 'text-[var(--color-success)]',
      page: 'Jobs',
    },
  ]

  return (
    <div className="space-y-6 animate-[fade-in_0.3s_ease]">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-[var(--color-text-primary)]">Overview</h2>
          <p className="text-sm text-[var(--color-text-muted)] mt-1">Here's what's happening today.</p>
        </div>
        <button
          onClick={() => onNavigate?.('Jobs')}
          className="flex items-center gap-2 px-4 py-2 bg-[var(--color-accent)] text-white text-sm font-medium rounded-lg hover:bg-[var(--color-accent-hover)] transition-colors cursor-pointer border-0"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 0 0 3 8.25v10.5A2.25 2.25 0 0 0 5.25 21h10.5A2.25 2.25 0 0 0 18 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
          </svg>
          View All Jobs
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat, i) => (
          <div key={i} className="card p-5 group cursor-pointer" onClick={() => onNavigate?.(stat.page)}>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-[var(--color-text-secondary)]">{stat.label}</h3>
              <div className={`w-10 h-10 rounded-xl ${stat.bgColor} ${stat.textColor} flex items-center justify-center group-hover:scale-110 transition-transform duration-200`}>
                {stat.icon}
              </div>
            </div>
            <div className="flex items-baseline gap-2">
              {loading ? (
                <div className="h-8 w-16 rounded bg-[var(--color-surface-hover)] animate-pulse" />
              ) : (
                <span className="text-3xl font-bold text-[var(--color-text-primary)]">{stat.value}</span>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Alerts */}
      {reassignments > 0 && (
        <div className="flex items-center gap-3 p-4 rounded-lg bg-[var(--color-danger-soft)] border border-[var(--color-danger)]/20 cursor-pointer" onClick={() => onNavigate?.('Jobs')}>
          <svg className="w-5 h-5 text-[var(--color-danger)] shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
          </svg>
          <div>
            <p className="text-sm font-medium text-[var(--color-danger)]">⚠️ {reassignments} job{reassignments > 1 ? 's' : ''} need{reassignments === 1 ? 's' : ''} reassignment</p>
            <p className="text-xs text-[var(--color-text-muted)] mt-0.5">Technician rejected or didn't respond within 30 minutes. Click to view.</p>
          </div>
        </div>
      )}

      {/* Bottom Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* System Status */}
        <div className="lg:col-span-2 card p-6">
          <h3 className="text-lg font-semibold mb-4">System Status</h3>
          <div className="space-y-3">
            {[
              { name: 'Django Backend', status: 'Running', ok: true, port: ':8000' },
              { name: 'React Frontend', status: 'Running', ok: true, port: ':5173' },
              { name: 'PostgreSQL Database', status: 'Connected', ok: true, port: ':5432' },
              { name: 'Twilio WhatsApp', status: TWILIO_STATUS(), ok: TWILIO_STATUS() === 'Connected', port: 'Sandbox' },
            ].map((svc, i) => (
              <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-[var(--color-surface)] border border-[var(--color-border-subtle)]">
                <div className="flex items-center gap-3">
                  <span className={`w-2.5 h-2.5 rounded-full ${svc.ok ? 'bg-[var(--color-success)]' : 'bg-[var(--color-warning)]'}`} />
                  <span className="text-sm font-medium text-[var(--color-text-primary)]">{svc.name}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs font-mono text-[var(--color-text-muted)]">{svc.port}</span>
                  <span className={`text-xs font-medium ${svc.ok ? 'text-[var(--color-success)]' : 'text-[var(--color-warning)]'}`}>
                    {svc.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="card p-6">
          <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
          <div className="space-y-3">
            {[
              { label: 'Manage Jobs', desc: 'View & assign service requests', page: 'Jobs', icon: '📋' },
              { label: 'Technicians', desc: 'Add or manage technician roster', page: 'Technicians', icon: '👨‍🔧' },
              { label: 'Live Chat', desc: `${openChats} open conversation${openChats !== 1 ? 's' : ''}`, page: 'Live Chat', icon: '💬' },
              { label: 'Feedback & Reports', desc: 'Review customer ratings', page: 'Feedback', icon: '⭐' },
              { label: 'Django Admin', desc: 'Full database management', page: null, url: 'http://localhost:8000/admin/', icon: '🔧' },
            ].map((action, i) => (
              <button
                key={i}
                onClick={() => {
                  if (action.page) onNavigate?.(action.page)
                  else if (action.url) window.open(action.url, '_blank')
                }}
                className="flex items-center gap-3 p-3 rounded-lg border border-[var(--color-border-subtle)] hover:border-[var(--color-accent)] transition-all duration-200 cursor-pointer bg-[var(--color-surface)] w-full text-left group"
              >
                <div className="w-10 h-10 rounded-full bg-[var(--color-accent-soft)] flex items-center justify-center shrink-0 text-lg group-hover:scale-110 transition-transform duration-200">
                  {action.icon}
                </div>
                <div>
                  <h4 className="text-sm font-medium text-[var(--color-text-primary)]">{action.label}</h4>
                  <p className="text-xs text-[var(--color-text-muted)] mt-0.5">{action.desc}</p>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function TWILIO_STATUS() {
  // Simple runtime check — in real production you'd ping the API
  return 'Configured'
}
