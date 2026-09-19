export type Maqam = {
  slug: string
  name: string
  arabic: string
  family: string
  tonic: string
  mood: string
  description: string
}

export type Song = {
  id: string
  title: string
  artist: string
  composer: string
  year: number
  maqam: string
  modulations: string[]
  tonic: string
  rhythm: string
  difficulty: 'Beginner' | 'Intermediate' | 'Advanced'
  mood: string
  theme: string
  lyricsExcerpt: string
  sources: { label: string; url: string }[]
}

export const MAQAMAT: Maqam[] = [
  {
    slug: 'bayati',
    name: 'Bayati',
    arabic: 'بياتي',
    family: 'Bayati',
    tonic: 'D (Dukah)',
    mood: 'Tender, intimate, longing',
    description:
      'One of the most beloved maqamat, Bayati carries a warm, emotional quality often used to express yearning and devotion.',
  },
  {
    slug: 'rast',
    name: 'Rast',
    arabic: 'راست',
    family: 'Rast',
    tonic: 'C (Rast)',
    mood: 'Noble, uplifting, balanced',
    description:
      'Considered the mother of maqamat, Rast has a proud and serene character, foundational to Arabic music theory.',
  },
  {
    slug: 'hijaz',
    name: 'Hijaz',
    arabic: 'حجاز',
    family: 'Hijaz',
    tonic: 'D (Dukah)',
    mood: 'Mystical, dramatic, spiritual',
    description:
      'With its distinctive augmented second, Hijaz evokes the desert and the sacred, common in devotional and cinematic music.',
  },
  {
    slug: 'nahawand',
    name: 'Nahawand',
    arabic: 'نهاوند',
    family: 'Nahawand',
    tonic: 'C (Rast)',
    mood: 'Romantic, cinematic, melancholic',
    description:
      'Close to the Western minor scale, Nahawand is expressive and lyrical, favored for love songs and film scores.',
  },
  {
    slug: 'kurd',
    name: 'Kurd',
    arabic: 'كرد',
    family: 'Kurd',
    tonic: 'D (Dukah)',
    mood: 'Contemplative, modern, calm',
    description:
      'A phrygian-flavored maqam with a modern, introspective feel, widely used in contemporary Arabic compositions.',
  },
  {
    slug: 'saba',
    name: 'Saba',
    arabic: 'صبا',
    family: 'Saba',
    tonic: 'D (Dukah)',
    mood: 'Sorrowful, aching, profound',
    description:
      'Saba is the maqam of grief and deep emotion, instantly recognizable and deeply moving to Arabic listeners.',
  },
]

export const RHYTHMS = [
  'Maqsum',
  'Baladi',
  'Wahda',
  'Samai Thaqil',
  'Masmudi',
  'Ayyub',
  'Chiftetelli',
  'Dawr Hindi',
]

export const DIFFICULTIES: Song['difficulty'][] = ['Beginner', 'Intermediate', 'Advanced']

