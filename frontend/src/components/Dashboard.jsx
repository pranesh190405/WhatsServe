import { useState } from 'react'

const stats = [
  { label: 'Total Feedback', value: '1,248', trend: '+12%', isPositive: true },
  { label: 'Avg Rating', value: '4.8', trend: '+0.2', isPositive: true },
  { label: 'Open Jobs', value: '42', trend: '-3', isPositive: false },
  { label: 'Automations', value: '8 active', trend: '0', isPositive: true },
]

export default function Dashboard() {
  return (
    <div className="space-y-6 animate-[fade-in_0.3s_ease]">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-[var(--color-text-primary)]">Overview</h2>
          <p className="text-sm text-[var(--color-text-muted)] mt-1">Here's what's happening today.</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-[var(--color-accent)] text-white text-sm font-medium rounded-lg hover:bg-[var(--color-accent-hover)] transition-colors">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          New Job
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, i) => (
          <div key={i} className="card p-5">
            <h3 className="text-sm font-medium text-[var(--color-text-secondary)]">{stat.label}</h3>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-3xl font-bold text-[var(--color-text-primary)]">{stat.value}</span>
              <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                stat.isPositive
                  ? 'bg-[var(--color-success-soft)] text-[var(--color-success)]'
                  : 'bg-[var(--color-danger-soft)] text-[var(--color-danger)]'
              }`}>
                {stat.trend}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Main Content Area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Col (2/3) */}
        <div className="lg:col-span-2 space-y-6">
          <div className="card p-6 min-h-[400px]">
            <h3 className="text-lg font-semibold mb-4">Recent Feedback</h3>
            <div className="flex items-center justify-center h-[300px] border border-dashed border-[var(--color-border)] rounded-lg bg-[var(--color-surface)]">
              <p className="text-[var(--color-text-muted)]">Data visualization will go here</p>
            </div>
          </div>
        </div>

        {/* Right Col (1/3) */}
        <div className="space-y-6">
          <div className="card p-6 min-h-[400px]">
            <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="flex items-center gap-3 p-3 rounded-lg border border-[var(--color-border-subtle)] hover:border-[var(--color-border)] transition-colors cursor-pointer bg-[var(--color-surface)]">
                  <div className="w-10 h-10 rounded-full bg-[var(--color-accent-soft)] text-[var(--color-accent)] flex items-center justify-center shrink-0">
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
                    </svg>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-[var(--color-text-primary)]">Action {i}</h4>
                    <p className="text-xs text-[var(--color-text-muted)] mt-0.5">Execute webhook flow</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
