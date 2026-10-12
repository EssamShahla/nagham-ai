import json
import re
from typing import Any

from typing import Any, Literal
from pydantic import BaseModel
from app.ai.llm_client import chat as llm_chat
from app.ai.arabic_text import (
    canonicalize_value,
    detect_difficulty,
    normalize_arabic,
    resolve_entities,
    strip_diacritics_for_llm,
)


class SearchFilter(BaseModel):
    field: Literal[
        "artist",
        "composer",
        "maqam",
        "difficulty",
        "year",
    ]
    value: str | int


class FilterGroup(BaseModel):
    operator: Literal["AND", "OR"] = "AND"
    filters: list[SearchFilter] = []


class SongSearchIntent(BaseModel):
    intent: Literal["song_search"]
    semantic_query: str = ""
    moods: list[str] = []
    topics: list[str] = []

    maqam: str | None = None

    artist: str | None = None
    artists: list[str] = []
    composers: list[str] = []

    difficulty: Literal["easy", "medium", "hard"] | None = None
    year: int | None = None
    result_limit: int | None = None
    filter_groups: list[FilterGroup] = []

    # Conditions the user explicitly wants EXCLUDED, e.g.
    # "اعطيني اغاني عن الحب بس مش لأم كلثوم" -> exclude artist = أم كلثوم
    exclude_filters: list[SearchFilter] = []


class SongCreationExtraction(BaseModel):
    """
    Fields explicitly stated in one message of a conversational
    "add a new song" request. Every field is optional -- the caller
    (app/ai/song_creation.py) merges whatever is non-null into its
    running draft across turns; nothing here is ever required by the
    schema itself, and nothing is invented when not mentioned.
    """

    title: str | None = None
    artist: str | None = None
    composer: str | None = None
    lyricist_name: str | None = None
    maqam: str | None = None
    musical_key: str | None = None
    rhythm: str | None = None
    difficulty: Literal["easy", "medium", "hard"] | None = None
    description: str | None = None
    source_url: str | None = None


SONG_CREATION_SYSTEM_PROMPT = """
You are extracting structured fields from ONE message of a conversation
where a user is adding a new song to Nagham AI's database, in Arabic or
Palestinian dialect.

Return valid JSON only, with exactly these fields:
{
  "title": string or null,
  "artist": string or null,
  "composer": string or null,
  "lyricist_name": string or null,
  "maqam": string or null,
  "musical_key": string or null,
  "rhythm": string or null,
  "difficulty": "easy", "medium", "hard", or null,
  "description": string or null,
  "source_url": string or null
}

RULES:
1. Only extract a field if it is EXPLICITLY stated in this message.
   Leave every other field null. Never guess, infer, or invent a value.
2. "title" is the song's name (e.g. after "اسمها", "عنوانها", "ضيف اغنية اسمها ...").
3. "artist" is the singer/performer (e.g. after "المغني", "الفنان", "غناء").
4. "composer" is who composed the melody (e.g. "الملحن", "لحنها", "ألحان").
5. "lyricist_name" is who wrote the words (e.g. "كلماتها", "الشاعر", "كتبها").
6. "maqam" is the maqam name (e.g. after "مقامها", "على مقام").
7. "musical_key" is the specific performed tonic/key (e.g. "على درجة دو", "مفتاحها").
   Do not confuse this with "maqam" -- they are different fields.
8. "rhythm" is the rhythm/meter name (e.g. "وزنها", "على ضرب").
9. "difficulty": normalize "سهل"->"easy", "متوسط"->"medium", "صعب"->"hard".
10. "description" is a free-text description the user gave about the song,
    not something you write yourself.
11. "source_url" is a URL the user gave as a reference, if any.
12. Never fabricate lyrics or any field not present in this message.
13. Return JSON only. No markdown, no explanation.
"""


