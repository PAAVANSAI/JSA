import csv
import os
import sqlite3
from datetime import datetime
from models.job import JobPost

class ApplicationTracker:
    """
    Maintains a local persistent spreadsheet (applications_tracker.csv) and
    SQLite database tracking all discovered jobs, application links, and outreach status.
    Syncs with Google Sheets or Excel easily.
    """
    CSV_PATH = "applications_tracker.csv"
    DB_PATH = "jsa_jobs.db"

    FIELDNAMES = [
        "date_discovered", "company", "title", "location", "match_score",
        "salary_range", "source", "apply_url", "recruiter_search_url", "status"
    ]

    def __init__(self):
        self._init_csv()
        self._init_db()

    def _init_csv(self):
        if not os.path.exists(self.CSV_PATH):
            with open(self.CSV_PATH, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.FIELDNAMES)
                writer.writeheader()

    def _init_db(self):
        with sqlite3.connect(self.DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS application_funnel (
                    fingerprint TEXT PRIMARY KEY,
                    company TEXT,
                    title TEXT,
                    location TEXT,
                    match_score REAL,
                    salary_range TEXT,
                    source TEXT,
                    apply_url TEXT,
                    recruiter_search_url TEXT,
                    date_discovered TIMESTAMP,
                    status TEXT DEFAULT 'DISCOVERED'
                )
            """)
            conn.commit()

    def log_application(self, job: JobPost, salary_range: str, recruiter_search_url: str):
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        fp = job.fingerprint or job.generate_fingerprint()

        # 1. Update SQLite Funnel
        with sqlite3.connect(self.DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO application_funnel
                (fingerprint, company, title, location, match_score, salary_range, source, apply_url, recruiter_search_url, date_discovered, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'DISCOVERED')
            """, (
                fp, job.company, job.title, job.location, job.match_score,
                salary_range, job.source_name, job.apply_url, recruiter_search_url,
                datetime.now()
            ))
            conn.commit()

        # 2. Append to CSV for Excel / Google Sheets
        row = {
            "date_discovered": date_str,
            "company": job.company,
            "title": job.title,
            "location": job.location,
            "match_score": f"{job.match_score:.0f}%",
            "salary_range": salary_range,
            "source": job.source_name,
            "apply_url": job.apply_url,
            "recruiter_search_url": recruiter_search_url,
            "status": "Ready to Apply"
        }
        with open(self.CSV_PATH, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.FIELDNAMES)
            writer.writerow(row)
