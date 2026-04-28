export default function Topbar() {
  return (
    <header
      id="topbar"
      className="
        h-16 shrink-0
        flex items-center justify-between px-6
        glass sticky top-0 z-20
        border-b border-[var(--color-border)]
      "
    >
      {/* Left — Page title */}
      <div className="flex items-center gap-3">
        <h1 className="text-lg font-semibold text-[var(--color-text-primary)]">
          Dashboard
        </h1>
        <span className="hidden sm:inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-[var(--color-success-soft)] text-[var(--color-success)]">
          Live
        </span>
      </div>

      {/* Right — Actions */}
      <div className="flex items-center gap-4">
        {/* Search */}
        <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text-muted)] text-sm">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
          </svg>
          <span>Search…</span>
          <kbd className="ml-4 px-1.5 py-0.5 text-xs rounded bg-[var(--color-surface-raised)] text-[var(--color-text-muted)] border border-[var(--color-border)]">
            ⌘K
          </kbd>
        </div>

        {/* Notification bell */}
        <button
          id="btn-notifications"
          className="
            relative p-2 rounded-lg
            text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]
            hover:bg-[var(--color-surface-hover)] transition-colors duration-200
            cursor-pointer border-0 bg-transparent
          "
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.967 8.967 0 0 1-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 0 1-5.714 0m5.714 0a3 3 0 1 1-5.714 0" />
          </svg>
          {/* Notification dot */}
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-[var(--color-danger)]" style={{ animation: 'pulse-glow 2s infinite' }} />
        </button>

        {/* Avatar */}
        <button
          id="btn-avatar"
          className="
            w-8 h-8 rounded-full
            bg-gradient-to-br from-[var(--color-accent)] to-[#a78bfa]
            flex items-center justify-center
            text-white text-xs font-bold
            cursor-pointer border-2 border-transparent
            hover:border-[var(--color-accent-hover)] transition-colors duration-200
          "
        >
          P
        </button>
      </div>
    </header>
  )
}
