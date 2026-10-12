"""
Populate verified maqam/jins theory data for the Maqam Explorer.

Idempotent (get-or-create by name_ar): safe to re-run. Source data and
provenance are documented in full in backend/docs/maqam_theory_research.md
-- this script only encodes what that document already verified; it does
not decide or invent any musical fact itself.

Scope: all 7 seeded maqamat (Saba was implemented and validated first, per
PHASE 2 instructions, before this script was extended to the other 6:
Bayati, Rast, Hijaz, Nahawand, Kurd, 'Ajam).

Usage:
    venv/Scripts/python.exe scripts/seed_maqam_theory.py
"""

from app.database.connection import SessionLocal
from app.models.ajnas import Jins
from app.models.maqam import Maqam
from app.models.maqam_jins import MaqamJins


SOURCES_NOTE = "See backend/docs/maqam_theory_research.md for full sourcing and cross-checks."

# Each entry: canonical DB identity (name_ar, name_en) + verified facts.
# scale_pattern is `None` where a source genuinely doesn't give the
# interval numbers -- left as an explicit incomplete-data state rather
# than guessed.
JINS_DEFS = [
    {
        "name_ar": "صبا",
        "name_en": "Saba",
        "tonic": "D4",
        "scale_pattern": [0.75, 0.75, 0.5],
        "degree_names": ["دوكاه (D)", "سيكاه (نصف بيمول) (E½♭)", "جهاركاه (F)", "(G♭)"],
        "description": (
            "الجنس الأساسي لمقام الصبا. درجة الحجم فيه غير محددة بدقة في "
            "المصادر (بعض المصادر تعتبره ثلاثي النغمات فقط)."
        ),
        "notes": (
            "maqamworld.com: 'Jins Saba has an ambiguous size,' tonic on D, "
            "ghammaz either the 3rd degree (F) or the 6th degree (Bb). "
            + SOURCES_NOTE
        ),
    },
    {
        "name_ar": "حجاز",
        "name_en": "Hijaz",
        "tonic": "D4",
        "scale_pattern": [0.5, 1.5, 0.5],
        "degree_names": ["دوكاه (D)", "كردي (E♭)", "حجاز (F♯/G♭)", "نوى (G)"],
        "description": "جنس رباعي (4 درجات)، نمطه المميز: نصف - زائدة ثانية - نصف.",
        "notes": (
            "maqamworld.com jins/hijaz.php: 4-note jins, tonic D, ghammaz G. "
            "Performance note (not baked into scale_pattern): the interval "
            "between the 2nd and 3rd degrees is usually played smaller than "
            "notated (2nd raised slightly, 3rd lowered slightly) -- "
            "performance-dependent intonation, not a fixed theoretical value. "
            + SOURCES_NOTE
        ),
    },
    {
        "name_ar": "عجم (ثلاثي)",
        "name_en": "Ajam (3-note)",
        "tonic": "Bb4",
        "scale_pattern": [1.0, 1.0],
        "degree_names": ["عجم عشيران (B♭)", "راست (C)", "دوكاه (D)"],
        "description": (
            "النسخة الثلاثية من جنس العجم، تظهر كجنس فرعي (ليست جنسًا أساسيًا "
            "مستقلاً) على الدرجة السادسة في مقامات الصبا والبيات والكرد."
        ),
        "notes": (
            "maqamworld.com jins/ajam.php: '3-note version ... occurs mostly "
            "when used as a secondary jins ... on the 6th scale degree of "
            "Maqam Bayati, Saba, and Kurd.' Interval pattern [1.0, 1.0] is "
            "derived (not directly stated as a number on that page) by "
            "reading the 6th-degree region of all three maqamat' documented "
            "scales, which independently agree. Distinct DB row from the "
            "5-note 'Ajam jins (root jins of Maqam 'Ajam) because they are "
            "musically different ajnas sharing one name. " + SOURCES_NOTE
        ),
    },
    {
        "name_ar": "نكريز",
        "name_en": "Nikriz",
        "tonic": "C4",
        "scale_pattern": None,
        "description": "جنس خماسي (5 درجات)، أحد البديلين الموثقين على الدرجة السادسة في مقام الصبا.",
        "notes": (
            "INCOMPLETE DATA: maqamworld.com jins/nikriz.php confirms 5 notes, "
            "tonic C, ghammaz G, but gives the exact interval structure only "
            "via a notation image that could not be read as text. Do not "
            "treat scale_pattern as verified until a textual/numeric source "
            "is found. " + SOURCES_NOTE
        ),
    },
    {
        "name_ar": "بياتي",
        "name_en": "Bayati",
        "tonic": "D4",
        "scale_pattern": [0.75, 0.75, 1.0],
        "degree_names": ["دوكاه (D)", "سيكاه (E½♭)", "جهاركاه (F)", "نوى (G)"],
        "description": "الجنس الأساسي لمقام البيات، أكثر الأجناس العربية شيوعًا في بلاد الشام.",
        "notes": "maqamworld.com. " + SOURCES_NOTE,
    },
    {
        "name_ar": "راست",
        "name_en": "Rast",
        "tonic": "C4",
        "scale_pattern": [1.0, 0.75, 0.75],
        "degree_names": ["راست (C)", "دوكاه (D)", "سيكاه (E½♭)", "جهاركاه (F)"],
        "description": "الجنس الأساسي لمقام الراست، ويُعتبر غالبًا الجنس المرجعي الأساسي في المنظومة العربية.",
        "notes": "maqamworld.com. " + SOURCES_NOTE,
    },
    {
        "name_ar": "راست العلوي",
        "name_en": "Upper Rast",
        "tonic": "G4",
        "scale_pattern": [1.0, 0.75, 0.75],
        "degree_names": ["نوى (G)", "حسيني (A)", "أوج (B½♭)", "كردان (C)"],
        "description": "نفس نمط جنس الراست، لكن منقول إلى الدرجة الخامسة من مقام الراست.",
        "notes": (
            "maqamworld.com maqam/rast.php: 'Jins Upper Rast (with its tonic "
            "up on the 8th degree)'. Interval pattern confirmed identical to "
            "the root Jins Rast by cross-checking thewholehorn's degree 5-8 "
            "cents against degree 1-4. " + SOURCES_NOTE
        ),
    },
    {
        "name_ar": "نهاوند",
        "name_en": "Nahawand",
        "tonic": "C4",
        "scale_pattern": [1.0, 0.5, 1.0],
        "degree_names": ["راست (C)", "دوكاه (D)", "كردي (E♭)", "جهاركاه (F)"],
        "description": (
            "الجنس الأساسي لمقام النهاوند، نمطه الصوتي أقرب للسلم الغربي الصغير "
            "(لا يحتوي درجات ربع صوتية حقيقية)."
        ),
        "notes": "maqamworld.com. " + SOURCES_NOTE,
    },
    {
        "name_ar": "كرد",
        "name_en": "Kurd",
        "tonic": "D4",
        "scale_pattern": [0.5, 1.0],
        "degree_names": ["دوكاه (D)", "كردي (E♭)", "جهاركاه (F)"],
        "description": "جنس ثلاثي، نمطه نصف - كامل، أقرب لما يُعرف غربيًا بالسلم الفريجي.",
        "notes": "maqamworld.com (interval pattern cross-derived from Maqam Kurd's documented scale, same method as Jins 'Ajam (3-note)). " + SOURCES_NOTE,
    },
    {
        "name_ar": "عجم",
        "name_en": "Ajam",
        "tonic": "C4",
        "scale_pattern": [1.0, 1.0, 0.5, 1.0],
        "degree_names": ["راست (C)", "دوكاه (D)", "(E طبيعية)", "جهاركاه (F)", "نوى (G)"],
        "description": (
            "النسخة الخماسية (الأكثر شيوعًا) من جنس العجم -- الجنس الأساسي لمقام "
            "العجم. لا يحتوي درجات ربع صوتية حقيقية (أقرب للسلم الكبير الغربي)."
        ),
        "notes": (
            "maqamworld.com jins/ajam.php: '5-note version ... the most "
            "common version', tonic on C, ghammaz G. Distinct DB row from the "
            "3-note 'Ajam (secondary jins elsewhere). " + SOURCES_NOTE
        ),
    },
    {
        "name_ar": "عجم العلوي",
        "name_en": "Upper Ajam",
        "tonic": "F4",
        "scale_pattern": [1.0, 1.0, 0.5],
        "degree_names": ["جهاركاه (F)", "نوى (G)", "حسيني (A)", "عجم عشيران (B♭، الثامنة)"],
        "description": (
            "امتداد جنس العجم إلى الدرجة الخامسة من مقام العجم (أربع درجات: "
            "جهاركاه-نوى-حسيني-عجم عشيران الثامنة)."
        ),
        "notes": (
            "maqamworld.com maqam/ajam.php: 'Jins Upper 'Ajam on the 5th "
            "degree (with its tonic up on the 8th degree)' -- read as the "
            "4-note tetrachord portion of Jins 'Ajam (matching the identical "
            "phrasing and span used for Jins Upper Rast, which is confirmed "
            "4-note), not the full 5-note version; the 5th note would fall "
            "outside the directly-confirmed one-octave cents range and is "
            "left unclaimed rather than inferred. " + SOURCES_NOTE
        ),
    },
]