def extract_song_creation_fields(user_message: str) -> dict[str, Any]:
    """
    Extract whatever song-creation fields are explicitly present in this
    one message. Returns a plain dict matching `SongCreationExtraction`'s
    fields, all `None` unless the message actually stated them.
    """

    llm_input = strip_diacritics_for_llm(user_message.strip())

    content = llm_chat(
        messages=[
            {"role": "system", "content": SONG_CREATION_SYSTEM_PROMPT},
            {"role": "user", "content": llm_input},
        ],
        json_mode=True,
    )

    try:
        raw_result = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM returned invalid JSON: {content}") from exc

    try:
        validated = SongCreationExtraction.model_validate(raw_result)
    except Exception as exc:
        raise ValueError(f"LLM returned invalid extraction data: {raw_result}") from exc

    return validated.model_dump()


SYSTEM_PROMPT = """
You are the intent analyzer for Nagham AI, an Arabic and Oriental music assistant.

Your task is to analyze a user's song search request and extract structured search constraints.

Return valid JSON only.

Use exactly these fields:
{
  "intent": "song_search",
  "semantic_query": string,
  "moods": array of strings,
  "topics": array of strings,
  "maqam": string or null,
  "artist": string or null,
  "artists": array of strings,
  "composers": array of strings,
  "difficulty": "easy", "medium", "hard", or null,
  "year": integer or null,
  "result_limit": integer or null,
  "filter_groups": [
    {
        "operator": "AND" or "OR",
        "filters": [
        {
            "field": "artist" | "composer" | "maqam" | "difficulty" | "year",
            "value": string or integer
        }
        ]
    }
    ],
  "exclude_filters": [
    {
        "field": "artist" | "composer" | "maqam" | "difficulty" | "year",
        "value": string or integer
    }
    ]
}


NEGATION / EXCLUSION RULES:

When the user explicitly excludes something using words such as:
"مش", "بس مش", "لكن ليس", "ليس", "عدا", "ما عدا", "غير", "not", "except",
put that condition in exclude_filters instead of the normal fields.

Do not also place an excluded value in artist, artists, composers,
maqam, or filter_groups -- exclude_filters is the only place it belongs.

Examples:

"اعطيني اغاني عن الحب بس مش لأم كلثوم"
→ topics = ["الحب"]
→ artist = null
→ exclude_filters = [{"field": "artist", "value": "أم كلثوم"}]

"أغاني على مقام الحجاز لكن ليس لصباح فخري"
→ maqam = "حجاز"
→ exclude_filters = [{"field": "artist", "value": "صباح فخري"}]

If the SAME value is both requested and excluded (a self-contradictory
request), keep both: put it in the normal field/filter_groups AND in
exclude_filters. The system will detect and report the contradiction.


STRUCTURED FILTER RULES:

For simple requests with one artist, maqam, difficulty, or year,
continue using the existing simple fields.

Use filter_groups when the user expresses alternatives or compound
structured conditions using words such as:
"أو", "or", "either".

Preserve the logical relationship exactly.

Examples:

"أغنية لفيروز"
→ artist = "فيروز"
→ filter_groups = []

"أغنية لفيروز على مقام البياتي"
→ artist = "فيروز"
→ maqam = "بياتي"
→ filter_groups = []

"أغاني لفيروز أو أم كلثوم"
→ filter_groups = [
    {
      "operator": "OR",
      "filters": [
        {"field": "artist", "value": "فيروز"},
        {"field": "artist", "value": "أم كلثوم"}
      ]
    }
  ]

"اقترح لي أغنيتين عن الاشتياق للملحن محمد عبد الوهاب أو لفيروز"
→ semantic_query = "الاشتياق"
→ topics = ["الاشتياق"]
→ result_limit = 2
→ filter_groups = [
    {
      "operator": "OR",
      "filters": [
        {"field": "composer", "value": "محمد عبد الوهاب"},
        {"field": "artist", "value": "فيروز"}
      ]
    }
  ]

When filter_groups represents a condition, do not duplicate that
same condition into artist, artists, composers, maqam, difficulty,
or year.

Do not classify a person explicitly described as "ملحن" or
"composer" as an artist filter.


ARTIST / COMPOSER RULES:

- "artist" is kept for backward compatibility when exactly one performer is requested.
- "artists" contains performer/singer names when multiple performers are requested.
- "composers" contains composer names.

Examples:

"أغنية لفيروز"
→ artist = "فيروز"
→ artists = []
→ composers = []

"أغاني لفيروز أو أم كلثوم"
→ artist = null
→ artists = ["فيروز", "أم كلثوم"]
→ composers = []

"أغنية من ألحان محمد عبد الوهاب"
→ artist = null
→ artists = []
→ composers = ["محمد عبد الوهاب"]

"أغنيتين عن الاشتياق للملحن محمد عبد الوهاب أو لفيروز"
→ artist = "فيروز"
→ artists = []
→ composers = ["محمد عبد الوهاب"]


RESULT COUNT RULES:

- Extract how many song recommendations the user explicitly requests.
- If the user asks for exactly one song using singular wording such as:
  "أغنية", "أغنية واحدة", "a song", "one song"
  → result_limit = 1

- "أغنيتين", "اغنيتين", "أغنيتان", "two songs"
  → result_limit = 2

- If the user explicitly gives another number, use that number.

- If the user asks generally for songs without specifying a number:
  "أغاني", "اقترح أغاني", "songs"
  → result_limit = null

- Never invent a requested count.
- result_limit must be between 1 and 10 when specified.



MOOD AND TOPIC EXTRACTION:

- moods represents emotional character or feeling.
  Examples:
  حزين، مفرح، رومانسي، هادئ، عاطفي، حماسي، حنين

- topics represents what the song is about.
  Examples:
  الغربة، الوطن، الحب، الفراق، الذكريات، السفر، الاشتياق، الأمل

- Extract moods and topics only when they are explicitly present
  or clearly expressed in the user's request.

- Preserve Arabic words and meaning. Do not invent unrelated moods or topics.

- semantic_query should still contain the meaning-related part of the request,
  including relevant moods and topics.

Examples:

User: أريد أغنية حزينة عن الغربة

{
  "intent": "song_search",
  "semantic_query": "حزينة الغربة",
  "moods": ["حزين"],
  "topics": ["الغربة"],
  "maqam": null,
  "artist": null,
  "difficulty": null,
  "year": null,
  "result_limit": 1
}

User: اقترح لي أغنيتين عن الاشتياق

{
  "intent": "song_search",
  "semantic_query": "الاشتياق",
  "moods": [],
  "topics": ["الاشتياق"],
  "maqam": null,
  "artist": null,
  "difficulty": null,
  "year": null,
  "result_limit": 2
}

User: "أريد أغنية لفيروز على مقام البياتي عن الحنين إلى الوطن والذكريات"

Output:
{
  "intent": "song_search",
  "semantic_query": "الحنين إلى الوطن والذكريات",
  "moods": ["حنين"],
  "topics": ["الوطن", "الذكريات"],
  "maqam": "بياتي",
  "artist": "فيروز",
  "difficulty": null,
  "year": null,
  "result_limit": 1
}

User: "أعطني أغاني على مقام البياتي"

Output:
{
  "intent": "song_search",
  "semantic_query": "",
  "moods": [],
  "topics": [],
  "maqam": "بياتي",
  "artist": null,
  "difficulty": null,
  "year": null,
  "result_limit": null
}



Rules:
1. intent must be "song_search" for requests asking to find or recommend songs.
2. Extract maqam when explicitly mentioned.
3. Extract artist when explicitly mentioned.
4. Extract difficulty when explicitly mentioned.
   Normalize difficulty to exactly one of these English values:
   "easy", "medium", or "hard".

   Arabic examples:
   "سهل" -> "easy"
   "متوسط" -> "medium"
   "صعب" -> "hard"

   If difficulty is not mentioned, return null.
5. Extract year when explicitly mentioned.
6. semantic_query should contain ONLY meaning-related information such as
   mood, topic, emotion, theme, situation, or description that requires
   semantic search.

   If the user provides only structured constraints such as maqam, artist,
   difficulty, or year, semantic_query MUST be an empty string "".

7. Remove structured constraints such as maqam, artist, difficulty, and year
   from semantic_query.

8. Preserve the user's original meaning-related words exactly whenever possible.
   Do NOT translate, creatively rewrite, summarize, or replace them with
   different words.

9. Never invent words that were not present in the user's request.

10. Never include generic search words such as:
    "أغنية", "أغاني", "أريد", "أعطني", "song", or "songs"
    in semantic_query.

11. For Arabic requests, keep semantic_query entirely in Arabic.

12. Do not invent information that the user did not provide.




Examples:

User: "أعطني أغاني على مقام البياتي"
Output:
{
  "intent": "song_search",
  "semantic_query": "",
  "maqam": "بياتي",
  "artist": null,
  "difficulty": null,
  "year": null
}

User: "أريد أغنية حزينة على مقام البياتي عن الغربة"
Output:
{
  "intent": "song_search",
  "semantic_query": "حزينة الغربة",
  "maqam": "بياتي",
  "artist": null,
  "difficulty": null,
  "year": null
}

User: "أريد أغنية لفيروز على مقام البياتي عن الحنين إلى الوطن والذكريات"
Output:
{
  "intent": "song_search",
  "semantic_query": "الحنين إلى الوطن والذكريات",
  "maqam": "بياتي",
  "artist": "فيروز",
  "difficulty": null,
  "year": null
}

13. Return JSON only. No markdown and no explanation.
"""


