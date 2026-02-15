import sys
import os
from pathlib import Path

# Add vendor directory to path for runtime dependencies
# Dependencies are vendored using: pip install -r requirements-runtime.txt -t vendor
_addon_root = Path(__file__).parent
_vendor_dir = _addon_root / "vendor"
if str(_vendor_dir) not in sys.path:
    sys.path.insert(0, str(_vendor_dir))

try:
    from aqt import mw, gui_hooks
    from aqt.qt import *
    from aqt.utils import tooltip, showWarning
    from anki import hooks
    IN_ANKI = True
except ImportError:
    IN_ANKI = False

import chromadb
import ollama
import itertools
import requests

class VectorEmbeddingManager:
    def __init__(self, model_name: str, collection_path: str, db):
        self.model_name = model_name
        self.db = db
        self.embed_text("") # check if ollama is running
        self.client = chromadb.PersistentClient(path=collection_path)
        self.collection = self.client.get_or_create_collection(
            name="ankivec",
            metadata={"model_name": model_name}
        )
        self._sync()

    def embed_text(self, text):
        try:
            return ollama.embed(model=self.model_name, input=text)['embeddings']
        except (requests.exceptions.ConnectionError, requests.exceptions.RequestException):
            error_msg = "Ollama is not running or not installed. Please install Ollama from https://ollama.ai and ensure it's running."
            if IN_ANKI:
                showWarning(error_msg)
            raise RuntimeError(error_msg)
        except Exception as e:
            if "model" in str(e).lower() and "not found" in str(e).lower():
                error_msg = f"Model '{self.model_name}' not found. Please run: ollama pull {self.model_name}"
                if IN_ANKI:
                    from aqt.utils import showWarning
                    showWarning(error_msg)
                raise RuntimeError(error_msg)
            raise

    def _sync(self):
        stored_model_name = self.collection.metadata.get("model_name")
        stored_mod = int(self.collection.metadata.get("mod", 0))

        if self.model_name != stored_model_name:
            if IN_ANKI:
                tooltip("Model changed. Reindexing all cards...", parent=mw)
            self.client.delete_collection("ankivec")
            self.collection = self.client.create_collection(
                name="ankivec",
                metadata={"model_name": self.model_name}
            )
            stored_mod = 0

        # Check if notes table has been modified since last sync
        total, notes_mod = self.db.first("SELECT COUNT(), max(mod) FROM notes where mod > ?", stored_mod)
        if total == 0: return

        total = self.db.scalar("SELECT count() FROM notes where mod > ?", stored_mod)
        notes_to_add = self.db.execute("SELECT id, flds FROM notes where mod > ?", stored_mod)

        if IN_ANKI:
            progress = QProgressDialog("Syncing cards to vector database...", "Cancel", 0, total, mw)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setWindowTitle("AnkiVec Sync")
            progress.setValue(0)
        else:
            progress = None
            sys.stdout.write(f"Syncing {total} Cards: ")
            sys.stdout.flush()
        self.add_cards(notes_to_add, progress)

        # Store the latest modification time
        self.collection.modify(metadata={"model_name": self.model_name, "mod": str(notes_mod or 0)})

    def add_cards(self, notes, progress):
        processed = 0
        for batch in itertools.batched(notes, 128):
            note_ids, card_text = zip(*batch)
            joined_text = ["search_document: " + " ".join(c.split(chr(0x1f))) for c in card_text]
            try:
                embeddings = self.embed_text(joined_text)
                self.collection.upsert(
                    ids=[str(i) for i in note_ids],
                    embeddings=embeddings)
            except:
                print(f"Failed to add : {card_text}")
            processed += len(batch)
            if progress:
                progress.setValue(processed)
                if progress.wasCanceled():
                    break
            else:
                sys.stdout.write(".")
                sys.stdout.flush()
        if progress:
            progress.cancel()
        else:
            print("")

    def search(self, query: str, n_results: int = 20) -> list[int]:
        embeddings = self.embed_text('search_query: ' + query)
        results = self.collection.query(
            query_embeddings=embeddings,
            n_results=n_results)
        return [int(id) for id in results["ids"][0]]

    def delete_notes(self, note_ids: list[int]) -> None:
        self.collection.delete(ids=[str(i) for i in note_ids])