export const SONGS: Song[] = [
  {
    id: 'inta-omri',
    title: 'Enta Omri',
    artist: 'Umm Kulthum',
    composer: 'Mohammed Abdel Wahab',
    year: 1964,
    maqam: 'Kurd',
    modulations: ['Nahawand', 'Hijaz'],
    tonic: 'D (Dukah)',
    rhythm: 'Wahda',
    difficulty: 'Advanced',
    mood: 'Romantic, nostalgic',
    theme: 'A lifetime of love awakened',
    lyricsExcerpt:
      'Your eyes took me back to my days that are gone — you are my life whose morning began with your light.',
    sources: [
      { label: 'AraMusic Archive', url: '#' },
      { label: 'Maqam World', url: '#' },
    ],
  },
  {
    id: 'lamma-bada',
    title: 'Lamma Bada Yatathanna',
    artist: 'Traditional (Muwashshah)',
    composer: 'Anonymous (Andalusian)',
    year: 1900,
    maqam: 'Nahawand',
    modulations: ['Rast'],
    tonic: 'C (Rast)',
    rhythm: 'Samai Thaqil',
    difficulty: 'Intermediate',
    mood: 'Graceful, yearning',
    theme: 'The swaying grace of a beloved',
    lyricsExcerpt:
      'When she began to sway, her beauty enraptured us — a branch that captured me as she moved.',
    sources: [{ label: 'Andalusian Songbook', url: '#' }],
  },
  {
    id: 'fog-el-nakhl',
    title: 'Fog El Nakhal',
    artist: 'Nazem Al-Ghazali',
    composer: 'Iraqi Folk',
    year: 1955,
    maqam: 'Bayati',
    modulations: ['Saba'],
    tonic: 'D (Dukah)',
    rhythm: 'Baladi',
    difficulty: 'Beginner',
    mood: 'Playful, longing',
    theme: 'Admiration from afar',
    lyricsExcerpt:
      'Above the palm trees, oh above them — I could not tell if it was her cheeks or the moon that shone.',
    sources: [{ label: 'Iraqi Heritage', url: '#' }],
  },
  {
    id: 'ya-msafer',
    title: 'Ya Msafer Wahdak',
    artist: 'Mohammed Abdel Wahab',
    composer: 'Mohammed Abdel Wahab',
    year: 1938,
    maqam: 'Hijaz',
    modulations: ['Bayati', 'Nahawand'],
    tonic: 'D (Dukah)',
    rhythm: 'Maqsum',
    difficulty: 'Intermediate',
    mood: 'Sorrowful, wistful',
    theme: 'Longing for one who traveled far',
    lyricsExcerpt:
      'Oh you who travels alone, why did you leave me behind — my heart travels with you across the distance.',
    sources: [
      { label: 'Classic Tarab', url: '#' },
      { label: 'Maqam World', url: '#' },
    ],
  },
  {
    id: 'zeeni',
    title: 'Zeeni',
    artist: 'Fairuz',
    composer: 'The Rahbani Brothers',
    year: 1971,
    maqam: 'Rast',
    modulations: ['Nahawand'],
    tonic: 'C (Rast)',
    rhythm: 'Maqsum',
    difficulty: 'Beginner',
    mood: 'Bright, tender',
    theme: 'Gentle affection and beauty',
    lyricsExcerpt:
      'Adorn me, oh you who fills my days with light — your presence is a morning that never fades.',
    sources: [{ label: 'Rahbani Collection', url: '#' }],
  },
  {
    id: 'gana-el-hawa',
    title: 'Gana El Hawa',
    artist: 'Abdel Halim Hafez',
    composer: 'Baligh Hamdi',
    year: 1969,
    maqam: 'Nahawand',
    modulations: ['Kurd', 'Hijaz'],
    tonic: 'G (Nawa)',
    rhythm: 'Maqsum',
    difficulty: 'Advanced',
    mood: 'Passionate, cinematic',
    theme: 'Love arriving like a storm',
    lyricsExcerpt:
      'Love came to us and stole us away — we walked its path together beneath the moonlight.',
    sources: [
      { label: 'Golden Era Egypt', url: '#' },
      { label: 'AraMusic Archive', url: '#' },
    ],
  },
  {
    id: 'wa-darat-el-ayam',
    title: 'Wa Darat El Ayam',
    artist: 'Umm Kulthum',
    composer: 'Mohammed Abdel Wahab',
    year: 1970,
    maqam: 'Bayati',
    modulations: ['Rast', 'Nahawand'],
    tonic: 'D (Dukah)',
    rhythm: 'Wahda',
    difficulty: 'Advanced',
    mood: 'Reflective, bittersweet',
    theme: 'The turning of days and old love',
    lyricsExcerpt:
      'And the days turned, and you returned to me — as if the years of longing were never gone.',
    sources: [{ label: 'Classic Tarab', url: '#' }],
  },
  {
    id: 'nassam-alayna',
    title: 'Nassam Alayna El Hawa',
    artist: 'Fairuz',
    composer: 'The Rahbani Brothers',
    year: 1975,
    maqam: 'Saba',
    modulations: ['Bayati'],
    tonic: 'D (Dukah)',
    rhythm: 'Baladi',
    difficulty: 'Intermediate',
    mood: 'Melancholic, homesick',
    theme: 'A breeze carrying memories of home',
    lyricsExcerpt:
      'The breeze blew over us from the valley of the beloved — oh breeze, take me to my homeland.',
    sources: [{ label: 'Rahbani Collection', url: '#' }],
  },
]

