import { useEffect, useMemo, useState } from 'react'

function normalizeSubject(subject) {
  const raw = (subject || '').trim()
  if (!raw) return ''

  // Strip common prefixes so threads/newsletters group better.
  let out = raw
  // Repeat because subjects can be "Re: Fwd: Re: ..."
  for (let i = 0; i < 5; i += 1) {
    const next = out.replace(/^(re|fwd|fw)\s*:\s*/i, '').trim()
    if (next === out) break
    out = next
  }

  return out
}

function safeDateLabel(value) {
  const time = Date.parse(value || '')
  if (!Number.isFinite(time)) return value || ''
  return new Date(time).toLocaleString()
}

export default function EmailGroups() {
  const [gmailStatus, setGmailStatus] = useState({ connected: false, emailAddress: null })
  const [emails, setEmails] = useState([])
  const [nextPageToken, setNextPageToken] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [search, setSearch] = useState('')
  const [scope, setScope] = useState('all') // 'all' | 'inbox'
  const [open, setOpen] = useState({})

  async function refreshGmailStatus() {
    try {
      const res = await fetch('/api/status')
      const data = await res.json()
      setGmailStatus({
        connected: Boolean(data.connected),
        emailAddress: data.emailAddress || null,
      })
    } catch {
      setGmailStatus({ connected: false, emailAddress: null })
    }
  }

  useEffect(() => {
    Promise.resolve().then(refreshGmailStatus).catch(() => {})
  }, [])

  function connectGmail() {
    window.location.href = '/auth/google'
  }

  async function disconnectGmail() {
    await fetch('/auth/logout', { method: 'POST' })
    setEmails([])
    setNextPageToken(null)
    await refreshGmailStatus()
  }

  async function loadEmails({ reset } = { reset: false }) {
    setIsLoading(true)
    try {
      const params = new URLSearchParams()
      params.set('max', '50')
      params.set('scope', scope)
      if (!reset && nextPageToken) params.set('pageToken', nextPageToken)

      const res = await fetch(`/api/emails?${params.toString()}`)
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Failed to load emails')

      setEmails((prev) => (reset ? data.emails || [] : [...prev, ...(data.emails || [])]))
      setNextPageToken(data.nextPageToken || null)

      if (reset) setOpen({})
    } catch (err) {
      alert(err.message || String(err))
    } finally {
      setIsLoading(false)
    }
  }

  async function trashEmail(emailId) {
    const ok = window.confirm('Move this email to Trash in Gmail?')
    if (!ok) return

    try {
      const res = await fetch(`/api/emails/${encodeURIComponent(emailId)}/trash`, {
        method: 'POST',
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Failed to trash email')

      setEmails((prev) => prev.filter((e) => e.id !== emailId))
    } catch (err) {
      alert(err.message || String(err))
    }
  }

  const groups = useMemo(() => {
    const query = search.trim().toLowerCase()
    const map = new Map()
    const order = []

    for (const email of emails) {
      const subject = email.subject || ''
      const from = email.from || ''
      const snippet = email.snippet || ''

      if (query) {
        const hay = `${subject}\n${from}\n${snippet}`.toLowerCase()
        if (!hay.includes(query)) continue
      }

      const normalized = normalizeSubject(subject)
      const key = normalized || '(no subject)'

      if (!map.has(key)) {
        map.set(key, { key, subject: normalized || '(no subject)', items: [] })
        order.push(key)
      }
      map.get(key).items.push(email)
    }

    return order.map((k) => map.get(k))
  }, [emails, search])

  return (
    <div className="board">
      <header className="header">
        <div>
          <h1 className="headerTitle">Gmail (Grouped)</h1>
          <p className="headerSubtitle">
            Read emails locally, group by similar subject, and optionally move to Trash.
          </p>
          <div className="toolbar">
            {gmailStatus.connected ? (
              <>
                <span className="pill">
                  Connected: {gmailStatus.emailAddress || 'Gmail'}
                </span>
                <button className="button secondary" type="button" onClick={() => loadEmails({ reset: true })}>
                  Refresh
                </button>
                <button className="button ghost" type="button" onClick={disconnectGmail}>
                  Disconnect
                </button>
              </>
            ) : (
              <button className="button secondary" type="button" onClick={connectGmail}>
                Connect Gmail
              </button>
            )}
          </div>
        </div>

        <div className="composer">
          <div className="composerRow">
            <input
              className="input"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search subject / from / snippet"
              aria-label="Search emails"
            />
            <button
              className="button"
              type="button"
              onClick={() => loadEmails({ reset: true })}
              disabled={!gmailStatus.connected || isLoading}
            >
              {isLoading ? 'Loading...' : 'Load'}
            </button>
          </div>

          <div className="segmented">
            <button
              className={`segButton${scope === 'all' ? ' isActive' : ''}`}
              type="button"
              onClick={() => setScope('all')}
            >
              All mail
            </button>
            <button
              className={`segButton${scope === 'inbox' ? ' isActive' : ''}`}
              type="button"
              onClick={() => setScope('inbox')}
            >
              Inbox only
            </button>
          </div>
          <p className="fineprint">
            Tip: after switching scope, click Load. Use Refresh to reload from the start.
          </p>
        </div>
      </header>

      <section className="groupList" aria-label="Grouped emails">
        {!gmailStatus.connected ? (
          <div className="empty">Connect Gmail to load and group your emails.</div>
        ) : groups.length === 0 ? (
          <div className="empty">No emails loaded yet. Click Load.</div>
        ) : (
          groups.map((group) => {
            const isOpen = Boolean(open[group.key])
            const count = group.items.length
            const latest = group.items[0]?.date

            return (
              <div key={group.key} className="group">
                <button
                  className="groupHeader"
                  type="button"
                  onClick={() => setOpen((prev) => ({ ...prev, [group.key]: !prev[group.key] }))}
                >
                  <div className="groupTitleRow">
                    <div className="groupTitle" title={group.subject}>
                      {group.subject}
                    </div>
                    <span className="badge">{count}</span>
                  </div>
                  <div className="groupMeta">{latest ? `Latest: ${safeDateLabel(latest)}` : ''}</div>
                </button>

                {isOpen ? (
                  <div className="groupBody">
                    {group.items.map((email) => (
                      <div key={email.id} className="emailRow">
                        <div className="emailMain">
                          <div className="emailFrom" title={email.from || ''}>
                            {email.from || '(unknown sender)'}
                          </div>
                          {email.snippet ? (
                            <div className="emailSnippet">{email.snippet}</div>
                          ) : null}
                          {email.date ? (
                            <div className="emailDate">{safeDateLabel(email.date)}</div>
                          ) : null}
                        </div>

                        <div className="emailActions">
                          {email.gmailUrl ? (
                            <a
                              className="linkButton"
                              href={email.gmailUrl}
                              target="_blank"
                              rel="noreferrer"
                            >
                              Open
                            </a>
                          ) : null}
                          <button
                            className="button danger"
                            type="button"
                            onClick={() => trashEmail(email.id)}
                          >
                            Trash
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : null}
              </div>
            )
          })
        )}

        {gmailStatus.connected && nextPageToken ? (
          <button
            className="button secondary loadMore"
            type="button"
            onClick={() => loadEmails({ reset: false })}
            disabled={isLoading}
          >
            {isLoading ? 'Loading...' : 'Load more'}
          </button>
        ) : null}
      </section>
    </div>
  )
}
