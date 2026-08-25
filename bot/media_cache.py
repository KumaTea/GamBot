import os
import time
import sqlite3
import logging
from typing import Optional
from bot.media import MediaRef, PHOTO


MEDIA_DATA_DIR = 'data/media'
MEDIA_DB_FILE = f'{MEDIA_DATA_DIR}/cache.db'

SCHEMA = """
CREATE TABLE IF NOT EXISTS urls (
    url         TEXT PRIMARY KEY,
    kind        TEXT NOT NULL DEFAULT 'photo',
    media_id    INTEGER NOT NULL,
    access_hash INTEGER NOT NULL,
    file_ref    BLOB,
    seen_at     INTEGER NOT NULL
);
"""


class MediaCache:
    """
    Pictures we have already put on Telegram, by where they came from.

    The gacha hands out the same few hundred images over and over; once
    Telegram has one, sending it again should not mean another trip to
    someone's wiki.
    """
    def __init__(self, path: str = MEDIA_DB_FILE):
        os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.executescript(SCHEMA)
        self.db.commit()

    def get(self, url: str) -> Optional[MediaRef]:
        row = self.db.execute(
            'SELECT kind, media_id, access_hash, file_ref FROM urls WHERE url = ?',
            (url,)).fetchone()
        if not row:
            return None
        kind, media_id, access_hash, file_ref = row
        return MediaRef(kind or PHOTO, media_id, access_hash, file_ref or b'')

    def put(self, url: str, ref: MediaRef):
        self.db.execute(
            'INSERT INTO urls (url, kind, media_id, access_hash, file_ref, seen_at) '
            'VALUES (?,?,?,?,?,?) ON CONFLICT(url) DO UPDATE SET '
            'kind = excluded.kind, media_id = excluded.media_id, '
            'access_hash = excluded.access_hash, file_ref = excluded.file_ref, '
            'seen_at = excluded.seen_at',
            (url, ref.kind, ref.id, ref.access_hash, ref.file_reference, int(time.time()))
        )
        self.db.commit()

    def drop(self, url: str):
        """Forget a reference Telegram no longer honours."""
        logging.info(f'[media]\tDropping stale cache entry for {url}')
        self.db.execute('DELETE FROM urls WHERE url = ?', (url,))
        self.db.commit()

    def count(self) -> int:
        return self.db.execute('SELECT COUNT(*) FROM urls').fetchone()[0]


media_cache = MediaCache()
