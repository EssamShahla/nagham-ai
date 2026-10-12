from sentence_transformers import SentenceTransformer

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_

from app.models.user import User
from app.models.artist import Artist
from app.models.composer import Composer
from app.models.rhythm import Rhythm
from app.models.ajnas import Jins
from app.models.maqam import Maqam
from app.models.song import Song
from app.models.song_maqam import SongMaqam
from app.models.song_source import SongSource
from app.models.otp_verification import OTPVerification


MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
MIN_RANKING_SCORE = 0.50

_embedding_model = SentenceTransformer(MODEL_NAME)

def build_song_embedding_text(song) -> str:
    """
    Build the semantic representation of a song.

    Only meaning-related fields are included here.
    Structured fields such as artist and maqam are handled
    separately by structured/hybrid search.
    """

    parts = []

    if song.title:
        parts.append(song.title)

    if song.description:
        parts.append(song.description)

    if song.moods:
        parts.append(" ".join(song.moods))

    if song.topics:
        parts.append(" ".join(song.topics))

    if song.lyrics:
        parts.append(song.lyrics)

    return "\n".join(parts)


def generate_embedding(text: str) -> list[float]:
    """
    Generate a normalized 384-dimensional embedding
    for semantic similarity search.
    """

    if not text or not text.strip():
        raise ValueError("Cannot generate embedding for empty text")

    embedding = _embedding_model.encode(
        text,
        normalize_embeddings=True
    )

    return embedding.tolist()


def calculate_metadata_score(
    song: Song,
    semantic_similarity: float,
    requested_moods: list[str] | None = None,
    requested_topics: list[str] | None = None,
) -> float:
    """
    Re-rank semantic results using explicit mood/topic metadata.

    Topics are treated as stronger requirements than moods:
    - exact topic match -> strong boost
    - requested topic but no match -> penalty
    - mood match -> smaller boost
    """

    requested_moods = requested_moods or []
    requested_topics = requested_topics or []

    song_moods = {
        str(mood).strip().lower()
        for mood in (song.moods or [])
        if mood
    }

    song_topics = {
        str(topic).strip().lower()
        for topic in (song.topics or [])
        if topic
    }

    normalized_moods = {
        str(mood).strip().lower()
        for mood in requested_moods
        if mood and str(mood).strip()
    }

    normalized_topics = {
        str(topic).strip().lower()
        for topic in requested_topics
        if topic and str(topic).strip()
    }

    mood_matches = len(normalized_moods & song_moods)
    topic_matches = len(normalized_topics & song_topics)

    score = semantic_similarity

    # Topics describe what the song is actually about,
    # so explicit topic matches receive a strong boost.
    if normalized_topics:
        if topic_matches > 0:
            score += topic_matches * 0.35
        else:
            score -= 0.20

    # Mood is useful, but weaker than the actual topic.
    if mood_matches > 0:
        score += mood_matches * 0.10

    return score


def semantic_search_songs(
    db: Session,
    query: str,
    limit: int = 10,
    moods: list[str] | None = None,
    topics: list[str] | None = None,
):
    """
    Search songs semantically, then re-rank the strongest
    candidates using explicit mood/topic metadata.
    """

    if not query or not query.strip():
        raise ValueError("Search query cannot be empty")

    query_embedding = generate_embedding(query.strip())
    distance = Song.embedding.cosine_distance(query_embedding)

    # Retrieve more candidates than we finally need so metadata
    # re-ranking has enough songs to work with.
    candidate_limit = max(limit * 5, 25)

    results = (
        db.query(
            Song,
            distance.label("distance")
        )
        .options(
            joinedload(Song.artist),
            joinedload(Song.composer),
            joinedload(Song.rhythm),
            joinedload(Song.maqam),
        )
        .filter(Song.embedding.isnot(None))
        .order_by(distance)
        .limit(candidate_limit)
        .all()
    )

    ranked_results = []

    for song, distance_value in results:
        semantic_similarity = max(
            0.0,
            min(1.0, 1.0 - float(distance_value))
        )

        final_score = calculate_metadata_score(
            song=song,
            semantic_similarity=semantic_similarity,
            requested_moods=moods,
            requested_topics=topics,
        )

        ranked_results.append(
            {
                "song": song,
                "similarity": semantic_similarity,
                "ranking_score": final_score,
            }
        )

    ranked_results.sort(
        key=lambda item: item["ranking_score"],
        reverse=True,
    )
    
    print("\n[RERANKING]")
    for item in ranked_results[:10]:
        song = item["song"]

        print(
            f"{song.title} | "
            f"semantic={item['similarity']:.4f} | "
            f"final={item['ranking_score']:.4f} | "
            f"moods={song.moods} | "
            f"topics={song.topics}"
        )

    relevant_results = [
        item
        for item in ranked_results
        if item["ranking_score"] >= MIN_RANKING_SCORE
    ]

    return relevant_results[:limit]
    
    
