import sys
import os
from pathlib import Path
from typing import List, Tuple
from typing_extensions import Iterator
from aqt import mw, gui_hooks
from aqt.qt import *
from aqt.utils import showInfo, tooltip
import itertools

# Hack to make anki use the virtual environment
ADDON_ROOT_DIR = Path(__file__).parent
sys.path.append(os.path.join(ADDON_ROOT_DIR, ".venv/lib/python3.13/site-packages/"))

import chromadb
from chromadb.config import Settings
import ollama

class VectorEmbeddingManager:
    def __init__(self, collection_path: str, model_name: str):
        self.model_name = model_name
        self.client = chromadb.PersistentClient(
            path=collection_path,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name="anki_cards",
            metadata={"hnsw:space": "cosine"}
        )
        self._sync_if_needed()

    def _sync_if_needed(self):
        anki_mod = mw.col.mod
        anki_card_count = mw.col.card_count()

        metadata = self.collection.metadata or {}
        stored_mod = metadata.get("anki_mod")
        stored_count = metadata.get("anki_card_count")

        if stored_mod == anki_mod and stored_count == anki_card_count:
            return

        total = col.db.scalar("select count() from notes")
        progress = QProgressDialog("Syncing cards to vector database...", "Cancel", 0, total, mw)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setWindowTitle("AnkiVec Sync")
        progress.setValue(0)

        self.add_cards(mw.col.db.execute("select id, flds from notes"), progress)
        progress.close()

        self.collection.modify(metadata={
            **metadata,
            "anki_mod": anki_mod,
            "anki_card_count": anki_card_count
        })

    def add_cards(self, notes, progress=None):
        processed = 0
        for batch in itertools.batched(notes, 64):
            card_ids, card_text = zip(*batch)
            embeddings = ollama.embed(model=self.model_name, text=card_text)["embeddings"]
            self.collection.upsert(
                ids=card_ids,
                embeddings=embeddings)

            if progress:
                processed += len(batch)
                progress.setValue(processed)
                if progress.wasCanceled():
                    break

    def search(self, query: str, n_results: int = 20) -> List[Tuple[int, float, str, str]]:
        return self.collection.query(
            query_embeddings= ollama.embed(model=self.model_name, text=query)["embeddings"],
            n_results=n_results)["ids"][0]

def init_hook():
    global manager, config

    config = mw.addonManager.getConfig("ankivec")

    db_path = os.path.join(os.path.dirname(mw.col.path), "ankivec_db")
    manager = VectorEmbeddingManager(db_path, config["model_name"])


gui_hooks.main_window_did_init.append(init_hook)

def handle_deleted(_, note_ids):
    pass

hooks.notes_will_be_deleted.append(handle_deleted)
