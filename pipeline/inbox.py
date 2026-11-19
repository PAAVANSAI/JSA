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
from pipeline.pdf_converter import PDFResumeBuilder
from pipeline.cold_pitch_generator import ColdPitchGenerator
from pipeline.company_intelligence import CompanyIntelligence
from pipeline.tracker import ApplicationTracker
from pipeline.link_validator import LinkValidator
from notifiers.telegram import TelegramNotifier
from config.settings import settings

logger = logging.getLogger("JSA.Inbox")

class UnifiedInboxManager:
    """
    Central orchestration engine for Charugundla Paavansai's Job Search Automation.
    Features:
    1. Multi-layer scanning (Career ATS + LinkedIn, Naukri, Indeed, Glassdoor, Foundit).
    2. Strict 24-hour filter & precision AWS/DevOps match scoring (>= 60%).
    3. Company salary intelligence and ratings.
    4. Auto-generated 1-tap copy cold pitches for LinkedIn & Email.
    5. Automatic PDF resume builder & Telegram document delivery.
    6. Persistent Excel/CSV Application Funnel Tracker.
    """
    def __init__(self):
        self.collectors: List[BaseCollector] = []
        self._register_collectors()
        
        self.deduplicator = Deduplicator(db_path=settings.db_path)
        self.scam_detector = ScamDetector()
        self.scorer = MatchScorer(profile_path="config/master_profile.json")
        self.html_resume_gen = ResumeGenerator(profile_path="config/master_profile.json")
        self.pdf_builder = PDFResumeBuilder(profile_path="config/master_profile.json")
        self.tracker = ApplicationTracker()
        self.notifier = TelegramNotifier()

    def _register_collectors(self):
        # Layer 1: Always on (Free, fast career page APIs)
        if settings.layer1_enabled:
            self.collectors.append(CareerPagesCollector(target_companies=settings.layer1_companies))
        
        # Layer 2: JobSpy (Naukri, LinkedIn, Indeed, Glassdoor)
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
        keywords = keywords or ["AWS", "DevOps"]
        locations = locations or ["Hyderabad", "Bengaluru", "Remote"]

        raw_inbox: List[JobPost] = []
        health_reports: List[CollectorHealth] = []

        logger.info(f"Starting unified collection cycle with {len(self.collectors)} plugins...")

        # 0. Maintenance: automatically delete generated resumes older than 2 days
        pruned_resumes = self.pdf_builder.cleanup_old_resumes(max_age_days=2)
        if pruned_resumes > 0:
            logger.info(f"Auto-cleaned {pruned_resumes} resumes older than 2 days.")

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

        # 3. Pipeline: Scam check -> Scoring -> Intelligence -> Tracker -> PDF -> Digest
        enriched_qualified: List[dict] = []
        for job in unique_jobs:
            # Scam check
            self.scam_detector.evaluate(job)
            if job.scam_score >= 0.8:
                logger.warning(f"Skipping scam job: {job.title} at {job.company} ({job.scam_reasons})")
                continue

            # Candidate match scoring (>= 60%)
            score = self.scorer.score_job(job)
            if score >= settings.min_match_score:
                # Working Link Validation
                if not LinkValidator.is_link_alive(job.apply_url):
                    logger.warning(f"Skipping job with dead or expired link: {job.title} at {job.company}")
                    continue

                # Intelligence & Salary enrichment
                intel = CompanyIntelligence.enrich_job(job)

                # Cold Pitch Generator (LinkedIn DM & Email)
                pitch = ColdPitchGenerator.generate_pitch(job)

                # Generate tailored PDF resume
                pdf_path = self.pdf_builder.generate_pdf(job)

                # Record in live Application Funnel Tracker (CSV + SQLite)
                self.tracker.log_application(job, intel['salary'], pitch['linkedin_search_url'])

                # Mark as notified in persistent DB
                self.deduplicator.mark_notified(job)

                enriched_qualified.append({
                    "job": job,
                    "intel": intel,
                    "pitch": pitch,
                    "pdf_path": pdf_path
                })

        # 4. Dispatch ALL matching jobs in ONE unified rich digest message
        if enriched_qualified:
            self.notifier.send_digest_alert(enriched_qualified)

            # Send the tailored PDF document for the highest-scoring job in this cycle
            top_job = max(enriched_qualified, key=lambda x: x["job"].match_score)
            caption = (
                f"📄 <b>Tailored Resume: {top_job['job'].company}</b>\n"
                f"Role: {top_job['job'].title} ({top_job['job'].match_score:.0f}% match)\n"
                f"<i>Ready to download & submit!</i>"
            )
            self.notifier.send_pdf_document(top_job["pdf_path"], caption)

        # 5. Heartbeat logged locally
        self.notifier.send_daily_heartbeat(health_reports)

        return {
            "total_harvested": total_harvested,
            "unique_new_jobs": new_jobs_count,
            "notified_jobs": len(enriched_qualified),
            "health_reports": health_reports
        }
