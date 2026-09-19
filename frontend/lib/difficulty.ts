import type { SongDifficulty } from "./types"

export const SONG_DIFFICULTY_LABELS: Record<SongDifficulty, string> = {
  easy: "Beginner",
  medium: "Intermediate",
  hard: "Advanced",
}

export interface SongDifficultyOption {
  value: SongDifficulty
  label: string
}

export const SONG_DIFFICULTY_OPTIONS: SongDifficultyOption[] = [
  { value: "easy", label: "Beginner" },
  { value: "medium", label: "Intermediate" },
  { value: "hard", label: "Advanced" },
]

export function difficultyLabel(value: SongDifficulty | null | undefined): string | null {
  if (value === null || value === undefined) return null
  return SONG_DIFFICULTY_LABELS[value]
}

export function toSongDifficulty(value: string | null | undefined): SongDifficulty | null {
  switch (value) {
    case "easy":
    case "Beginner":
    case "beginner":
      return "easy"
    case "medium":
    case "Intermediate":
    case "intermediate":
      return "medium"
    case "hard":
    case "Advanced":
    case "advanced":
      return "hard"
    default:
      return null
  }
}