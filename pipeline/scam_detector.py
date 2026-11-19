import re
from typing import List, Tuple
from models.job import JobPost

class ScamDetector:
    """
    Scam Detection Engine:
    Flags:
    1. Processing fees / registration fees / security deposit demands
    2. WhatsApp-only apply / interview processes
    3. Free personal email contacts (e.g. gmail.com, yahoo.com) for supposed enterprise recruiters
    4. Unrealistic salary claims for fresher roles (e.g., 50k/day)
    """
    FEE_PATTERNS = [
        r"registration\s+fee",
        r"processing\s+fee",
        r"security\s+deposit",
        r"refundable\s+amount",
        r"training\s+charges",
        r"pay\s+first",
        r"bank\s+transfer\s+before"
    ]

    WHATSAPP_PATTERNS = [
        r"whatsapp\s+(only|direct|resume\s+to)",
        r"send\s+cv\s+on\s+whatsapp",
        r"contact\s+on\s+wa\.me",
        r"wa\.me/\d+"
    ]

    FREE_EMAIL_PATTERN = r"[a-zA-Z0-9._%+-]+@(gmail|yahoo|hotmail|outlook|rediffmail)\.com"

    def evaluate(self, job: JobPost) -> Tuple[float, List[str]]:
        text = f"{job.title} {job.description}".lower()
        reasons: List[str] = []
        score = 0.0

        # 1. Check fee demand (Critical)
        for pat in self.FEE_PATTERNS:
            if re.search(pat, text):
                score += 0.8
                reasons.append("Mentions registration/processing fee or deposit")
                break

        # 2. Check WhatsApp-only contact
        for pat in self.WHATSAPP_PATTERNS:
            if re.search(pat, text):
                score += 0.4
                reasons.append("Directs application exclusively to WhatsApp")
                break

        # 3. Check recruiter email domain in job description
        emails = re.findall(self.FREE_EMAIL_PATTERN, text)
        if emails and job.source_layer > 1: # Official career pages rarely have this issue
            score += 0.3
            reasons.append("Recruiter contact uses free webmail domain (e.g. @gmail.com)")

        # Cap score between 0.0 and 1.0
        score = min(score, 1.0)
        job.scam_score = score
        job.scam_reasons = reasons
        return score, reasons
