import sqlite3
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class ImageCacheDB:
    """Database class for managing image cache with a persistent connection."""

    def __init__(self, db_path: str):
        self.db_path = db_path
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

    def get_image_url(self, keyword: str) -> Optional[str]:
        """Get cached image URL for a keyword."""
        if not keyword:
            return None
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT image_url FROM image_cache WHERE keyword = ?', (keyword.lower(),))
            result = cursor.fetchone()
            return result[0] if result else None
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            return None

    def save_image_url(self, keyword: str, image_url: str) -> bool:
        """Save image URL to cache. Returns True if successful."""
        if not keyword or not image_url:
            return False
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO image_cache (keyword, image_url) 
                VALUES (?, ?)
            ''', (keyword.lower(), image_url))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Failed to save image URL for keyword '{keyword}': {e}")
            return False

    def clear(self) -> bool:
        """Clear all cache entries. Returns True if successful."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM image_cache')
            self.conn.commit()
            logger.info("Cache cleared successfully")
            return True
        except sqlite3.Error as e:
            logger.error(f"Failed to clear cache: {e}")
            return False

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()