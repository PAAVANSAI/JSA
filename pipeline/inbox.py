import logging
from typing import List, Dict, Any
from models.job import JobPost, CollectorHealth
from collectors.base import BaseCollector
from collectors.layer1_career_pages import CareerPagesCollector
from collectors.layer2_jobspy import JobSpyCollector
from collectors.layer3_apify import ApifyIndiaPortalsCollector
from collectors.layer3_india_portals import IndiaTopPortalsCollector
from collectors.layer4_google_jobs import GoogleJobsCollector
from collectors.layer5_web_search import WebSearchAICollector
from collectors.layer6_alerts import CommunityAlertsCollector

from pipeline.deduplicator import Deduplicator
from pipeline.scam_detector import ScamDetector
from pipeline.scorer import MatchScorer
from pipeline.resume_generator import ResumeGenerator
from pipeline.link_validator import LinkValidator
from notifiers.telegram import TelegramNotifier
from config.settings import settings

logger = logging.getLogger("JSA.Inbox")

class UnifiedInboxManager:
    """
    Central orchestration engine for Job Search Automation:
    1. Triggers enabled collector plugins.
    2. Gathers raw feeds into one unified inbox.
    3. Runs deduplication ('best link wins', removes repeats).
    4. Evaluates scam probability.
    5. Calculates match score against master_profile.json.
    6. Generates tailored ATS resume for qualified matches.
    7. Dispatches alerts to Telegram and produces heartbeat metrics.
    """
    def __init__(self):
        self.collectors: List[BaseCollector] = []
        self._register_collectors()
        
        self.deduplicator = Deduplicator(db_path=settings.db_path)
        self.scam_detector = ScamDetector()
        self.scorer = MatchScorer(profile_path="config/master_profile.json")
        self.resume_gen = ResumeGenerator(profile_path="config/master_profile.json")
        self.notifier = TelegramNotifier()

    def _register_collectors(self):
        # Layer 1: Always on (Free, fast career page APIs)
        if settings.layer1_enabled:
            self.collectors.append(CareerPagesCollector(target_companies=settings.layer1_companies))
        
        # Layer 2: JobSpy (Free portals)
        if settings.layer2_enabled:
            self.collectors.append(JobSpyCollector(
                sites=settings.jobspy_sites, 
                enable_naukri=settings.jobspy_enable_naukri_local
            ))

        # Layer 3: India Top Portals (Foundit, Shine, etc.)
        self.collectors.append(IndiaTopPortalsCollector())
        if settings.layer3_enabled:
            self.collectors.append(ApifyIndiaPortalsCollector(
                api_token=settings.apify_token,
                monthly_budget_usd=settings.apify_monthly_budget_usd
            ))

        # Layer 4: Google Jobs API
        if settings.layer4_enabled:
            self.collectors.append(GoogleJobsCollector(api_key=settings.jsearch_api_key))

        # Layer 5: Web Search
        if settings.layer5_enabled:
            self.collectors.append(WebSearchAICollector(api_key=settings.tavily_api_key))

        # Layer 6: Alerts
        self.collectors.append(CommunityAlertsCollector())

    def run_cycle(self, keywords: List[str] = None, locations: List[str] = None) -> Dict[str, Any]:
        keywords = keywords or ["AWS", "Cloud", "DevOps", "Support"]
        locations = locations or ["Hyderabad", "Bengaluru", "Remote"]

        raw_inbox: List[JobPost] = []
        health_reports: List[CollectorHealth] = []

        logger.info(f"Starting unified collection cycle with {len(self.collectors)} plugins...")

        # 1. Harvest from all active layers
        for collector in self.collectors:
            try:
                posts = collector.collect(keywords=keywords, locations=locations)
                raw_inbox.extend(posts)
                health_reports.append(collector.check_health())
            except Exception as e:
                logger.error(f"Collector {collector.name} encountered an unhandled error: {e}")
                health_reports.append(collector.check_health())

        total_harvested = len(raw_inbox)

        # 2. Deduplicate: remove duplicates across sources & select authoritative best link
        unique_jobs = self.deduplicator.deduplicate_batch(raw_inbox)
        new_jobs_count = len(unique_jobs)

        # 3. Pipeline: Scam check -> Scoring -> Resume Generation -> Telegram Alert
        notified_jobs: List[JobPost] = []
        for job in unique_jobs:
            # Scam check
            self.scam_detector.evaluate(job)
            
            # Skip blatant scams
            if job.scam_score >= 0.8:
                logger.warning(f"Skipping scam job: {job.title} at {job.company} ({job.scam_reasons})")
                continue

            # Candidate match scoring
            score = self.scorer.score_job(job)

            if score >= settings.min_match_score:
                # 4. Working Link Validation: verify URL is live before alerting
                if not LinkValidator.is_link_alive(job.apply_url):
                    logger.warning(f"Skipping job with dead or expired link: {job.title} at {job.company} ({job.apply_url})")
                    continue

                # Tailored resume generation
                resume_path = None
                if settings.auto_generate_resume:
                    resume_path = self.resume_gen.generate_tailored_resume(job)

                # Mark as notified in persistent DB and add to batch digest
                self.deduplicator.mark_notified(job)
                notified_jobs.append(job)

        # 4. Dispatch ALL matching jobs in ONE unified digest message (No spam / multiple pings)
        if notified_jobs:
            self.notifier.send_digest_alert(notified_jobs)

        # 5. Heartbeat logged locally (no Telegram ping)
        self.notifier.send_daily_heartbeat(health_reports)

        return {
            "total_harvested": total_harvested,
            "unique_new_jobs": new_jobs_count,
            "notified_jobs": len(notified_jobs),
            "health_reports": health_reports
        }
