import { useState, useEffect, useCallback } from 'react'
import { fetchJobs } from '../services/api'

const STATUS_CONFIG = {
  pending: {
    label: 'Pending',
    bg: 'bg-[var(--color-warning-soft)]',
    text: 'text-[var(--color-warning)]',
    dot: 'bg-[var(--color-warning)]',
  },
  in_progress: {
    label: 'In Progress',
    bg: 'bg-[var(--color-info-soft)]',
    text: 'text-[var(--color-info)]',
    dot: 'bg-[var(--color-info)]',
  },
  completed: {
    label: 'Completed',
    bg: 'bg-[var(--color-success-soft)]',
    text: 'text-[var(--color-success)]',
    dot: 'bg-[var(--color-success)]',
  },
  cancelled: {
    label: 'Cancelled',
    bg: 'bg-[var(--color-danger-soft)]',
    text: 'text-[var(--color-danger)]',
    dot: 'bg-[var(--color-danger)]',
  },
}

const STATUS_FILTERS = [
  { value: '', label: 'All Status' },
  { value: 'pending', label: 'Pending' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'completed', label: 'Completed' },
  { value: 'cancelled', label: 'Cancelled' },
]

function StatusBadge({ status }) {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.pending
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${config.dot}`} />
      {config.label}
    </span>
  )
}

function formatDate(dateStr) {
  if (!dateStr) return '—'
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-IN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function SkeletonRow() {
  return (
    <tr className="animate-pulse">
      {[...Array(6)].map((_, i) => (
        <td key={i} className="px-4 py-3.5">
          <div className="h-4 rounded bg-[var(--color-surface-hover)] w-3/4" />
        </td>
      ))}
    </tr>
  )
}

export default function JobsTable() {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [statusFilter, setStatusFilter] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [refreshing, setRefreshing] = useState(false)

  const loadJobs = useCallback(async (isRefresh = false) => {
    try {
      if (isRefresh) setRefreshing(true)
      else setLoading(true)

      setError(null)
      const data = await fetchJobs({
        status: statusFilter || undefined,
        search: searchQuery || undefined,
      })
      // DRF pagination returns { results: [...] } or raw array
      setJobs(data.results || data)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to load jobs')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [statusFilter, searchQuery])

  useEffect(() => {
    loadJobs()
  }, [loadJobs])

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => loadJobs(true), 30000)
    return () => clearInterval(interval)
  }, [loadJobs])

  return (
    <div className="space-y-4 animate-[fade-in_0.3s_ease]">
      {/* Header + Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-[var(--color-text-primary)]">Jobs</h2>
          <p className="text-sm text-[var(--color-text-muted)] mt-1">
            Manage and track all service requests
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Search */}
          <div className="relative">
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
            </svg>
            <input
              id="search-jobs"
              type="text"
              placeholder="Search jobs…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 pr-4 py-2 w-56 text-sm rounded-lg
                bg-[var(--color-surface)] border border-[var(--color-border)]
                text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)]
                focus:outline-none focus:border-[var(--color-accent)]
                transition-colors"
            />
          </div>

          {/* Status filter */}
          <select
            id="filter-status"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 text-sm rounded-lg cursor-pointer
              bg-[var(--color-surface)] border border-[var(--color-border)]
              text-[var(--color-text-primary)]
              focus:outline-none focus:border-[var(--color-accent)]
              transition-colors"
          >
            {STATUS_FILTERS.map(f => (
              <option key={f.value} value={f.value}>{f.label}</option>
            ))}
          </select>

          {/* Refresh */}
          <button
            id="btn-refresh"
            onClick={() => loadJobs(true)}
            disabled={refreshing}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg
              bg-[var(--color-accent)] text-white
              hover:bg-[var(--color-accent-hover)]
              disabled:opacity-50 disabled:cursor-not-allowed
              transition-all duration-200 cursor-pointer"
          >
            <svg className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182" />
            </svg>
            {refreshing ? 'Refreshing…' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="flex items-center gap-3 p-4 rounded-lg bg-[var(--color-danger-soft)] border border-[var(--color-danger)] text-[var(--color-danger)]">
          <svg className="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
          </svg>
          <span className="text-sm font-medium">{error}</span>
          <button onClick={() => loadJobs()} className="ml-auto text-xs underline cursor-pointer bg-transparent border-0 text-[var(--color-danger)]">
            Retry
          </button>
        </div>
      )}

      {/* Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--color-border)]">
                <th className="text-left px-4 py-3 font-semibold text-[var(--color-text-secondary)] text-xs uppercase tracking-wider">Job ID</th>
                <th className="text-left px-4 py-3 font-semibold text-[var(--color-text-secondary)] text-xs uppercase tracking-wider">Customer</th>
                <th className="text-left px-4 py-3 font-semibold text-[var(--color-text-secondary)] text-xs uppercase tracking-wider">Issue</th>
                <th className="text-left px-4 py-3 font-semibold text-[var(--color-text-secondary)] text-xs uppercase tracking-wider">Status</th>
                <th className="text-left px-4 py-3 font-semibold text-[var(--color-text-secondary)] text-xs uppercase tracking-wider">Technician</th>
                <th className="text-left px-4 py-3 font-semibold text-[var(--color-text-secondary)] text-xs uppercase tracking-wider">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--color-border-subtle)]">
              {loading ? (
                [...Array(5)].map((_, i) => <SkeletonRow key={i} />)
              ) : jobs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-16">
                    <div className="flex flex-col items-center gap-3">
                      <svg className="w-12 h-12 text-[var(--color-text-muted)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 14.15v4.25c0 1.094-.787 2.036-1.872 2.18-2.087.277-4.216.42-6.378.42s-4.291-.143-6.378-.42c-1.085-.144-1.872-1.086-1.872-2.18v-4.25m16.5 0a2.18 2.18 0 0 0 .75-1.661V8.706c0-1.081-.768-2.015-1.837-2.175a48.114 48.114 0 0 0-3.413-.387m4.5 8.006c-.194.165-.42.295-.673.38A23.978 23.978 0 0 1 12 15.75c-2.648 0-5.195-.429-7.577-1.22a2.016 2.016 0 0 1-.673-.38m0 0A2.18 2.18 0 0 1 3 12.489V8.706c0-1.081.768-2.015 1.837-2.175a48.111 48.111 0 0 1 3.413-.387m7.5 0V5.25A2.25 2.25 0 0 0 13.5 3h-3a2.25 2.25 0 0 0-2.25 2.25v.894m7.5 0a48.667 48.667 0 0 0-7.5 0" />
                      </svg>
                      <p className="text-[var(--color-text-muted)] font-medium">No jobs found</p>
                      <p className="text-[var(--color-text-muted)] text-xs">Jobs created via WhatsApp will appear here</p>
                    </div>
                  </td>
                </tr>
              ) : (
                jobs.map((job) => (
                  <tr
                    key={job.id}
                    className="hover:bg-[var(--color-surface-hover)] transition-colors duration-150 cursor-pointer"
                  >
                    <td className="px-4 py-3.5">
                      <span className="font-mono text-xs font-semibold text-[var(--color-accent)]">
                        {job.job_id}
                      </span>
                    </td>
                    <td className="px-4 py-3.5">
                      <span className="font-medium text-[var(--color-text-primary)]">
                        {job.customer_name}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 max-w-xs">
                      <span className="text-[var(--color-text-secondary)] truncate block">
                        {job.description || job.title}
                      </span>
                    </td>
                    <td className="px-4 py-3.5">
                      <StatusBadge status={job.status} />
                    </td>
                    <td className="px-4 py-3.5">
                      <span className="text-[var(--color-text-secondary)]">
                        {job.technician_name || (
                          <span className="italic text-[var(--color-text-muted)]">Unassigned</span>
                        )}
                      </span>
                    </td>
                    <td className="px-4 py-3.5">
                      <span className="text-[var(--color-text-muted)] text-xs">
                        {formatDate(job.created_at)}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Footer with count */}
        {!loading && jobs.length > 0 && (
          <div className="px-4 py-3 border-t border-[var(--color-border-subtle)] flex items-center justify-between">
            <span className="text-xs text-[var(--color-text-muted)]">
              Showing {jobs.length} job{jobs.length !== 1 ? 's' : ''}
            </span>
            <span className="text-xs text-[var(--color-text-muted)]">
              Auto-refreshes every 30s
            </span>
          </div>
        )}
      </div>
    </div>
  )
}
