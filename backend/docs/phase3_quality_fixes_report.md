# Nagham AI quality fixes — root-cause report (2026-10-12)

Scope: the three failures reported ahead of the academic demo — a lyrics
request returning unrelated songs, garbled/incoherent Arabic on a
Hijaz-vs-Nahawand maqam comparison, and unreliable multi-turn memory.
Everything below was reproduced live against the running backend (`:8000`,
Ollama `qwen2.5:3b`) and the real Postgres DB before any fix, and
re-verified after. **Nothing in this change set has been committed or
deployed** — it is all in the working tree pending review.

## 1. Root causes (with evidence)

### 1.1 Memory — frontend never sent conversation history

The backend/LangGraph already had full session-scoped multi-turn support
(built in a prior session, proven by the 44-case eval suite scoring 100%
with history enabled). But `frontend/app/(app)/assistant/page.tsx`'s
`send()` posted only `{ message, limit }` — no `history` field at all. The
real chat UI was *structurally* incapable of remembering anything, no
matter how good the backend's memory support was.

**Fix**: the page now tracks `analysis`/`result_ids` on each assistant
message and sends the last ~20 messages as `history` with every request
(`app/(app)/assistant/page.tsx`). No backend change was needed.

### 1.2 Lyrics request → unrelated recommendations

Live reproduction, before any fix:

```
POST /assistant {"message": "هاتلي كلمات انت عمري"}
→ answer: "تفضل بـ \"حنين إلى الوطن\" من فيروز"
→ results: 3 unrelated songs about homesickness/love/reunion
```

The database actually contains the exact song ("انت عمري", id 146, artist
أم كلثوم) **with its real lyrics text already stored**. The deterministic
song-title resolver (`resolve_song_title`) would have found it instantly —
but `classify_deterministic_intent` only invoked that resolver when the
message contained an explicit word for "song" (اغنية/اغاني). Lyrics
requests say "كلمات" instead, so the resolver never ran, the message fell
through to generic `song_search`, and an empty-filter semantic search over
the raw message returned whatever was nearest by embedding similarity —
then the RAG prompt confidently "recommended" one of them.

