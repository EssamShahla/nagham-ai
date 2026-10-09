'use client'

import { useEffect, useRef, useState } from 'react'
import { Sparkles, Send, Plus, Loader2 } from 'lucide-react'
import { NaghamMark } from '@/components/nagham-logo'
import { RecommendationCard } from '@/components/assistant/recommendation-card'
import { SUGGESTED_PROMPTS } from '@/lib/mock-data'
import { useCurrentUser } from '@/components/use-current-user'
import { api, ApiError } from '@/lib/api'
import { cn } from '@/lib/utils'

let idCounter = 0
const nextId = () => `msg-${++idCounter}`


type AssistantSong = {
  id: number
  title: string
  artist: string | null
  maqam: string | null
  difficulty: 'easy' | 'medium' | 'hard' | null
  year: number | null
  description: string | null
  moods: string[] | null
  topics: string[] | null
  similarity: number | null
}

type AssistantApiResponse = {
  answer: string
  search_type: 'structured' | 'semantic' | 'hybrid'
  analysis: {
    intent: string
    semantic_query: string
    maqam: string | null
    artist: string | null
    difficulty: string | null
    year: number | null
  }
  results: AssistantSong[]
}

type AssistantChatMessage = {
  id: string
  role: 'user' | 'assistant'
  content: string
  songs?: AssistantSong[]
}



