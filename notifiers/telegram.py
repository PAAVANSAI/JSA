import os
import httpx
import logging
from typing import List, Dict
from models.job import JobPost, CollectorHealth

logger = logging.getLogger("JSA.Telegram")

class TelegramNotifier:
    """
    Dispatches job alerts to Telegram.
    - Bundles all new jobs into ONE single digest message per sweep.
    - No separate notifications per job.
    - Heartbeat debug messages disabled to prevent clutter.
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

    def send_digest_alert(self, jobs: List[JobPost]) -> bool:
        """
        Sends all qualified jobs in ONE unified digest message.
        Prevents multiple phone notifications.
        """
        if not jobs:
            return True

        header = (
            f"🎯 <b>AWS & DevOps Job Digest ({len(jobs)} New Openings)</b>\n"
            f"⏱ <i>Posted: Today / Last 24 Hours • Match: 60%+</i>\n"
            f"━━━━━━━━━━━━━━━━━━━\n\n"
        )

        entries = []
        for idx, job in enumerate(jobs, 1):
            source_badge = "🏢 Official ATS" if job.source_layer == 1 else f"🌐 {job.source_name}"
            entry = (
                f"<b>{idx}. {job.title}</b>\n"
                f"🏢 <b>{job.company}</b> | 📍 {job.location}\n"
                f"🎯 Match: <b>{job.match_score:.0f}%</b> | 📡 {source_badge}\n"
                f"👉 <a href='{job.apply_url}'><b>Click Here to Apply</b></a>\n"
            )
            entries.append(entry)

        # Telegram limit is 4096 characters per message.
        # Pack entries into chunks so all fit in unified digest messages.
        current_msg = header
        for entry in entries:
            if len(current_msg) + len(entry) + 25 > 3900:
                self._send_message(current_msg)
                current_msg = "🎯 <b>Job Digest (Continued)</b>\n━━━━━━━━━━━━━━━━━━━\n\n" + entry
            else:
                current_msg += entry + "\n"

        if current_msg:
            return self._send_message(current_msg)
        return True

    def send_daily_heartbeat(self, health_reports: List[CollectorHealth]) -> bool:
        """
        Muted: Only logs locally to console; does not ping the user's phone.
        """
        for h in health_reports:
            logger.info(f"Collector status: {h.source_name} (L{h.layer}): {h.jobs_found} found ({h.jobs_new} new) - {h.status}")
        return True
