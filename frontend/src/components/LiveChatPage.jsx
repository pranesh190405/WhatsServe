import { useState, useEffect, useCallback, useRef } from 'react'
import { fetchConversations, fetchConversationDetail, sendMessage, closeConversation } from '../services/api'

const STATUS_CONFIG = {
  open:        { label: 'Open',        bg: 'bg-[var(--color-warning-soft)]', text: 'text-[var(--color-warning)]' },
  assigned:    { label: 'Assigned',    bg: 'bg-[var(--color-info-soft)]',    text: 'text-[var(--color-info)]' },
  in_progress: { label: 'In Progress', bg: 'bg-[var(--color-info-soft)]',    text: 'text-[var(--color-info)]' },
  resolved:    { label: 'Resolved',    bg: 'bg-[var(--color-success-soft)]', text: 'text-[var(--color-success)]' },
  closed:      { label: 'Closed',      bg: 'bg-[var(--color-surface-hover)]',text: 'text-[var(--color-text-muted)]' },
}

function StatusBadge({ status }) {
  const c = STATUS_CONFIG[status] || STATUS_CONFIG.open
  return <span className={`px-2 py-0.5 rounded text-xs font-medium ${c.bg} ${c.text}`}>{c.label}</span>
}

export default function LiveChatPage() {
  const [conversations, setConversations] = useState([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState('open')

  const [activeSession, setActiveSession] = useState(null)
  const [messages, setMessages] = useState([])
  const [messageInput, setMessageInput] = useState('')
  const [sending, setSending] = useState(false)
  const messagesEndRef = useRef(null)

  const loadConversations = useCallback(async () => {
    setLoading(true)
    try {
      const data = await fetchConversations({ status: statusFilter !== 'all' ? statusFilter : undefined })
      setConversations(data.results || data)
    } catch { /* silent */ }
    finally { setLoading(false) }
  }, [statusFilter])

  useEffect(() => { loadConversations() }, [loadConversations])

  // Auto-refresh lists and active chat
  useEffect(() => {
    const interval = setInterval(() => {
      loadConversations()
      if (activeSession) {
        loadMessages(activeSession.id, false)
      }
    }, 15000)
    return () => clearInterval(interval)
  }, [loadConversations, activeSession])

  const loadMessages = async (id, scroll = true) => {
    try {
      const data = await fetchConversationDetail(id)
      setActiveSession(data.conversation)
      setMessages(data.messages)
      if (scroll) {
        setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 100)
      }
    } catch { /* silent */ }
  }

  const handleSelectSession = (session) => {
    loadMessages(session.id)
  }

  const handleSend = async (e) => {
    e.preventDefault()
    if (!messageInput.trim() || !activeSession) return

    setSending(true)
    try {
      const data = await sendMessage(activeSession.id, messageInput)
      setMessages([...messages, data.chat_message])
      setMessageInput('')
      setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 100)
      loadConversations() // update list
    } catch { /* silent */ }
    finally { setSending(false) }
  }

  const handleClose = async () => {
    if (!activeSession || !confirm('Mark this conversation as resolved?')) return
    try {
      const data = await closeConversation(activeSession.id)
      setActiveSession(data.conversation)
      loadConversations()
      loadMessages(activeSession.id)
    } catch { /* silent */ }
  }

  return (
    <div className="flex flex-col md:flex-row gap-4 h-[calc(100vh-8rem)] animate-[fade-in_0.3s_ease]">
      {/* ── Left Sidebar: Conversations List ── */}
      <div className="card flex flex-col w-full md:w-1/3 h-full overflow-hidden shrink-0">
        <div className="p-4 border-b border-[var(--color-border)]">
          <h2 className="text-lg font-bold text-[var(--color-text-primary)] mb-3">Live Chat</h2>
          <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}
            className="w-full px-3 py-2 text-sm rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text-primary)] focus:outline-none focus:border-[var(--color-accent)] cursor-pointer">
            <option value="open">Open / In Progress</option>
            <option value="resolved">Resolved</option>
            <option value="all">All Conversations</option>
          </select>
        </div>
        
        <div className="flex-1 overflow-y-auto">
          {loading && conversations.length === 0 ? (
            <div className="p-4 space-y-3">
              {[1,2,3].map(i => <div key={i} className="h-16 bg-[var(--color-surface-hover)] animate-pulse rounded-lg" />)}
            </div>
          ) : conversations.length === 0 ? (
            <div className="p-8 text-center text-sm text-[var(--color-text-muted)]">No conversations found.</div>
          ) : (
            <div className="divide-y divide-[var(--color-border-subtle)]">
              {conversations.map(conv => (
                <button key={conv.id} onClick={() => handleSelectSession(conv)}
                  className={`w-full text-left p-4 hover:bg-[var(--color-surface-hover)] transition-colors border-0 cursor-pointer ${activeSession?.id === conv.id ? 'bg-[var(--color-surface-hover)] border-l-2 border-l-[var(--color-accent)]' : 'bg-transparent border-l-2 border-l-transparent'}`}>
                  <div className="flex justify-between items-start mb-1">
                    <span className="font-medium text-sm text-[var(--color-text-primary)]">{conv.customer_name}</span>
                    <StatusBadge status={conv.status} />
                  </div>
                  <p className="text-xs text-[var(--color-text-secondary)] truncate">
                    {conv.last_message ? conv.last_message.content : 'No messages yet'}
                  </p>
                  <div className="flex justify-between items-center mt-2 text-[10px] text-[var(--color-text-muted)]">
                    <span>{conv.job ? `Job: ${conv.job}` : 'General Inquiry'}</span>
                    <span>{new Date(conv.updated_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ── Right Area: Chat Window ── */}
      <div className="card flex flex-col w-full md:w-2/3 h-full overflow-hidden">
        {activeSession ? (
          <>
            {/* Chat Header */}
            <div className="p-4 border-b border-[var(--color-border)] flex justify-between items-center bg-[var(--color-surface-alt)]">
              <div>
                <h3 className="font-semibold text-[var(--color-text-primary)] flex items-center gap-2">
                  {activeSession.customer_name}
                  <StatusBadge status={activeSession.status} />
                </h3>
                <p className="text-xs text-[var(--color-text-secondary)] mt-0.5">
                  {activeSession.job ? `Regarding Job: ${activeSession.job}` : 'General Inquiry'}
                </p>
              </div>
              {['open', 'assigned', 'in_progress'].includes(activeSession.status) && (
                <button onClick={handleClose} className="px-3 py-1.5 text-xs font-medium rounded text-[var(--color-success)] border border-[var(--color-success)] hover:bg-[var(--color-success-soft)] transition-colors cursor-pointer bg-transparent">
                  Mark Resolved
                </button>
              )}
            </div>

            {/* Chat Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-[var(--color-surface)]">
              {messages.map((msg, i) => {
                const isAgent = msg.sender_type === 'agent'
                const isSystem = msg.sender_type === 'system'
                
                if (isSystem) {
                  return (
                    <div key={msg.id} className="text-center">
                      <span className="text-[10px] px-2 py-1 rounded bg-[var(--color-surface-hover)] text-[var(--color-text-muted)]">
                        {msg.content}
                      </span>
                    </div>
                  )
                }
                
                return (
                  <div key={msg.id} className={`flex flex-col ${isAgent ? 'items-end' : 'items-start'}`}>
                    <span className="text-[10px] text-[var(--color-text-muted)] mb-1 mx-1">
                      {isAgent ? 'You' : msg.sender_name} • {new Date(msg.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                    </span>
                    <div className={`px-4 py-2 rounded-2xl max-w-[80%] text-sm ${
                      isAgent 
                        ? 'bg-[var(--color-accent)] text-white rounded-tr-sm' 
                        : 'bg-[var(--color-surface-hover)] text-[var(--color-text-primary)] border border-[var(--color-border)] rounded-tl-sm'
                    }`}>
                      {msg.content}
                    </div>
                  </div>
                )
              })}
              <div ref={messagesEndRef} />
            </div>

            {/* Chat Input */}
            {['open', 'assigned', 'in_progress'].includes(activeSession.status) ? (
              <form onSubmit={handleSend} className="p-3 border-t border-[var(--color-border)] bg-[var(--color-surface-alt)] flex gap-2">
                <input
                  type="text"
                  value={messageInput}
                  onChange={e => setMessageInput(e.target.value)}
                  placeholder="Type a message... (Will be sent via WhatsApp)"
                  className="flex-1 px-4 py-2 text-sm rounded-full bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:border-[var(--color-accent)] transition-colors"
                />
                <button type="submit" disabled={sending || !messageInput.trim()}
                  className="w-10 h-10 rounded-full bg-[var(--color-accent)] text-white flex items-center justify-center hover:bg-[var(--color-accent-hover)] disabled:opacity-50 transition-colors cursor-pointer border-0 shrink-0">
                  <svg className="w-4 h-4 ml-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
                  </svg>
                </button>
              </form>
            ) : (
              <div className="p-3 border-t border-[var(--color-border)] bg-[var(--color-surface-alt)] text-center text-xs text-[var(--color-text-muted)]">
                This conversation is closed.
              </div>
            )}
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-[var(--color-text-muted)] p-8">
            <svg className="w-16 h-16 mb-4 opacity-20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M8.625 9.75a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375m-13.5 3.01c0 1.6 1.123 2.994 2.707 3.227 1.087.16 2.185.283 3.293.369V21l4.184-4.183a1.14 1.14 0 01.778-.332 48.294 48.294 0 005.83-.498c1.585-.233 2.708-1.626 2.708-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z" />
            </svg>
            <p>Select a conversation from the left to start chatting.</p>
          </div>
        )}
      </div>
    </div>
  )
}
