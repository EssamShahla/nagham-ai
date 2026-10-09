"""
Model registry.

Importing this package guarantees every ORM model is registered on
Base.metadata. The lazy string references used by relationships
(e.g. Song.sections -> "SongSection") resolve correctly as long as
the target model module has been imported, which this module does.

NOTE: Do NOT import this module inside app.database.base.
That file only declares Base; keeping model imports here avoids
circular-import chains between database and models.
"""

from app.models.ajnas import Jins
from app.models.artist import Artist
from app.models.composer import Composer
from app.models.rhythm import Rhythm
from app.models.maqam import Maqam
from app.models.otp_verification import OTPVerification
from app.models.song import Song
from app.models.song_maqam import SongMaqam
from app.models.song_section import SongSection
from app.models.song_source import SongSource
from app.models.user import User

__all__ = [
    "Jins",
    "Artist",
    "Composer",
    "Rhythm",
    "Maqam",
    "OTPVerification",
    "Song",
    "SongMaqam",
    "SongSection",
    "SongSource",
    "User",
]
