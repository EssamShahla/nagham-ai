# Conversational song creation through the Nagham AI agent — implementation report (2026-10-12)

A new multi-turn LangGraph workflow lets a logged-in user add a song to
Nagham AI purely by chatting in Arabic/Palestinian dialect: the agent
collects missing required fields across turns, resolves artists/
composers/maqamat/rhythms against the real database, shows an Arabic
confirmation summary, writes the song (and any newly-named artist/
composer) in one atomic transaction only after explicit confirmation, and
verifies the row actually persisted before claiming success. **Nothing
has been committed or deployed; no demo song has been inserted into the
real dev database** — all verification below used the disposable pytest
test database.

## 1. What was built, mapped to the requirements

### Architecture reuse (requirement 1)
- `app/services/song_service.py` (previously empty) now holds the real
  validation/duplicate-detection/embedding logic, shared by both the
  pre-existing `POST /songs` REST endpoint and the new conversational
  flow — one code path, not two. `routers/songs.py`'s `create_song` is
  now a thin wrapper over `create_song_and_embed`.
- Embeddings are generated through the unchanged existing pipeline
  (`build_song_embedding_text` + `generate_embedding` in
  `app/ai/semantic_search.py`).
- Entity resolution reuses `app/ai/arabic_text.py`'s fuzzy DB matching
  (`canonicalize_value`/a new `resolve_to_id` that also returns the id,
  plus a new `"rhythm"` category added to the existing generic matcher)
  — the same machinery already used by song search.
- The new `song_creation` intent follows the exact same
  deterministic-routing + LangGraph-node pattern as every other
  non-search intent from prior sessions (`lyrics_request`, `follow_up`,
  etc.) in `app/ai/conversation.py` / `app/ai/graph.py`.

### Intent recognition (requirement 2)
`app/ai/song_creation.py`'s `SONG_CREATION_MARKERS` require an explicit
add/create verb ("ضيف", "أضيف", "اضافة", "سجل اغنية", "انشاء اغنية", ...),
checked in `classify_deterministic_intent` — deliberately not just the
word "جديدة" (new), so "أعطيني أغاني جديدة" (give me new songs, an
ordinary search) never matches. **Continuation takes priority**: if the
most recent assistant turn was itself an in-progress song-creation draft,
the next message is routed there regardless of its wording — this is
what lets a bare "اسمها نسمة ليل" continue a draft.

### Conversational collection (requirement 3)
One LLM extraction call per turn (`extract_song_creation_fields` in
`app/ai/agent.py`, a `SongCreationExtraction` schema mirroring the
existing `SongSearchIntent` pattern) pulls whatever fields are explicitly
stated; only `title` and `artist` are ever required (matching the DB's
actual `NOT NULL` columns). The in-progress draft round-trips through the
client-resent `history` in the assistant turn's `analysis.draft_song` —
reusing the existing session-scoped history mechanism, no new
persistence, exactly as specified.

### Validation + confirmation (requirement 4)
- Artist/composer names are fuzzy-matched against real rows
  (`resolve_to_id`); maqam/rhythm are curated reference data and are
  **never auto-created** — an unresolved one prompts the user to pick a
  real value or explicitly skip it ("بدون مقام").
