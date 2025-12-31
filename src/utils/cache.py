"""SQLite-based caching for API responses"""

import sqlite3
import json
import hashlib
import time
import os
from typing import Optional, Any, Dict
from pathlib import Path
from datetime import datetime, timedelta


class Cache:
    """SQLite-based cache for API responses"""
    
    def __init__(self, cache_dir: str = "./data/cache", ttl_hours: int = 24):
        """
        Initialize cache
        
        Args:
            cache_dir: Directory for cache database
            ttl_hours: Time-to-live in hours
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.cache_dir / "cache.db"
        self.ttl_seconds = ttl_hours * 3600
        self._init_db()
    
    def _init_db(self):
        """Initialize cache database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                created_at REAL NOT NULL,
                expires_at REAL NOT NULL
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_expires_at ON cache(expires_at)
        """)
        conn.commit()
        conn.close()
    
    def _make_key(self, source: str, query: str, params: Dict[str, Any]) -> str:
        """Generate cache key from query parameters"""
        key_data = {
            "source": source,
            "query": query,
            "params": params
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    def get(self, source: str, query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """
        Get cached value
        
        Args:
            source: Data source (arxiv/pubmed)
            query: Search query
            params: Additional parameters
            
        Returns:
            Cached value or None if not found/expired
        """
        if params is None:
            params = {}
        
        key = self._make_key(source, query, params)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = time.time()
        cursor.execute("""
            SELECT value FROM cache
            WHERE key = ? AND expires_at > ?
        """, (key, now))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return json.loads(result[0])
        return None
    
    def set(self, source: str, query: str, value: Any, params: Optional[Dict[str, Any]] = None):
        """
        Set cached value
        
        Args:
            source: Data source (arxiv/pubmed)
            query: Search query
            value: Value to cache (must be JSON-serializable)
            params: Additional parameters
        """
        if params is None:
            params = {}
        
        key = self._make_key(source, query, params)
        now = time.time()
        expires_at = now + self.ttl_seconds
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO cache (key, value, created_at, expires_at)
            VALUES (?, ?, ?, ?)
        """, (key, json.dumps(value), now, expires_at))
        
        conn.commit()
        conn.close()
    
    def clear_expired(self):
        """Remove expired entries"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        now = time.time()
        cursor.execute("DELETE FROM cache WHERE expires_at <= ?", (now,))
        conn.commit()
        conn.close()
    
    def clear_all(self):
        """Clear all cached entries"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cache")
        conn.commit()
        conn.close()

