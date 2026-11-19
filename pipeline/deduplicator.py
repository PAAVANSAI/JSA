import sqlite3
import os
import csv
import re
import urllib.parse
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Set
from models.job import JobPost

logger = logging.getLogger("JSA.Deduplicator")

class Deduplicator:
    """
    Bulletproof Multi-Layer Deduplication Engine:
    Guarantees that once a job is notified to the user, it is NEVER sent again.
    
    Checks across 4 distinct gates:
    1. Canonical Content Fingerprint (normalized company + title + city)
    2. Normalized Canonical URL (strips tracking, session, and referral query params)
    3. Persistent SQLite Database (seen_jobs & seen_urls tables)
    4. Permanent CSV Tracker Backup (applications_tracker.csv)
    """
    CSV_TRACKER_PATH = "applications_tracker.csv"

    def __init__(self, db_path: str = "jsa_jobs.db"):
        self.db_path = db_path
        self._init_db()
        self.csv_seen_urls: Set[str] = set()
        self._load_csv_history()

    @staticmethod
    def clean_url(raw_url: str) -> str:
        """
        Strips tracking, referral, and session parameters (utm_*, ref, trackingId).
        Preserves essential identifiers like 'jk' on Indeed.
        """
        if not raw_url:
            return ""
        try:
            parsed = urllib.parse.urlparse(raw_url)
            # Remove trailing slashes and lower-case domain
            clean_netloc = parsed.netloc.lower()
            clean_path = parsed.path.rstrip('/')

            # Filter query params
            params = urllib.parse.parse_qs(parsed.query)
            keep_params = {}
            # Essential job ID params to retain
            for key in ['jk', 'jobId', 'id']:
                if key in params:
                    keep_params[key] = params[key]

            clean_query = urllib.parse.urlencode(keep_params, doseq=True) if keep_params else ""
            clean = urllib.parse.urlunparse((parsed.scheme, clean_netloc, clean_path, '', clean_query, ''))
            return clean
        except Exception:
            return raw_url.split('?')[0].rstrip('/')

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
                    notified INTEGER DEFAULT 1
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS seen_urls (
                    clean_url TEXT PRIMARY KEY,
                    first_seen_at TIMESTAMP
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_seen_url ON seen_jobs (best_apply_url)")
            conn.commit()

    def _load_csv_history(self):
        """
        Loads all previously sent apply URLs from applications_tracker.csv.
        Acts as a permanent fail-safe memory shield even across clean database installs.
        """
        if os.path.exists(self.CSV_TRACKER_PATH):
            try:
                with open(self.CSV_TRACKER_PATH, mode='r', encoding='utf-8-sig', errors='ignore') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        url = row.get("apply_url", "").strip()
                        if url:
                            self.csv_seen_urls.add(self.clean_url(url))
                logger.info(f"Loaded {len(self.csv_seen_urls)} previously sent jobs from tracker backup.")
            except Exception as e:
                logger.debug(f"Could not load CSV tracker history: {e}")

    def is_already_processed(self, fingerprint: str, apply_url: str) -> bool:
        """
        Returns True if this exact job or application URL was ever notified.
        """
        clean_u = self.clean_url(apply_url)

        # 1. Check in-memory permanent CSV tracker
        if clean_u and clean_u in self.csv_seen_urls:
            return True

        # 2. Check SQLite persistent database
        with sqlite3.connect(self.db_path, timeout=30.0) as conn:
            cursor = conn.cursor()
            # Check fingerprint
            cursor.execute("SELECT 1 FROM seen_jobs WHERE fingerprint = ?", (fingerprint,))
            if cursor.fetchone():
                return True

            # Check cleaned URL
            if clean_u:
                cursor.execute("SELECT 1 FROM seen_urls WHERE clean_url = ?", (clean_u,))
                if cursor.fetchone():
                    return True

                cursor.execute("SELECT 1 FROM seen_jobs WHERE best_apply_url = ? OR best_apply_url = ?", (apply_url, clean_u))
                if cursor.fetchone():
                    return True

        return False

    def deduplicate_batch(self, raw_jobs: List[JobPost]) -> List[JobPost]:
        """
        Filters out any jobs older than 24 hours AND any jobs already sent to the user.
        Selects the authoritative best link for duplicates within the current batch.
        """
        cluster: Dict[str, JobPost] = {}

        for job in raw_jobs:
            # 1. Age cutoff: Strictly ignore if older than 24 hours
            if job.posted_date:
                try:
                    if job.posted_date.tzinfo is not None:
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

            # 3. Permanent Suppression: Check if already sent previously
            if self.is_already_processed(fp, job.apply_url):
                logger.debug(f"Suppressing repeat job: {job.title} at {job.company}")
                continue

            # 4. In-batch best link resolution
            if fp not in cluster:
                cluster[fp] = job
            else:
                existing = cluster[fp]
                if job.source_layer < existing.source_layer:
                    job.alternate_links.append(existing.apply_url)
                    job.alternate_links.extend(existing.alternate_links)
                    cluster[fp] = job
                else:
                    existing.alternate_links.append(job.apply_url)

        return list(cluster.values())

    def mark_notified(self, job: JobPost):
        """
        Records the job into SQLite seen_jobs, seen_urls, and in-memory set.
        Guarantees it will never be notified again.
        """
        fp = job.fingerprint or job.generate_fingerprint()
        clean_u = self.clean_url(job.apply_url)
        now_ts = datetime.now()

        # Update in-memory tracker
        if clean_u:
            self.csv_seen_urls.add(clean_u)

        # Update SQLite
        with sqlite3.connect(self.db_path, timeout=30.0) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO seen_jobs 
                (fingerprint, company, title, location, best_apply_url, best_source_name, best_source_layer, first_seen_at, match_score, notified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                fp, job.company, job.title, job.location, job.apply_url,
                job.source_name, job.source_layer, now_ts, job.match_score
            ))
            if clean_u:
                cursor.execute("""
                    INSERT OR IGNORE INTO seen_urls (clean_url, first_seen_at) VALUES (?, ?)
                """, (clean_u, now_ts))
            conn.commit()