if IN_ANKI:
    _original_table_search = None
    _ADDON_ID = "1516019916"
    _LEGACY_CONFIG_KEY = "ankivec"
    _DEFAULT_CONFIG = {
        "model_name": "nomic-embed-text",
        "search_results_limit": 20,
        "ollama_host": "http://localhost:11434",
    }

    def _get_addon_config(addon_id: str):
        manager = mw.addonManager
        if hasattr(manager, "getConfig"):
            return manager.getConfig(addon_id)
        if hasattr(manager, "get_config"):
            return manager.get_config(addon_id)
        return None

    def _set_addon_config(addon_id: str, config_data: dict) -> None:
        manager = mw.addonManager
        if hasattr(manager, "setConfig"):
            manager.setConfig(addon_id, config_data)
            return
        if hasattr(manager, "writeConfig"):
            manager.writeConfig(addon_id, config_data)
            return
        if hasattr(manager, "set_config"):
            manager.set_config(addon_id, config_data)
            return
        if IN_ANKI:
            showWarning("Could not persist AnkiVec config: no config setter found in AddonManager.")

    def wrap_vec_search(txt, n):
        if not isinstance(txt, str):
            return txt
        parts = txt.split("vec:", 1)
        regular_query = parts[0].strip()
        if len(parts) > 1:
            vec_query = parts[1].strip()
            note_ids = manager.search(vec_query, n_results=n)
            return f"{regular_query} (" + " OR ".join(f"nid:{nid}" for nid in note_ids) + ")"
        return regular_query

    def patched_table_search(self, txt: str) -> None:
        global manager
        transformed_txt = wrap_vec_search(txt, config.get("search_results_limit", _DEFAULT_CONFIG["search_results_limit"]))
        return _original_table_search(self, transformed_txt)

    def init_hook():
        global manager, config, _original_table_search
        config = _get_addon_config(_ADDON_ID)
        legacy_config = None
        if config is None:
            legacy_config = _get_addon_config(_LEGACY_CONFIG_KEY)
        if config is None:
            config = legacy_config
        if config is None:
            config = dict(_DEFAULT_CONFIG)
        else:
            merged = dict(_DEFAULT_CONFIG)
            merged.update(config)
            config = merged
        _set_addon_config(_ADDON_ID, config)
        collection_path = str(Path(mw.col.path).parent / "ankivec_chromadb")
        manager = VectorEmbeddingManager(config.get("model_name", _DEFAULT_CONFIG["model_name"]), collection_path, mw.col.db)

    def browser_did_init(browser):
        global _original_table_search
        from aqt.browser.table.table import Table
        if _original_table_search is None:
            _original_table_search = Table.search
            Table.search = patched_table_search

    gui_hooks.main_window_did_init.append(init_hook)
    gui_hooks.browser_will_show.append(browser_did_init)

    def handle_deleted(_, note_ids):
        manager.delete_notes(note_ids)

    def handle_saved(note):
        card_text = " ".join(note.fields)
        joined_text = "search_document: " + card_text
        try:
            embedding = ollama.embed(model=manager.model_name, input=joined_text)["embeddings"][0]
        except requests.exceptions.ConnectionError:
            error_msg = "Lost connection to Ollama. Please ensure Ollama is running."
            from aqt.utils import showWarning
            showWarning(error_msg)
            return
        except Exception as e:
            if "model" in str(e).lower() and "not found" in str(e).lower():
                error_msg = f"Model '{manager.model_name}' not found. Please run: ollama pull {manager.model_name}"
                from aqt.utils import showWarning
                showWarning(error_msg)
                return
            print("Failed to embed note:", e)
            return
        manager.collection.upsert(
            ids=[str(note.id)],
            embeddings=[embedding],
            metadatas=[{"note_id": note.id}]
        )

    hooks.notes_will_be_deleted.append(handle_deleted)
    hooks.note_will_be_added.append(lambda c, n, d: handle_saved(n))
    hooks.note_will_flush.append(handle_saved)
