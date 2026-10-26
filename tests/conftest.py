"""Test harness fixtures and mock SQLite hadith databases for Masar."""

import json
import sqlite3
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TEST_ARTIFACTS_DIR = REPO_ROOT / "test-artifacts"


@pytest.fixture(scope="session")
def test_artifacts_dir() -> Path:
    """Ensure test-artifacts directory exists and return its path."""
    TEST_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    return TEST_ARTIFACTS_DIR


# Sample Hadith Records for Multi-Sectarian & Edge Case Testing
MOCK_HADITH_RECORDS = [
    {
        "id": 1,
        "collection": "sahih_bukhari",
        "book_number": 1,
        "hadith_number": "1",
        "sect": "sunni",
        "full_text": "حدثنا الحميدي عبد الله بن الزبير قال حدثنا سفيان قال حدثنا يحيى بن سعيد الأنصاري قال أخبرني محمد بن إبراهيم التيمي أنه سمع علقمة بن وقاص الليثي يقول سمعت عمر بن الخطاب رضي الله عنه على المنبر قال سمعت رسول الله صلى الله عليه وسلم يقول إنما الأعمال بالنيات وإنما لكل امرئ ما نوى فمن كانت هجرته إلى دنيا يصيبها أو إلى امرأة ينكحها فهجرته إلى ما هاجر إليه",
        "matn_start": 235,
        "matn_end": 371,
        "isnad_raw": "حدثنا الحميدي عبد الله بن الزبير قال حدثنا سفيان قال حدثنا يحيى بن سعيد الأنصاري قال أخبرني محمد بن إبراهيم التيمي أنه سمع علقمة بن وقاص الليثي يقول سمعت عمر بن الخطاب رضي الله عنه على المنبر قال سمعت رسول الله صلى الله عليه وسلم يقول",
        "matn": "إنما الأعمال بالنيات وإنما لكل امرئ ما نوى فمن كانت هجرته إلى دنيا يصيبها أو إلى امرأة ينكحها فهجرته إلى ما هاجر إليه",
        "primary_narrators": json.dumps(["al_humaydi", "sufyan", "yahya_b_said", "muhammad_b_ibrahim", "alqama_b_waqqas", "umar_b_al_khattab"]),
    },
    {
        "id": 2,
        "collection": "sahih_muslim",
        "book_number": 33,
        "hadith_number": "1907",
        "sect": "sunni",
        "full_text": "وحدثنا عبد الله بن مسلمة بن قعنب حدثنا مالك عن يحيى بن سعيد عن محمد بن إبراهيم عن علقمة بن وقاص عن عمر بن الخطاب قال قال رسول الله صلى الله عليه وسلم إنما الأعمال بالنية وإنما لامرئ ما نوى فمن كانت هجرته إلى الله ورسوله فهجرته إلى الله ورسوله ومن كانت هجرته لدنيا يصيبها أو امرأة يتزوجها فهجرته إلى ما هاجر إليه",
        "matn_start": 150,
        "matn_end": 320,
        "isnad_raw": "وحدثنا عبد الله بن مسلمة بن قعنب حدثنا مالك عن يحيى بن سعيد عن محمد بن إبراهيم عن علقمة بن وقاص عن عمر بن الخطاب قال قال رسول الله صلى الله عليه وسلم",
        "matn": "إنما الأعمال بالنية وإنما لامرئ ما نوى فمن كانت هجرته إلى الله ورسوله فهجرته إلى الله ورسوله ومن كانت هجرته لدنيا يصيبها أو امرأة يتزوجها فهجرته إلى ما هاجر إليه",
        "primary_narrators": json.dumps(["ibn_qanab", "malik", "yahya_b_said", "muhammad_b_ibrahim", "alqama_b_waqqas", "umar_b_al_khattab"]),
    },
    {
        # Taqṭīʿ (fragmentation) record: only quotes the second half of the tradition
        "id": 3,
        "collection": "sahih_bukhari",
        "book_number": 2,
        "hadith_number": "54",
        "sect": "sunni",
        "full_text": "حدثنا مسدد قال حدثنا يحيى عن شعبة عن قتادة عن أنس قال فمن كانت هجرته إلى دنيا يصيبها أو امرأة ينكحها فهجرته إلى ما هاجر إليه",
        "matn_start": 54,
        "matn_end": 126,
        "isnad_raw": "حدثنا مسدد قال حدثنا يحيى عن شعبة عن قتادة عن أنس قال",
        "matn": "فمن كانت هجرته إلى دنيا يصيبها أو امرأة ينكحها فهجرته إلى ما هاجر إليه",
        "primary_narrators": json.dumps(["musaddad", "yahya_al_qattan", "shuba", "qatadah", "anas_b_malik"]),
    },
    {
        # Boundary Bleed defect (FM-01): matn_start is set too early (175 instead of 235), capturing isnad connector
        "id": 4,
        "collection": "sahih_bukhari",
        "book_number": 54,
        "hadith_number": "2529",
        "sect": "sunni",
        "full_text": "حدثنا يحيى بن قزعة حدثنا مالك عن يحيى بن سعيد عن محمد بن إبراهيم بن الحارث عن علقمة بن وقاص عن عمر رضي الله عنه قال قال رسول الله صلى الله عليه وسلم إنما الأعمال بالنية وإنما لامرئ ما نوى",
        "matn_start": 110,  # Defect: starts at "قال قال رسول الله صلى الله عليه وسلم إنما الأعمال بالنية..."
        "matn_end": 190,
        "isnad_raw": "حدثنا يحيى بن قزعة حدثنا مالك عن يحيى بن سعيد عن محمد بن إبراهيم بن الحارث عن علقمة بن وقاص عن عمر رضي الله عنه",
        "matn": "قال قال رسول الله صلى الله عليه وسلم إنما الأعمال بالنية وإنما لامرئ ما نوى",
        "primary_narrators": json.dumps(["yahya_b_qazaa", "malik", "yahya_b_said", "muhammad_b_ibrahim", "alqama_b_waqqas", "umar_b_al_khattab"]),
    },
    {
        # Shīʿī tradition: al-Kāfī cross-sectarian report
        "id": 5,
        "collection": "al_kafi",
        "book_number": 1,
        "hadith_number": "35",
        "sect": "shia",
        "full_text": "علي بن إبراهيم عن أبيه عن النوفلي عن السكوني عن أبي عبد الله عليه السلام قال قال رسول الله صلى الله عليه وآله إنما الأعمال بالنيات ولكل امرئ ما نوى فمن غزا ابتغاء ما عند الله فقد وقع أجره على الله",
        "matn_start": 109,
        "matn_end": 204,
        "isnad_raw": "علي بن إبراهيم عن أبيه عن النوفلي عن السكوني عن أبي عبد الله عليه السلام قال قال رسول الله صلى الله عليه وآله",
        "matn": "إنما الأعمال بالنيات ولكل امرئ ما نوى فمن غزا ابتغاء ما عند الله فقد وقع أجره على الله",
        "primary_narrators": json.dumps(["ali_b_ibrahim", "ibrahim_b_hashim", "al_nawfali", "al_sakuni", "jafar_al_sadiq", "prophet_muhammad"]),
    },
    {
        # Topical False Positive (FM-03): High semantic cosine regarding actions/intentions, but distinct tradition & isnad
        "id": 6,
        "collection": "musnad_ahmad",
        "book_number": 5,
        "hadith_number": "21840",
        "sect": "sunni",
        "full_text": "حدثنا أبو المغيرة قال حدثنا الأوزاعي قال حدثني يحيى بن أبي كثير عن أبي قلابة عن أبي أسماء الرحبي عن ثوبان قال قال رسول الله صلى الله عليه وسلم إنما الأعمال بخواتيمها وإنما الأعمال بالخواتيم",
        "matn_start": 139,
        "matn_end": 193,
        "isnad_raw": "حدثنا أبو المغيرة قال حدثنا الأوزاعي قال حدثني يحيى بن أبي كثير عن أبي قلابة عن أبي أسماء الرحبي عن ثوبان قال قال رسول الله صلى الله عليه وسلم",
        "matn": "إنما الأعمال بخواتيمها وإنما الأعمال بالخواتيم",
        "primary_narrators": json.dumps(["abu_al_mughirah", "al_awzai", "yahya_b_abi_kathir", "abu_qilaba", "abu_asma", "thawban"]),
    },
]


