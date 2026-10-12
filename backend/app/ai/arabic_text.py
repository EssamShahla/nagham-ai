"""
Deterministic Arabic text normalization and entity resolution.

The small local LLM (qwen2.5:3b) is reliable at understanding *intent* but is
not a dependable deterministic matcher for spelling variants, diacritics, or
missing/extra letters in proper nouns (artist, composer, maqam names). This
module exists so matching against the database is never left purely to LLM
prompt instructions, per the project's Arabic-robustness requirements.

Two independent things live here:

1. `normalize_arabic` - a pure string transform used to compare two Arabic
   strings regardless of diacritics, hamza seat, alef maqsura/ya, or tatweel.
   Only used for *matching*; original user-facing text is never altered.

2. `resolve_entities` - scans a raw user message for the closest known
   artist / composer / maqam names stored in the database (normalized +
   fuzzy match), so structured filters key off the canonical DB spelling
   instead of whatever the user (or the LLM) typed.
"""

import re
from dataclasses import dataclass
from functools import lru_cache

from sqlalchemy.orm import Session

from app.models.artist import Artist
from app.models.composer import Composer
from app.models.maqam import Maqam
from app.models.rhythm import Rhythm
from app.models.song import Song


# Arabic diacritics (tashkeel/harakat) + Quranic annotation marks + tatweel.
_DIACRITICS_RE = re.compile(
    r"[ؐ-ًؚ-ٰٟۖ-ۭـ]"
)

# Punctuation that commonly glues onto the last word of a question/clause
# with no space ("الراست؟", "فيروز،") and would otherwise break matching.
_PUNCTUATION_RE = re.compile(r"[؟!،,.؛:;\"'()\[\]{}]")

# Leading possessive/conjunction prefixes commonly glued onto Arabic proper
# nouns with no space ("لفيروز" = "for Fairuz", "وأم كلثوم" = "and Um Kulthum").
# Longest-first so "لل" strips before "ل".
_PREFIXES = ["بال", "كال", "فال", "وال", "لل", "ال", "بـ", "لـ", "فـ", "كـ", "و", "ف", "ب", "ل"]

_HAMZA_SEATS = str.maketrans({
    "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
    "ؤ": "و",
    "ئ": "ي",
    "ى": "ي",   # alef maqsura -> ya
    "ة": "ه",   # ta marbuta -> ha (matching-only; never used for display)
})


def normalize_arabic(text: str) -> str:
    """
    Normalize Arabic text for matching only. Never use the result for
    display -- it deliberately collapses distinctions (hamza seat, alef
    maqsura vs ya, ta marbuta vs ha) that are meaningful in writing but
    irrelevant to recognizing the same word/name.
    """

    if not text:
        return ""

    text = _DIACRITICS_RE.sub("", text)
    text = _PUNCTUATION_RE.sub(" ", text)
    text = text.translate(_HAMZA_SEATS)
    text = re.sub(r"\s+", " ", text).strip()

    return text.lower()


def strip_diacritics_for_llm(text: str) -> str:
    """
    Remove only tashkeel/tatweel, preserving original letters, word
    boundaries, and punctuation. Unlike `normalize_arabic`, this does NOT
    unify hamza seats or ta marbuta/ha -- it's meant to be fed to the LLM
    as cleaner input (heavy diacritics measurably confuse qwen2.5:3b's
    counting/extraction, e.g. "أَغَانِي فَيْرُوز" vs "أغاني فيروز"), not
    for matching, so spelling distinctions that matter for display/meaning
    are kept intact.
    """

    if not text:
        return text

    return re.sub(r"\s+", " ", _DIACRITICS_RE.sub("", text)).strip()


def strip_leading_prefix(word: str) -> str:
    """
    Strip one leading possessive/conjunction prefix from a normalized word,
    e.g. "لفيروز" -> "فيروز", "والبياتي" -> "بياتي" (via the compound "وال"
    entry). Deliberately a single pass: compounding single-letter prefixes
    (و, ب, ف, ك, ل) is unsafe since real word beginnings coincidentally
    collide with them often (e.g. "بياتي" itself starts with "ب").
    Only strips when the remainder is still a plausible word (>=2 chars).
    """

    for prefix in _PREFIXES:
        if word.startswith(prefix) and len(word) - len(prefix) >= 2:
            return word[len(prefix):]

    return word


