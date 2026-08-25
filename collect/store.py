import os
import time
import sqlite3
import hashlib
import logging
from typing import Optional
from dataclasses import dataclass
from bot.media import MediaRef, PHOTO


COLLECT_DATA_DIR = 'data/collect'
COLLECT_DB_FILE = f'{COLLECT_DATA_DIR}/collect.db'
COLLECT_BLOB_DIR = f'{COLLECT_DATA_DIR}/blobs'

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    collection  TEXT    NOT NULL,
    kind        TEXT    NOT NULL DEFAULT 'photo',
    media_id    INTEGER,
    access_hash INTEGER,
    file_ref    BLOB,
    src_chat_id INTEGER,
    src_msg_id  INTEGER,
    blob_name   TEXT,
    url         TEXT,
    sha256      TEXT,
    added_by    INTEGER,
    added_at    INTEGER NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS items_media
    ON items (collection, media_id) WHERE media_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS items_sha
    ON items (collection, sha256) WHERE sha256 IS NOT NULL;
CREATE INDEX IF NOT EXISTS items_collection ON items (collection);
"""


@dataclass
class Item:
    id: int
    collection: str
    kind: str
    media_id: Optional[int]
    access_hash: Optional[int]
    file_ref: Optional[bytes]
    src_chat_id: Optional[int]
    src_msg_id: Optional[int]
    blob_name: Optional[str]
    url: Optional[str]
    sha256: Optional[str]
    added_by: Optional[int]
    added_at: int

    @property
    def ref(self) -> Optional[MediaRef]:
        if self.media_id is None or self.access_hash is None:
            return None
        return MediaRef(self.kind or PHOTO, self.media_id, self.access_hash, self.file_ref or b'')

    @property
    def blob_path(self) -> Optional[str]:
        return f'{COLLECT_BLOB_DIR}/{self.blob_name}' if self.blob_name else None


def digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


class CollectStore:
    """
    The pictures, on disk.

    Rows are small and the queries are single-row, so plain sqlite3 on
    the event loop costs less than the machinery to move it off.
    """
    def __init__(self, path: str = COLLECT_DB_FILE):
        self.path = path
        os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
        os.makedirs(COLLECT_BLOB_DIR, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        self.db.commit()

    # -- writing

    def add(
            self,
            collection: str,
            ref: MediaRef = None,
            src_chat_id: int = None,
            src_msg_id: int = None,
            blob: bytes = None,
            url: str = None,
            added_by: int = None,
    ) -> Optional[int]:
        """
        File one picture. Returns its id, or None if we already had it.

        Every way of naming the same picture is kept side by side: the
        media ref is the fast way back, the source message and the blob
        are what rebuild the ref once Telegram expires it.
        """
        sha = digest(blob) if blob else None
        blob_name = None
        if blob:
            blob_name = f'{sha}.bin'
            path = f'{COLLECT_BLOB_DIR}/{blob_name}'
            if not os.path.isfile(path):
                with open(path, 'wb') as f:
                    f.write(blob)

        try:
            cur = self.db.execute(
                'INSERT INTO items (collection, kind, media_id, access_hash, file_ref, '
                'src_chat_id, src_msg_id, blob_name, url, sha256, added_by, added_at) '
                'VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                (
                    collection,
                    ref.kind if ref else PHOTO,
                    ref.id if ref else None,
                    ref.access_hash if ref else None,
                    ref.file_reference if ref else None,
                    src_chat_id, src_msg_id, blob_name, url, sha,
                    added_by, int(time.time()),
                )
            )
        except sqlite3.IntegrityError:
            logging.info(f'[collect]\t{collection}: already had this picture')
            return None
        self.db.commit()
        return cur.lastrowid

    def update_ref(self, item_id: int, ref: MediaRef):
        """Remember a freshly obtained media reference for next time."""
        self.db.execute(
            'UPDATE items SET kind = ?, media_id = ?, access_hash = ?, file_ref = ? WHERE id = ?',
            (ref.kind, ref.id, ref.access_hash, ref.file_reference, item_id)
        )
        self.db.commit()

    def clear_ref(self, item_id: int):
        """Forget a media reference Telegram no longer honours."""
        self.db.execute(
            'UPDATE items SET media_id = NULL, access_hash = NULL, file_ref = NULL WHERE id = ?',
            (item_id,)
        )
        self.db.commit()

    def save_blob(self, item_id: int, content: bytes):
        sha = digest(content)
        blob_name = f'{sha}.bin'
        path = f'{COLLECT_BLOB_DIR}/{blob_name}'
        if not os.path.isfile(path):
            with open(path, 'wb') as f:
                f.write(content)
        self.db.execute(
            'UPDATE items SET blob_name = ?, sha256 = COALESCE(sha256, ?) WHERE id = ?',
            (blob_name, sha, item_id)
        )
        self.db.commit()

    def remove(self, item_id: int):
        self.db.execute('DELETE FROM items WHERE id = ?', (item_id,))
        self.db.commit()

    # -- reading

    def _row(self, row) -> Optional[Item]:
        return Item(**dict(row)) if row else None

    def get(self, item_id: int) -> Optional[Item]:
        return self._row(self.db.execute(
            'SELECT * FROM items WHERE id = ?', (item_id,)).fetchone())

    def random(self, collection: str, exclude: int = None) -> Optional[Item]:
        return self._row(self.db.execute(
            'SELECT * FROM items WHERE collection = ? AND id IS NOT ? '
            'ORDER BY RANDOM() LIMIT 1',
            (collection, exclude)).fetchone())

    def count(self, collection: str) -> int:
        return self.db.execute(
            'SELECT COUNT(*) FROM items WHERE collection = ?', (collection,)).fetchone()[0]

    def has_media(self, collection: str, media_id: int) -> bool:
        return bool(self.db.execute(
            'SELECT 1 FROM items WHERE collection = ? AND media_id = ?',
            (collection, media_id)).fetchone())

    def by_url(self, collection: str, url: str) -> Optional[Item]:
        return self._row(self.db.execute(
            'SELECT * FROM items WHERE collection = ? AND url = ? LIMIT 1',
            (collection, url)).fetchone())


collect_store = CollectStore()