def populate_hadith_db(conn: sqlite3.Connection):
    """Create schema and populate with mock hadiths."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hadiths (
            id INTEGER PRIMARY KEY,
            collection TEXT NOT NULL,
            book_number INTEGER,
            hadith_number TEXT,
            sect TEXT NOT NULL,
            full_text TEXT NOT NULL,
            matn_start INTEGER NOT NULL,
            matn_end INTEGER NOT NULL,
            isnad_raw TEXT,
            matn TEXT NOT NULL,
            normalized_matn TEXT,
            primary_narrators TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS narrators (
            id TEXT PRIMARY KEY,
            canonical_name TEXT NOT NULL,
            death_ah INTEGER,
            sect TEXT
        )
    """)

    for record in MOCK_HADITH_RECORDS:
        cursor.execute(
            """
            INSERT INTO hadiths (
                id, collection, book_number, hadith_number, sect,
                full_text, matn_start, matn_end, isnad_raw, matn,
                normalized_matn, primary_narrators
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["id"],
                record["collection"],
                record["book_number"],
                record["hadith_number"],
                record["sect"],
                record["full_text"],
                record["matn_start"],
                record["matn_end"],
                record["isnad_raw"],
                record["matn"],
                record.get("normalized_matn", record["matn"]),
                record["primary_narrators"],
            ),
        )

    narrators_data = [
        ("al_humaydi", "عبد الله بن الزبير الحميدي", 219, "sunni"),
        ("sufyan", "سفيان بن عيينة", 198, "sunni"),
        ("yahya_b_said", "يحيى بن سعيد الأنصاري", 143, "sunni"),
        ("muhammad_b_ibrahim", "محمد بن إبراهيم التيمي", 120, "sunni"),
        ("alqama_b_waqqas", "علقمة بن وقاص الليثي", None, "sunni"),
        ("umar_b_al_khattab", "عمر بن الخطاب", 23, "sunni"),
        ("malik", "مالك بن أنس", 179, "sunni"),
        ("ali_b_ibrahim", "علي بن إبراهيم القمي", 307, "shia"),
        ("ibrahim_b_hashim", "إبراهيم بن هاشم القمي", None, "shia"),
        ("al_sakuni", "إسماعيل بن مسلم السكوني", None, "shia"),
        ("jafar_al_sadiq", "جعفر بن محمد الصادق", 148, "shia"),
    ]

    for nid, cname, death, sect in narrators_data:
        cursor.execute(
            "INSERT INTO narrators (id, canonical_name, death_ah, sect) VALUES (?, ?, ?, ?)",
            (nid, cname, death, sect),
        )

    conn.commit()


@pytest.fixture
def mock_db_path(tmp_path: Path) -> Path:
    """Fixture providing path to a temporary SQLite database populated with mock hadiths."""
    db_file = tmp_path / "mock_riwayat.db"
    conn = sqlite3.connect(db_file)
    populate_hadith_db(conn)
    conn.close()
    return db_file
