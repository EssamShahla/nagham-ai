# Maqam & Jins theory research notes

Research pass for the Maqam Explorer (Phase 2). Covers the 7 maqamat currently
seeded in the database: Saba (reference implementation, done first per
instruction), Bayati, Rast, Hijaz, Nahawand, Kurd, 'Ajam.

## Method and provenance

Three source types were cross-checked against each other for every maqam
below; a fact is only recorded as "documented theory" when at least two of
these agree, or a single primary source states it unambiguously:

1. **maqamworld.com** (`/en/maqam/<name>.php`, `/en/jins/<name>.php`) -- the
   project's designated reference. Used here only for the *structural* facts
   it states in prose (root jins, secondary/branch ajnas and which scale
   degree they start on, maqam family, ghammaz where stated). Its interactive
   notation is an image/JS widget, not extractable as text -- no pitch/cents
   data was taken from it directly.
2. **Wikipedia** (`Saba_(music)`, general Arabic-maqam articles) -- used for
   qualitative cross-checks and citations (Farraj & Abu Shumays 2019,
   Aydemir 2010).
3. **thewholehorn.com/maqam-theory/** -- provides a concrete note-name/cents
   table per maqam, citing al-Shawwa (1946) and the Digital Arabic Maqam
   Archive (AUB). Treated with more scrutiny since it's a lesser-known
   secondary source and web-content extraction here goes through an
   AI summarization step (risk of paraphrase drift). **Validated** by
   checking that every single one of its reported interval patterns matches
   the well-known, textbook jins interval shapes (e.g. Hijaz jins =
   half-step + augmented-second + half-step; Nahawand jins = whole + half +
   whole; Rast jins = whole + three-quarter + three-quarter) AND matches
   maqamworld's structural claims exactly, degree-for-degree, for all 7
   maqamat. This cross-validation is recorded per maqam below.

**Units:** `scale_pattern` in this codebase is stored as successive
intervals in tone units (1.0 = whole tone = 200 cents), matching the existing
`Maqam.scale_pattern` / `Jins.scale_pattern` column convention and the one
real seeded example (Jins Bayati: `[0.75, 0.75, 1.0]`, which independently
checks out against the research below).

**What's a documented fact vs. an approximation vs. performance-dependent:**
- *Documented theory*: jins/maqam structure (which jins, which degree),
  and interval shapes, as stated by maqamworld.com and corroborated above.
- *Tuning approximation*: the 24-tone-equal-temperament cents values (e.g.
  "150 cents" for a neutral second). This is the standard simplification
  used for notation and the one this project uses for synthesized audio,
  but it is a theoretical grid, not a claim about how any given performer
  tunes.
- *Performance-dependent intonation*: explicitly called out where a source
  says so, e.g. Jins Hijaz: "the interval between the 2nd and 3rd degrees is
  usually played smaller than notated, by raising the 2nd a little and
  lowering the 3rd a little" (maqamworld.com). Never baked into the stored
  `scale_pattern`; only recorded as a note.

## Saba (reference implementation -- do this one first)

- **Tonic:** D (Dugah / دوكاه).
- **Root jins:** Jins Saba on the tonic.
- **Branch ajnas:** Jins Hijaz on the 3rd degree; then **either** Jins 'Ajam
  (3-note version) **or** Jins Nikriz on the 6th degree. maqamworld states
  both alternatives explicitly ("followed by either Jins 'Ajam or Jins
  Nikriz on the 6th degree") -- this is a documented *branch ambiguity*, not
  something to resolve by guessing. Jins 'Ajam's own page confirms its
  3-note version specifically "occurs ... on the 6th scale degree of Maqam
  Bayati, Saba, and Kurd," which is why 'Ajam (not Nikriz) is recorded as the
  primary `branch_jins_id` here, with Nikriz noted as the documented
  alternative.
- **Ghammaz:** *Ambiguous by design* -- maqamworld's Jins Saba page states
  two possible resting points, "the 3rd degree (notated on F) or the 6th
  degree (notated on Bb)." Wikipedia's Saba article agrees: "Jins Saba lacks
  a single, well-defined ghammaz ... the secondary center of melodic emphasis
  is usually pitch 3, while the pivot for modulating to other ajnas is
  pitch 6." Both are recorded in `notes`; no single value is forced into
  `ghammaz`.
- **Scale (ascending), tonic D:**

  | Degree | Note name | Pitch | Cents | Tone-units from prior degree |
  |---|---|---|---|---|
  | 1 | Dugah (دوكاه) | D | 0 | tonic |
  | 2 | Sikah (سيكاه) | half-flat E | 150 | 0.75 |
  | 3 | Jaharkah (جهاركاه) | F | 300 | 0.75 |
  | 4 | (Hijaz jins note) | Gb | 400 | 0.5 |
  | 5 | Husayni (حسيني) | A | 700 | 1.5 |
  | 6 | 'Ajam / Nikriz branch | Bb | 800 | 0.5 |
  | 7 | Kurdan (كردان) | C | 1000 | 1.0 |
  | 8 | (octave) | D | 1200 | 1.0 |

  `scale_pattern = [0.75, 0.75, 0.5, 1.5, 0.5, 1.0, 1.0]`. Degree 2's
  "quarter tone" is the one Wikipedia independently flags as genuinely
  in-between a minor and major second -- i.e. not a notation artifact, a
  real documented microtonal degree.
- **Character:** "Often associated with troubled, distressed, or yearning
  emotions" (Wikipedia, citing Farraj & Abu Shumays 2019); the name Saba
  itself means "yearning"/"longing."
- **No Western equal-tempered equivalent** -- degree 2 (neutral 2nd) and
  degree 4 (the Hijaz-jins-flavoured diminished-4th-ish degree) both fall
  outside 12-TET; this must not be flattened to the nearest semitone when
  the interactive notation/audio is built (see Phase 2 instructions:
  "Do not represent equal-tempered MIDI notes as accurate quarter-tone
  maqam pitches").
- **Jins Saba interval shape (root jins alone, degrees 1-4 of the maqam
  scale above):** `[0.75, 0.75, 0.5]` (D - half-flat E - F - Gb). Noted as
  "ambiguous size" by maqamworld -- some treatments stop at 3 notes
  (D - half-flat E - F, with F as the secondary center), consistent with the
  dual-ghammaz note above.

## Bayati

- **Tonic:** D (Dugah). Root jins: Jins Bayati on tonic. Branch: Jins
  Nahawand **or** Jins Rast on the 4th degree (documented alternative,
  not resolved to one -- Nahawand recorded as primary since it's listed
  first and is the one with full corroborating interval data).
- **Scale:** D(0) - half-flat E(150) - F(300) - G(500) - A(700) - Bb(800) -
  C(1000) - D(1200). `scale_pattern = [0.75, 0.75, 1.0, 1.0, 0.5, 1.0, 1.0]`
  (matches the pre-existing seeded `Jins Bayati` row's pattern for the
  degree 1-3 portion exactly: `[0.75, 0.75, 1.0]`).
- **Character:** "By far one of the most popular and common maqamat in the
  Arabic repertory" (maqamworld); "the most common maqam in the Levant."
- Muhayyar is documented as a sayr-variant of Bayati (same scale, different
  melodic path, starting at the octave) -- not a separate maqam for this
  project's purposes.

## Rast

- **Tonic:** C (Rast). Root jins: Jins Rast on tonic. Branch: Jins Upper
  Rast (same intervallic shape as Jins Rast, transposed to the 5th degree)
  **or** Jins Nahawand, on the 5th degree.
- **Scale:** C(0) - D(200) - half-flat E(350) - F(500) - G(700) - A(900) -
  half-flat B/Awj(1050) - C(1200).
  `scale_pattern = [1.0, 0.75, 0.75, 1.0, 1.0, 0.75, 0.75]`.
  Cross-check: degrees 5-8 (G-A-Awj-C) reproduce the exact same
  [1.0, 0.75, 0.75] shape as degrees 1-4 (C-D-E-F) -- confirms "Jins Upper
  Rast" is genuinely the same jins transposed, as maqamworld's name implies.
- **Called "the mother maqam"** in the wider literature -- historically
  central to the whole system.

## Hijaz

- **Tonic:** D (Dugah). Root jins: Jins Hijaz on tonic (confirmed 4-note by
  its dedicated page). Branch: Jins Nahawand **or** Jins Rast on the 4th
  degree.
- **Scale:** D(0) - Eb(100) - F#/Gb("Hijaz" note)(400) - G(500) - A(700) -
  Bb(800) - C(1000) - D(1200).
  `scale_pattern = [0.5, 1.5, 0.5, 1.0, 0.5, 1.0, 1.0]`.
  Jins Hijaz shape alone (degrees 1-4): `[0.5, 1.5, 0.5]` (half-step,
  augmented 2nd, half-step) -- the textbook Hijaz jins shape.
- **Performance note (do not bake into the stored scale):** maqamworld's
  Jins Hijaz page: "the interval between the 2nd and 3rd degrees is usually
  played smaller than notated, by raising the 2nd a little and lowering the
  3rd a little" -- performance-dependent intonation, recorded only as a
  note.

## Nahawand

- **Tonic:** C (Rast, as a pitch name -- this is Maqam Nahawand's tonic
  pitch, distinct from Maqam Rast which happens to share the same tonic
  pitch but a different jins). Root jins: Jins Nahawand on tonic. Branch:
  Jins Hijaz **or** Jins Kurd, on the 5th degree.
- **Scale:** C(0) - D(200) - Eb(300) - F(500) - G(700) - Ab(800) -
  B(1100) - C(1200). `scale_pattern = [1.0, 0.5, 1.0, 1.0, 0.5, 1.5, 0.5]`.
  Cross-check: degrees 5-8 (G-Ab-B-C) reproduce `[0.5, 1.5, 0.5]`, the same
  Hijaz-jins shape found above -- confirms "Jins Hijaz on the 5th degree" as
  stated by maqamworld.
- Maqam Farahfaza is documented as the same maqam transposed to tonic G --
  not a separate entry here.
- **Descending form differs from the harmonic-minor-like ascending set**
  per thewholehorn ("differs in sayr, ghammaz, and descending") but the
  specific descending alterations were not found in extractable text on
  either source -- recorded as not-yet-verified rather than guessed.

## Kurd

- **Tonic:** D (Dugah). Root jins: Jins Kurd on tonic. Branch: Jins Nahawand
  on the 4th degree (single alternative, no "or" documented here).
- **Scale:** D(0) - Eb(100) - F(300) - G(500) - A(700) - Bb(800) -
  C(1000) - D(1200). `scale_pattern = [0.5, 1.0, 1.0, 1.0, 0.5, 1.0, 1.0]`.
  Jins Kurd shape alone (degrees 1-3): `[0.5, 1.0]` (half-step then
  whole-step -- a Phrygian trichord). Degrees 4-7 reproduce `[1.0, 0.5,
  1.0, 1.0]`... actually the Nahawand-jins shape re-derived here as
  `[1.0, 0.5, 1.0]` for degrees 4-6-7 matches the Nahawand shape used above
  for Bayati/Hijaz's branch (same 3-interval pattern confirmed again).

## 'Ajam

- **Tonic:** Bb (Ajam 'Ushayran) -- maqamworld explicitly identifies this
  database's maqam as **Egyptian 'Ajam**, i.e. the common transposition
  with tonic on Bb, not the theoretical tonic-C form. Root jins: Jins 'Ajam
  (5-note version) on tonic. Branch: Jins Upper 'Ajam (same shape,
  transposed) **or** Jins Nahawand, on the 5th degree.
- **Scale:** Bb(0) - C(200) - D(400) - Eb(500) - F(700) - G(900) -
  A(1100) - Bb(1200). `scale_pattern = [1.0, 1.0, 0.5, 1.0, 1.0, 1.0, 0.5]`.
  Cross-check: degrees 5-8 (F-G-A-Bb) reproduce `[1.0, 1.0, 0.5]`, the same
  shape as degrees 1-4 -- confirms "Jins Upper 'Ajam" is the same jins
  transposed to the 5th degree.
- **Note:** this is the one maqam of the 7 whose documented fixed-pitch
  tonic (Bb) does not match the "generic" degree-1 pitch used loosely above
  for the others; it was deliberately kept as Bb because that's what
  maqamworld's Egyptian-'Ajam framing states, not assumed.

## Shared ajnas referenced above (for the `ajnas` table)

| Jins | Size | Interval shape (tone units) | Used as root of | Used as branch of (degree) |
|---|---|---|---|---|
| Saba | ambiguous (3 or 4 notes) | `[0.75, 0.75, 0.5]` (4-note form) | Saba | -- |
| Hijaz | 4-note | `[0.5, 1.5, 0.5]` | Hijaz | Saba (3rd), Nahawand (5th) |
| 'Ajam (3-note) | 3-note | `[1.0, 1.0]` (derived -- see note) | -- | Saba (6th), Bayati (6th), Kurd (6th) |
| 'Ajam (5-note) | 5-note | `[1.0, 1.0, 0.5]` | 'Ajam | -- |
| Upper 'Ajam | 4-note (tetrachord) | `[1.0, 1.0, 0.5]` -- the lower tetrachord of 'Ajam (5-note), transposed (see note below) | -- | 'Ajam (5th) |
| Nikriz | 5-note | not extracted (notation-only on source page) | -- | Saba (6th, alt.) |
| Bayati | 4-note | `[0.75, 0.75, 1.0]` (already seeded, confirmed correct) | Bayati | -- |
| Rast | 4-note | `[1.0, 0.75, 0.75]` | Rast | -- |
| Upper Rast | 4-note | same shape as Rast, transposed | -- | Rast (5th) |
| Nahawand | 4-note | `[1.0, 0.5, 1.0]` | Nahawand | Bayati (4th, alt.), Hijaz (4th, alt.), 'Ajam (5th, alt.) |
| Kurd | 3-note | `[0.5, 1.0]` | Kurd | -- |

**'Ajam (3-note) derivation:** maqamworld's jins/ajam.php states (prose
only, no numbers) that the 3-note version "occurs ... on the 6th scale
degree of Maqam Bayati, Saba, and Kurd." Reading off thewholehorn's
per-maqam cents tables at exactly that degree range in all three maqamat
independently gives the same two intervals every time: Bayati Bb(800)-
C(1000)-D(1200), Saba Bb(800)-C(1000)-D(1200), Kurd Bb(800)-C(1000)-D(1200)
-- i.e. `[1.0, 1.0]` (whole, whole) in every case. This is treated as a
derived-but-solid fact (three independent confirmations of the same two
numbers), not a guess.

**Nikriz** is the one jins left genuinely incomplete: maqamworld's
dedicated page gives only "5-note jins, tonic C, ghammaz G" with the
interval structure shown solely in an un-extractable notation image. Its
DB row will have `scale_pattern = null` until someone can read the actual
notation or cite a source with the numbers, consistent with the "explicit
incomplete-data state" instruction.

## Addendum: generalization pass (all 7 seeded)

All 6 remaining maqamat (Bayati, Rast, Hijaz, Nahawand, Kurd, 'Ajam) were
seeded via `backend/scripts/seed_maqam_theory.py` using the data above,
cross-checked once more by running the notation algorithm
(`lib/maqam-theory.ts:computeScaleDegrees`) against each maqam's scale and
confirming every letter+accidental matches this document's hand-derived
table exactly (6/6 matched, including the pre-existing Bayati jins row from
the original seed data, which turned out to already be correct and is now
also fully filled in with tonic/degree_names/notes it was previously
missing).

One correction made during this pass: Jins Upper 'Ajam was initially
assumed to be the full 5-note 'Ajam shape transposed (matching the pattern
used for Upper Rast), but maqamworld's identical phrasing for both
("...with its tonic up on the 8th degree") combined with Upper Rast being
confirmed 4-note made the 5-note assumption inconsistent -- corrected to
record Upper 'Ajam as a 4-note tetrachord (the lower portion of 'Ajam's
pattern), since a 5th note would fall outside the one-octave cents range
actually confirmed from source data, and extending it by assuming simple
octave-equivalence would have been an inference, not a sourced fact.

## Open items to flag for expert/user review

1. **Branch-jins ambiguity**: five of the seven maqamat document an "either
   jins X or jins Y" choice at the branch position, but the DB schema has a
   single `branch_jins_id`. The first-listed/better-corroborated option was
   recorded as the primary branch; the alternative is preserved in the
   `notes` text field rather than dropped. Confirm this is an acceptable
   modeling choice, or whether the schema should grow a
   `branch_jins_alternate_id`.
2. **Saba's dual ghammaz** (3rd or 6th degree) is recorded as-is (both
   degrees noted) rather than forced into a single value -- confirm this
   matches how you want it presented in the UI.
3. **Nahawand's descending-form differences** and **Nikriz's precise
   interval pattern** were not found in extractable text from either source
   and are left unverified rather than guessed.
4. Degree-2/quarter-tone cents (150 for most of these, except Rast at
   150/350/1050-style offsets) are the standard 24-TET theoretical grid.
   Real performance intonation varies by school/performer -- flagged in the
   provenance section above, not baked into a false precision claim.