export const CURRENT_USER = {
  name: 'Layla Mansour',
  role: 'Musician',
  instrument: 'Oud',
  musicRole: 'Performer & Composer',
  experience: 12,
  country: 'Lebanon',
  city: 'Beirut',
  email: 'layla@nagham.ai',
  bio: 'Oud player and composer exploring the crossroads of classical tarab and contemporary Arabic music. Passionate about preserving maqam traditions while writing new repertoire.',
  contributions: 8,
}

export type ChatMessage = {
  id: string
  role: 'user' | 'assistant'
  content: string
  songs?: (Song & { reason: string })[]
}

export const SUGGESTED_PROMPTS = [
  'Give me emotional songs in Maqam Bayati',
  'Find songs about longing and separation',
  'What songs can I play after Enta Omri?',
  'Suggest beginner-friendly songs in Maqam Rast',
  'Which maqam best expresses grief?',
]

export const SAMPLE_CONVERSATION: ChatMessage[] = [
  {
    id: 'm1',
    role: 'user',
    content: 'Give me emotional songs in Maqam Bayati about longing.',
  },
  {
    id: 'm2',
    role: 'assistant',
    content:
      'Bayati is a wonderful choice for longing — its warm, tender character suits songs of yearning beautifully. Here are two pieces that stay in Bayati and center on longing:',
    songs: [
      {
        ...SONGS.find((s) => s.id === 'wa-darat-el-ayam')!,
        reason:
          'Rooted in Bayati with a reflective mood, its lyrics dwell on years of longing and a bittersweet return.',
      },
      {
        ...SONGS.find((s) => s.id === 'fog-el-nakhl')!,
        reason:
          'A Bayati folk gem expressing admiration and yearning from afar, gentle and accessible to play.',
      },
    ],
  },
]

export const PAST_CONVERSATIONS = [
  { id: 'c1', title: 'Emotional songs in Bayati', time: 'Today' },
  { id: 'c2', title: 'Transitions from Hijaz to Nahawand', time: 'Today' },
  { id: 'c3', title: 'Songs about separation', time: 'Yesterday' },
  { id: 'c4', title: 'Beginner oud repertoire', time: 'Yesterday' },
  { id: 'c5', title: 'Umm Kulthum maqam analysis', time: '3 days ago' },
]

export const SEMANTIC_RESULTS = [
  {
    song: SONGS.find((s) => s.id === 'ya-msafer')!,
    relevance: 0.96,
    theme: 'Separation & travel',
    explanation:
      'Directly addresses someone who has traveled far, expressing the ache of being left behind — a near-perfect match for distance and missing.',
  },
  {
    song: SONGS.find((s) => s.id === 'nassam-alayna')!,
    relevance: 0.91,
    theme: 'Homesickness & memory',
    explanation:
      'A breeze carries memories of a distant homeland and beloved, evoking the longing of being apart from what you love.',
  },
  {
    song: SONGS.find((s) => s.id === 'wa-darat-el-ayam')!,
    relevance: 0.84,
    theme: 'Longing over time',
    explanation:
      'Explores years of separation and eventual return, resonating with the feeling of missing someone across a long distance in time.',
  },
  {
    song: SONGS.find((s) => s.id === 'inta-omri')!,
    relevance: 0.72,
    theme: 'Love reawakened',
    explanation:
      'Touches on absence and the pain of days gone by, with strong emotional overlap on themes of yearning.',
  },
]