MOOD_KEYWORDS = {
    "حزين": "حزين",
    "حزينة": "حزين",
    "حزينةً": "حزين",
    "فرح": "سعيد",
    "فرحة": "سعيد",
    "سعيد": "سعيد",
    "سعيدة": "سعيد",
    "رومانسي": "رومانسي",
    "رومانسية": "رومانسي",
    "هادئ": "هادئ",
    "هادئة": "هادئ",
    "عاطفي": "عاطفي",
    "عاطفية": "عاطفي",
    "حنين": "حنين",
}

TOPIC_KEYWORDS = {
    "الغربة": "الغربة",
    "الوطن": "الوطن",
    "الحب": "الحب",
    "الفراق": "الفراق",
    "الذكريات": "الذكريات",
    "السفر": "السفر",
    "الاشتياق": "الاشتياق",
    "الأمل": "الأمل",
}

MOOD_KEYWORDS.update({
    "الحزن": "حزين",
    "حزن": "حزين",
    "حزينة": "حزين",
    "حزين": "حزين",

    "الحنين": "حنين",
    "حنين": "حنين",

    "الرومانسية": "رومانسي",
    "رومانسية": "رومانسي",
    "رومانسي": "رومانسي",

    "الهدوء": "هادئ",
    "هادئة": "هادئ",
    "هادئ": "هادئ",
})