MAQAM_DEFS = [
    {
        "name_ar": "صبا",
        "name_en": "Saba",
        "tonic": "D4",
        "ghammaz": "الدرجة 3 أو 6 (غير محدد قطعيًا، راجع notes)",
        "accidentals": "سيكاه (مي نصف بيمول) على الدرجة الثانية؛ درجة ربع-صوتية تقريبية على الدرجة الرابعة (جنس الحجاز)",
        "scale_pattern": [0.75, 0.75, 0.5, 1.5, 0.5, 1.0, 1.0],
        "degree_names": [
            "دوكاه (D)", "سيكاه (E½♭)", "جهاركاه (F)", "(G♭)",
            "حسيني (A)", "عجم/نكريز (B♭)", "كردان (C)", "دوكاه (D، الثامنة)",
        ],
        "mood": "حزين، شجي، متعلق بالشوق والحنين (اسم المقام نفسه يعني الشوق)",
        "description": (
            "مقام الصبا يبدأ بجنس الصبا على درجة القرار (ري)، يتداخل معه جنس "
            "الحجاز على الدرجة الثالثة، ثم إما جنس العجم أو جنس النكريز على "
            "الدرجة السادسة. لا يوجد له مكافئ غربي دقيق بسبب درجاته ربع "
            "الصوتية، وهو من أكثر المقامات ارتباطًا بالحزن والشجن في الموسيقى "
            "العربية."
        ),
        "notes": (
            "Ghammaz deliberately left as a documented ambiguity (both "
            "candidate degrees recorded) rather than forced to one value -- "
            "maqamworld.com's Jins Saba page and Wikipedia's Saba article "
            "agree on this ambiguity. Branch jins at the 6th degree is "
            "documented as EITHER 'Ajam (3-note) or Nikriz; 'Ajam is recorded "
            "as the primary branch_jins_id because its interval pattern could "
            "be verified (see Jins 'Ajam (3-note) notes), while Nikriz is "
            "preserved as the documented alternative via the MaqamJins "
            "breakdown table, with scale_pattern left null/unverified. "
            + SOURCES_NOTE
        ),
        "ajnas_breakdown": [
            {"jins_name_ar": "صبا", "start_degree": 1, "is_primary_alternative": True, "notes": "الجنس الأساسي على درجة القرار."},
            {"jins_name_ar": "حجاز", "start_degree": 3, "is_primary_alternative": True, "notes": "يتداخل على الدرجة الثالثة."},
            {"jins_name_ar": "عجم (ثلاثي)", "start_degree": 6, "is_primary_alternative": True, "notes": "أحد خيارين موثقين على الدرجة السادسة؛ مُسجَّل كخيار أساسي لتوفر بيانات موثقة لأبعاده."},
            {"jins_name_ar": "نكريز", "start_degree": 6, "is_primary_alternative": False, "notes": "البديل الموثق الآخر على الدرجة السادسة (maqamworld.com)؛ أبعاده غير متوفرة حاليًا."},
        ],
    },
    {
        "name_ar": "بياتي",
        "name_en": "Bayati",
        "tonic": "D4",
        "ghammaz": "الدرجة 4 (نوى)",
        "accidentals": "سيكاه (مي نصف بيمول) على الدرجة الثانية -- ربع صوتية حقيقية",
        "scale_pattern": [0.75, 0.75, 1.0, 1.0, 0.5, 1.0, 1.0],
        "degree_names": [
            "دوكاه (D)", "سيكاه (E½♭)", "جهاركاه (F)", "نوى (G)",
            "حسيني (A)", "عجم (B♭)", "كردان (C)", "دوكاه (D، الثامنة)",
        ],
        "mood": "دافئ وعاطفي؛ من أكثر المقامات شيوعًا في بلاد الشام",
        "description": (
            "مقام البيات يبدأ بجنس البيات على درجة القرار (ري)، ثم إما جنس "
            "النهاوند أو جنس الراست على الدرجة الرابعة. يحتوي درجة ربع صوتية "
            "حقيقية واحدة (سيكاه)."
        ),
        "notes": (
            "Branch at the 4th degree documented as EITHER Jins Nahawand or "
            "Jins Rast (maqamworld.com); Nahawand recorded as primary "
            "(interval pattern verified), Rast preserved as the documented "
            "alternative. " + SOURCES_NOTE
        ),
        "ajnas_breakdown": [
            {"jins_name_ar": "بياتي", "start_degree": 1, "is_primary_alternative": True, "notes": "الجنس الأساسي."},
            {"jins_name_ar": "نهاوند", "start_degree": 4, "is_primary_alternative": True, "notes": "أحد خيارين موثقين على الدرجة الرابعة."},
            {"jins_name_ar": "راست", "start_degree": 4, "is_primary_alternative": False, "notes": "البديل الموثق الآخر على الدرجة الرابعة (maqamworld.com)."},
        ],
    },
    {
        "name_ar": "راست",
        "name_en": "Rast",
        "tonic": "C4",
        "ghammaz": "الدرجة 5 (نوى)",
        "accidentals": "سيكاه (مي نصف بيمول) على الثالثة وأوج (سي نصف بيمول) على السابعة -- ربعا صوتية حقيقيان",
        "scale_pattern": [1.0, 0.75, 0.75, 1.0, 1.0, 0.75, 0.75],
        "degree_names": [
            "راست (C)", "دوكاه (D)", "سيكاه (E½♭)", "جهاركاه (F)",
            "نوى (G)", "حسيني (A)", "أوج (B½♭)", "راست (C، الثامنة)",
        ],
        "mood": "متزن وأصيل؛ يوصف غالبًا بأنه 'المقام الأم'",
        "description": (
            "مقام الراست يبدأ بجنس الراست على درجة القرار (دو)، ثم إما جنس "
            "الراست العلوي (نفس النمط منقولًا للدرجة الثامنة) أو جنس النهاوند "
            "على الدرجة الخامسة. يحتوي درجتي ربع صوتية حقيقيتين."
        ),
        "notes": (
            "Branch at the 5th degree documented as EITHER Jins Upper Rast or "
            "Jins Nahawand (maqamworld.com); Upper Rast recorded as primary. "
            + SOURCES_NOTE
        ),
        "ajnas_breakdown": [
            {"jins_name_ar": "راست", "start_degree": 1, "is_primary_alternative": True, "notes": "الجنس الأساسي."},
            {"jins_name_ar": "راست العلوي", "start_degree": 5, "is_primary_alternative": True, "notes": "أحد خيارين موثقين على الدرجة الخامسة؛ نفس نمط جنس الراست منقولًا."},
            {"jins_name_ar": "نهاوند", "start_degree": 5, "is_primary_alternative": False, "notes": "البديل الموثق الآخر على الدرجة الخامسة (maqamworld.com)."},
        ],
    },
    {
        "name_ar": "حجاز",
        "name_en": "Hijaz",
        "tonic": "D4",
        "ghammaz": "الدرجة 4 (نوى)",
        "accidentals": "لا توجد درجات ربع صوتية حقيقية؛ يعتمد على الثانية الزائدة بين الدرجتين 2 و3",
        "scale_pattern": [0.5, 1.5, 0.5, 1.0, 0.5, 1.0, 1.0],
        "degree_names": [
            "دوكاه (D)", "كردي (E♭)", "حجاز (F♯/G♭)", "نوى (G)",
            "حسيني (A)", "عجم (B♭)", "كردان (C)", "دوكاه (D، الثامنة)",
        ],
        "mood": "شرقي عاطفي قوي؛ يقارب ما يُعرف غربيًا بالسلم الفريجي المسيطر (Phrygian dominant)",
        "description": (
            "مقام الحجاز يبدأ بجنس الحجاز على درجة القرار، ثم إما جنس النهاوند "
            "أو جنس الراست على الدرجة الرابعة."
        ),
        "notes": (
            "Branch at the 4th degree documented as EITHER Jins Nahawand or "
            "Jins Rast (maqamworld.com); Nahawand recorded as primary. "
            "Performance note: the interval between the jins's own 2nd and "
            "3rd degrees is usually played smaller than notated (not baked "
            "into scale_pattern). " + SOURCES_NOTE
        ),
        "ajnas_breakdown": [
            {"jins_name_ar": "حجاز", "start_degree": 1, "is_primary_alternative": True, "notes": "الجنس الأساسي."},
            {"jins_name_ar": "نهاوند", "start_degree": 4, "is_primary_alternative": True, "notes": "أحد خيارين موثقين على الدرجة الرابعة."},
            {"jins_name_ar": "راست", "start_degree": 4, "is_primary_alternative": False, "notes": "البديل الموثق الآخر على الدرجة الرابعة (maqamworld.com)."},
        ],
    },
    {
        "name_ar": "نهاوند",
        "name_en": "Nahawand",
        "tonic": "C4",
        "ghammaz": "الدرجة 5 (نوى)",
        "accidentals": "لا توجد درجات ربع صوتية حقيقية (مجموعة درجات أقرب للسلم الصغير التوافقي الغربي)",
        "scale_pattern": [1.0, 0.5, 1.0, 1.0, 0.5, 1.5, 0.5],
        "degree_names": [
            "راست (C)", "دوكاه (D)", "كردي (E♭)", "جهاركاه (F)",
            "نوى (G)", "حصار (A♭)", "نيم ماهور (B)", "راست (C، الثامنة)",
        ],
        "mood": "عاطفي وحزين نوعًا ما؛ أقرب للسلم الغربي الصغير التوافقي",
        "description": (
            "مقام النهاوند يبدأ بجنس النهاوند على درجة القرار، ثم إما جنس "
            "الحجاز أو جنس الكرد على الدرجة الخامسة."
        ),
        "notes": (
            "Branch at the 5th degree documented as EITHER Jins Hijaz or "
            "Jins Kurd (maqamworld.com); Hijaz recorded as primary. "
            "Descending-form differences mentioned by a secondary source but "
            "not found in extractable text -- not recorded, to avoid "
            "guessing. " + SOURCES_NOTE
        ),
        "ajnas_breakdown": [
            {"jins_name_ar": "نهاوند", "start_degree": 1, "is_primary_alternative": True, "notes": "الجنس الأساسي."},
            {"jins_name_ar": "حجاز", "start_degree": 5, "is_primary_alternative": True, "notes": "أحد خيارين موثقين على الدرجة الخامسة."},
            {"jins_name_ar": "كرد", "start_degree": 5, "is_primary_alternative": False, "notes": "البديل الموثق الآخر على الدرجة الخامسة (maqamworld.com)."},
        ],
    },
    {
        "name_ar": "كرد",
        "name_en": "Kurd",
        "tonic": "D4",
        "ghammaz": "الدرجة 4 (نوى)",
        "accidentals": "لا توجد درجات ربع صوتية حقيقية (أقرب للسلم الفريجي الغربي)",
        "scale_pattern": [0.5, 1.0, 1.0, 1.0, 0.5, 1.0, 1.0],
        "degree_names": [
            "دوكاه (D)", "كردي (E♭)", "جهاركاه (F)", "نوى (G)",
            "حسيني (A)", "عجم (B♭)", "كردان (C)", "دوكاه (D، الثامنة)",
        ],
        "mood": "طابع شرقي معتدل؛ يقارب المقام الفريجي الغربي",
        "description": "مقام الكرد يبدأ بجنس الكرد على درجة القرار، ثم جنس النهاوند على الدرجة الرابعة (بديل واحد موثّق فقط).",
        "notes": "maqamworld.com -- no 'or' alternative documented for the branch here, unlike most of the others. " + SOURCES_NOTE,
        "ajnas_breakdown": [
            {"jins_name_ar": "كرد", "start_degree": 1, "is_primary_alternative": True, "notes": "الجنس الأساسي."},
            {"jins_name_ar": "نهاوند", "start_degree": 4, "is_primary_alternative": True, "notes": "الخيار الوحيد الموثّق على الدرجة الرابعة."},
        ],
    },
    {
        "name_ar": "عجم",
        "name_en": "Ajam",
        "tonic": "Bb4",
        "ghammaz": "الدرجة 5 (جهاركاه)",
        "accidentals": "لا توجد درجات ربع صوتية حقيقية (أقرب للسلم الكبير الغربي/Ionian)",
        "scale_pattern": [1.0, 1.0, 0.5, 1.0, 1.0, 1.0, 0.5],
        "degree_names": [
            "عجم عشيران (B♭)", "راست (C)", "دوكاه (D)", "كردي (E♭)",
            "جهاركاه (F)", "نوى (G)", "حسيني (A)", "عجم عشيران (B♭، الثامنة)",
        ],
        "mood": "مبهج ومنتصر؛ أقرب نقطة دخول للسلم الغربي الكبير",
        "description": (
            "هذا التسجيل هو 'مقام العجم المصري' (tonic سي بيمول) بحسب "
            "maqamworld.com. يبدأ بجنس العجم الخماسي على درجة القرار، ثم إما "
            "جنس العجم العلوي (نفس النمط منقولًا) أو جنس النهاوند على الدرجة "
            "الخامسة."
        ),
        "notes": (
            "Branch at the 5th degree documented as EITHER Jins Upper 'Ajam "
            "or Jins Nahawand (maqamworld.com); Upper 'Ajam recorded as "
            "primary. " + SOURCES_NOTE
        ),
        "ajnas_breakdown": [
            {"jins_name_ar": "عجم", "start_degree": 1, "is_primary_alternative": True, "notes": "الجنس الأساسي (النسخة الخماسية)."},
            {"jins_name_ar": "عجم العلوي", "start_degree": 5, "is_primary_alternative": True, "notes": "أحد خيارين موثقين على الدرجة الخامسة؛ نفس نمط جنس العجم منقولًا."},
            {"jins_name_ar": "نهاوند", "start_degree": 5, "is_primary_alternative": False, "notes": "البديل الموثق الآخر على الدرجة الخامسة (maqamworld.com)."},
        ],
    },
]


