/**
 * Minimal Web Audio synthesis for maqam scale preview/playback.
 *
 * These are clearly SYNTHESIZED DEMONSTRATION tones (a filtered triangle
 * oscillator), not a recording of an oud or any real instrument -- always
 * label them as such in the UI. Pitch accuracy is what matters here:
 * frequencies come straight from `computeScaleDegrees`'s exact-cents math,
 * so quarter-tone degrees play at their real in-between frequency instead
 * of snapping to the nearest 12-TET semitone.
 */

let sharedContext: AudioContext | null = null

function getAudioContext(): AudioContext {
  if (!sharedContext) {
    sharedContext = new AudioContext()
  }
  if (sharedContext.state === "suspended") {
    void sharedContext.resume()
  }
  return sharedContext
}

export function playTone(frequencyHz: number, durationSeconds = 0.9): void {
  const ctx = getAudioContext()
  const now = ctx.currentTime

  const oscillator = ctx.createOscillator()
  oscillator.type = "triangle"
  oscillator.frequency.setValueAtTime(frequencyHz, now)

  const filter = ctx.createBiquadFilter()
  filter.type = "lowpass"
  filter.frequency.value = 2200

  const gain = ctx.createGain()
  gain.gain.setValueAtTime(0, now)
  gain.gain.linearRampToValueAtTime(0.28, now + 0.02)
  gain.gain.exponentialRampToValueAtTime(0.0008, now + durationSeconds)

  oscillator.connect(filter).connect(gain).connect(ctx.destination)
  oscillator.start(now)
  oscillator.stop(now + durationSeconds + 0.05)
}

export interface PlaybackHandle {
  cancel: () => void
}

/**
 * Play a sequence of frequencies back to back, calling `onNoteStart` as
 * each one begins (for highlighting). `noteDurationMs` controls tempo;
 * returns a handle so the caller can stop playback early.
 */
export function playSequence(
  frequencies: number[],
  noteDurationMs: number,
  onNoteStart: (index: number) => void,
  onDone?: () => void,
): PlaybackHandle {
  let cancelled = false
  let timeoutId: ReturnType<typeof setTimeout> | null = null

  const step = (index: number) => {
    if (cancelled || index >= frequencies.length) {
      if (!cancelled) onDone?.()
      return
    }
    onNoteStart(index)
    playTone(frequencies[index], (noteDurationMs / 1000) * 0.92)
    timeoutId = setTimeout(() => step(index + 1), noteDurationMs)
  }

  step(0)

  return {
    cancel: () => {
      cancelled = true
      if (timeoutId) clearTimeout(timeoutId)
    },
  }
}