TOPIC_KEYWORDS.update({
    "الغربة": "الغربة",

    "الوطن": "الوطن",

    "الحب": "الحب",

    "الفراق": "الفراق",

    "الفقد": "الفقد",

    "الذكريات": "الذكريات",

    "السفر": "السفر",

    "البعد": "البعد",

    "الاشتياق": "الاشتياق",
    "الشوق": "الاشتياق",

    "الأمل": "الأمل",

    "الانتظار": "الانتظار",

    "العودة": "العودة",
})




TOPIC_NORMALIZATION = {
    "اشتياق": "الاشتياق",
    "الاشتياق": "الاشتياق",

    "غربة": "الغربة",
    "الغربة": "الغربة",

    "وطن": "الوطن",
    "الوطن": "الوطن",

    "حب": "الحب",
    "الحب": "الحب",

    "فراق": "الفراق",
    "الفراق": "الفراق",

    "فقد": "الفقد",
    "الفقد": "الفقد",

    "سفر": "السفر",
    "السفر": "السفر",

    "بعد": "البعد",
    "البعد": "البعد",
}

def _detect_contradiction(intent: dict) -> bool:
    """
    True when the same (field, value) is both required and excluded,
    e.g. "اعطيني اغاني لأم كلثوم بس مش لأم كلثوم".
    """

    required: set[tuple[str, str]] = set()

    if intent.get("maqam"):
        required.add(("maqam", str(intent["maqam"]).strip().lower()))

    if intent.get("artist"):
        required.add(("artist", str(intent["artist"]).strip().lower()))

    for name in intent.get("artists") or []:
        required.add(("artist", str(name).strip().lower()))

    for name in intent.get("composers") or []:
        required.add(("composer", str(name).strip().lower()))

    for group in intent.get("filter_groups") or []:
        for search_filter in group.get("filters", []):
            field = search_filter.get("field")
            value = search_filter.get("value")
            if field and value is not None:
                required.add((field, str(value).strip().lower()))

    for search_filter in intent.get("exclude_filters") or []:
        field = search_filter.get("field")
        value = search_filter.get("value")
        if field and value is not None and (field, str(value).strip().lower()) in required:
            return True

    return False