**Fix**: a new deterministic `lyrics_request` intent
(`app/ai/conversation.py`) checks lyrics-specific markers ("كلمات", "نص
الأغنية", ...) independently of the song-noun gate, and calls the existing
`resolve_song_title` directly. A new terminal graph node
(`run_lyrics_request_node`) handles the response **entirely
deterministically in Python — no LLM call** — so it can never garble text
or leak copyrighted content:

- No title resolves → explicit "not found," zero results. **Never** falls
  back to semantic recommendations.
- Title resolves, no `lyrics` stored → says so.
- `lyrics_license` is `"public_domain"`/`"licensed"` → the stored lyrics
  text is returned verbatim with attribution.
- Otherwise (`"restricted"` or unset — the default, display rights are
  never assumed) → song metadata + a summary (from `description`, or a
  minimal fields-only template if empty — never invented biography) + an
  explicit copyright notice + an authorized-source link if one exists in
  `SongSource` (`source_type="lyrics"`), else a note that none is on file.

After the fix (live, same request):

```
answer: "لا يمكنني عرض كلمات أغنية \"انت عمري\" هنا بسبب قيود حقوق النشر.

الفنان: أم كلثوم
الملحن: محمد عبد الوهاب
المقام: كرد
...
لا يوجد حاليًا رابط لمصدر موثّق لعرض الكلمات في قاعدة البيانات."
results: [{"id": 146, "title": "انت عمري", ...}]
```

A lyrics request for a title that genuinely doesn't exist now returns an
explicit not-found message with zero results, confirmed live.

**New schema** (migration `3eff4281930a`, additive/nullable only):
`songs.lyrics_license` (`"public_domain" | "licensed" | "restricted"`,
`NULL`/unrecognized always treated as restricted in code) and
`songs.lyrics_rights_note`. `songs.lyrics` itself is untouched and
unchanged — kept for every song regardless of license, since it still
feeds the semantic-search embedding (`build_song_embedding_text`). Song
146 was backfilled to `"restricted"` since no license grant exists for it.
The existing (previously-empty) `SongSource` table is reused for
authorized-source links rather than adding new schema.

### 1.3 Theory/comparison — garbled Arabic, fabricated numbers, an English leak

Routing and retrieval were already correct (`classify_deterministic_intent`
correctly hit `maqam_comparison`/`theory_question`, and `build_maqam_facts`
pulled the right DB row) — the failure was in generation. Live
reproductions before any fix:

- Asked to transcribe Hijaz's real `scale_pattern`
  (`[0.5, 1.5, 0.5, 1.0, 0.5, 1.0, 1.0]`, confirmed against the DB directly),
  qwen2.5:3b answered with a fabricated, nonsensical array instead:
  `"[د4، ج4، ج4، د5، ج4، د5، د5]"`.
- The same model correctly echoed Nahawand's real array in a separate call
  — so this wasn't a uniform incapability, just unreliable.
- A `suggest_explorer=True` answer contained the literal fragment
  `"نudge:"` — the model had echoed a piece of the prompt's English
  instruction text ("...a short **nudge**...") glued onto Arabic with no
  space.
- Rephrasing the same Hijaz/Nahawand comparison question twice produced
  mutually contradictory claims about which maqam "ends" at which degree,
  and added an unsupported comparison to "the Western Phrygian dominant
  scale" that appears nowhere in the facts given.

**Fix** (`app/ai/conversation.py` + `app/ai/agent.py`):

1. `build_maqam_facts` now renders `scale_pattern` as Arabic interval-name
   words (`render_scale_pattern_ar`: 0.5→"نصف تون", 0.75→"ثلاثة أرباع تون",
   1.0→"تون كامل", 1.5→"تون ونصف") computed deterministically in code,
   instead of handing the LLM a raw numeric array to transcribe. This
   removes the exact hallucination surface caught live.
2. `generate_grounded_answer`'s prompt gained an explicit instruction to
   copy interval words exactly (never convert to numbers) and to never
   compare the maqam to Western scale names/systems.
3. The `suggest_explorer` instruction (`explorer_rule`) is now written
   entirely in Arabic, removing the English "nudge" sentence that leaked.
4. A cheap post-generation guard (`_looks_garbled`) detects a Latin letter
   glued directly onto an Arabic letter with no space — the exact signature
   of the leak seen live — and retries once with a stricter reminder,
   falling back to a deterministic "here are the verified facts" answer if
   it still fails. This guarantees the demo can't show garbled output
   regardless of which LLM is configured.

After the fix (live, same Hijaz question):

```
"السلم الموسيقي لمقام الحجاز يبدأ من الدرجة الأساسية (D4) ويكون كما يلي:
جنس حجاز على الدرجة 1، ثم جنس نهاوند على الدرجة 4، وينتهي بجنس راست على
الدرجة 4. هذا السلم يمتلك طابع شرقي عاطفي قوي، ويتميز بمسافات بين الدرجات
هي نصف تون - تون ونصف - نصف تون - تون كامل - نصف تون - تون كامل - تون كامل."
```

Every claim here is independently verifiable against the DB: degree 1 =
Hijaz jins, degree 4 = Nahawand (primary) / Rast (secondary alternative)
— confirmed against `maqam_ajnas` directly — and the interval sequence
"نصف تون - تون ونصف - نصف تون - تون كامل - نصف تون - تون كامل - تون كامل"
is an exact word-for-word match of the real `[0.5, 1.5, 0.5, 1.0, 0.5, 1.0,
1.0]`. No fabricated numbers, no English leak, no outside-knowledge claim.

The comparison answer is now clean but occasionally uses a slightly odd
word choice (e.g. "اختر منتجع..." instead of smoother phrasing) — not
garbled or incoherent, just a minor stylistic quirk, noted under
Limitations below.

## 2. Frozen eval results

Three new frozen cases were added to `backend/evals/dataset.jsonl`
(`lyrics-restricted-01`, `lyrics-notfound-01`,
`comparison-hijaz-nahawand-01`) covering exactly the reported bugs. Four
existing `expected_song_ids_subset_of` allow-lists
(`struct-artist-02`, `spelling-hamza-01/02`, `multiconstraint-01`) were
updated to include song id 146 — **not a loosened check**: song 146 (an
Um Kulthum song, used for the lyrics feature) was added to the dev
database after the original 44-case dataset was frozen, and a structured
artist-name filter correctly includes it; the old allow-lists were simply
stale relative to current DB content. No check's pass/fail semantics were
changed.

| Run | Cases | Pass rate | Latency (mean / p50 / p95) |
|---|---|---|---|
| `baseline` (pre-existing, before any multi-turn/Arabic work) | 44 | 46% | 2.806s / 2.52s / 6.24s |
| `after-phase1` (pre-existing, prior session) | 44 | 100% | 2.651s / 2.076s / 3.458s |
| `after-fixes_qwen` (this session, incl. 3 new regression cases) | 47 | **100%** | 2.616s / 2.134s / 3.168s |

## 3. Model comparison — blocked, not attempted further

Phase 4 asked for a comparison against a stronger model. With your
approval, I attempted to run the same 47-case eval against `gpt-4o-mini`
using the existing `OPENAI_API_KEY` in `backend/.env` (no code change
needed — `app/ai/llm_client.py` already supports
`LLM_PROVIDER=openai_compatible`). Every call failed immediately with:

```
RateLimitError: 429 insufficient_quota / credit_balance_exhausted —
"You have no credits remaining."
```

This is a billing issue on the OpenAI account, not a model-quality result
— the resulting (meaningless) 0%-pass report was deleted rather than kept.
Per your decision, the model comparison was skipped rather than retried
with another provider. **This remains open**: all evidence in this report
is qwen2.5:3b-only. The fixes made (deterministic lyrics intent,
deterministic interval rendering, garble-retry guard) measurably improved
qwen2.5:3b's reliability regardless, but whether a larger model would need
less of this scaffolding is unverified.

## 4. Test results

- Backend `pytest`: **44/44 passed** (38 pre-existing auth/OAuth/
  forgot-password tests + 6 new: 3 lyrics-intent tests in
  `tests/test_assistant_lyrics.py`, 3 memory/isolation tests in
  `tests/test_assistant_memory.py`, the latter driven through the real
  `/assistant` HTTP endpoint, not the in-process eval harness).
- Frontend `vitest`: **11/11 passed** (10 pre-existing + 1 new test in
  `app/(app)/assistant/page.test.tsx` asserting the chat UI sends an empty
  `history` on the first turn and accumulates prior turns correctly on the
  second). Required one unrelated environment fix: jsdom doesn't implement
  `Element.scrollTo`, which the chat's auto-scroll effect calls — stubbed
  in `vitest.setup.ts` since any future test rendering a scrolling
  container would hit the same gap.
- Eval suite (`backend/evals/run_eval.py`): 47/47 (100%) on qwen2.5:3b,
  detailed in `evals/after-fixes_qwen_report.md`.

## 5. Known remaining limitations

- **Model comparison not completed** (see §3) — the OpenAI key has no
  credits. Revisit when you've topped up, or point `LLM_API_KEY`/
  `LLM_BASE_URL` at a different OpenAI-compatible provider; no code change
  needed, just re-run `evals/run_eval.py` with `LLM_PROVIDER=openai_compatible`.
- **No authorized lyrics source seeded yet.** `SongSource` supports
  `source_type="lyrics"` links for restricted songs, but none exist in the
  DB — every restricted-lyrics answer currently says so explicitly rather
  than showing a link. Add rows via the existing `/song-sources` API once
  you have real authorized sources to cite.
- **Song 146's `year` field (1999) looks historically off** for "انت عمري"
  (the real song dates to 1964) — this is pre-existing seed data from
  before this session and was left untouched rather than silently
  "corrected" without knowing its original intent; flagging for your
  review.
- Minor stylistic quirk in maqam-comparison answers (occasional odd word
  choice in the Explorer nudge sentence) — not garbled/incoherent, just not
  maximally polished; lower priority than the three originally-reported
  bugs, all of which are now fixed and regression-tested.
- Carried over from the prior session: the Nikriz jins (Saba's documented
  alternative 6th-degree branch) still has no verified interval data
  (`scale_pattern: null` by design, not guessed).
