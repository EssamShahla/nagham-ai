from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func

from app.database.base import Base


class PendingSongCreation(Base):
    """
    A validated, fully-resolved "add a new song" draft awaiting the user's
    explicit confirmation through the AI agent (app/ai/song_creation.py).

    Same precedent as `LoginExchangeCode`/`PendingGoogleLink`: an opaque,
    single-use, short-lived server-side record. The client only ever sees
    the opaque `token` (round-tripped through conversation `history`) --
    never the payload itself, so a tampered/forged `history` entry cannot
    be used to authorize a write. `confirm` must re-validate `user_id`
    against the user authenticated on *that* request, and `expires_at` /
    `is_used` before ever executing the write.
    """

    __tablename__ = "pending_song_creations"

    id = Column(Integer, primary_key=True, index=True)

    token = Column(String(255), unique=True, nullable=False, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # The fully-resolved/staged draft: title, artist/composer tagged
    # choices ({"kind": "existing", "id": ...} | {"kind": "new", "name": ...}),
    # maqam_id, rhythm_id, lyricist_name, musical_key, difficulty,
    # description, year, moods, topics, source_url.
    payload = Column(JSON, nullable=False)

    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