_NEGATION_MARKERS = ["مش", "ليس", "عدا", "ما عدا", "غير"]


def _deterministic_negation_fallback(db, user_message: str, intent: dict) -> dict:
    """
    If the message clearly contains a negation marker ("مش", "ليس", ...)
    but the LLM didn't populate exclude_filters, recover the excluded
    entity from the deterministic resolver: whichever artist/composer/maqam
    it finds mentioned that ISN'T already one of the positive constraints
    is almost certainly the one being excluded.
    """

    if intent.get("exclude_filters"):
        return intent

    normalized_message = normalize_arabic(user_message)
    if not any(normalize_arabic(marker) in normalized_message for marker in _NEGATION_MARKERS):
        return intent

    matches = resolve_entities(db, user_message)
    exclude_filters = []

    artist_match = matches.get("artist")
    positive_artists = set(
        filter(None, [intent.get("artist"), *(intent.get("artists") or [])])
    )
    if artist_match and artist_match.canonical_name not in positive_artists:
        exclude_filters.append({"field": "artist", "value": artist_match.canonical_name})

    composer_match = matches.get("composer")
    positive_composers = set(intent.get("composers") or [])
    if (
        composer_match
        and composer_match.canonical_name not in positive_composers
        and composer_match.canonical_name not in positive_artists
    ):
        exclude_filters.append({"field": "composer", "value": composer_match.canonical_name})

    maqam_match = matches.get("maqam")
    if maqam_match and maqam_match.canonical_name != intent.get("maqam"):
        exclude_filters.append({"field": "maqam", "value": maqam_match.canonical_name})

    if exclude_filters:
        intent["exclude_filters"] = exclude_filters

    return intent


def _collect_structured_values(intent: dict) -> list[str]:
    values = []

    if intent.get("artist"):
        values.append(intent["artist"])

    values.extend(intent.get("artists") or [])
    values.extend(intent.get("composers") or [])

    if intent.get("maqam"):
        values.append(intent["maqam"])

    for group in intent.get("filter_groups") or []:
        for search_filter in group.get("filters", []):
            value = search_filter.get("value")
            if isinstance(value, str):
                values.append(value)

    for search_filter in intent.get("exclude_filters") or []:
        value = search_filter.get("value")
        if isinstance(value, str):
            values.append(value)

    return values


def _sanitize_semantic_query(user_message: str, semantic_query: str) -> str:
    """
    Guard against two small-LLM failure modes seen with qwen2.5:3b:
    (1) echoing a few-shot example's semantic_query verbatim instead of
        reasoning about THIS message, and
    (2) leaving a stray 1-2 character fragment after structured-value
        stripping (e.g. a leftover definite article).

    A semantic_query is only kept if every one of its words actually
    appears somewhere in the user's real message.
    """

    if not semantic_query or not semantic_query.strip():
        return ""

    normalized_message = normalize_arabic(user_message)
    query_words = [w for w in normalize_arabic(semantic_query).split() if w]

    if not query_words:
        return ""

    if len("".join(query_words)) < 3:
        return ""

    if not all(word in normalized_message for word in query_words):
        return ""

    return semantic_query.strip()


