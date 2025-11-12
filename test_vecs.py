import sqlite3
import tempfile
import pytest
from pathlib import Path
from ankivec import VectorEmbeddingManager

@pytest.fixture
def synth_db():
    with tempfile.NamedTemporaryFile(suffix=".db") as f:
        conn = sqlite3.connect(f.name)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE notes (
                id INTEGER PRIMARY KEY,
                flds TEXT,
                mod INTEGER
            )
        """)
        cursor.execute("INSERT INTO notes (id, flds, mod) VALUES (1, 'cat gato', 1234567890)")
        cursor.execute("INSERT INTO notes (id, flds, mod) VALUES (2, 'fig leaf', 1234567890)")
        conn.commit()
        conn.close()
        yield f.name

@pytest.fixture
def notes_and_manager():
    # Fetch first 20 notes
    conn = sqlite3.connect(
        "/Users/sam/Library/Application Support/Anki2/User 1/collection.anki2"
    ).cursor()
    notes = conn.execute("SELECT id, flds, mod FROM notes order by mod desc LIMIT 20").fetchall()
    conn.close()

    # Create subset database
    with tempfile.NamedTemporaryFile(suffix=".db") as f:
        subset_conn = sqlite3.connect(f.name)
        subset_cursor = subset_conn.cursor()

        # Create notes table
        subset_cursor.execute("""
            CREATE TABLE notes (
                id INTEGER PRIMARY KEY,
                flds TEXT,
                mod INTEGER
            )
        """)

        # Insert notes
        subset_cursor.executemany("INSERT INTO notes (id, flds, mod) VALUES (?, ?, ?)", notes)
        subset_conn.commit()
        subset_conn.close()

        yield (notes, VectorEmbeddingManager("snowflake-arctic-embed", f.name))

def test_search_first_note_syth(synth_db):
    manager = VectorEmbeddingManager("snowflake-arctic-embed", synth_db)
    results = manager.search("cat", n_results=1)
    assert len(results) == 1
    assert results[0] == 1

def test_closest_card_self(notes_and_manager):
    notes, manager = notes_and_manager
    for (nid, flds, _) in notes:
        assert nid == manager.search(flds, 1)[0]