def get_or_create_jins(db, jins_def: dict) -> Jins:
    jins = db.query(Jins).filter(Jins.name_ar == jins_def["name_ar"]).first()
    if jins is None:
        jins = Jins(name_ar=jins_def["name_ar"])
        db.add(jins)

    jins.name_en = jins_def["name_en"]
    jins.tonic = jins_def["tonic"]
    jins.scale_pattern = jins_def["scale_pattern"]
    jins.degree_names = jins_def.get("degree_names")
    jins.description = jins_def["description"]
    jins.notes = jins_def["notes"]

    db.flush()
    return jins


def seed() -> None:
    db = SessionLocal()

    jins_by_name = {}
    for jins_def in JINS_DEFS:
        jins = get_or_create_jins(db, jins_def)
        jins_by_name[jins_def["name_ar"]] = jins

    for maqam_def in MAQAM_DEFS:
        maqam = db.query(Maqam).filter(Maqam.name_ar == maqam_def["name_ar"]).first()
        if maqam is None:
            raise RuntimeError(
                f"Maqam '{maqam_def['name_ar']}' not found -- this script only "
                "updates existing seeded maqamat, it does not create new ones."
            )

        maqam.tonic = maqam_def["tonic"]
        maqam.ghammaz = maqam_def["ghammaz"]
        maqam.accidentals = maqam_def["accidentals"]
        maqam.scale_pattern = maqam_def["scale_pattern"]
        maqam.degree_names = maqam_def.get("degree_names")
        maqam.mood = maqam_def["mood"]
        maqam.description = maqam_def["description"]
        maqam.notes = maqam_def["notes"]
        maqam.notation_format = "scale_pattern_v1"

        breakdown = maqam_def["ajnas_breakdown"]
        maqam.root_jins_id = jins_by_name[breakdown[0]["jins_name_ar"]].id
        primary_branches = [b for b in breakdown[1:] if b["is_primary_alternative"]]
        if primary_branches:
            # The legacy root/branch pair is meant to show the two
            # "endpoint" ajnas (tonic jins + furthest upper-register jins),
            # not an intermediate overlap -- pick the highest-degree one.
            furthest_branch = max(primary_branches, key=lambda b: b["start_degree"])
            maqam.branch_jins_id = jins_by_name[furthest_branch["jins_name_ar"]].id

        db.query(MaqamJins).filter(MaqamJins.maqam_id == maqam.id).delete()
        for entry in breakdown:
            db.add(MaqamJins(
                maqam_id=maqam.id,
                jins_id=jins_by_name[entry["jins_name_ar"]].id,
                start_degree=entry["start_degree"],
                is_primary_alternative=entry["is_primary_alternative"],
                notes=entry["notes"],
            ))

        print(f"Updated maqam: {maqam.name_ar} ({maqam.name_en})")

    db.commit()
    db.close()


if __name__ == "__main__":
    seed()
