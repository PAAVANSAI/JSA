import os
import httpx
import logging
from typing import List, Dict, Optional
from models.job import JobPost, CollectorHealth

logger = logging.getLogger("JSA.Telegram")

class TelegramNotifier:
    """
    Advanced Telegram Dispatcher for Charugundla Paavansai:
    1. Single clean digest with Salary intel, Glassdoor ratings, and direct apply links.
    2. 1-Tap Copy Cold Outreach message (code syntax) to DM recruiters.
    3. Direct PDF Resume document delivery to your Telegram chat.
    """
    def __init__(self, bot_token: str = None, chat_id: str = None):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")

    def _send_message(self, text: str) -> bool:
        if not self.bot_token or not self.chat_id:
            logger.info("Telegram credentials not configured. Printing message to stdout:\n" + text)
            print("\n" + "="*50 + "\n[TELEGRAM PREVIEW]\n" + text + "\n" + "="*50)
            return True

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.post(url, json=payload)
                return res.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    def send_pdf_document(self, pdf_path: str, caption: str) -> bool:
        """
        Sends the actual compiled .pdf resume file directly to Telegram chat.
        """
        if not self.bot_token or not self.chat_id or not os.path.exists(pdf_path):
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendDocument"
        try:
            with open(pdf_path, "rb") as f:
                files = {"document": (os.path.basename(pdf_path), f, "application/pdf")}
                data = {"chat_id": self.chat_id, "caption": caption, "parse_mode": "HTML"}
                with httpx.Client(timeout=30.0) as client:
                    res = client.post(url, data=data, files=files)
                    return res.status_code == 200
        except Exception as e:
            logger.warning(f"Could not send PDF to Telegram: {e}")
            return False

    def send_digest_alert(self, enriched_jobs: List[dict]) -> bool:
        """
        Sends the rich unified digest with cold pitches and salary intel.
        """
        if not enriched_jobs:
            return True

        header = (
            f"🎯 <b>AWS & DEVOPS RADAR — {len(enriched_jobs)} NEW OPENINGS</b>\n"
            f"👤 <b>Candidate:</b> Charugundla Paavansai\n"
            f"⏱ <i>Posted: Today / Last 24 Hours • Score: 60%+</i>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        )

        entries = []
        for idx, item in enumerate(enriched_jobs, 1):
            job = item["job"]
            intel = item["intel"]
            pitch = item["pitch"]
            source_badge = "🏢 Official ATS" if job.source_layer == 1 else f"🌐 {job.source_name}"

            entry = (
                f"<b>{idx}. {job.title}</b>\n"
                f"🏢 <b>{job.company}</b> ({intel['rating']})\n"
                f"📍 {job.location} | 💰 Est: <b>{intel['salary']}</b>\n"
                f"🎯 Match Score: <b>{job.match_score:.0f}%</b> | 📡 {source_badge}\n"
                f"👉 <a href='{job.apply_url}'><b>[Click Here to Apply Directly]</b></a>\n"
                f"🔍 <a href='{pitch['linkedin_search_url']}'><b>[Find Recruiters on LinkedIn]</b></a>\n"
                f"💬 <b>1-Tap Copy Cold DM Pitch:</b>\n"
                f"<code>{pitch['linkedin_dm']}</code>\n"
            )
            entries.append(entry)

        current_msg = header
        for entry in entries:
            if len(current_msg) + len(entry) + 25 > 3900:
                self._send_message(current_msg)
                current_msg = "🎯 <b>Job Radar Digest (Continued)</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n" + entry
            else:
                current_msg += entry + "\n"

        if current_msg:
            return self._send_message(current_msg)
        return True

    def send_daily_heartbeat(self, health_reports: List[CollectorHealth]) -> bool:
        for h in health_reports:
            logger.info(f"Collector status: {h.source_name} (L{h.layer}): {h.jobs_found} found - {h.status}")
        return True
