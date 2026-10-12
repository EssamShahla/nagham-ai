'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import { Accidental, Formatter, Renderer, Stave, StaveNote, Voice } from 'vexflow'
import { Pause, Play, Volume2 } from 'lucide-react'

import {
  ACCIDENTAL_LABEL_AR,
  VEXFLOW_ACCIDENTAL_CODE,
  computeScaleDegrees,
  type ScaleDegree,
} from '@/lib/maqam-theory'
import { playSequence, playTone, type PlaybackHandle } from '@/lib/maqam-audio'
import { Button } from '@/components/ui/button'

type PlayDirection = 'ascending' | 'descending' | 'both'

const HIGHLIGHT_COLOR = '#c9a227' // matches the --gold token's approximate hex
const DEFAULT_COLOR = '#1f2d2d'

function setNoteColor(el: SVGElement, color: string) {
  el.querySelectorAll('path, ellipse, rect, line').forEach((node) => {
    ;(node as SVGElement).style.fill = color
    ;(node as SVGElement).style.stroke = color
  })
}

export function MaqamNotation({
  tonic,
  scalePattern,
  degreeNames,
  title,
}: {
  tonic: string
  scalePattern: number[]
  degreeNames?: string[] | null
  title?: string
}) {
  const containerRef = useRef<HTMLDivElement>(null)
  const noteElementsRef = useRef<SVGElement[]>([])
  const playbackRef = useRef<PlaybackHandle | null>(null)

  const [playingIndex, setPlayingIndex] = useState<number | null>(null)
  const [noteDurationMs, setNoteDurationMs] = useState(650)

  const { degrees, theoryError } = useMemo((): {
    degrees: ScaleDegree[]
    theoryError: string | null
  } => {
    try {
      return { degrees: computeScaleDegrees(tonic, scalePattern, degreeNames), theoryError: null }
    } catch (error) {
      return {
        degrees: [],
        theoryError: error instanceof Error ? error.message : 'Could not compute the scale.',
      }
    }
  }, [tonic, scalePattern, degreeNames])

  useEffect(() => {
    if (!containerRef.current || degrees.length === 0) return

    containerRef.current.innerHTML = ''

    const width = Math.max(420, 62 * degrees.length + 90)
    const renderer = new Renderer(containerRef.current, Renderer.Backends.SVG)
    renderer.resize(width, 170)
    const context = renderer.getContext()

    const stave = new Stave(10, 28, width - 24)
    stave.addClef('treble')
    stave.setContext(context).draw()

    const notes = degrees.map((degree) => {
      const key = `${degree.letter.toLowerCase()}/${degree.octave}`
      const note = new StaveNote({ keys: [key], duration: 'q' })
      const accidentalCode = VEXFLOW_ACCIDENTAL_CODE[degree.accidental]
      if (accidentalCode) {
        note.addModifier(new Accidental(accidentalCode))
      }
      return note
    })

    const voice = new Voice({ numBeats: degrees.length, beatValue: 4 })
    voice.setStrict(false)
    voice.addTickables(notes)
    new Formatter().joinVoices([voice]).format([voice], width - 110)
    voice.draw(context, stave)

    const elements = notes
      .map((note) => note.getSVGElement())
      .filter((el): el is SVGElement => Boolean(el))

    elements.forEach((el, index) => {
      el.style.cursor = 'pointer'
      el.setAttribute('tabindex', '0')
      el.setAttribute('role', 'button')
      const degree = degrees[index]
      const label = degree.label ?? `${degree.letter}${degree.accidental !== 'natural' ? ` ${ACCIDENTAL_LABEL_AR[degree.accidental]}` : ''}`
      el.setAttribute('aria-label', `تشغيل الدرجة: ${label}`)

      const play = () => {
        playTone(degree.frequencyHz)
        setPlayingIndex(index)
        window.setTimeout(() => setPlayingIndex((current) => (current === index ? null : current)), 500)
      }
      el.addEventListener('click', play)
      el.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault()
          play()
        }
      })
    })

    noteElementsRef.current = elements

    return () => {
      playbackRef.current?.cancel()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [degrees])

  useEffect(() => {
    noteElementsRef.current.forEach((el, index) => {
      setNoteColor(el, index === playingIndex ? HIGHLIGHT_COLOR : DEFAULT_COLOR)
    })
  }, [playingIndex])

  const handlePlayScale = (direction: PlayDirection) => {
    playbackRef.current?.cancel()

    const ascendingIndices = degrees.map((_, i) => i)
    const descendingIndices = [...ascendingIndices].reverse()
    const order =
      direction === 'ascending'
        ? ascendingIndices
        : direction === 'descending'
          ? descendingIndices
          : [...ascendingIndices, ...descendingIndices.slice(1)]

    const frequencies = order.map((i) => degrees[i].frequencyHz)

    playbackRef.current = playSequence(
      frequencies,
      noteDurationMs,
      (sequencePosition) => setPlayingIndex(order[sequencePosition]),
      () => setPlayingIndex(null),
    )
  }

  const handleStop = () => {
    playbackRef.current?.cancel()
    setPlayingIndex(null)
  }

  if (theoryError) {
    return (
      <div className="rounded-xl border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
        تعذر عرض السلم الموسيقي: {theoryError}
      </div>
    )
  }

  return (
    <div className="rounded-2xl border border-gold/20 bg-background/40 p-4 md:p-6">
      {title && <h3 className="mb-2 font-display text-lg font-semibold">{title}</h3>}

      <div className="overflow-x-auto">
        <div ref={containerRef} className="min-w-fit" />
      </div>

      <p className="mt-2 flex items-center gap-1.5 text-xs text-muted-foreground">
        <Volume2 className="size-3.5" />
        نغمات تجريبية صناعية (Synthesized demo tones) — ليست تسجيلًا لآلة عود حقيقية.
      </p>

      <div className="mt-4 flex flex-wrap items-center gap-2">
        <Button size="sm" variant="outline" onClick={() => handlePlayScale('ascending')}>
          <Play className="size-3.5" /> صعودًا
        </Button>
        <Button size="sm" variant="outline" onClick={() => handlePlayScale('descending')}>
          <Play className="size-3.5 -scale-x-100" /> نزولًا
        </Button>
        <Button size="sm" variant="outline" onClick={() => handlePlayScale('both')}>
          <Play className="size-3.5" /> صعودًا ونزولًا
        </Button>
        <Button size="sm" variant="ghost" onClick={handleStop}>
          <Pause className="size-3.5" /> إيقاف
        </Button>

        <label className="ml-auto flex items-center gap-2 text-xs text-muted-foreground">
          السرعة
          <input
            type="range"
            min={300}
            max={1200}
            step={50}
            value={1500 - noteDurationMs}
            onChange={(event) => setNoteDurationMs(1500 - Number(event.target.value))}
            className="accent-gold"
            aria-label="سرعة التشغيل"
          />
        </label>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-x-4 gap-y-1.5 text-xs text-muted-foreground sm:grid-cols-4">
        {degrees.map((degree, index) => (
          <button
            key={index}
            type="button"
            onClick={() => {
              playTone(degree.frequencyHz)
              setPlayingIndex(index)
              window.setTimeout(() => setPlayingIndex((c) => (c === index ? null : c)), 500)
            }}
            className={`rounded-md px-2 py-1 text-right transition-colors hover:bg-gold-muted ${
              index === playingIndex ? 'bg-gold-muted text-gold' : ''
            }`}
          >
            {degree.label ?? `${degree.letter}${degree.octave}`}
            {degree.accidental !== 'natural' && (
              <span className="text-[10px] opacity-70"> ({ACCIDENTAL_LABEL_AR[degree.accidental]})</span>
            )}
          </button>
        ))}
      </div>
    </div>
  )
}
