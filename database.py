import sqlite3
import logging
from typing import Optional

logger = logging.getLogger("database")

class ImageCacheDB:
    """Database class for managing image cache with a persistent connection."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        logger.info(f"Initialisiere Datenbankverbindung zu: {db_path}")
        self.conn = sqlite3.connect(self.db_path, timeout=30.0, check_same_thread=False)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA journal_mode = WAL")
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS image_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT UNIQUE NOT NULL,
                image_url TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_keyword ON image_cache(keyword)
        ''')
        self.conn.commit()
        logger.info("Datenbank erfolgreich initialisiert.")

    def get_image_url(self, keyword: str) -> Optional[str]:
        """Get cached image URL for a keyword."""
        if not keyword:
            logger.warning("Leeres Keyword an get_image_url übergeben.")
            return None
        try:
            logger.debug(f"Suche Cache für Keyword: '{keyword}'")
            cursor = self.conn.cursor()
            cursor.execute('SELECT image_url FROM image_cache WHERE keyword = ?', (keyword.lower(),))
            result = cursor.fetchone()
            if result:
                logger.info(f"Cache-Treffer für Keyword: '{keyword}'")
                return result[0]
            else:
                logger.info(f"Cache-Miss für Keyword: '{keyword}'")
                return None
        except sqlite3.Error as e:
            logger.error(f"Datenbankfehler: {e}")
            return None

    def save_image_url(self, keyword: str, image_url: str) -> bool:
        """Save image URL to cache. Returns True if successful."""
        if not keyword or not image_url:
            logger.warning("Leeres Keyword oder Bild-URL an save_image_url übergeben.")
            return False
        try:
            logger.debug(f"Speichere in Cache - Keyword: '{keyword}', URL: {image_url}")
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO image_cache (keyword, image_url) 
                VALUES (?, ?)
            ''', (keyword.lower(), image_url))
            self.conn.commit()
            logger.info(f"Bild-URL für Keyword '{keyword}' erfolgreich im Cache gespeichert.")
            return True
        except sqlite3.Error as e:
            logger.error(f"Fehler beim Speichern der Bild-URL für Keyword '{keyword}': {e}")
            return False

    def clear(self) -> bool:
        """Clear all cache entries. Returns True if successful."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM image_cache')
            self.conn.commit()
            logger.info("Cache erfolgreich geleert.")
            return True
        except sqlite3.Error as e:
            logger.error(f"Fehler beim Leeren des Caches: {e}")
            return False

    def close(self):
        """Close the database connection."""
        if self.conn:
            logger.info("Schließe Datenbankverbindung.")
            self.conn.close()
            logger.debug("Datenbankverbindung erfolgreich geschlossen.")