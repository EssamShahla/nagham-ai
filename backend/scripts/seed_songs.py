from app.database.connection import SessionLocal

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


SONGS = [
    {
        "title": "حنين إلى الوطن",
        "artist": "فيروز",
        "maqam": "بياتي",
        "description": "أغنية وجدانية عن الاشتياق إلى الوطن والبيت والذكريات البعيدة.",
        "moods": ["حنين", "عاطفي", "هادئ"],
        "topics": ["الوطن", "الغربة", "الذكريات", "الاشتياق"],
        "difficulty": "medium",
    },
    {
        "title": "ليلة من الذكريات",
        "artist": "أم كلثوم",
        "maqam": "نهاوند",
        "description": "أغنية عاطفية عن ليلة تعيد ذكريات الحب القديم واللحظات التي لا تنسى.",
        "moods": ["رومانسي", "حنين", "هادئ"],
        "topics": ["الحب", "الليل", "الذكريات"],
        "difficulty": "hard",
    },
    {
        "title": "موعد بعد الغياب",
        "artist": "عبد الحليم حافظ",
        "maqam": "عجم",
        "description": "أغنية مبهجة عن لقاء الحبيب بعد غياب طويل والفرح بعودته.",
        "moods": ["سعيد", "مبهج", "رومانسي"],
        "topics": ["اللقاء", "الحب", "الفرح", "العودة"],
        "difficulty": "medium",
    },
    {
        "title": "رسالة إلى حبيب بعيد",
        "artist": "وردة الجزائرية",
        "maqam": "كرد",
        "description": "أغنية عن شخص يرسل مشاعره إلى حبيب بعيد ويشتاق إلى رؤيته.",
        "moods": ["شوق", "رومانسي", "حزين"],
        "topics": ["الحب", "البعد", "الاشتياق", "الرسائل"],
        "difficulty": "medium",
    },
    {
        "title": "دموع الفراق",
        "artist": "أم كلثوم",
        "maqam": "صبا",
        "description": "أغنية شديدة الحزن عن نهاية علاقة وفراق شخص عزيز.",
        "moods": ["حزين", "مؤلم", "شجي"],
        "topics": ["الفراق", "الحب", "الخسارة"],
        "difficulty": "hard",
    },
    {
        "title": "صباح جديد",
        "artist": "محمد عبد الوهاب",
        "maqam": "عجم",
        "description": "أغنية مشرقة عن بداية جديدة والأمل والتفاؤل بالمستقبل.",
        "moods": ["متفائل", "مشرق", "سعيد"],
        "topics": ["الأمل", "البداية", "المستقبل", "الحياة"],
        "difficulty": "easy",
    },
    {
        "title": "على طريق السفر",
        "artist": "فيروز",
        "maqam": "كرد",
        "description": "أغنية تأملية عن السفر والابتعاد عن المكان والأشخاص والبحث عن حياة جديدة.",
        "moods": ["تأملي", "حنين", "هادئ"],
        "topics": ["السفر", "الغربة", "البعد", "الحياة"],
        "difficulty": "medium",
    },
    {
        "title": "فرحة اللقاء",
        "artist": "وردة الجزائرية",
        "maqam": "راست",
        "description": "أغنية مليئة بالسعادة والاحتفال بلقاء الأحبة بعد انتظار طويل.",
        "moods": ["سعيد", "احتفالي", "مبهج"],
        "topics": ["اللقاء", "الفرح", "الأحبة", "الاحتفال"],
        "difficulty": "easy",
    },
    {
        "title": "ليل الشوق",
        "artist": "عبد الحليم حافظ",
        "maqam": "بياتي",
        "description": "أغنية هادئة عن السهر ليلًا والتفكير في الحبيب والشوق إليه.",
        "moods": ["شوق", "رومانسي", "هادئ"],
        "topics": ["الليل", "الحب", "الاشتياق", "الانتظار"],
        "difficulty": "medium",
    },
    {
        "title": "نداء الروح",
        "artist": "صباح فخري",
        "maqam": "حجاز",
        "description": "أغنية ذات طابع روحاني وتأملي تبحث عن السكينة والسلام الداخلي.",
        "moods": ["روحاني", "تأملي", "هادئ"],
        "topics": ["الروح", "السكينة", "التأمل"],
        "difficulty": "hard",
    },
    {
        "title": "حب بلا نهاية",
        "artist": "أم كلثوم",
        "maqam": "راست",
        "description": "أغنية رومانسية عن حب عميق يستمر رغم مرور الزمن والصعوبات.",
        "moods": ["رومانسي", "دافئ", "عاطفي"],
        "topics": ["الحب", "الوفاء", "الزمن"],
        "difficulty": "hard",
    },
    {
        "title": "وحدي في المدينة",
        "artist": "فيروز",
        "maqam": "نهاوند",
        "description": "أغنية عن الوحدة في مدينة بعيدة والشعور بالغربة وسط الناس.",
        "moods": ["وحيد", "حزين", "تأملي"],
        "topics": ["الوحدة", "الغربة", "المدينة", "البعد"],
        "difficulty": "medium",
    },
    {
        "title": "رقصة الفرح",
        "artist": "صباح فخري",
        "maqam": "عجم",
        "description": "أغنية احتفالية سريعة عن الفرح والرقص واجتماع الأصدقاء.",
        "moods": ["مبهج", "احتفالي", "نشيط"],
        "topics": ["الفرح", "الرقص", "الأصدقاء", "الاحتفال"],
        "difficulty": "medium",
    },
    {
        "title": "انتظار على النافذة",
        "artist": "وردة الجزائرية",
        "maqam": "بياتي",
        "description": "أغنية عن انتظار شخص عزيز والنظر من النافذة أملًا في عودته.",
        "moods": ["شوق", "هادئ", "حزين"],
        "topics": ["الانتظار", "العودة", "الحب", "الاشتياق"],
        "difficulty": "medium",
    },
    {
        "title": "أيام الطفولة",
        "artist": "فيروز",
        "maqam": "راست",
        "description": "أغنية دافئة تستعيد ذكريات الطفولة والبيت والأيام البسيطة.",
        "moods": ["حنين", "دافئ", "هادئ"],
        "topics": ["الطفولة", "الذكريات", "البيت", "الماضي"],
        "difficulty": "easy",
    },
    {
        "title": "قلب مكسور",
        "artist": "عبد الحليم حافظ",
        "maqam": "صبا",
        "description": "أغنية حزينة عن خيبة الحب والألم بعد فقدان الحبيب.",
        "moods": ["حزين", "مؤلم", "عاطفي"],
        "topics": ["الحب", "الفقد", "الفراق", "الألم"],
        "difficulty": "hard",
    },
    {
        "title": "طريق الأمل",
        "artist": "محمد عبد الوهاب",
        "maqam": "راست",
        "description": "أغنية تشجع على الاستمرار وتجاوز الصعوبات والتطلع إلى مستقبل أفضل.",
        "moods": ["متفائل", "قوي", "ملهم"],
        "topics": ["الأمل", "المستقبل", "الصمود", "النجاح"],
        "difficulty": "medium",
    },
    {
        "title": "نسيم المساء",
        "artist": "صباح فخري",
        "maqam": "حجاز",
        "description": "أغنية هادئة وتأملية عن المساء والهدوء واستعادة الذكريات.",
        "moods": ["هادئ", "تأملي", "حنين"],
        "topics": ["المساء", "الذكريات", "الهدوء"],
        "difficulty": "medium",
    },
    {
        "title": "عودة المسافر",
        "artist": "فيروز",
        "maqam": "عجم",
        "description": "أغنية سعيدة عن عودة شخص من السفر واجتماعه بعائلته وأحبائه.",
        "moods": ["سعيد", "دافئ", "مبهج"],
        "topics": ["العودة", "السفر", "العائلة", "اللقاء"],
        "difficulty": "easy",
    },
    {
        "title": "بين الحلم والحقيقة",
        "artist": "محمد عبد الوهاب",
        "maqam": "نهاوند",
        "description": "أغنية تأملية عن الأحلام والواقع والحيرة بين ما نتمناه وما نعيشه.",
        "moods": ["تأملي", "عاطفي", "غامض"],
        "topics": ["الأحلام", "الحياة", "الحيرة", "الواقع"],
        "difficulty": "hard",
    },
]