def levenshtein_ratio(a: str, b: str) -> float:
    """
    Similarity ratio in [0, 1] based on Levenshtein edit distance,
    1.0 meaning identical strings. Pure-Python (no extra dependency);
    fine at the scale of names/short phrases this project matches against.
    """

    if a == b:
        return 1.0

    if not a or not b:
        return 0.0

    len_a, len_b = len(a), len(b)
    previous_row = list(range(len_b + 1))

    for i, char_a in enumerate(a, start=1):
        current_row = [i] + [0] * len_b

        for j, char_b in enumerate(b, start=1):
            cost = 0 if char_a == char_b else 1
            current_row[j] = min(
                previous_row[j] + 1,       # deletion
                current_row[j - 1] + 1,    # insertion
                previous_row[j - 1] + cost,  # substitution
            )

        previous_row = current_row

    distance = previous_row[len_b]
    return 1.0 - (distance / max(len_a, len_b))


FUZZY_MATCH_THRESHOLD = 0.75


@dataclass(frozen=True)
class EntityMatch:
    canonical_name: str
    entity_id: int
    score: float
    is_composer_context: bool = False


_COMPOSER_MARKERS = ["ملحن", "الملحن", "ملحنها", "ألحان", "الحان", "لحن"]


def _db_entity_rows(db: Session) -> dict[str, list[tuple[int, str]]]:
    return {
        "artist": [(a.id, a.name_ar) for a in db.query(Artist).all()],
        "composer": [(c.id, c.name_ar) for c in db.query(Composer).all()],
        "maqam": [(m.id, m.name_ar) for m in db.query(Maqam).all()],
        "rhythm": [(r.id, r.name_ar) for r in db.query(Rhythm).all()],
        "song": [(s.id, s.title) for s in db.query(Song).all()],
    }


def _best_match(
    normalized_ngram: str,
    candidates: list[tuple[int, str]],
) -> EntityMatch | None:
    best: EntityMatch | None = None

    for entity_id, name_ar in candidates:
        normalized_name = normalize_arabic(name_ar)
        score = levenshtein_ratio(normalized_ngram, normalized_name)

        if score >= FUZZY_MATCH_THRESHOLD and (best is None or score > best.score):
            best = EntityMatch(
                canonical_name=name_ar,
                entity_id=entity_id,
                score=score,
            )

    return best


def canonicalize_value(db: Session, category: str, raw_value: str | None) -> str | None:
    """
    Correct a single already-extracted value (artist/composer/maqam name,
    however the user or the LLM spelled it) to its canonical DB spelling.

    Falls back to the original value unchanged if nothing in the database
    is a close enough match -- this function corrects spelling, it never
    invents an entity that isn't actually in the database.
    """

    if not raw_value or category not in ("artist", "composer", "maqam", "rhythm"):
        return raw_value

    rows = _db_entity_rows(db)[category]
    normalized = strip_leading_prefix(normalize_arabic(raw_value))

    match = _best_match(normalized, rows)

    return match.canonical_name if match else raw_value


def resolve_to_id(db: Session, category: str, raw_value: str | None) -> tuple[int, str] | None:
    """
    Like `canonicalize_value`, but returns the matched row's
    `(id, canonical_name)` instead of just the name -- for callers that
    need to store a foreign key (e.g. conversational song creation
    staging `maqam_id`/`rhythm_id`/an existing artist's id). Returns
    `None` when nothing in the database is a close enough match -- never
    invents an id for an entity that doesn't exist.
    """

    if not raw_value or category not in ("artist", "composer", "maqam", "rhythm"):
        return None

    rows = _db_entity_rows(db)[category]
    normalized = strip_leading_prefix(normalize_arabic(raw_value))

    match = _best_match(normalized, rows)

    return (match.entity_id, match.canonical_name) if match else None


