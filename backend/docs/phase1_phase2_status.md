# Nagham AI — Phase 1 & 2 status (2026-10-10)

This documents what was implemented, what was verified, and what still
needs attention, per the project brief's "document changes, test results,
limitations, and remaining work" requirement. Pairs with
`maqam_theory_research.md` (musical sourcing) and `backend/evals/` (the
reproducible eval harness).

## Phase 1 — AI agent

### What changed

- **Arabic normalization** (`app/ai/arabic_text.py`, new): diacritic/tatweel
  stripping, hamza-seat/alef-maqsura/ta-marbuta unification for matching,
  a pure-Python Levenshtein-ratio fuzzy matcher (threshold 0.75, chosen
  after confirming zero false-positive collisions among the actual DB's
  artist/maqam names), and deterministic entity resolution against the
  real database (never invents an entity that isn't in the DB).
- **Negation/exclusion**: `exclude_filters` added to the intent schema and
  to structured/hybrid search; a deterministic fallback recovers an
  excluded entity even when the LLM misses it, keyed off negation markers
  ("مش", "ليس", "عدا", ...). Self-contradictory requests (same value
  required and excluded) are detected and explained rather than silently
  returning nothing.
- **Five new intents**, routed deterministically before the LLM gets
  involved (`app/ai/conversation.py`): `theory_question`,
  `maqam_comparison`, `song_question`, `follow_up`, `recommend_similar`.
  Each grounds its answer only in verified DB facts.
- **Session-scoped multi-turn memory**: an explicit `history` list the
  caller resends each request (API: `AssistantRequest.history`; eval
  harness: `USE_HISTORY=True`). Nothing is persisted server-side.
- **Architecture fix**: `run_nagham_agent` (used by the eval harness) now
  invokes the same LangGraph the production API uses, instead of a
  bypassed hybrid-only shortcut that ran every query — including pure
  structured ones — through an irrelevant semantic-similarity gate. This
  was the single largest source of baseline failures.
- **LLM-input hygiene**: diacritics are stripped before the text is sent
  to qwen2.5:3b (`strip_diacritics_for_llm`) -- confirmed this measurably
  improves the small model's result-count extraction. A message-
  containment check (`_sanitize_semantic_query`) discards `semantic_query`
  values the LLM echoed from a few-shot example or left as stray
  fragments, since both were observed failure modes of the 3B model.
- **System prompt cleanup**: removed a duplicated/contradictory trailing
  block and a `None`-instead-of-`null` typo in `agent.py`'s `SYSTEM_PROMPT`.
- **Data cleanup** (confirmed with the user before doing it): removed 2
  leftover test-fixture song rows ("Semantic Test Song", "Semantic
  Embedding Test") that were mis-attributed to Fairuz and skewing
  structured-search results.

### Test results

| Run | Pass rate | Notes |
|---|---|---|
| `baseline` | 46% (20/44) | Before any Phase 1 change |
| `after-phase1` | 100% (44/44) | After all Phase 1 changes + data cleanup |

Latency: baseline mean 2.81s / p95 6.24s; after-phase1 mean 2.65s / p95
3.46s (improved, partly because theory/comparison/follow-up intents skip
the LLM intent-extraction call entirely).

Full per-category breakdown and failing-case detail: see
`backend/evals/baseline_report.md` and `after-phase1_report.md`.
Reproduce with:
```
venv/Scripts/python.exe evals/run_eval.py --label <name>
```

### Known limitations

- The 44-case dataset is a good regression net for the categories it
  covers, but it is not exhaustive (e.g. no coverage yet of 3+ chained
  constraints, or maqam-comparison between more than 2 maqamat).
- The frontend chat UI (`app/(app)/assistant/page.tsx`) does not yet send
  or receive the `history` field -- multi-turn support exists in the API
  and eval harness but isn't exposed in the actual chat experience yet.
  Each chat session there is still effectively single-turn against the
  backend, even though the backend can do better.
- Fuzzy matching threshold (0.75) was validated against the *current*
  small dataset (7 maqamat, ~6 artists, 1 composer). If the artist/maqam
  catalog grows substantially, re-check for new fuzzy collisions.
- No backend unit test suite exists in this project yet (only the eval
  harness) -- there was nothing to run for a "backend tests" regression
  pass beyond the eval suite and manual smoke tests.

## Phase 2 — Maqam Explorer (Saba + generalization)

### What changed

- **Schema**: new additive `maqam_ajnas` table (`app/models/maqam_jins.py`)
  representing an ordered, multi-row ajnas breakdown per maqam (maqam_id,
  jins_id, start_degree, is_primary_alternative, notes) -- the old
  `root_jins_id`/`branch_jins_id` pair only has room for 2 ajnas, but real
  maqamat (Saba specifically) overlap 3+, and several document two valid
  alternatives at the same degree. The old columns are kept and still
  populated (used by the pre-existing simple root/branch badges) for
  backward compatibility. New `degree_names` JSON column on both `Maqam`
  and `Jins` for the ordered, documented note names.
- **Data**: all 7 seeded maqamat (Saba, Bayati, Rast, Hijaz, Nahawand,
  Kurd, 'Ajam) now have verified tonic, scale_pattern, degree_names,
  ghammaz, accidentals, mood, description, and a full ajnas breakdown --
  populated by the idempotent `backend/scripts/seed_maqam_theory.py`.
  Full sourcing, cross-checks, and every judgment call made (including
  one correction found during the generalization pass) are in
  `maqam_theory_research.md`.
- **Notation math** (`frontend/lib/maqam-theory.ts`): tonic + scale_pattern
  -> per-degree letter, accidental (including quarter-tone kinds), and
  *exact* frequency in Hz (computed from cents, not rounded to 12-TET).
  Verified by hand against the research document for all 7 maqamat (both
  a natural-tonic case and a flat-tonic case) -- every letter and
  accidental matched.
- **Notation rendering** (`frontend/components/maqamat/maqam-notation.tsx`):
  VexFlow 5, confirmed (via its own type definitions and test suite) to
  support the Arabic quarter-tone accidental glyphs this project needs
  (`d` half-flat, `+` half-sharp, plus `b`/`#`/`db`/`++` for the less
  common cases). Clickable/keyboard-accessible notes, playing-note
  highlight, ascending/descending/both playback with adjustable speed.
- **Audio** (`frontend/lib/maqam-audio.ts`): Web Audio oscillator-based
  synthesis at the real computed frequency, clearly labeled in the UI as
  a synthesized demonstration tone, not an oud recording.
- **UI integration** (`components/maqamat/maqam-detail.tsx`): notation
  section (or an explicit "data not verified yet" state for any maqam
  that lacks it -- none currently, since all 7 are filled in), ajnas
  breakdown cards (showing primary vs. documented-alternative ajnas), a
  maqamworld.com source link, and an "Ask Nagham AI about this maqam" CTA.
- **Phase 3 integration**: `theory_question`/`maqam_comparison` answers
  now read the *full* ajnas breakdown (all layers + alternatives), not
  just the legacy root/branch pair -- this was a real gap found and fixed
  during this pass (Saba's 3rd-degree Hijaz overlap was missing from
  grounded answers before the fix). Both intents now also nudge the user
  toward the interactive explorer in their closing line.

### Test results / verification performed

- `npx tsc --noEmit`: clean, no errors.
- `npm run build` (production): succeeds; `/assistant` still prerenders as
  static despite the new `useSearchParams()` usage (isolated behind a
  `Suspense` boundary per Next.js 16's prerendering rules).
- All 7 maqamat's notation math cross-checked programmatically against
  the hand-derived research table -- 7/7 match exactly (letters,
  accidentals, and cents).
- SSR output verified via direct HTTP fetch for Saba, Bayati, and Kurd
  (the one maqam with only a single documented branch alternative, to
  check that edge case doesn't crash) -- all 200 OK, all expected Arabic
  labels present, no error-boundary text.
- Direct backend smoke tests: structured search, maqam comparison, and
  theory-question intents all produce correct, grounded answers.
- Full eval suite re-run after all Phase 2/3 changes as a regression
  check: still 100% (44/44), no new failures. Latency that run was
  anomalously high (~68s mean vs. 2.65s) because two dev servers plus the
  eval script's own embedding-model instance were all competing for the
  same CPU/Ollama at once -- confirmed environmental (Ollama and the
  Python process were both actively burning CPU, not deadlocked) rather
  than a code regression; re-run it standalone for a trustworthy latency
  number.

### What was NOT verified (and why)

- **No in-browser interactive testing.** This sandbox's network is
  severely rate-limited (~15kB/s observed), making a Playwright + Chromium
  install impractically slow (projected 40+ minutes for the browser
  binary alone). Verification instead relied on: static type-checking,
  production build, direct SSR HTTP inspection, and independent
  verification of the underlying math/API calls against the installed
  VexFlow package's actual type definitions and test suite. **You should
  open `http://localhost:3000/maqamat/<id>` yourself** (both dev servers
  were left running) to confirm the notation renders and audio plays as
  expected -- this is the one layer I could not close the loop on myself.
- **No audio frequency measurement against a reference instrument.** The
  frequencies are computed correctly from the documented cents (verified
  programmatically), but nobody has confirmed them against a real tuner
  or an actual oud/qanun recording.

## Remaining work / flagged for expert review

See `maqam_theory_research.md`'s "Open items" section for the full list.
Highlights:

1. Nikriz jins (Saba's documented 6th-degree alternative) has no verified
   interval data -- explicitly left incomplete, not guessed.
2. Several maqamat document two valid branch-jins alternatives at the
   same degree; the better-corroborated one was recorded as primary and
   the other preserved as a documented alternative via the new
   `maqam_ajnas` table. Confirm this modeling choice reads correctly to
   you in the UI.
3. Saba's ghammaz is genuinely ambiguous between sources (3rd or 6th
   degree) -- both are recorded rather than one being picked.
4. The chat UI doesn't yet use multi-turn `history` -- only the API and
   eval harness do.
5. No cloud deployment, no destructive migrations, and no `git push` were
   performed, per standing instructions. Nothing has been committed to
   git either -- all changes are currently only in the working tree.
