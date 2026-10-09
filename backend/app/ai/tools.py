from typing import Optional

from sqlalchemy.orm import Session, joinedload

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
from app.ai.semantic_search import apply_filter_groups


def structured_search_songs(
    db: Session,
    maqam: Optional[str] = None,
    artist: Optional[str] = None,
    difficulty: Optional[str] = None,
    year: Optional[int] = None,
    filter_groups: Optional[list] = None,
    limit: int = 10,
):
    """
    Search songs using explicit structured constraints.

    Examples:
    - maqam="بياتي"
    - artist="فيروز"
    - difficulty="medium"
    - year=2020

    Multiple filters can be combined.
    """

    query = (
        db.query(Song)
        .options(
            joinedload(Song.artist),
            joinedload(Song.composer),
            joinedload(Song.rhythm),
            joinedload(Song.maqam),
        )
    )

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

    query = apply_filter_groups(query, filter_groups)

    songs = (
        query
        .order_by(Song.id.desc())
        .limit(limit)
        .all()
    )

    return songs