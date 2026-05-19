import { useEffect, useMemo, useState } from 'react'
import Column from './Column.jsx'

const COLUMNS = [
  { id: 'inbox', title: 'Inbox' },
  { id: 'to_reply', title: 'To Reply' },
  { id: 'follow_up', title: 'Follow Up' },
  { id: 'done', title: 'Done' },
]

function makeId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) return crypto.randomUUID()
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`
}

const STARTER_CARDS = [
  {
    id: makeId(),
    title: 'Welcome!',
    description: 'Drag cards between columns, or use the arrow buttons.',
    status: 'inbox',
  },
  {
    id: makeId(),
    title: 'Reply to recruiter',
    description: 'Confirm interview time and ask about next steps.',
    status: 'to_reply',
  },
  {
    id: makeId(),
    title: 'Vendor invoice',
    description: 'Follow up if payment is still pending after Friday.',
    status: 'follow_up',
  },
]

export default function Board() {
  const [cards, setCards] = useState(STARTER_CARDS)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [gmailStatus, setGmailStatus] = useState({ connected: false, emailAddress: null })
  const [isImporting, setIsImporting] = useState(false)

  const statusOrder = useMemo(() => COLUMNS.map((c) => c.id), [])

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
    Promise.resolve().then(refreshGmailStatus)
  }, [])

  function addCard(event) {
    event.preventDefault()

    const trimmedTitle = title.trim()
    const trimmedDescription = description.trim()
    if (!trimmedTitle) return

    const newCard = {
      id: makeId(),
      title: trimmedTitle,
      description: trimmedDescription,
      status: 'inbox',
    }

    setCards((prev) => [newCard, ...prev])
    setTitle('')
    setDescription('')
  }

  function connectGmail() {
    window.location.href = '/auth/google'
  }

  async function disconnectGmail() {
    await fetch('/auth/logout', { method: 'POST' })
    await refreshGmailStatus()
  }

  async function importFromGmail() {
    setIsImporting(true)
    try {
      const res = await fetch('/api/emails?max=15')
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Failed to import emails')

      setCards((prev) => {
        const already = new Set(
          prev.filter((c) => c.source === 'gmail').map((c) => c.externalId),
        )

        const imported = (data.emails || [])
          .filter((e) => e.id && !already.has(e.id))
          .map((e) => ({
            id: makeId(),
            title: e.subject || '(no subject)',
            description: [e.from, e.snippet].filter(Boolean).join('\n'),
            status: 'inbox',
            source: 'gmail',
            externalId: e.id,
            url: e.gmailUrl || null,
          }))

        return [...imported, ...prev]
      })
    } catch (error) {
      alert(error.message || String(error))
    } finally {
      setIsImporting(false)
    }
  }

  function moveCardToStatus(cardId, nextStatus) {
    setCards((prev) =>
      prev.map((card) => (card.id === cardId ? { ...card, status: nextStatus } : card)),
    )
  }

  function moveCardLeft(cardId) {
    setCards((prev) => {
      const card = prev.find((c) => c.id === cardId)
      if (!card) return prev

      const currentIndex = statusOrder.indexOf(card.status)
      const nextIndex = currentIndex - 1
      if (nextIndex < 0) return prev

      return prev.map((c) =>
        c.id === cardId ? { ...c, status: statusOrder[nextIndex] } : c,
      )
    })
  }

  function moveCardRight(cardId) {
    setCards((prev) => {
      const card = prev.find((c) => c.id === cardId)
      if (!card) return prev

      const currentIndex = statusOrder.indexOf(card.status)
      const nextIndex = currentIndex + 1
      if (nextIndex >= statusOrder.length) return prev

      return prev.map((c) =>
        c.id === cardId ? { ...c, status: statusOrder[nextIndex] } : c,
      )
    })
  }

  return (
    <div className="board">
      <header className="header">
        <div>
          <h1 className="headerTitle">Email Kanban</h1>
          <p className="headerSubtitle">A simple way to track email follow-ups.</p>
          <div className="toolbar">
            {gmailStatus.connected ? (
              <>
                <span className="pill">
                  Connected: {gmailStatus.emailAddress || 'Gmail'}
                </span>
                <button
                  className="button secondary"
                  type="button"
                  onClick={importFromGmail}
                  disabled={isImporting}
                >
                  {isImporting ? 'Importing...' : 'Import from Gmail'}
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

        <form className="composer" onSubmit={addCard}>
          <div className="composerRow">
            <input
              className="input"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Email title (required)"
              aria-label="Email title"
            />
            <button className="button" type="submit" disabled={!title.trim()}>
              Add
            </button>
          </div>
          <textarea
            className="textarea"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Short description (optional)"
            aria-label="Email description"
            rows={2}
          />
        </form>
      </header>

      <div className="columns">
        {COLUMNS.map((column) => {
          const columnCards = cards.filter((c) => c.status === column.id)
          const columnIndex = statusOrder.indexOf(column.id)

          return (
            <Column
              key={column.id}
              column={column}
              cards={columnCards}
              canMoveLeft={columnIndex > 0}
              canMoveRight={columnIndex < statusOrder.length - 1}
              onDropCard={(cardId) => moveCardToStatus(cardId, column.id)}
              onMoveLeft={moveCardLeft}
              onMoveRight={moveCardRight}
            />
          )
        })}
      </div>
    </div>
  )
}
