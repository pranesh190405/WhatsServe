import { useState, useEffect, useCallback, useRef } from 'react'
import { fetchTechnicians, createTechnician, deleteTechnician, importTechnicians, importTechniciansFile } from '../services/api'

const AVAILABILITY_CONFIG = {
  available: { label: 'Available', bg: 'bg-[var(--color-success-soft)]', text: 'text-[var(--color-success)]', dot: 'bg-[var(--color-success)]' },
  busy:      { label: 'Busy',      bg: 'bg-[var(--color-warning-soft)]', text: 'text-[var(--color-warning)]', dot: 'bg-[var(--color-warning)]' },
  offline:   { label: 'Offline',   bg: 'bg-[var(--color-danger-soft)]',  text: 'text-[var(--color-danger)]',  dot: 'bg-[var(--color-danger)]' },
}

function Badge({ status, config }) {
  const c = config[status] || config[Object.keys(config)[0]]
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${c.bg} ${c.text}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${c.dot}`} />
      {c.label}
    </span>
  )
}

function StarRating({ rating }) {
  return (
    <span className="flex items-center gap-0.5">
      {[1,2,3,4,5].map(i => (
        <svg key={i} className={`w-3.5 h-3.5 ${i <= Math.round(rating) ? 'text-yellow-400' : 'text-[var(--color-text-muted)]'}`} fill="currentColor" viewBox="0 0 20 20">
          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/>
        </svg>
      ))}
      <span className="ml-1 text-xs text-[var(--color-text-muted)]">{Number(rating).toFixed(1)}</span>
    </span>
  )
}

/* ═══ Add Technician Modal ═══ */
function AddTechnicianModal({ onClose, onSave }) {
  const [form, setForm] = useState({ username: '', first_name: '', last_name: '', email: '', phone_number: '', skills: '', availability: 'available', notes: '' })
  const [extraFields, setExtraFields] = useState([])
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  const addExtraField = () => setExtraFields([...extraFields, { key: '', value: '' }])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      const data = { ...form }
      if (extraFields.length) {
        data.extra_fields = {}
        extraFields.forEach(f => { if (f.key) data.extra_fields[f.key] = f.value })
      }
      await createTechnician(data)
      onSave()
      onClose()
    } catch (err) {
      setError(err.response?.data?.detail || err.response?.data?.username?.[0] || 'Failed to create technician')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={onClose}>
      <div className="card p-6 w-full max-w-lg max-h-[85vh] overflow-y-auto" onClick={e => e.stopPropagation()} style={{ animation: 'fade-in 0.2s ease' }}>
        <h3 className="text-lg font-semibold mb-4">Add Technician</h3>
        {error && <div className="mb-4 p-3 rounded-lg bg-[var(--color-danger-soft)] text-[var(--color-danger)] text-sm">{error}</div>}
        <form onSubmit={handleSubmit} className="space-y-3">
          {[
            { name: 'username', label: 'Username *', required: true },
            { name: 'first_name', label: 'First Name' },
            { name: 'last_name', label: 'Last Name' },
            { name: 'email', label: 'Email', type: 'email' },
            { name: 'phone_number', label: 'Phone Number' },
            { name: 'skills', label: 'Skills (comma-separated)' },
            { name: 'notes', label: 'Notes' },
          ].map(f => (
            <div key={f.name}>
              <label className="block text-xs font-medium text-[var(--color-text-secondary)] mb-1">{f.label}</label>
              <input
                type={f.type || 'text'}
                value={form[f.name]}
                onChange={e => setForm({ ...form, [f.name]: e.target.value })}
                required={f.required}
                className="w-full px-3 py-2 text-sm rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:border-[var(--color-accent)] transition-colors"
              />
            </div>
          ))}
          <div>
            <label className="block text-xs font-medium text-[var(--color-text-secondary)] mb-1">Availability</label>
            <select value={form.availability} onChange={e => setForm({ ...form, availability: e.target.value })}
              className="w-full px-3 py-2 text-sm rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text-primary)] focus:outline-none focus:border-[var(--color-accent)] cursor-pointer">
              <option value="available">Available</option>
              <option value="busy">Busy</option>
              <option value="offline">Offline</option>
            </select>
          </div>

          {/* Extra fields */}
          <div className="border-t border-[var(--color-border-subtle)] pt-3 mt-3">
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-medium text-[var(--color-text-secondary)]">Extra Columns</label>
              <button type="button" onClick={addExtraField} className="text-xs text-[var(--color-accent)] hover:underline cursor-pointer bg-transparent border-0">+ Add Column</button>
            </div>
            {extraFields.map((ef, i) => (
              <div key={i} className="flex gap-2 mb-2">
                <input placeholder="Column Name" value={ef.key} onChange={e => { const n = [...extraFields]; n[i].key = e.target.value; setExtraFields(n) }}
                  className="flex-1 px-3 py-1.5 text-sm rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text-primary)] focus:outline-none focus:border-[var(--color-accent)]" />
                <input placeholder="Value" value={ef.value} onChange={e => { const n = [...extraFields]; n[i].value = e.target.value; setExtraFields(n) }}
                  className="flex-1 px-3 py-1.5 text-sm rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text-primary)] focus:outline-none focus:border-[var(--color-accent)]" />
                <button type="button" onClick={() => setExtraFields(extraFields.filter((_,j) => j !== i))} className="text-[var(--color-danger)] hover:text-[var(--color-text-primary)] cursor-pointer bg-transparent border-0 text-sm">✕</button>
              </div>
            ))}
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm rounded-lg border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-hover)] cursor-pointer bg-transparent">Cancel</button>
            <button type="submit" disabled={saving} className="px-4 py-2 text-sm font-medium rounded-lg bg-[var(--color-accent)] text-white hover:bg-[var(--color-accent-hover)] disabled:opacity-50 cursor-pointer border-0">{saving ? 'Creating…' : 'Create Technician'}</button>
          </div>
        </form>
      </div>
    </div>
  )
}

/* ═══ Import Modal ═══ */
function ImportModal({ onClose, onImport }) {
  const [mode, setMode] = useState('json')
  const [jsonText, setJsonText] = useState('[\n  {\n    "username": "tech_example",\n    "first_name": "Example",\n    "skills": "AC Repair, Plumbing"\n  }\n]')
  const [importing, setImporting] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const fileRef = useRef(null)

  const handleJsonImport = async () => {
    setImporting(true); setError(null); setResult(null)
    try {
      const parsed = JSON.parse(jsonText)
      const techs = Array.isArray(parsed) ? parsed : parsed.technicians || []
      const res = await importTechnicians({ technicians: techs })
      setResult(res)
      if (res.created?.length) onImport()
    } catch (err) {
      setError(err.response?.data?.error || err.message || 'Import failed')
    } finally { setImporting(false) }
  }

  const handleFileImport = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setImporting(true); setError(null); setResult(null)
    try {
      const res = await importTechniciansFile(file)
      setResult(res)
      if (res.created?.length) onImport()
    } catch (err) {
      setError(err.response?.data?.error || 'File import failed')
    } finally { setImporting(false) }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={onClose}>
      <div className="card p-6 w-full max-w-xl max-h-[85vh] overflow-y-auto" onClick={e => e.stopPropagation()} style={{ animation: 'fade-in 0.2s ease' }}>
        <h3 className="text-lg font-semibold mb-4">Import Technicians</h3>

        <div className="flex gap-2 mb-4">
          {['json', 'file'].map(m => (
            <button key={m} onClick={() => setMode(m)}
              className={`px-4 py-2 text-sm rounded-lg cursor-pointer border-0 transition-colors ${mode === m ? 'bg-[var(--color-accent)] text-white' : 'bg-[var(--color-surface)] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-hover)]'}`}>
              {m === 'json' ? '📋 JSON' : '📂 Excel / JSON File'}
            </button>
          ))}
        </div>

        {mode === 'json' ? (
          <>
            <label className="block text-xs font-medium text-[var(--color-text-secondary)] mb-1">Paste JSON array:</label>
            <textarea value={jsonText} onChange={e => setJsonText(e.target.value)} rows={8}
              className="w-full px-3 py-2 text-sm font-mono rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text-primary)] focus:outline-none focus:border-[var(--color-accent)] resize-y" />
            <button onClick={handleJsonImport} disabled={importing}
              className="mt-3 px-4 py-2 text-sm font-medium rounded-lg bg-[var(--color-accent)] text-white hover:bg-[var(--color-accent-hover)] disabled:opacity-50 cursor-pointer border-0 w-full">
              {importing ? 'Importing…' : 'Import from JSON'}
            </button>
          </>
        ) : (
          <div className="space-y-3">
            <p className="text-sm text-[var(--color-text-secondary)]">
              Upload an <strong>.xlsx</strong> or <strong>.json</strong> file. Excel columns: username, first_name, last_name, email, phone_number, skills, availability, notes. Any extra columns will be stored as custom fields.
            </p>
            <input ref={fileRef} type="file" accept=".xlsx,.xls,.json" onChange={handleFileImport}
              className="block w-full text-sm text-[var(--color-text-secondary)] file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-[var(--color-accent)] file:text-white hover:file:bg-[var(--color-accent-hover)] file:cursor-pointer cursor-pointer" />
          </div>
        )}

        {error && <div className="mt-3 p-3 rounded-lg bg-[var(--color-danger-soft)] text-[var(--color-danger)] text-sm">{error}</div>}
        {result && (
          <div className="mt-3 p-3 rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] text-sm space-y-1">
            <p className="text-[var(--color-success)] font-medium">{result.message}</p>
            {result.created?.length > 0 && <p className="text-[var(--color-text-secondary)]">Created: {result.created.join(', ')}</p>}
            {result.errors?.length > 0 && (
              <div className="text-[var(--color-danger)]">
                <p className="font-medium">Errors:</p>
                {result.errors.map((e, i) => <p key={i}>Row {e.row}: {e.error}</p>)}
              </div>
            )}
          </div>
        )}

        <div className="flex justify-end mt-4">
          <button onClick={onClose} className="px-4 py-2 text-sm rounded-lg border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-hover)] cursor-pointer bg-transparent">Close</button>
        </div>
      </div>
    </div>
  )
}

/* ═══ Main Page ═══ */
export default function TechniciansPage() {
  const [technicians, setTechnicians] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [availability, setAvailability] = useState('')
  const [showAddModal, setShowAddModal] = useState(false)
  const [showImportModal, setShowImportModal] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const data = await fetchTechnicians({ availability: availability || undefined, search: search || undefined })
      setTechnicians(data.results || data)
    } catch { /* silent */ }
    finally { setLoading(false) }
  }, [availability, search])

  useEffect(() => { load() }, [load])

  const handleDelete = async (id, username) => {
    if (!confirm(`Deactivate technician "${username}"?`)) return
    try { await deleteTechnician(id); load() } catch { /* silent */ }
  }

  return (
    <div className="space-y-4 animate-[fade-in_0.3s_ease]">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-[var(--color-text-primary)]">Technicians</h2>
          <p className="text-sm text-[var(--color-text-muted)] mt-1">Manage your service technicians</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
            </svg>
            <input type="text" placeholder="Search…" value={search} onChange={e => setSearch(e.target.value)}
              className="pl-9 pr-4 py-2 w-48 text-sm rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:border-[var(--color-accent)] transition-colors" />
          </div>
          <select value={availability} onChange={e => setAvailability(e.target.value)}
            className="px-3 py-2 text-sm rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text-primary)] focus:outline-none focus:border-[var(--color-accent)] cursor-pointer">
            <option value="">All Status</option>
            <option value="available">Available</option>
            <option value="busy">Busy</option>
            <option value="offline">Offline</option>
          </select>
          <button onClick={() => setShowImportModal(true)} className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg border border-[var(--color-accent)] text-[var(--color-accent)] hover:bg-[var(--color-accent-soft)] cursor-pointer bg-transparent transition-colors">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5" /></svg>
            Import
          </button>
          <button onClick={() => setShowAddModal(true)} className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-[var(--color-accent)] text-white hover:bg-[var(--color-accent-hover)] cursor-pointer border-0 transition-colors">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" /></svg>
            Add Technician
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--color-border)]">
                {['Name', 'Phone', 'Skills', 'Status', 'Rating', 'Jobs Done', 'Reports', 'Actions'].map(h => (
                  <th key={h} className="text-left px-4 py-3 font-semibold text-[var(--color-text-secondary)] text-xs uppercase tracking-wider">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--color-border-subtle)]">
              {loading ? (
                [...Array(4)].map((_, i) => (
                  <tr key={i} className="animate-pulse">
                    {[...Array(8)].map((_, j) => <td key={j} className="px-4 py-3.5"><div className="h-4 rounded bg-[var(--color-surface-hover)] w-3/4" /></td>)}
                  </tr>
                ))
              ) : technicians.length === 0 ? (
                <tr>
                  <td colSpan={8} className="text-center py-16">
                    <p className="text-[var(--color-text-muted)] font-medium">No technicians found</p>
                    <p className="text-[var(--color-text-muted)] text-xs mt-1">Add technicians manually or import from a file</p>
                  </td>
                </tr>
              ) : technicians.map(tech => {
                const p = tech.profile || {}
                return (
                  <tr key={tech.id} className="hover:bg-[var(--color-surface-hover)] transition-colors">
                    <td className="px-4 py-3.5">
                      <div>
                        <span className="font-medium text-[var(--color-text-primary)]">{tech.first_name || tech.username} {tech.last_name || ''}</span>
                        <span className="block text-xs text-[var(--color-text-muted)]">@{tech.username}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3.5 text-[var(--color-text-secondary)]">{tech.phone_number || '—'}</td>
                    <td className="px-4 py-3.5">
                      <div className="flex flex-wrap gap-1">
                        {(p.skills_list || []).slice(0, 3).map((s, i) => (
                          <span key={i} className="px-2 py-0.5 text-xs rounded-full bg-[var(--color-accent-soft)] text-[var(--color-accent)]">{s}</span>
                        ))}
                        {(p.skills_list || []).length > 3 && <span className="text-xs text-[var(--color-text-muted)]">+{p.skills_list.length - 3}</span>}
                      </div>
                    </td>
                    <td className="px-4 py-3.5"><Badge status={p.availability || 'offline'} config={AVAILABILITY_CONFIG} /></td>
                    <td className="px-4 py-3.5"><StarRating rating={p.average_rating || 0} /></td>
                    <td className="px-4 py-3.5 text-center text-[var(--color-text-secondary)]">{p.total_jobs_completed || 0}</td>
                    <td className="px-4 py-3.5 text-center">
                      <span className={`text-sm font-medium ${(p.report_count || 0) > 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-text-muted)]'}`}>
                        {p.report_count || 0}
                      </span>
                    </td>
                    <td className="px-4 py-3.5">
                      <button onClick={() => handleDelete(tech.id, tech.username)}
                        className="text-xs text-[var(--color-danger)] hover:underline cursor-pointer bg-transparent border-0">Deactivate</button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
        {!loading && technicians.length > 0 && (
          <div className="px-4 py-3 border-t border-[var(--color-border-subtle)]">
            <span className="text-xs text-[var(--color-text-muted)]">{technicians.length} technician{technicians.length !== 1 ? 's' : ''}</span>
          </div>
        )}
      </div>

      {/* Modals */}
      {showAddModal && <AddTechnicianModal onClose={() => setShowAddModal(false)} onSave={load} />}
      {showImportModal && <ImportModal onClose={() => setShowImportModal(false)} onImport={load} />}
    </div>
  )
}