def _apply_deterministic_entity_resolution(
    db,
    user_message: str,
    intent: dict,
) -> dict:
    """
    Correct LLM-extracted artist/composer/maqam/difficulty values to their
    canonical database spelling, and fill in any of those fields the LLM
    left empty when the raw message clearly names an entity that exists
    in the database.
    """

    if intent.get("maqam"):
        intent["maqam"] = canonicalize_value(db, "maqam", intent["maqam"])

    if intent.get("artist"):
        intent["artist"] = canonicalize_value(db, "artist", intent["artist"])

    intent["artists"] = [
        canonicalize_value(db, "artist", name)
        for name in (intent.get("artists") or [])
    ]

    intent["composers"] = [
        canonicalize_value(db, "composer", name)
        for name in (intent.get("composers") or [])
    ]

    for group in intent.get("filter_groups") or []:
        for search_filter in group.get("filters", []):
            field = search_filter.get("field")
            if field in ("artist", "composer", "maqam"):
                search_filter["value"] = canonicalize_value(
                    db, field, search_filter.get("value")
                )

    for search_filter in intent.get("exclude_filters") or []:
        field = search_filter.get("field")
        if field in ("artist", "composer", "maqam"):
            search_filter["value"] = canonicalize_value(
                db, field, search_filter.get("value")
            )

    has_any_person_or_maqam = bool(
        intent.get("maqam")
        or intent.get("artist")
        or intent.get("artists")
        or intent.get("composers")
        or intent.get("filter_groups")
    )

    if not has_any_person_or_maqam:
        matches = resolve_entities(db, user_message)

        maqam_match = matches.get("maqam")
        if maqam_match:
            intent["maqam"] = maqam_match.canonical_name

        artist_match = matches.get("artist")
        composer_match = matches.get("composer")

        if composer_match and composer_match.is_composer_context:
            intent["composers"] = [composer_match.canonical_name]
        elif artist_match:
            intent["artist"] = artist_match.canonical_name
        elif composer_match:
            intent["composers"] = [composer_match.canonical_name]

    if not intent.get("difficulty"):
        detected_difficulty = detect_difficulty(user_message)
        if detected_difficulty:
            intent["difficulty"] = detected_difficulty

    intent = _deterministic_negation_fallback(db, user_message, intent)
    intent["contradictory"] = _detect_contradiction(intent)

    return intent


def enrich_intent_metadata(
    user_message: str,
    intent: dict,
    db=None,
) -> dict:
    """
    Deterministic fallback for explicit mood/topic words, and (when a
    database session is available) deterministic Arabic entity correction
    and gap-filling.

    The LLM remains responsible for understanding the request, but
    spelling/diacritic/hamza variants of artist, composer, and maqam names
    are never left to the LLM alone -- they are corrected against the
    actual database here. The LLM can also simply miss an entity that was
    clearly stated; the resolver fills the gap in that case, but only with
    names that genuinely exist in the database (never invented).
    """

    moods = set(intent.get("moods") or [])
    topics = {
        TOPIC_NORMALIZATION.get(
            str(topic).strip(),
            str(topic).strip(),
        )
        for topic in (intent.get("topics") or [])
        if topic and str(topic).strip()
    }

    for keyword, normalized_value in MOOD_KEYWORDS.items():
        if keyword in user_message:
            moods.add(normalized_value)

    for keyword, normalized_value in TOPIC_KEYWORDS.items():
        if keyword in user_message:
            topics.add(normalized_value)

    intent["moods"] = list(moods)
    intent["topics"] = list(topics)
    
    # Build an OR filter group when the user explicitly uses "أو"
    # and the LLM extracted multiple structured people/roles.
    if " أو " in f" {user_message} " and not intent.get("filter_groups"):
        artists = intent.get("artists") or []
        composers = intent.get("composers") or []

        filters = []

        # Composer names should not also be treated as artists
        composer_names = set(composers)

        for composer in composers:
            filters.append({
                "field": "composer",
                "value": composer,
            })

        for artist in artists:
            if artist not in composer_names:
                filters.append({
                    "field": "artist",
                    "value": artist,
                })

        if len(filters) >= 2:
            intent["filter_groups"] = [
                {
                    "operator": "OR",
                    "filters": filters,
                }
            ]

            # Avoid applying the same conditions again as AND filters.
            intent["artist"] = None
            intent["artists"] = []
            intent["composers"] = []

    # The small local LLM sometimes echoes already-structured values
    # (artist/composer/maqam names) into semantic_query even though the
    # prompt asks it not to -- strip BOTH the value as the LLM originally
    # spelled it and its corrected canonical spelling, since the DB
    # correction below often changes the spelling (e.g. "نهوند" ->
    # "نهاوند") after the LLM has already embedded the former in
    # semantic_query.
    structured_values = _collect_structured_values(intent)

    if db is not None:
        intent = _apply_deterministic_entity_resolution(
            db=db,
            user_message=user_message,
            intent=intent,
        )

    structured_values.extend(_collect_structured_values(intent))

    cleaned_semantic_query = intent.get("semantic_query") or ""

    for value in structured_values:
        value = str(value).strip()
        if value:
            cleaned_semantic_query = cleaned_semantic_query.replace(value, "")

    intent["semantic_query"] = _sanitize_semantic_query(
        user_message, cleaned_semantic_query
    )

    return intent