def main():
    db = SessionLocal()

    try:
        user = db.query(User).order_by(User.id).first()

        if not user:
            raise RuntimeError(
                "No users found. Create a user before running the seed."
            )

        created = 0
        skipped = 0

        for data in SONGS:
            artist = (
                db.query(Artist)
                .filter(Artist.name_ar == data["artist"])
                .first()
            )

            if not artist:
                print(f'SKIP: Artist not found: {data["artist"]}')
                skipped += 1
                continue

            maqam = (
                db.query(Maqam)
                .filter(Maqam.name_ar == data["maqam"])
                .first()
            )

            if not maqam:
                print(f'SKIP: Maqam not found: {data["maqam"]}')
                skipped += 1
                continue

            existing = (
                db.query(Song)
                .filter(
                    Song.title == data["title"],
                    Song.artist_id == artist.id,
                )
                .first()
            )

            if existing:
                print(f'SKIP: {data["title"]}')
                skipped += 1
                continue

            song = Song(
                title=data["title"],
                description=data["description"],
                moods=data["moods"],
                topics=data["topics"],
                difficulty=data["difficulty"],
                artist_id=artist.id,
                maqam_id=maqam.id,
                created_by=user.id,
            )

            db.add(song)
            db.flush()

            # Relationships are needed by build_song_embedding_text()
            song.artist = artist
            song.maqam = maqam

            embedding_text = build_song_embedding_text(song)
            song.embedding = generate_embedding(embedding_text)

            print(f'ADD: {song.title}')
            created += 1

        db.commit()

        print()
        print(f"Created: {created}")
        print(f"Skipped: {skipped}")
        print("Seed completed successfully.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()