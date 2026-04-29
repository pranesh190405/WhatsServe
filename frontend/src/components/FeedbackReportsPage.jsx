import { useState, useEffect, useCallback } from 'react'
import { fetchFeedback, fetchReports, createReport, resolveReport } from '../services/api'

const SEVERITY_CONFIG = {
  low:      { label: 'Low',      bg: 'bg-[var(--color-info-soft)]',    text: 'text-[var(--color-info)]' },
  medium:   { label: 'Medium',   bg: 'bg-[var(--color-warning-soft)]', text: 'text-[var(--color-warning)]' },
  high:     { label: 'High',     bg: 'bg-[var(--color-danger-soft)]',  text: 'text-[var(--color-danger)]' },
  critical: { label: 'Critical', bg: 'bg-red-900/30',                  text: 'text-red-400' },
}

function Stars({ count }) {
  return (
    <span className="flex items-center gap-0.5">
      {[1,2,3,4,5].map(i => (
        <svg key={i} className={`w-4 h-4 ${i <= count ? 'text-yellow-400' : 'text-[var(--color-text-muted)]'}`} fill="currentColor" viewBox="0 0 20 20">
          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/>
        </svg>
      ))}
    </span>
  )
}

function ReportModal({ feedback, onClose, onCreated }) {
  const [form, setForm] = useState({
    technician_id: '',
    severity: 'medium',
    reason: feedback ? `Based on feedback: "${feedback.comment}" (${feedback.rating}★)` : '',
    feedback_id: feedback?.id || null,
    job_id: feedback?.job_id || '',
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true); setError(null)
    try {
      // If we have feedback, use the technician from the feedback
      const data = { ...form }
      if (!data.technician_id && feedback?.technician_name) {
        setError('Technician ID required. Check the feedback details.')
        setSaving(false)
        return
      }
      await createReport(data)
      onCreated()
      onClose()
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to file report')
    } finally { setSaving(false) }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={onClose}>
      <div className="card p-6 w-full max-w-md" onClick={e => e.stopPropagation()} style={{ animation: 'fade-in 0.2s ease' }}>
        <h3 className="text-lg font-semibold mb-4">Report Technician</h3>
        {error && <div className="mb-3 p-3 rounded-lg bg-[var(--color-danger-soft)] text-[var(--color-danger)] text-sm">{error}</div>}
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-[var(--color-text-secondary)] mb-1">Technician ID *</label>
            <input type="number" value={form.technician_id} onChange={e => setForm({...form, technician_id: e.target.value})} required
              className="w-full px-3 py-2 text-sm rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text-primary)] focus:outline-none focus:border-[var(--color-accent)]" />
          </div>
          <div>
            <label className="block text-xs font-medium text-[var(--color-text-secondary)] mb-1">Severity</label>
            <select value={form.severity} onChange={e => setForm({...form, severity: e.target.value})}
              className="w-full px-3 py-2 text-sm rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text-primary)] focus:outline-none focus:border-[var(--color-accent)] cursor-pointer">
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-[var(--color-text-secondary)] mb-1">Reason *</label>
            <textarea value={form.reason} onChange={e => setForm({...form, reason: e.target.value})} required rows={3}
              className="w-full px-3 py-2 text-sm rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text-primary)] focus:outline-none focus:border-[var(--color-accent)] resize-y" />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm rounded-lg border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-hover)] cursor-pointer bg-transparent">Cancel</button>
            <button type="submit" disabled={saving} className="px-4 py-2 text-sm font-medium rounded-lg bg-[var(--color-danger)] text-white hover:opacity-90 disabled:opacity-50 cursor-pointer border-0">{saving ? 'Filing…' : 'File Report'}</button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function FeedbackReportsPage() {
  const [tab, setTab] = useState('feedback')
  const [feedbacks, setFeedbacks] = useState([])
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)
  const [ratingFilter, setRatingFilter] = useState('')
  const [severityFilter, setSeverityFilter] = useState('')
  const [reportTarget, setReportTarget] = useState(null)

  const loadFeedback = useCallback(async () => {
    setLoading(true)
    try {
      const data = await fetchFeedback({ rating: ratingFilter || undefined })
      setFeedbacks(data.results || data)
    } catch { /* silent */ }
    finally { setLoading(false) }
  }, [ratingFilter])

  const loadReports = useCallback(async () => {
    setLoading(true)
    try {
      const data = await fetchReports({ severity: severityFilter || undefined })
      setReports(data.results || data)
    } catch { /* silent */ }
    finally { setLoading(false) }
  }, [severityFilter])

  useEffect(() => { tab === 'feedback' ? loadFeedback() : loadReports() }, [tab, loadFeedback, loadReports])

  const handleResolve = async (id) => {
    const action = prompt('Action taken:')
    if (!action) return
    try { await resolveReport(id, action); loadReports() } catch { /* silent */ }
  }

  const formatDate = (d) => d ? new Date(d).toLocaleDateString('en-IN', { year: 'numeric', month: 'short', day: 'numeric' }) : '—'

  return (
    <div className="space-y-4 animate-[fade-in_0.3s_ease]">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-[var(--color-text-primary)]">Feedback & Reports</h2>
          <p className="text-sm text-[var(--color-text-muted)] mt-1">Review customer feedback and manage technician reports</p>
        </div>
      </div>

      {/* Tab switcher */}
      <div className="flex gap-1 p-1 rounded-xl bg-[var(--color-surface-alt)] border border-[var(--color-border)] w-fit">
        {[{id: 'feedback', label: '💬 Customer Feedback'}, {id: 'reports', label: '⚠️ Technician Reports'}].map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`px-5 py-2 text-sm font-medium rounded-lg cursor-pointer border-0 transition-all ${tab === t.id ? 'bg-[var(--color-accent)] text-white shadow-lg' : 'bg-transparent text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]'}`}>
            {t.label}
          </button>
        ))}
      </div>

      {/* ── Feedback Tab ── */}
      {tab === 'feedback' && (
        <>
          <div className="flex gap-3">
            <select value={ratingFilter} onChange={e => setRatingFilter(e.target.value)}
              className="px-3 py-2 text-sm rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text-primary)] focus:outline-none focus:border-[var(--color-accent)] cursor-pointer">
              <option value="">All Ratings</option>
              {[1,2,3,4,5].map(r => <option key={r} value={r}>{r}★</option>)}
            </select>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {loading ? (
              [...Array(4)].map((_, i) => <div key={i} className="card p-5 animate-pulse"><div className="h-24 rounded bg-[var(--color-surface-hover)]" /></div>)
            ) : feedbacks.length === 0 ? (
              <div className="col-span-2 text-center py-16"><p className="text-[var(--color-text-muted)]">No feedback found</p></div>
            ) : feedbacks.map(fb => (
              <div key={fb.id} className="card p-5 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-full bg-[var(--color-accent-soft)] text-[var(--color-accent)] flex items-center justify-center text-sm font-bold">
                      {(fb.customer_name || '?')[0].toUpperCase()}
                    </div>
                    <div>
                      <span className="font-medium text-[var(--color-text-primary)] text-sm">{fb.customer_name}</span>
                      <span className="block text-xs text-[var(--color-text-muted)]">{formatDate(fb.created_at)}</span>
                    </div>
                  </div>
                  <Stars count={fb.rating} />
                </div>
                <p className="text-sm text-[var(--color-text-secondary)]">{fb.comment || <em className="text-[var(--color-text-muted)]">No comment</em>}</p>
                <div className="flex items-center justify-between pt-2 border-t border-[var(--color-border-subtle)]">
                  <div className="flex items-center gap-4 text-xs text-[var(--color-text-muted)]">
                    <span>Job: <strong className="text-[var(--color-accent)]">{fb.job_id}</strong></span>
                    {fb.technician_name && <span>Tech: <strong>{fb.technician_name}</strong></span>}
                  </div>
                  {fb.rating <= 2 && (
                    <button onClick={() => setReportTarget(fb)}
                      className="text-xs text-[var(--color-danger)] hover:underline cursor-pointer bg-transparent border-0 font-medium">
                      ⚠️ Report Technician
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* ── Reports Tab ── */}
      {tab === 'reports' && (
        <>
          <div className="flex gap-3">
            <select value={severityFilter} onChange={e => setSeverityFilter(e.target.value)}
              className="px-3 py-2 text-sm rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text-primary)] focus:outline-none focus:border-[var(--color-accent)] cursor-pointer">
              <option value="">All Severities</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
            <button onClick={() => setReportTarget({})}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-[var(--color-danger)] text-white hover:opacity-90 cursor-pointer border-0">
              + File New Report
            </button>
          </div>
          <div className="card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[var(--color-border)]">
                    {['Technician', 'Severity', 'Reason', 'Status', 'Action Taken', 'Date', ''].map(h => (
                      <th key={h} className="text-left px-4 py-3 font-semibold text-[var(--color-text-secondary)] text-xs uppercase tracking-wider">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--color-border-subtle)]">
                  {loading ? (
                    [...Array(3)].map((_, i) => <tr key={i} className="animate-pulse">{[...Array(7)].map((_, j) => <td key={j} className="px-4 py-3.5"><div className="h-4 rounded bg-[var(--color-surface-hover)] w-3/4" /></td>)}</tr>)
                  ) : reports.length === 0 ? (
                    <tr><td colSpan={7} className="text-center py-16 text-[var(--color-text-muted)]">No reports filed</td></tr>
                  ) : reports.map(r => {
                    const sc = SEVERITY_CONFIG[r.severity] || SEVERITY_CONFIG.medium
                    return (
                      <tr key={r.id} className="hover:bg-[var(--color-surface-hover)] transition-colors">
                        <td className="px-4 py-3.5 font-medium text-[var(--color-text-primary)]">{r.technician_name}</td>
                        <td className="px-4 py-3.5"><span className={`px-2.5 py-1 rounded-full text-xs font-medium ${sc.bg} ${sc.text}`}>{sc.label}</span></td>
                        <td className="px-4 py-3.5 max-w-xs text-[var(--color-text-secondary)] truncate">{r.reason}</td>
                        <td className="px-4 py-3.5">
                          <span className={`text-xs font-medium ${r.is_resolved ? 'text-[var(--color-success)]' : 'text-[var(--color-warning)]'}`}>
                            {r.is_resolved ? '✅ Resolved' : '⏳ Open'}
                          </span>
                        </td>
                        <td className="px-4 py-3.5 max-w-xs text-[var(--color-text-secondary)] truncate">{r.action_taken || '—'}</td>
                        <td className="px-4 py-3.5 text-xs text-[var(--color-text-muted)]">{formatDate(r.created_at)}</td>
                        <td className="px-4 py-3.5">
                          {!r.is_resolved && (
                            <button onClick={() => handleResolve(r.id)} className="text-xs text-[var(--color-success)] hover:underline cursor-pointer bg-transparent border-0 font-medium">Resolve</button>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {reportTarget && <ReportModal feedback={reportTarget.id ? reportTarget : null} onClose={() => setReportTarget(null)} onCreated={() => { loadReports(); setReportTarget(null) }} />}
    </div>
  )
}