# method 1

def analyze_user_request(user_message: str, db=None) -> dict[str, Any]:
    """
    Analyze a natural-language music request using the configured LLM.

    When a database session is passed, extracted artist/composer/maqam
    values are deterministically corrected/filled against the real data
    (see `_apply_deterministic_entity_resolution`) instead of relying
    solely on the LLM.
    """

    if not user_message or not user_message.strip():
        raise ValueError("User message cannot be empty")

    # Heavy tashkeel measurably confuses qwen2.5:3b's counting/extraction
    # (e.g. plural "أَغَانِي" misread as singular). Diacritics carry no
    # extra information the LLM needs here, so strip them for the LLM call
    # only -- `user_message` (with diacritics intact) is still what's used
    # for display, history, and the deterministic resolver below.
    llm_input = strip_diacritics_for_llm(user_message.strip())

    content = llm_chat(
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": llm_input,
            },
        ],
        json_mode=True,
    )

    try:
        raw_result = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"LLM returned invalid JSON: {content}"
        ) from exc

    try:
        validated_result = SongSearchIntent.model_validate(raw_result)
    except Exception as exc:
        raise ValueError(
            f"LLM returned invalid intent data: {raw_result}"
        ) from exc

    result = validated_result.model_dump()

    result = enrich_intent_metadata(
        user_message=user_message,
        intent=result,
        db=db,
    )

    return result


# method 2

def build_rag_context(search_results: list) -> str:
    """
    Convert retrieved songs into grounded context for the LLM.
    """

    if not search_results:
        return "No matching songs were found."

    context_parts = []

    for index, result in enumerate(search_results, start=1):
        song = result["song"]
        
        similarity = result.get("similarity")

        similarity_text = (
            f"{similarity:.4f}"
            if similarity is not None
            else "Not applicable (structured search)"
        )

        context_parts.append(
            f"""
Song {index}
Title: {song.title}
Artist: {song.artist.name_ar if song.artist else "Unknown"}
Maqam: {song.maqam.name_ar if song.maqam else "Unknown"}
Difficulty: {song.difficulty or "Unknown"}
Description: {song.description or "No description"}
Moods: {", ".join(song.moods or [])}
Topics: {", ".join(song.topics or [])}
Similarity: {similarity_text}
""".strip()
        )

    return "\n\n".join(context_parts)




# method 3

