import os
import html
import httpx
import logging
from datetime import datetime
from typing import List, Dict, Optional
from models.job import JobPost, CollectorHealth

logger = logging.getLogger("JSA.Telegram")

class TelegramNotifier:
    """
    State-of-the-art Telegram Dispatcher for Charugundla Paavansai:
    1. Elegant visual spacing, bold highlights, blockquote card styling, and emoji badges.
    2. Zero clutter: Strictly AWS & DevOps (No Azure/GCP bleed).
    3. 1-Tap Copy Cold Outreach message (code syntax) to DM recruiters.
    4. Direct PDF Resume document delivery to your Telegram chat.
    5. HTML Entity Safe: escapes special characters to prevent Telegram API crashes.
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
        Sends the compiled ATS .pdf resume file directly to Telegram chat.
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
        Sends the visually polished, well-spaced unified digest message.
        """
        if not enriched_jobs:
            return True

        now_str = datetime.now().strftime("%d %b %Y • %I:%M %p")
        header = (
            f"🚀 <b>AWS & DEVOPS RADAR — NEW OPENINGS</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Candidate:</b> Charugundla Paavansai\n"
            f"⏱ <b>Filter:</b> Last 24 Hours • Score: 60%+\n"
            f"📅 <b>Scanned:</b> {now_str}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        )

        entries = []
        for idx, item in enumerate(enriched_jobs, 1):
            job = item["job"]
            intel = item["intel"]
            pitch = item["pitch"]
            source_badge = "🏢 Official Career ATS" if job.source_layer == 1 else f"🌐 {html.escape(job.source_name)}"

            safe_title = html.escape(job.title)
            safe_company = html.escape(job.company)
            safe_location = html.escape(job.location)
            safe_dm = html.escape(pitch['linkedin_dm'])

            card = (
                f"📌 <b>{idx}. {safe_title}</b>\n"
                f"<blockquote>"
                f"🏢 <b>{safe_company}</b>  •  ⭐ <b>{intel['rating']}</b> ({intel['tier']})\n"
                f"📍 <b>{safe_location}</b>  •  💰 <b>{intel['salary']}</b>\n"
                f"🎯 <b>Match Score: {job.match_score:.0f}%</b>  •  📡 <i>{source_badge}</i>"
                f"</blockquote>\n\n"
                f"🔗 <b><a href='{job.apply_url}'>APPLY DIRECTLY (Official Board) ↗</a></b>\n"
                f"👔 <b><a href='{pitch['linkedin_search_url']}'>FIND HIRING MANAGERS ON LINKEDIN ↗</a></b>\n\n"
                f"💬 <b>1-Tap Cold Outreach Pitch (Tap below to copy):</b>\n"
                f"<code>{safe_dm}</code>\n\n"
                f"──────────────────────────\n"
            )
            entries.append(card)

        current_msg = header
        for card in entries:
            if len(current_msg) + len(card) + 30 > 3800:
                self._send_message(current_msg)
                current_msg = (
                    f"🚀 <b>AWS & DEVOPS RADAR (CONTINUED)</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n" + card
                )
            else:
                current_msg += card + "\n"

        if current_msg:
            return self._send_message(current_msg)
        return True

    def send_daily_heartbeat(self, health_reports: List[CollectorHealth]) -> bool:
        for h in health_reports:
            logger.info(f"Collector status: {h.source_name} (L{h.layer}): {h.jobs_found} found - {h.status}")
        return True