def _read_field_value(search_filter):
    """Supports both Pydantic objects and plain dictionaries."""

    field = (
        search_filter.field
        if hasattr(search_filter, "field")
        else search_filter.get("field")
    )

    value = (
        search_filter.value
        if hasattr(search_filter, "value")
        else search_filter.get("value")
    )

    return field, value


def _build_filter_condition(field, value):
    """Build a single SQLAlchemy condition for one (field, value) pair, or
    None when the field/value combination can't produce a valid condition."""

    if field == "artist":
        return Song.artist.has(Artist.name_ar.ilike(str(value).strip()))

    if field == "composer":
        return Song.composer.has(Composer.name_ar.ilike(str(value).strip()))

    if field == "maqam":
        return Song.maqam.has(Maqam.name_ar.ilike(str(value).strip()))

    if field == "difficulty":
        return Song.difficulty.ilike(str(value).strip())

    if field == "year":
        try:
            return Song.year == int(value)
        except (TypeError, ValueError):
            return None

    return None


def apply_filter_groups(query, filter_groups):
    if not filter_groups:
        return query

    for group in filter_groups:
        # Supports both Pydantic objects and dictionaries
        operator = (
            group.operator
            if hasattr(group, "operator")
            else group.get("operator", "AND")
        )

        filters = (
            group.filters
            if hasattr(group, "filters")
            else group.get("filters", [])
        )

        conditions = []
        for search_filter in filters:
            field, value = _read_field_value(search_filter)
            condition = _build_filter_condition(field, value)
            if condition is not None:
                conditions.append(condition)

        if not conditions:
            continue

        if operator == "OR":
            query = query.filter(or_(*conditions))
        else:
            query = query.filter(and_(*conditions))

    return query


def apply_exclude_filters(query, exclude_filters):
    """
    Exclude songs matching any of the given (field, value) conditions.
    Each exclusion is independent/AND-ed together: excluding artist=X and
    maqam=Y removes songs matching EITHER, not only songs matching both.
    """

    if not exclude_filters:
        return query

    for search_filter in exclude_filters:
        field, value = _read_field_value(search_filter)
        condition = _build_filter_condition(field, value)
        if condition is not None:
            query = query.filter(~condition)

    return query


def hybrid_search_songs(
    db: Session,
    semantic_query: str,
    maqam: str | None = None,
    artist: str | None = None,
    difficulty: str | None = None,
    year: int | None = None,
    moods: list[str] | None = None,
    topics: list[str] | None = None,
    filter_groups: list | None = None,
    exclude_filters: list | None = None,
    limit: int = 10,
):
    """
    Combine structured filtering with semantic search
    and metadata-aware re-ranking.
    """

    if not semantic_query or not semantic_query.strip():
        raise ValueError("Semantic query cannot be empty")

    query_embedding = generate_embedding(semantic_query.strip())
    distance = Song.embedding.cosine_distance(query_embedding)

    query = (
        db.query(Song, distance.label("distance"))
        .options(
            joinedload(Song.artist),
            joinedload(Song.composer),
            joinedload(Song.rhythm),
            joinedload(Song.maqam),
        )
        .filter(Song.embedding.isnot(None))
    )

    # Structured filters
    if maqam:
        query = query.join(Song.maqam).filter(
            Maqam.name_ar.ilike(maqam.strip())
        )

    if artist:
        query = query.join(Song.artist).filter(
            Artist.name_ar.ilike(artist.strip())
        )

    if difficulty:
        query = query.filter(
            Song.difficulty.ilike(difficulty.strip())
        )

    if year is not None:
        query = query.filter(Song.year == year)
    
    query = apply_filter_groups(
        query,
        filter_groups,
    )

    query = apply_exclude_filters(
        query,
        exclude_filters,
    )

    # Retrieve a wider candidate pool before metadata re-ranking.
    candidate_limit = max(limit * 5, 25)

    results = (
        query
        .order_by(distance)
        .limit(candidate_limit)
        .all()
    )

    ranked_results = []

    for song, distance_value in results:
        semantic_similarity = max(
            0.0,
            min(1.0, 1.0 - float(distance_value))
        )

        final_score = calculate_metadata_score(
            song=song,
            semantic_similarity=semantic_similarity,
            requested_moods=moods,
            requested_topics=topics,
        )

        ranked_results.append(
            {
                "song": song,
                "similarity": semantic_similarity,
                "ranking_score": final_score,
            }
        )

    ranked_results.sort(
        key=lambda item: item["ranking_score"],
        reverse=True,
    )

    print("\n[HYBRID RERANKING]")
    for item in ranked_results[:10]:
        song = item["song"]

        print(
            f"{song.title} | "
            f"semantic={item['similarity']:.4f} | "
            f"final={item['ranking_score']:.4f} | "
            f"moods={song.moods} | "
            f"topics={song.topics}"
        )

    relevant_results = [
        item
        for item in ranked_results
        if item["ranking_score"] >= MIN_RANKING_SCORE
    ]

    return relevant_results[:limit]