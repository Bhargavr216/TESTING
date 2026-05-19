import dotenv from 'dotenv'
import express from 'express'
import { google } from 'googleapis'
import fs from 'node:fs/promises'
import path from 'node:path'

dotenv.config({ path: path.join(process.cwd(), 'server', '.env') })

const PORT = process.env.PORT ? Number(process.env.PORT) : 5174
const CLIENT_URL = process.env.CLIENT_URL || 'http://localhost:5173/'

const GOOGLE_CLIENT_ID = process.env.GOOGLE_CLIENT_ID
const GOOGLE_CLIENT_SECRET = process.env.GOOGLE_CLIENT_SECRET
const GOOGLE_REDIRECT_URI =
  process.env.GOOGLE_REDIRECT_URI || `http://localhost:${PORT}/auth/google/callback`

const DATA_DIR = path.join(process.cwd(), 'server', '.data')
const TOKENS_PATH = path.join(DATA_DIR, 'tokens.json')

const SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

function getOAuthClient() {
  if (!GOOGLE_CLIENT_ID || !GOOGLE_CLIENT_SECRET) {
    throw new Error(
      'Missing GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET. Copy server/.env.example to server/.env and fill it in.',
    )
  }

  return new google.auth.OAuth2(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI)
}

async function readTokens() {
  try {
    const raw = await fs.readFile(TOKENS_PATH, 'utf8')
    return JSON.parse(raw)
  } catch {
    return null
  }
}

async function writeTokens(tokens) {
  await fs.mkdir(DATA_DIR, { recursive: true })
  await fs.writeFile(TOKENS_PATH, JSON.stringify(tokens, null, 2), 'utf8')
}

async function clearTokens() {
  try {
    await fs.unlink(TOKENS_PATH)
  } catch {
    // ignore
  }
}

async function getGmailClient() {
  const tokens = await readTokens()
  if (!tokens) return null

  const auth = getOAuthClient()
  auth.setCredentials(tokens)
  auth.on('tokens', (newTokens) => {
    // Persist refreshed access tokens so the connection keeps working across restarts.
    writeTokens({ ...tokens, ...newTokens }).catch(() => {})
  })
  return google.gmail({ version: 'v1', auth })
}

function headerValue(headers, name) {
  const hit = headers?.find((h) => String(h.name).toLowerCase() === name.toLowerCase())
  return hit?.value || ''
}

const app = express()
app.use(express.json())

app.get('/api/status', async (req, res) => {
  try {
    const gmail = await getGmailClient()
    if (!gmail) return res.json({ connected: false })

    const profile = await gmail.users.getProfile({ userId: 'me' })
    return res.json({
      connected: true,
      emailAddress: profile.data.emailAddress || null,
    })
  } catch (error) {
    return res.json({ connected: false, error: String(error.message || error) })
  }
})

app.get('/auth/google', async (req, res) => {
  try {
    const auth = getOAuthClient()
    const url = auth.generateAuthUrl({
      access_type: 'offline',
      prompt: 'consent',
      scope: SCOPES,
    })

    res.redirect(url)
  } catch (error) {
    res
      .status(500)
      .send(
        `Gmail auth setup error: ${error.message || error}\n\nTip: copy server/.env.example -> server/.env`,
      )
  }
})

app.get('/auth/google/callback', async (req, res) => {
  try {
    const code = req.query.code
    if (!code) return res.status(400).send('Missing ?code from Google callback.')

    const auth = getOAuthClient()
    const { tokens } = await auth.getToken(String(code))
    await writeTokens(tokens)

    res.redirect(CLIENT_URL)
  } catch (error) {
    res.status(500).send(`OAuth callback failed: ${error.message || error}`)
  }
})

app.post('/auth/logout', async (req, res) => {
  await clearTokens()
  res.json({ ok: true })
})

app.get('/api/emails', async (req, res) => {
  try {
    const gmail = await getGmailClient()
    if (!gmail) return res.status(401).json({ error: 'Not connected to Gmail.' })

    const scope = String(req.query.scope || 'all') // 'all' | 'inbox'
    const pageToken = req.query.pageToken ? String(req.query.pageToken) : undefined
    const max = Math.min(Math.max(Number(req.query.max || 25), 1), 50)

    const listArgs = {
      userId: 'me',
      maxResults: max,
      pageToken,
    }

    if (scope === 'inbox') {
      listArgs.labelIds = ['INBOX']
    }

    const list = await gmail.users.messages.list(listArgs)

    const messages = list.data.messages || []
    const out = []

    for (const message of messages) {
      const full = await gmail.users.messages.get({
        userId: 'me',
        id: message.id,
        format: 'metadata',
        metadataHeaders: ['Subject', 'From', 'Date'],
      })

      const headers = full.data.payload?.headers || []
      const id = full.data.id
      const threadId = full.data.threadId || null
      const subject = headerValue(headers, 'Subject')
      const from = headerValue(headers, 'From')
      const date = headerValue(headers, 'Date')
      const snippet = full.data.snippet || ''
      const base = scope === 'inbox' ? 'inbox' : 'all'

      out.push({
        id,
        threadId,
        subject,
        from,
        date,
        snippet,
        gmailUrl: id ? `https://mail.google.com/mail/u/0/#${base}/${id}` : null,
      })
    }

    res.json({ emails: out, nextPageToken: list.data.nextPageToken || null })
  } catch (error) {
    res.status(500).json({ error: String(error.message || error) })
  }
})

app.post('/api/emails/:id/trash', async (req, res) => {
  try {
    const gmail = await getGmailClient()
    if (!gmail) return res.status(401).json({ error: 'Not connected to Gmail.' })

    const id = String(req.params.id || '')
    if (!id) return res.status(400).json({ error: 'Missing message id.' })

    await gmail.users.messages.trash({ userId: 'me', id })
    res.json({ ok: true })
  } catch (error) {
    res.status(500).json({ error: String(error.message || error) })
  }
})

app.listen(PORT, () => {
  console.log(`Gmail backend listening on http://localhost:${PORT}`)
  console.log(`OAuth redirect URI: ${GOOGLE_REDIRECT_URI}`)
})
