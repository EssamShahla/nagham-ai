export type SongDifficulty = "easy" | "medium" | "hard"

export interface SongResponse {
  id: number
  title: string
  lyrics: string | null
  description: string | null
  moods: string[] | null
  topics: string[] | null
  year: number | null
  difficulty: SongDifficulty | null
  artist_id: number
  artist_name: string
  composer_id: number | null
  composer_name: string | null
  rhythm_id: number | null
  rhythm_name: string | null
  maqam_id: number | null
  maqam_name: string | null
  created_by: number
}

export interface SemanticSearchResult {
  id: number
  title: string
  artist_id: number
  artist_name: string | null
  description: string | null
  moods: string[] | null
  topics: string[] | null
  maqam_id: number | null
  maqam_name: string | null
  similarity: number
}

export interface SemanticSearchResponse {
  query: string
  count: number
  results: SemanticSearchResult[]
}

export interface SongListResponse {
  items: SongResponse[]
  page: number
  page_size: number
  total: number
  pages: number
}

export type SongSourceType =
  | "website"
  | "book"
  | "article"
  | "database"
  | "user_contribution"
  | "other"

export interface SongSourceResponse {
  id: number
  song_id: number
  source_type: string
  source_url: string | null
  title: string | null
  description: string | null
  created_by: number
  created_at: string
}

export interface ArtistResponse {
  id: number
  name_ar: string
  name_en: string | null
  bio: string | null
}

export interface ComposerResponse {
  id: number
  name_ar: string
  name_en: string | null
  bio: string | null
}

export interface JinsResponse {
  id: number
  name_ar: string
  name_en: string | null
  tonic: string | null
  accidentals: string | null
  scale_pattern: number[] | null
  description: string | null
  notes: string | null
}

export interface MaqamResponse {
  id: number
  name_ar: string
  name_en: string | null
  tonic: string | null
  accidentals: string | null
  scale_pattern: number[] | null
  root_jins_id: number | null
  branch_jins_id: number | null
  root_jins: JinsResponse | null
  branch_jins: JinsResponse | null
  ghammaz: string | null
  mood: string | null
  notation_format: string
  musicxml_data: string | null
  audio_sample_url: string | null
  description: string | null
  notes: string | null
}

export interface RhythmResponse {
  id: number
  name_ar: string
  name_en: string | null
  time_signature: string | null
  pattern_text: string | null
  notation_format: string
  musicxml_data: string | null
  audio_sample_url: string | null
  sample_bpm: number | null
  description: string | null
  notes: string | null
}

export interface UserResponse {
  id: number
  name: string
  email: string
  instrument: string | null
  phone: string | null
  country: string | null
  city: string | null
  music_role: string | null
  years_of_experience: number | null
  bio: string | null
  is_verified: boolean
  profile_completed: boolean
  auth_provider: string
  role: string
}