import json
from typing import Any

from typing import Any, Literal
from pydantic import BaseModel
from app.ai.semantic_search import hybrid_search_songs
from app.ai.llm_client import chat as llm_chat


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
    ]
}


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
  "result_limit": None
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
  "semantic_query": "حزينة غربة",
  "maqam": "بياتي",
  "artist": null,
  "difficulty": null,
  "year": null
}

10. Return JSON only. No markdown and no explanation.
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

def enrich_intent_metadata(
    user_message: str,
    intent: dict,
) -> dict:
    """
    Deterministic fallback for explicit mood/topic words.

    The LLM remains responsible for understanding the request,
    but explicit keywords are recovered here if the small model
    fails to extract them.
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
    # prompt asks it not to. Strip them out deterministically so a pure
    # structured request isn't misrouted into (and rejected by) semantic
    # search just because semantic_query is non-empty.
    structured_values = []

    if intent.get("artist"):
        structured_values.append(intent["artist"])

    structured_values.extend(intent.get("artists") or [])
    structured_values.extend(intent.get("composers") or [])

    if intent.get("maqam"):
        structured_values.append(intent["maqam"])

    for group in intent.get("filter_groups") or []:
        for search_filter in group.get("filters", []):
            value = search_filter.get("value")
            if isinstance(value, str):
                structured_values.append(value)

    cleaned_semantic_query = intent.get("semantic_query") or ""

    for value in structured_values:
        value = str(value).strip()
        if value:
            cleaned_semantic_query = cleaned_semantic_query.replace(value, "")

    intent["semantic_query"] = cleaned_semantic_query.strip()

    return intent


# method 1

def analyze_user_request(user_message: str) -> dict[str, Any]:
    """
    Analyze a natural-language music request using the configured LLM.
    """

    if not user_message or not user_message.strip():
        raise ValueError("User message cannot be empty")

    content = llm_chat(
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_message.strip(),
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
    )

    return result


# method 2

def search_from_user_request(db, user_message: str, limit: int = 10):
    """
    Analyze the user's natural-language request and execute
    the appropriate song search.
    """

    analysis = analyze_user_request(user_message)

    if analysis.get("intent") != "song_search":
        raise ValueError(
            f"Unsupported intent: {analysis.get('intent')}"
        )

    semantic_query = analysis.get("semantic_query")

    if not semantic_query:
        semantic_query = user_message

    results = hybrid_search_songs(
        db=db,
        semantic_query=semantic_query,
        maqam=analysis.get("maqam"),
        artist=analysis.get("artist"),
        difficulty=analysis.get("difficulty"),
        year=analysis.get("year"),
        limit=limit,
    )

    return {
        "analysis": analysis,
        "results": results,
    }
    
    
    

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
) -> str:
    """
    Generate a grounded natural-language answer using
    only the songs retrieved from the database.
    """

    if not search_results:
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



# method 4

def run_nagham_agent(
    db,
    user_message: str,
    limit: int = 5,
) -> dict:
    """
    Run the complete Nagham AI pipeline:

    User request
        -> intent analysis
        -> hybrid retrieval
        -> RAG context
        -> grounded final answer
    """

    search_data = search_from_user_request(
        db=db,
        user_message=user_message,
        limit=limit,
    )

    answer = generate_rag_answer(
        user_message=user_message,
        search_results=search_data["results"],
    )

    return {
        "analysis": search_data["analysis"],
        "results": search_data["results"],
        "answer": answer,
    }