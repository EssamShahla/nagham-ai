/**
 * Pure music-theory math shared by the interactive notation and the audio
 * engine: turns a tonic + `scale_pattern` (tone-unit intervals, the
 * project's existing DB convention -- 1.0 = whole tone = 200 cents) into
 * per-degree pitch data.
 *
 * Frequencies are computed from exact cents, NOT rounded to the nearest
 * 12-TET semitone -- quarter-tone degrees (half-flat, etc.) get their real
 * in-between frequency. Only the *notation spelling* (which letter +
 * which accidental glyph) snaps to the nearest 50-cent quarter-tone grid,
 * since that's what can actually be drawn/labeled.
 */

const LETTER_ORDER = ["C", "D", "E", "F", "G", "A", "B"] as const
type Letter = (typeof LETTER_ORDER)[number]

const NATURAL_SEMITONE: Record<Letter, number> = {
  C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11,
}

export interface ParsedTonic {
  letter: Letter
  accidentalSemitones: number // -1 flat, 0 natural, +1 sharp
  octave: number
}

export function parseTonic(tonic: string): ParsedTonic {
  const match = /^([A-G])(#|b)?(\d)$/.exec(tonic.trim())
  if (!match) {
    throw new Error(`Unrecognized tonic format: "${tonic}" (expected e.g. "D4", "Bb4")`)
  }
  const [, letter, accidental, octaveStr] = match
  return {
    letter: letter as Letter,
    accidentalSemitones: accidental === "b" ? -1 : accidental === "#" ? 1 : 0,
    octave: Number(octaveStr),
  }
}

/** Standard 12-TET reference frequency for the tonic itself (A4 = 440Hz). */
export function tonicFrequencyHz(tonic: ParsedTonic): number {
  const absoluteSemitone =
    NATURAL_SEMITONE[tonic.letter] + tonic.accidentalSemitones + tonic.octave * 12
  const a4AbsoluteSemitone = NATURAL_SEMITONE.A + 4 * 12
  return 440 * Math.pow(2, (absoluteSemitone - a4AbsoluteSemitone) / 12)
}

export type AccidentalKind =
  | "natural"
  | "half-flat"
  | "flat"
  | "three-quarter-flat"
  | "half-sharp"
  | "sharp"
  | "three-quarter-sharp"

export interface ScaleDegree {
  /** 0-based index; the last entry (index length-1) is the octave. */
  index: number
  /** Cumulative cents from the tonic, exact (not snapped). */
  cents: number
  /** Real frequency in Hz, computed from exact cents -- never 12-TET-rounded. */
  frequencyHz: number
  /** Natural letter name this degree is spelled with (diatonic letter-cycling). */
  letter: Letter
  octave: number
  accidental: AccidentalKind
  /** Documented Arabic degree name, if the DB provided one (never invented). */
  label: string | null
}

const ACCIDENTAL_BY_DEVIATION: Record<number, AccidentalKind> = {
  [-150]: "three-quarter-flat",
  [-100]: "flat",
  [-50]: "half-flat",
  [0]: "natural",
  [50]: "half-sharp",
  [100]: "sharp",
  [150]: "three-quarter-sharp",
}

/**
 * Compute every scale degree (including the octave) for a jins/maqam.
 *
 * `scalePattern` has N intervals for an (N+1)-note scale (the last note
 * being the octave/end of this jins/maqam fragment).
 */
export function computeScaleDegrees(
  tonic: string,
  scalePattern: number[],
  degreeNames?: string[] | null,
): ScaleDegree[] {
  const parsedTonic = parseTonic(tonic)
  const tonicHz = tonicFrequencyHz(parsedTonic)
  const tonicLetterIndex = LETTER_ORDER.indexOf(parsedTonic.letter)
  const tonicNaturalAbs = NATURAL_SEMITONE[parsedTonic.letter]
  const tonicActualAbs = tonicNaturalAbs + parsedTonic.accidentalSemitones

  const cumulativeCents = [0]
  for (const toneInterval of scalePattern) {
    cumulativeCents.push(cumulativeCents[cumulativeCents.length - 1] + toneInterval * 200)
  }

  return cumulativeCents.map((cents, index) => {
    const letterIndex = (tonicLetterIndex + index) % 7
    const octaveOffset = Math.floor((tonicLetterIndex + index) / 7)
    const letter = LETTER_ORDER[letterIndex]
    const naturalAbs = NATURAL_SEMITONE[letter] + 12 * octaveOffset
    const expectedDistanceSemitones = naturalAbs - tonicActualAbs
    const deviationCents = cents - expectedDistanceSemitones * 100
    const snappedDeviation = Math.round(deviationCents / 50) * 50
    const accidental = ACCIDENTAL_BY_DEVIATION[snappedDeviation] ?? "natural"

    return {
      index,
      cents,
      frequencyHz: tonicHz * Math.pow(2, cents / 1200),
      letter,
      octave: parsedTonic.octave + octaveOffset,
      accidental,
      label: degreeNames?.[index] ?? null,
    }
  })
}

/** VexFlow accidental codes (verified against VexFlow 5's microtonal glyph set). */
export const VEXFLOW_ACCIDENTAL_CODE: Record<AccidentalKind, string | null> = {
  natural: null,
  "half-flat": "d",
  flat: "b",
  "three-quarter-flat": "db",
  "half-sharp": "+",
  sharp: "#",
  "three-quarter-sharp": "++",
}

export const ACCIDENTAL_LABEL_AR: Record<AccidentalKind, string> = {
  natural: "",
  "half-flat": "نصف بيمول",
  flat: "بيمول",
  "three-quarter-flat": "ثلاثة أرباع بيمول",
  "half-sharp": "نصف دييز",
  sharp: "دييز",
  "three-quarter-sharp": "ثلاثة أرباع دييز",
}
