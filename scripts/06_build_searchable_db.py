"""
Script 6: Build Searchable Database
Creates an SQLite DB (FTS) from processed media hashes and page text for fast searching
"""

import sys
import os
import sqlite3
import csv
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_PATH = 'data/manifests/media_index.db'
HASH_CSV = 'data/manifests/media_hashes.csv'

def main():
    if not os.path.exists(HASH_CSV):
        logger.error(f"Hash CSV not found: {HASH_CSV}. Run scripts/03_hash_media.py first.")
        return

    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Create table
    cur.execute('''
        CREATE TABLE media (
            id INTEGER PRIMARY KEY,
            file_id TEXT,
            filename TEXT,
            local_path TEXT,
            phash TEXT,
            average_hash TEXT,
            dhash TEXT,
            width INTEGER,
            height INTEGER,
            format TEXT,
            thumbnail_path TEXT,
            page_text_snippet TEXT,
            keywords_found TEXT,
            google_mentions INTEGER DEFAULT 0,
            reddit_mentions INTEGER DEFAULT 0,
            nitter_mentions INTEGER DEFAULT 0,
            virality_score REAL DEFAULT 0.0,
            is_underreported INTEGER DEFAULT 0
        )
    ''')

    # FTS table for full-text search on page_text_snippet and filename
    cur.execute('CREATE VIRTUAL TABLE media_fts USING fts5(filename, page_text_snippet, keywords_found, content="media", content_rowid="id")')

    # Insert rows
    with open(HASH_CSV, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

    for r in rows:
        cur.execute('''INSERT INTO media (file_id, filename, local_path, phash, average_hash, dhash, width, height, format, thumbnail_path, page_text_snippet, keywords_found)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''', (
            r.get('file_id'), r.get('filename'), r.get('local_path'), r.get('phash'), r.get('average_hash'), r.get('dhash'), r.get('width') or 0, r.get('height') or 0, r.get('format'), r.get('thumbnail_path'), r.get('page_text_snippet') or '', r.get('keywords_found') or ''
        ))

    # Populate FTS
    cur.execute('INSERT INTO media_fts(media_fts) VALUES ("rebuild")')

    conn.commit()
    conn.close()

    logger.info(f"✅ Searchable DB created: {DB_PATH}")

if __name__ == '__main__':
    main()