def resolve_entities(db: Session, message: str) -> dict[str, EntityMatch | None]:
    """
    Scan a raw user message for the closest known artist, composer, and
    maqam by sliding a window of 1-4 tokens, stripping one leading
    Arabic prefix per token, and fuzzy-matching against the database.

    Returns the single best match per category (or None), each carrying
    the canonical DB spelling so callers never have to guess which of two
    near-identical strings to filter on.
    """

    rows = _db_entity_rows(db)

    raw_tokens = message.split()
    tokens = [normalize_arabic(t) for t in raw_tokens]

    best_by_category: dict[str, EntityMatch | None] = {
        "artist": None,
        "composer": None,
        "maqam": None,
    }

    for window in (4, 3, 2, 1):
        for start in range(0, max(0, len(tokens) - window + 1)):
            span_tokens = tokens[start:start + window]
            if not span_tokens:
                continue

            span_tokens = list(span_tokens)
            span_tokens[0] = strip_leading_prefix(span_tokens[0])
            ngram = " ".join(span_tokens)

            if len(ngram) < 2:
                continue

            for category in ("artist", "composer", "maqam"):
                match = _best_match(ngram, rows[category])
                if match is None:
                    continue

                current_best = best_by_category[category]
                if current_best is None or match.score > current_best.score:
                    preceding = " ".join(tokens[max(0, start - 3):start])
                    is_composer_context = any(
                        marker in preceding or marker in ngram
                        for marker in _COMPOSER_MARKERS
                    )
                    best_by_category[category] = EntityMatch(
                        canonical_name=match.canonical_name,
                        entity_id=match.entity_id,
                        score=match.score,
                        is_composer_context=is_composer_context,
                    )

    return best_by_category


def find_all_entity_mentions(
    db: Session,
    message: str,
    category: str,
    max_window: int = 4,
) -> list[EntityMatch]:
    """
    Like `resolve_entities`, but returns every distinct entity of the given
    category mentioned in the message (not just the single best match).
    Needed for maqam comparison ("الفرق بين الصبا والبياتي") where two
    maqamat must both be recognized in one message.
    """

    rows = _db_entity_rows(db)[category]
    raw_tokens = message.split()
    tokens = [normalize_arabic(t) for t in raw_tokens]

    best_by_entity: dict[int, EntityMatch] = {}

    for window in range(max_window, 0, -1):
        for start in range(0, max(0, len(tokens) - window + 1)):
            span_tokens = list(tokens[start:start + window])
            if not span_tokens:
                continue

            span_tokens[0] = strip_leading_prefix(span_tokens[0])
            ngram = " ".join(span_tokens)

            if len(ngram) < 2:
                continue

            match = _best_match(ngram, rows)
            if match is None:
                continue

            existing = best_by_entity.get(match.entity_id)
            if existing is None or match.score > existing.score:
                best_by_entity[match.entity_id] = match

    return sorted(best_by_entity.values(), key=lambda m: m.score, reverse=True)


def resolve_song_title(db: Session, message: str) -> tuple[int, str] | None:
    """
    Fuzzy-match an explicitly named song title inside a message, e.g.
    'شو مقام اغنية حنين إلى الوطن؟' -> (song_id, 'حنين إلى الوطن').
    Song titles can be several words long, so this scans wider windows
    than the entity resolver.
    """

    rows = _db_entity_rows(db)["song"]
    raw_tokens = message.split()
    tokens = [normalize_arabic(t) for t in raw_tokens]

    best: EntityMatch | None = None

    for window in range(min(8, len(tokens)), 1, -1):
        for start in range(0, max(0, len(tokens) - window + 1)):
            span_tokens = list(tokens[start:start + window])
            span_tokens[0] = strip_leading_prefix(span_tokens[0])
            ngram = " ".join(span_tokens)

            if len(ngram) < 3:
                continue

            match = _best_match(ngram, rows)
            if match is not None and (best is None or match.score > best.score):
                best = match

    if best is None:
        return None

    return best.entity_id, best.canonical_name


_DIFFICULTY_KEYWORDS = {
    "سهل": "easy", "سهلة": "easy", "سهلة جدا": "easy", "بسيط": "easy", "بسيطة": "easy",
    "متوسط": "medium", "متوسطة": "medium", "وسط": "medium",
    "صعب": "hard", "صعبة": "hard", "صعبة جدا": "hard", "معقد": "hard", "معقدة": "hard",
}


def detect_difficulty(message: str) -> str | None:
    """Deterministic difficulty keyword fallback for when the LLM misses it."""

    normalized = normalize_arabic(message)

    for keyword, value in _DIFFICULTY_KEYWORDS.items():
        if normalize_arabic(keyword) in normalized:
            return value

    return None
