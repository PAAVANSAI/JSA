import sqlite3
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from models.job import JobPost

logger = logging.getLogger("JSA.Deduplicator")

class Deduplicator:
    """
    Handles deduplication across all 6 layers:
    1. Canonical fingerprint: (company + title + city).
    2. 'Best link wins' resolution hierarchy:
       Layer 1 (Direct ATS / Career Page) > Layer 2/3 (JobSpy / Apify Portals) > Layer 4 (Google Jobs) > Layer 5/6 (Web/Telegram).
    3. Persistent SQLite registry to suppress already seen/notified postings.
    4. 48-hour age cutoff filter.
    """
    def __init__(self, db_path: str = "jsa_jobs.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path, timeout=30.0) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS seen_jobs (
                    fingerprint TEXT PRIMARY KEY,
                    company TEXT,
                    title TEXT,
                    location TEXT,
                    best_apply_url TEXT,
                    best_source_name TEXT,
                    best_source_layer INTEGER,
                    first_seen_at TIMESTAMP,
                    match_score REAL,
                    notified INTEGER DEFAULT 0
                )
            """)
            conn.commit()

    def is_already_processed(self, fingerprint: str) -> bool:
        with sqlite3.connect(self.db_path, timeout=30.0) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM seen_jobs WHERE fingerprint = ?", (fingerprint,))
            return cursor.fetchone() is not None

    def deduplicate_batch(self, raw_jobs: List[JobPost]) -> List[JobPost]:
        """
        Deduplicates incoming jobs in the current run and merges duplicates.
        Ensures the 'best link wins' (lowest source_layer number wins).
        Strictly drops anything older than 24 hours (timezone safe).
        """
        cluster: Dict[str, JobPost] = {}

        for job in raw_jobs:
            # 1. Strictly ignore if older than 24 hours (timezone safe)
            if job.posted_date:
                try:
                    if job.posted_date.tzinfo is not None:
                        from datetime import timezone
                        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
                        if job.posted_date < cutoff:
                            continue
                    else:
                        cutoff = datetime.now() - timedelta(hours=24)
                        if job.posted_date < cutoff:
                            continue
                except Exception:
                    pass

            # 2. Compute canonical fingerprint
            fp = job.generate_fingerprint()

            # 3. Check if already seen in SQLite database from earlier runs
            if self.is_already_processed(fp):
                continue

            if fp not in cluster:
                cluster[fp] = job
            else:
                existing = cluster[fp]
                # Best link wins: lower layer number is more direct and authoritative
                if job.source_layer < existing.source_layer:
                    # Upgrade to direct company ATS link
                    job.alternate_links.append(existing.apply_url)
                    job.alternate_links.extend(existing.alternate_links)
                    cluster[fp] = job
                else:
                    # Keep existing, append new link as alternate
                    existing.alternate_links.append(job.apply_url)

        return list(cluster.values())

    def mark_notified(self, job: JobPost):
        """
        Persists newly processed jobs into SQLite so subsequent runs skip them.
        """
        fp = job.fingerprint or job.generate_fingerprint()
        with sqlite3.connect(self.db_path, timeout=30.0) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO seen_jobs 
                (fingerprint, company, title, location, best_apply_url, best_source_name, best_source_layer, first_seen_at, match_score, notified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                fp,
                job.company,
                job.title,
                job.location,
                job.apply_url,
                job.source_name,
                job.source_layer,
                datetime.now(),
                job.match_score
            ))
            conn.commit()