def generate_rag_answer(
    user_message: str,
    search_results: list,
    contradictory: bool = False,
) -> str:
    """
    Generate a grounded natural-language answer using
    only the songs retrieved from the database.
    """

    if not search_results:
        if contradictory:
            return (
                "طلبك يحتوي على شرط متناقض (نفس القيمة مطلوبة ومستبعدة في "
                "آن واحد)، لذلك لا توجد نتائج ممكنة. يرجى تعديل الطلب."
            )
        return (
            "لم أجد أغاني مطابقة لطلبك في قاعدة البيانات الحالية."
        )

    context = build_rag_context(search_results)
    result_count = len(search_results)

    prompt = f"""
You are Nagham, an AI assistant specialized in Oriental music.

The search system found exactly {result_count} matching song(s).

Search context:
{context}

User request:
{user_message}

IMPORTANT OUTPUT RULES:

- Write the entire final answer in clear, natural Arabic only.
- Keep the answer short: maximum 2-3 sentences.
- The search system found exactly {result_count} result(s).
- NEVER claim that you found, selected, or recommend more songs than the number of results provided.
- Mention ONLY songs that exist in the provided context.
- If there is exactly one result, recommend only that one song.
- If there are multiple results, you may recommend only from those results.
- Copy song titles and artist names EXACTLY as they appear in the context.
- Never modify, translate, misspell, or reconstruct song titles or artist names.
- Do not infer the artist's gender.
- Do not invent songs, lyrics, maqamat, composers, rhythms, or other musical facts.
- Do not mention similarity scores.
- Explain the recommendation only using information explicitly present in the context.


User request:
{user_message}

Retrieved context:
{context}

Write the final answer now in Arabic only:
"""

    content = llm_chat(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    return content.strip()


_LATIN_GLUED_TO_ARABIC_RE = re.compile(
    r"[؀-ۿ][A-Za-z]|[A-Za-z][؀-ۿ]"
)


def _looks_garbled(text: str) -> bool:
    """
    Cheap detector for the exact failure caught live: qwen2.5:3b echoing a
    literal English prompt fragment glued directly onto Arabic text with no
    space (e.g. "نudge:"). A real English word used on its own with normal
    spacing does not match this -- only a Latin/Arabic letter boundary with
    no separator, which never happens in legitimate bilingual text.
    """

    return bool(_LATIN_GLUED_TO_ARABIC_RE.search(text))


def _deterministic_facts_answer(facts: str) -> str:
    """
    Last-resort fallback when the LLM can't produce a clean answer even
    after a retry: surface the verified facts directly instead of risking
    another garbled generation. Never invents anything -- it's the same
    facts text the LLM was given.
    """

    return "إليك المعلومات الموثقة المتوفرة:\n\n" + facts


def generate_grounded_answer(
    user_message: str,
    facts: str,
    suggest_explorer: bool = False,
) -> str:
    """
    Answer a music-theory / comparison / song-fact question using ONLY the
    verified facts text passed in. Used by the theory, maqam-comparison,
    song-question, and follow-up graph nodes -- never invents musical
    information; a missing fact must be stated as missing, not guessed.
    """

    explorer_rule = (
        "- اختم إجابتك بجملة نصفية قصيرة تدعو المستخدم لتجربة السلم "
        "الموسيقي التفاعلي لهذا المقام في قسم \"مستكشف المقامات\" بالتطبيق.\n"
        if suggest_explorer
        else ""
    )

    base_prompt = f"""
You are Nagham, an AI assistant specialized in Oriental (Arabic) music theory.

Verified facts available (from our database/sources):
{facts}

STRICT RULES:
- Answer using ONLY the facts given above.
- If a fact the user asked about is marked unavailable/missing, say clearly
  that it is not yet available in the database -- never guess or invent it.
- Do not add outside music-theory knowledge not present in the facts above.
  In particular, never compare the maqam to Western scale names (minor,
  major, Phrygian, etc.) or any other musical system -- that comparison is
  not in the facts above and must not be invented.
- If the facts describe scale intervals using words (e.g. "نصف تون", "تون
  كامل"), copy those exact words -- never convert them to numbers or invent
  different ones.
- Maximum 2-3 sentences, natural Arabic only. Do not mix in any English
  words or letters.
{explorer_rule}
User question:
{user_message}

Write the final answer now in Arabic only:
"""

    content = llm_chat(messages=[{"role": "user", "content": base_prompt}]).strip()

    if _looks_garbled(content):
        retry_prompt = base_prompt + (
            "\n\nYour previous attempt mixed in stray Latin characters. "
            "Write the answer again, entirely in Arabic, with no Latin "
            "letters anywhere."
        )
        content = llm_chat(messages=[{"role": "user", "content": retry_prompt}]).strip()

    if _looks_garbled(content):
        return _deterministic_facts_answer(facts)

    return content


# method 4

def run_nagham_agent(
    db,
    user_message: str,
    limit: int = 5,
    history: list[dict] | None = None,
) -> dict:
    """
    Run the complete Nagham AI pipeline via the LangGraph agent
    (the same graph the HTTP API uses), so evaluation always exercises
    the real structured/semantic/hybrid routing and conversation-aware
    intents instead of a separate, simplified code path.
    """

    # Local import: app.ai.graph imports from this module at import time,
    # so importing it back at module scope here would be circular.
    from app.ai.graph import nagham_graph

    graph_result = nagham_graph.invoke({
        "user_message": user_message,
        "db": db,
        "limit": limit,
        "history": history or [],
    })

    return {
        "analysis": graph_result.get("analysis", {}),
        "results": graph_result.get("results", []),
        "answer": graph_result["answer"],
        "search_type": graph_result.get("search_type"),
    }