export default function AssistantPage() {
  const currentUser = useCurrentUser()
  const [messages, setMessages] = useState<AssistantChatMessage[]>([])
  const [input, setInput] = useState('')
  const [thinking, setThinking] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, thinking])

  async function send(text: string) {
  const trimmed = text.trim()

  if (!trimmed || thinking) return

  const userMsg: AssistantChatMessage = {
    id: nextId(),
    role: 'user',
    content: trimmed,
  }

  setMessages((prev) => [...prev, userMsg])
  setInput('')
  setThinking(true)

  try {
    const data = await api<AssistantApiResponse>('/assistant', {
      method: 'POST',
      body: { message: trimmed, limit: 5 },
    })

    setMessages((prev) => [
      ...prev,
      {
        id: nextId(),
        role: 'assistant',
        content: data.answer,
        songs: data.results,
      },
    ])
  } catch (error) {
    console.error('Assistant error:', error)

    const content =
      error instanceof ApiError
        ? typeof error.detail === 'string'
          ? error.detail
          : 'Nagham AI ran into a problem answering that. Please try again.'
        : 'Sorry, I could not reach Nagham AI. Please check your connection and try again.'

    setMessages((prev) => [
      ...prev,
      {
        id: nextId(),
        role: 'assistant',
        content,
      },
    ])
  } finally {
    setThinking(false)
  }
}

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      if (e.nativeEvent.isComposing || e.keyCode === 229) return
      e.preventDefault()
      send(input)
    }
  }

  const empty = messages.length === 0

  return (
    <div className="mx-auto grid h-[calc(100vh-8rem)] max-w-6xl gap-6 lg:grid-cols-[260px_1fr]">
      {/* Side rail */}
      <aside className="hidden flex-col lg:flex">
        <button
          onClick={() => setMessages([])}
          disabled={empty}
          className="flex items-center gap-2 rounded-lg border border-gold/25 bg-gold-muted px-3 py-2.5 text-sm font-medium text-gold transition-colors hover:bg-gold hover:text-gold-foreground disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Plus className="size-4" /> New conversation
        </button>
        <p className="mt-6 mb-2 px-1 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
          How Nagham searches
        </p>
        <div className="flex flex-col gap-3 rounded-lg px-3 py-2 text-sm text-muted-foreground">
          <p>
            Nagham reads your request, then chooses structured search (artist, maqam, year),
            semantic search (meaning and mood), or a hybrid of both before answering.
          </p>
          <p>Conversations are not saved between visits — each session starts fresh.</p>
        </div>
      </aside>

      {/* Chat column */}
      <div className="flex min-h-0 flex-col rounded-2xl border border-border bg-card">
        <div ref={scrollRef} className="flex-1 overflow-y-auto p-5 md:p-6">
          {empty ? (
            <div className="flex h-full flex-col items-center justify-center text-center">
              <NaghamMark className="size-14" />
              <h2 className="mt-5 font-display text-2xl font-semibold">Ask Nagham anything</h2>
              <p className="mt-2 max-w-md text-sm text-muted-foreground">
                Describe a mood, a maqam, an occasion, or a song you love. Nagham understands the
                language of Oriental music.
              </p>
              <div className="mt-6 flex max-w-lg flex-wrap justify-center gap-2">
                {SUGGESTED_PROMPTS.map((p) => (
                  <button
                    key={p}
                    onClick={() => send(p)}
                    className="rounded-full border border-border bg-background/50 px-3.5 py-2 text-xs text-muted-foreground transition-colors hover:border-gold/40 hover:text-foreground"
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="flex flex-col gap-6">
              {messages.map((m) => (
                <Message key={m.id} message={m} userName={currentUser.data?.name ?? null} />
              ))}
              {thinking && (
                <div className="flex items-center gap-3">
                  <span className="flex size-8 shrink-0 items-center justify-center rounded-full border border-gold/25 bg-gold-muted">
                    <NaghamMark className="size-5" />
                  </span>
                  <span className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Loader2 className="size-4 animate-spin" />
                    Nagham is thinking…
                  </span>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Composer */}
        <div className="border-t border-border p-3 md:p-4">
          <div className="flex items-end gap-2 rounded-xl border border-input bg-background/40 p-2 focus-within:border-gold/60 focus-within:ring-2 focus-within:ring-ring">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKeyDown}
              rows={1}
              placeholder="Ask for songs by maqam, mood, or moment…"
              className="max-h-32 flex-1 resize-none bg-transparent px-2 py-1.5 text-sm text-foreground outline-none placeholder:text-muted-foreground/70"
            />
            <button
              onClick={() => send(input)}
              disabled={!input.trim() || thinking}
              aria-label="Send message"
              className={cn(
                'flex size-9 shrink-0 items-center justify-center rounded-lg transition-colors',
                input.trim() && !thinking
                  ? 'bg-gold text-gold-foreground hover:bg-gold/90'
                  : 'cursor-not-allowed bg-secondary text-muted-foreground',
              )}
            >
              <Send className="size-4" />
            </button>
          </div>
          <p className="mt-2 px-1 text-center text-xs text-muted-foreground/70">
            Nagham can make mistakes. Verify maqam and rhythm before performance.
          </p>
        </div>
      </div>
    </div>
  )
}

function Message({
  message,
  userName,
}: {
  message: AssistantChatMessage
  userName: string | null
}) {
  if (message.role === 'user') {
    const initials = userName
      ? userName
          .split(' ')
          .filter(Boolean)
          .map((n) => n[0])
          .join('')
          .slice(0, 2)
          .toUpperCase()
      : 'You'.slice(0, 2)
    return (
      <div className="flex items-start justify-end gap-3">
        <div className="max-w-[80%] rounded-2xl rounded-tr-sm bg-secondary px-4 py-2.5 text-sm text-secondary-foreground">
          {message.content}
        </div>
        <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-gold text-xs font-semibold text-gold-foreground">
          {initials}
        </span>
      </div>
    )
  }

  return (
    <div className="flex items-start gap-3">
      <span className="flex size-8 shrink-0 items-center justify-center rounded-full border border-gold/25 bg-gold-muted">
        <NaghamMark className="size-5" />
      </span>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-1.5">
          <span className="text-sm font-semibold">Nagham</span>
          <Sparkles className="size-3.5 text-gold" />
        </div>
        <p className="mt-1.5 text-sm leading-relaxed text-foreground/90">{message.content}</p>
        {message.songs && message.songs.length > 0 && (
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {message.songs.map((s) => (
              <RecommendationCard key={s.id} song={s} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