- Duplicate title+artist is checked both at collection time (so the user
  isn't walked through confirming a doomed insert) and again, fresh, at
  final-confirmation time.
- A concise Arabic summary (title, artist, maqam, composer, lyricist,
  musical key, rhythm, difficulty, description — whichever are set) is
  shown before any write, with an explicit yes/no ask.

### The write (requirement 5) — and the three security adjustments you required
This is the part most different from a naive "LLM calls a tool"
implementation:

1. **No speculative entity creation.** An unresolved artist/composer name
   is only ever *staged* as `{"kind": "new", "name": ...}` after the user
   explicitly confirms creating it — nothing is written to `artists`/
   `composers` during collection.
2. **Server-authoritative confirmation.** Reaching the confirmation stage
   creates a `PendingSongCreation` row (new table, modeled directly on
   the existing `LoginExchangeCode`/`PendingGoogleLink` pattern: opaque
   `secrets.token_urlsafe(32)` token, `user_id`, JSON `payload`,
   `expires_at`, single-use `is_used`). Only the opaque token crosses
   through `history` from then on. A confirm re-fetches this row with
   `SELECT ... FOR UPDATE`, rejects if it's missing/expired/already-used/
   belongs to a different authenticated user, and only ever writes the
   row's own stored payload — **never** anything a client might have
   echoed back in a forged `history`.
3. **Corrections re-validate.** At the confirming stage, a message that
   changes a field (detected by re-running extraction and diffing against
   the stored payload — a plain "نعم"/"لا" is checked first and never
   reaches the extractor, see §3 below) invalidates the old pending row
   (`is_used = True`) and issues a brand-new one with a fresh summary and
   token. The old token is permanently dead even if resent.

The actual insert — `create_song_with_staged_entities` in
`song_service.py` — creates any staged-new `Artist`/`Composer` row, the
`Song` row, and its embedding inside **one transaction**: any failure
rolls back everything (no orphan artist left behind). After commit, the
row is **re-queried fresh** (not just the in-memory ORM object) before
success is ever reported — on any exception, the pending row is already
marked used (so the failed attempt can't be silently replayed) and the
agent states plainly that the song was *not* saved.

### Success + searchability (requirement 6)
The success message names the song's id, title, artist, and maqam, all
read back from the verified, re-fetched row. Because the write goes
through the exact same embedding pipeline as every other song, the new
row is immediately visible to both structured and semantic search with
no extra wiring — proven directly in
`test_success_with_new_artist_is_atomic_and_searchable` (§4).

### Protecting existing behavior (requirement 7)
- `/assistant` gained an **optional** auth dependency
  (`get_current_user_optional` in `app/core/security.py`,
  `HTTPBearer(auto_error=False)`) — search/theory/lyrics stay usable
  anonymously exactly as before; only song creation requires a logged-in
  user, replying with an Arabic login prompt otherwise. The existing
  `get_current_user` (hard-required by `POST /songs` etc.) is untouched.
- A bare "نعم"/"لا" is intercepted by a deterministic keyword check
  **before** ever reaching the LLM extractor — necessary because a direct
  test showed qwen2.5:3b will hallucinate an entire fake song (fabricated
  title/artist/composer/maqam/difficulty/description/URL) if asked to
  extract fields from a one-word message. See §3.
- No lyrics are ever fabricated by this flow (it never writes `lyrics` at
  all — only metadata fields).
- The REST `/songs`, `/song-sources`, auth, and Maqam Explorer endpoints
  are either untouched or (in `/songs`' case) refactored to call the same
  underlying service with identical validation order and status codes.

## 2. New schema (additive only, migration `6be68279fb4e`)

- `songs.lyricist_name TEXT NULL`, `songs.musical_key TEXT NULL`.
- New table `pending_song_creations` (see above).

No existing rows were touched.

## 3. A real bug this work surfaced (not just a test issue)

While testing, a bare confirmation reply ("نعم") run through
`extract_song_creation_fields` caused qwen2.5:3b to fabricate an entire
unrelated song — e.g. asked to extract fields from just "نعم", it
returned `{"title": "اسمها نور", "artist": "الفنان عمر خيرت", "composer":
"الملحن محمد مصطفى", "maqam": "مقام الكورد", ...}`, a fully invented
song with no relation to the conversation. The fix
(`app/ai/song_creation.py`'s `_handle_collecting`) skips the extractor
call entirely for a bare yes/no or a bare "بدون مقام/وزن" skip
instruction — these carry no extractable information, and the
deterministic keyword check already handles them. This is the same class
of small-model unreliability documented in the previous session's quality
report, now also fixed here.

## 4. Test results

- **`backend/tests/test_assistant_song_creation.py`: 12/12 passing**,
  covering: login-required, multi-turn collection across `history`,
  one-shot multi-field extraction, unknown maqam → explicit skip, 
  duplicate refused at collection, cancellation, a simulated DB failure
  (honest error, pending row left non-replayable), success with a
  brand-new artist created atomically and proven immediately searchable
  (both structured and semantic), an ordinary search never triggering
  creation, replay-of-confirmation rejected, cross-user token theft
  rejected (and the legitimate owner's token proven still usable
  afterward), and a mid-confirmation correction issuing a fresh token
  while the old one is permanently dead.
- **Full backend `pytest`: 56/56** (44 pre-existing + 12 new), after also
  fixing a latent flakiness bug discovered in a *prior* session's
  `tests/test_assistant_memory.py` (a maqam name built as `"كرد-<hex>"` —
  the same hyphen-glued-hex-suffix pattern qwen2.5:3b unreliably
  transcribes; fixed to a space-separated, digit-only suffix).
- **Eval suite (`evals/after-song-creation_report.md`): 47/47 (100%)** —
  no routing regression from adding the new intent.
- **Frontend `vitest`: 11/11** — unaffected; this feature is backend/
  conversation-only, no new frontend code.

**Known test flakiness (honestly disclosed, not hidden):**
`test_success_with_new_artist_is_atomic_and_searchable` — the one test
that extracts title+brand-new-artist+maqam from a single combined
sentence — intermittently fails under a full-suite run (passed in
isolation every time it was retried; failed in roughly 1 of 3 full-suite
runs). This is qwen2.5:3b's inherent run-to-run extraction variance on its
hardest case (three fields in one sentence), the same characteristic
documented in the previous session's model-quality report, not a logic
bug — the retry helper already in the test (`_post_retry`) absorbs most
of this, but not 100% of it. If this matters for a live demo, prefer
supplying the artist/maqam across two shorter turns rather than one long
combined sentence (see the demo script below, which already does this).

## 5. Known remaining limitations

- Composer/lyricist/musical-key/rhythm fields work but are less
  exercised by the test suite than title/artist/maqam — they follow the
  same resolution code paths, so risk is low, but worth a manual spot
  check if you lean on them for the demo.
- `PendingSongCreation` rows are never garbage-collected (no cleanup job
  for expired/used rows) — fine for a demo/academic project, would want a
  periodic cleanup for a real deployment.
- As noted above, 3-field-combined extraction occasionally drops a field
  with this specific local model; this is a pre-existing, documented
  characteristic, not something this feature could fix on its own
  (Phase 4's model-comparison work from the previous session, blocked on
  OpenAI billing, is the real lever here).

## 6. Browser demo script

**Setup**: backend (`uvicorn`) and frontend (`next dev`) running, Ollama
up with `qwen2.5:3b`, Postgres up. Log in as any existing user (or
register one) — song creation requires it; search/theory/lyrics do not.

1. Open the chat (**Assistant** page).
2. Type: **"بدي أضيف أغنية جديدة"** and send.
   - Agent recognizes the creation intent and asks what's missing (at
     minimum: song title and artist).
3. Type: **"اسمها نسمة ليل"** and send.
   - Agent now asks for the artist specifically (title is held in the
     draft from the previous turn).
4. Type: **"المغني مروان خليل"** (or any name — if it's not an existing
   artist, the agent will ask "هل تريد إضافته كفنان جديد؟" first; answer
   **"نعم"**).
   - Once title + artist are both resolved, the agent shows an Arabic
     summary (title, artist, and any other details given) and asks for
     explicit confirmation.
5. *(Optional, to demonstrate correction support)* Type: **"غيّر العنوان
   إلى نسمة الليل"** — the agent shows a fresh summary with the corrected
   title and a new confirmation request; the previous confirmation is now
   dead even if resent.
6. Type: **"نعم"** to confirm.
   - The agent performs the real database write (new artist row if
     needed, the song row, its embedding — all in one transaction),
     verifies the row persisted, and replies with a success message
     containing the song's id, title, artist, and maqam (if given).
7. Type: **"اعطيني اغاني مروان خليل"** (or whatever artist name was used).
   - The newly created song appears in the structured-search results —
     proving it's immediately real, persisted, and retrievable through
     the exact same search path as every other song, not a one-off
     in-memory response.
