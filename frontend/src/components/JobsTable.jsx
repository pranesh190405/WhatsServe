import { useState, useEffect, useCallback } from 'react'
import { fetchJobs, fetchTechnicians, assignTechnician, fetchPendingReassignments } from '../services/api'

const STATUS_CONFIG = {
  pending:     { label: 'Pending',     bg: 'bg-[var(--color-warning-soft)]', text: 'text-[var(--color-warning)]', dot: 'bg-[var(--color-warning)]' },
  in_progress: { label: 'In Progress', bg: 'bg-[var(--color-info-soft)]',    text: 'text-[var(--color-info)]',    dot: 'bg-[var(--color-info)]' },
  completed:   { label: 'Completed',   bg: 'bg-[var(--color-success-soft)]', text: 'text-[var(--color-success)]', dot: 'bg-[var(--color-success)]' },
  cancelled:   { label: 'Cancelled',   bg: 'bg-[var(--color-danger-soft)]',  text: 'text-[var(--color-danger)]',  dot: 'bg-[var(--color-danger)]' },
}

function StatusBadge({ status }) {
  const c = STATUS_CONFIG[status] || STATUS_CONFIG.pending
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${c.bg} ${c.text}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${c.dot}`} />
      {c.label}
    </span>
  )
}

function formatDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('en-IN', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

/* ═══ Assign Modal ═══ */
function AssignModal({ job, onClose, onAssigned }) {
  const [technicians, setTechnicians] = useState([])
  const [loading, setLoading] = useState(true)
  const [assigning, setAssigning] = useState(null)
  const [search, setSearch] = useState('')

  useEffect(() => {
    (async () => {
      try {
        const data = await fetchTechnicians({ availability: 'available', search: search || undefined })
        setTechnicians(data.results || data)
      } catch { /* silent */ }
      finally { setLoading(false) }
    })()
  }, [search])

  const handleAssign = async (techId, techName) => {
    setAssigning(techId)
    try {
      await assignTechnician(job.job_id, techId)
      onAssigned()
      onClose()
    } catch { setAssigning(null) }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={onClose}>
      <div className="card p-6 w-full max-w-md max-h-[80vh] overflow-y-auto" onClick={e => e.stopPropagation()} style={{ animation: 'fade-in 0.2s ease' }}>
        <h3 className="text-lg font-semibold mb-1">Assign Technician</h3>
        <p className="text-sm text-[var(--color-text-muted)] mb-4">
          Job: <strong className="text-[var(--color-accent)]">{job.job_id}</strong> — {job.title}
        </p>
        <input type="text" placeholder="Search technicians…" value={search} onChange={e => setSearch(e.target.value)}
          className="w-full px-3 py-2 mb-3 text-sm rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:border-[var(--color-accent)]" />

        <div className="space-y-2">
          {loading ? (
            <div className="text-center py-8 text-[var(--color-text-muted)]">Loading…</div>
          ) : technicians.length === 0 ? (
            <div className="text-center py-8 text-[var(--color-text-muted)]">No available technicians</div>
          ) : technicians.map(tech => {
            const p = tech.profile || {}
            return (
              <div key={tech.id} className="flex items-center justify-between p-3 rounded-lg bg-[var(--color-surface)] border border-[var(--color-border-subtle)] hover:border-[var(--color-accent)] transition-colors">
                <div>
                  <span className="font-medium text-sm text-[var(--color-text-primary)]">{tech.first_name || tech.username} {tech.last_name || ''}</span>
                  <div className="flex items-center gap-2 mt-0.5">
                    {(p.skills_list || []).slice(0, 2).map((s, i) => (
                      <span key={i} className="text-xs px-1.5 py-0.5 rounded bg-[var(--color-accent-soft)] text-[var(--color-accent)]">{s}</span>
                    ))}
                    <span className="text-xs text-[var(--color-text-muted)]">{Number(p.average_rating || 0).toFixed(1)}★</span>
                  </div>
                </div>
                <button onClick={() => handleAssign(tech.id, tech.username)} disabled={assigning === tech.id}
                  className="px-3 py-1.5 text-xs font-medium rounded-lg bg-[var(--color-accent)] text-white hover:bg-[var(--color-accent-hover)] disabled:opacity-50 cursor-pointer border-0">
                  {assigning === tech.id ? 'Assigning…' : 'Assign'}
                </button>
              </div>
            )
          })}
        </div>

        <p className="text-xs text-[var(--color-text-muted)] mt-3">⏱ Technician will have 30 minutes to accept or reject.</p>
        <div className="flex justify-end mt-4">
          <button onClick={onClose} className="px-4 py-2 text-sm rounded-lg border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-hover)] cursor-pointer bg-transparent">Cancel</button>
        </div>
      </div>
    </div>
  )
}

/* ═══ Main Jobs Page ═══ */
export default function JobsTable() {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [statusFilter, setStatusFilter] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [refreshing, setRefreshing] = useState(false)
  const [assignTarget, setAssignTarget] = useState(null)
  const [reassignments, setReassignments] = useState([])

  const loadJobs = useCallback(async (isRefresh = false) => {
    try {
      if (isRefresh) setRefreshing(true)
      else setLoading(true)
      setError(null)
      const data = await fetchJobs({ status: statusFilter || undefined, search: searchQuery || undefined })
      setJobs(data.results || data)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to load jobs')
    } finally { setLoading(false); setRefreshing(false) }
  }, [statusFilter, searchQuery])

  const loadReassignments = useCallback(async () => {
    try {
      const data = await fetchPendingReassignments()
      setReassignments(data.results || data)
    } catch { /* silent */ }
  }, [])

  useEffect(() => { loadJobs(); loadReassignments() }, [loadJobs, loadReassignments])
  useEffect(() => { const i = setInterval(() => { loadJobs(true); loadReassignments() }, 30000); return () => clearInterval(i) }, [loadJobs, loadReassignments])

  return (
    <div className="space-y-4 animate-[fade-in_0.3s_ease]">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-[var(--color-text-primary)]">Jobs</h2>
          <p className="text-sm text-[var(--color-text-muted)] mt-1">Manage service requests and assign technicians</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" /></svg>
            <input type="text" placeholder="Search jobs…" value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
              className="pl-9 pr-4 py-2 w-56 text-sm rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:border-[var(--color-accent)] transition-colors" />
          </div>
          <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}
            className="px-3 py-2 text-sm rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text-primary)] focus:outline-none focus:border-[var(--color-accent)] cursor-pointer">
            <option value="">All Status</option>
            <option value="pending">Pending</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
            <option value="cancelled">Cancelled</option>
          </select>
          <button onClick={() => loadJobs(true)} disabled={refreshing}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-[var(--color-accent)] text-white hover:bg-[var(--color-accent-hover)] disabled:opacity-50 cursor-pointer border-0 transition-all">
            <svg className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182" /></svg>
            {refreshing ? 'Refreshing…' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Reassignment Alert */}
      {reassignments.length > 0 && (
        <div className="flex items-center gap-3 p-4 rounded-lg bg-[var(--color-danger-soft)] border border-[var(--color-danger)]/30">
          <svg className="w-5 h-5 text-[var(--color-danger)] shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
          </svg>
          <div>
            <p className="text-sm font-medium text-[var(--color-danger)]">
              ⚠️ {reassignments.length} job{reassignments.length > 1 ? 's' : ''} need{reassignments.length === 1 ? 's' : ''} reassignment
            </p>
            <p className="text-xs text-[var(--color-text-muted)] mt-0.5">Technician rejected or didn't respond within 30 minutes</p>
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="flex items-center gap-3 p-4 rounded-lg bg-[var(--color-danger-soft)] border border-[var(--color-danger)] text-[var(--color-danger)]">
          <span className="text-sm font-medium">{error}</span>
          <button onClick={() => loadJobs()} className="ml-auto text-xs underline cursor-pointer bg-transparent border-0 text-[var(--color-danger)]">Retry</button>
        </div>
      )}

      {/* Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--color-border)]">
                {['Job ID', 'Customer', 'Issue', 'Status', 'Technician', 'Created', 'Actions'].map(h => (
                  <th key={h} className="text-left px-4 py-3 font-semibold text-[var(--color-text-secondary)] text-xs uppercase tracking-wider">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--color-border-subtle)]">
              {loading ? (
                [...Array(5)].map((_, i) => <tr key={i} className="animate-pulse">{[...Array(7)].map((_, j) => <td key={j} className="px-4 py-3.5"><div className="h-4 rounded bg-[var(--color-surface-hover)] w-3/4" /></td>)}</tr>)
              ) : jobs.length === 0 ? (
                <tr><td colSpan={7} className="text-center py-16">
                  <p className="text-[var(--color-text-muted)] font-medium">No jobs found</p>
                </td></tr>
              ) : jobs.map(job => {
                const needsAssignment = job.status === 'pending' && !job.technician_name
                const isReassignment = reassignments.some(r => r.job_id === job.job_id)
                return (
                  <tr key={job.id} className={`hover:bg-[var(--color-surface-hover)] transition-colors ${isReassignment ? 'bg-[var(--color-danger-soft)]/50' : ''}`}>
                    <td className="px-4 py-3.5"><span className="font-mono text-xs font-semibold text-[var(--color-accent)]">{job.job_id}</span></td>
                    <td className="px-4 py-3.5 font-medium text-[var(--color-text-primary)]">{job.customer_name}</td>
                    <td className="px-4 py-3.5 max-w-xs text-[var(--color-text-secondary)] truncate">{job.description || job.title}</td>
                    <td className="px-4 py-3.5"><StatusBadge status={job.status} /></td>
                    <td className="px-4 py-3.5 text-[var(--color-text-secondary)]">
                      {job.technician_name || <span className="italic text-[var(--color-text-muted)]">Unassigned</span>}
                    </td>
                    <td className="px-4 py-3.5 text-xs text-[var(--color-text-muted)]">{formatDate(job.created_at)}</td>
                    <td className="px-4 py-3.5">
                      {(needsAssignment || isReassignment) && (
                        <button onClick={() => setAssignTarget(job)}
                          className={`px-3 py-1.5 text-xs font-medium rounded-lg cursor-pointer border-0 transition-colors ${isReassignment ? 'bg-[var(--color-danger)] text-white hover:opacity-90' : 'bg-[var(--color-accent)] text-white hover:bg-[var(--color-accent-hover)]'}`}>
                          {isReassignment ? '🔄 Reassign' : '👤 Assign'}
                        </button>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
        {!loading && jobs.length > 0 && (
          <div className="px-4 py-3 border-t border-[var(--color-border-subtle)] flex items-center justify-between">
            <span className="text-xs text-[var(--color-text-muted)]">{jobs.length} job{jobs.length !== 1 ? 's' : ''}</span>
            <span className="text-xs text-[var(--color-text-muted)]">Auto-refreshes every 30s</span>
          </div>
        )}
      </div>

      {/* Assign Modal */}
      {assignTarget && <AssignModal job={assignTarget} onClose={() => setAssignTarget(null)} onAssigned={() => { loadJobs(); loadReassignments() }} />}
    </div>
  )
}
