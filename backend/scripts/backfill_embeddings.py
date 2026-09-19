from sqlalchemy.orm import joinedload

from app.database.connection import SessionLocal

# Import all models so SQLAlchemy can resolve relationships correctly.
# Keep these imports here — do NOT move them to database/base.py.
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

from app.ai.semantic_search import (
    build_song_embedding_text,
    generate_embedding,
)


def main():
    db = SessionLocal()

    try:
        songs = (
            db.query(Song)
            .options(
                joinedload(Song.artist),
                joinedload(Song.composer),
                joinedload(Song.rhythm),
                joinedload(Song.maqam),
            )
            .order_by(Song.id)
            .all()
        )

        if not songs:
            print("No songs found.")
            return

        print(f"Found {len(songs)} songs.")
        print("Regenerating embeddings...")
        print()

        updated = 0
        skipped = 0

        for song in songs:
            embedding_text = build_song_embedding_text(song)

            if not embedding_text.strip():
                print(f"SKIP [{song.id}]: no semantic content")
                skipped += 1
                continue

            song.embedding = generate_embedding(embedding_text)

            updated += 1
            print(f"UPDATED [{song.id}]: {song.title}")

        db.commit()

        print()
        print("-----------------------------")
        print(f"Updated: {updated}")
        print(f"Skipped: {skipped}")
        print("Embedding backfill completed successfully.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()