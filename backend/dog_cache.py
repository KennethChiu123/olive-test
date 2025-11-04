"""
Dog cache implementation using SQLite.
Provides persistent storage for dog breeds with built-in duplicate prevention.
"""

import sqlite3
import logging
from datetime import datetime
from typing import List, Dict

logger = logging.getLogger(__name__)


class DogCache:
    """
    sqlite-based cache for dog breeds with primary key 
    constraint on breed to ensure uniqueness.
    """
    
    def __init__(self, db_path='dogs_cache.db'):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dogs 
            (
                breed TEXT PRIMARY KEY,
                image TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # adding index for faster breed lookups
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_dogs_breed ON dogs(breed)
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"Initialized sqlite cache at {self.db_path}")
    
    def add_dogs_batch(self, dogs: List[Dict]) -> int:

        if not dogs:
            return 0
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Batch insert with INSERT OR IGNORE for duplicates
        cursor.executemany('''
            INSERT OR REPLACE INTO dogs (breed, image, updated_at)
            VALUES (?, ?, ?)
        ''', [(dog['breed'], dog['image'], datetime.now()) for dog in dogs])
        
        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        logger.info(f"Batch added {rows_affected} dogs")
        return rows_affected
    
    
    def get_all_dogs_dict(self) -> Dict[str, str]:

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT breed, image FROM dogs ORDER BY breed')
        results = cursor.fetchall()
        conn.close()
        return {row[0]: row[1] for row in results}
    