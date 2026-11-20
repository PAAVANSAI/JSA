import json
import os
import re
import html
import logging
from typing import Dict, Any, List, Tuple
from models.job import JobPost

logger = logging.getLogger("JSA.Scorer")

class MatchScorer:
    """
    Precision Match Scorer tailored strictly for Charugundla Paavansai:
    - Experience: 1 Year (Fresher, Trainee, Junior, Associate, 0-2 years ONLY).
    - Deep JD Scanning: Inspects full job description, metadata, and title for experience requirements.
    - Hard Rejection: Blocks ANY Senior, Sr., Lead, Principal, Architect, Level II/III, or 3+ years role.
    - Cloud Scope: Strictly AWS & DevOps (Zero Azure/GCP tolerance).
    """
    # Instant rejection if ANY of these words appear in the job title
    HARD_REJECT_TITLES = [
        # Seniority levels (STRICT ZERO TOLERANCE)
        r"\bsenior\b", r"\bsr\b", r"\bsr\.\b", r"\blead\b", r"\bprincipal\b",
        r"\barchitect\b", r"\bstaff\b", r"\bmanager\b", r"\bdirector\b", r"\bvp\b",
        r"\btech lead\b", r"\bteam lead\b", r"\bhead of\b",
        r"\bii\b", r"\biii\b", r"\biv\b", r"\bv\b",  # Levels II, III, IV
        r"\b2\b", r"\b3\b", r"\b4\b",               # Levels 2, 3, 4 (e.g., DevOps Engineer 2)
        r"\bl[2-9]\b", r"\bl-[2-9]\b",              # L2, L3, L4, L-3 (Level 2/3 Engineer)
        r"\blevel\s*[2-9]\b", r"\blevel\s*(ii|iii|iv|v)\b",
        
        # Non-AWS Clouds
        r"\bazure\b", r"\bgcp\b", r"\bgoogle cloud\b",
        
        # Unrelated domains
        r"\bfrontend\b", r"\breact\b", r"\bangular\b", r"\bvue\b", r"\bflutter\b",
        r"\bios\b", r"\bandroid\b", r"\bqa manual\b", r"\bsales\b", r"\bmarketing\b",
        r"\baccountant\b", r"\bhr\b", r"\brecruiter\b", r"\bgraphic\b", r"\bui/ux\b",
        r"\bproduct manager\b", r"\bscrum master\b"
    ]

    # Reject if JD describes a senior or leadership responsibility
    DESC_SENIOR_PATTERNS = [
        r"(?:seeking|looking for|hiring|role:?|as a|position:?)\s*(?:a|an)?\s*(?:senior|sr|lead|principal|architect|staff)",
        r"(?:lead|manage|head|guide)\s+(?:the|our)\s+(?:team|devops|cloud|infrastructure|engineers)",
        r"\b(?:senior|sr|lead|principal)\s+(?:devops|cloud|infrastructure|systems|aws)\s+engineer\b",
        r"\b(?:senior|lead)\s+architect\b",
        r"\barchitecting\s+and\s+designing\s+large\s*scale\b"
    ]

    # Positive fresher / junior keywords
    FRESHER_EXP_PATTERNS = [
        r"\b(0-1|0-2|1-2|0-3|0\s*to\s*1|0\s*to\s*2|1\s*to\s*2|0\s*to\s*3)\s*(years|yrs|year|yr|yoe)\b",
        r"\b(fresher|freshers|entry level|entry-level|trainee|intern|internship|graduate|junior|jr\.|associate)\b",
        r"\b(recent graduate|college graduate|campus hire|no prior experience|batch 2024|batch 2025|2024 batch|2025 batch)\b"
    ]

    def __init__(self, profile_path: str = "config/master_profile.json"):
        self.profile = self._load_profile(profile_path)

    def _load_profile(self, path: str) -> Dict[str, Any]:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    @staticmethod
    def clean_text(raw_html: str) -> str:
        """Strip HTML tags and unescape HTML entities for clean NLP evaluation."""
        text = re.sub(r"<[^>]+>", " ", raw_html or "")
        text = html.unescape(text)
        return " ".join(text.split())

    def evaluate_experience(self, job: JobPost) -> Tuple[bool, str, float]:
        """
        Deep analysis of Job Description, metadata, and URL to determine exact experience requirement.
        Returns: (is_qualified, rejection_reason, experience_bonus_score)
        """
        clean_desc = self.clean_text(job.description).lower()
        title_lower = job.title.lower()
        url_lower = job.apply_url.lower()
        full_text = f"{title_lower} {clean_desc} {url_lower}"

        # 1. Check metadata for senior levels or high experience
        if job.raw_data and isinstance(job.raw_data, dict):
            job_level = str(job.raw_data.get("job_level", "")).lower()
            if any(lvl in job_level for lvl in ["mid-senior", "director", "executive", "senior"]):
                return False, f"Job level metadata is '{job_level}'", 0.0

            for exp_field in ["min_exp", "minExp", "minimumExperience", "min_experience"]:
                val = job.raw_data.get(exp_field)
                if val is not None:
                    try:
                        if float(val) >= 3.0:
                            return False, f"Metadata {exp_field}={val} requires 3+ years experience", 0.0
                    except (ValueError, TypeError):
                        pass

        # 2. Check Description for Senior/Lead/Architect role descriptions
        for pat in self.DESC_SENIOR_PATTERNS:
            if re.search(pat, clean_desc):
                return False, f"Description specifies senior/lead scope ({pat})", 0.0

        # 3. Check for high experience ranges in description or URL (e.g., '3-5 years', '4 to 8 yrs')
        # Also check URL slug patterns (e.g. '8-to-13-years')
        range_matches = re.findall(r"(\d+(?:\.\d+)?)\s*(?:-|to|–)\s*(\d+(?:\.\d+)?)\s*(?:years|yrs|year|yr|yoe)\b", full_text)
        for lower_str, upper_str in range_matches:
            try:
                low, high = float(lower_str), float(upper_str)
                # If minimum required is 3+, or range is mid-level like 2-5 or 3-6
                if low >= 3.0 or high >= 4.0:
                    return False, f"Description requires {low}-{high} years of experience", 0.0
            except ValueError:
                continue

        # 4. Check for 'X+ years' requirements (e.g., '3+ years', '5+ years')
        plus_matches = re.findall(r"(\d+(?:\.\d+)?)\s*\+\s*(?:years|yrs|year|yr|yoe)\b", full_text)
        for match in plus_matches:
            try:
                val = float(match)
                if val >= 3.0:
                    return False, f"Description specifies {val}+ years experience requirement", 0.0
            except ValueError:
                continue

        # 5. Check for 'minimum X years' / 'at least X years'
        min_matches = re.findall(r"(?:minimum|min|at least|requires?)\s*(\d+(?:\.\d+)?)\s*(?:years|yrs|year|yr|yoe)\b", full_text)
        for match in min_matches:
            try:
                val = float(match)
                if val >= 2.5:
                    return False, f"Description requires minimum {val} years experience", 0.0
            except ValueError:
                continue

        # 6. Experience match score determination
        has_fresher_indicator = any(re.search(pat, full_text) for pat in self.FRESHER_EXP_PATTERNS)
        if has_fresher_indicator:
            # Full experience bonus for explicit fresher / junior / 0-2 years
            return True, "Fresher / Junior experience match", 15.0
        
        # Neutral score for unstated or general entry-level experience
        return True, "Acceptable experience range", 8.0

    def score_job(self, job: JobPost) -> float:
        title_lower = job.title.lower()
        clean_desc = self.clean_text(job.description).lower()
        loc_lower = job.location.lower()
        url_lower = job.apply_url.lower()
        raw_str = str(job.raw_data).lower()
        full_text = f"{title_lower} {clean_desc} {url_lower} {raw_str}"

        # 1. HARD REJECTION: Check title against senior, non-AWS, and unrelated blacklists
        for pattern in self.HARD_REJECT_TITLES:
            if re.search(pattern, title_lower):
                job.match_score = 0.0
                return 0.0

        # 2. DEEP EXPERIENCE EVALUATION (Description + Metadata + URL)
        is_exp_ok, exp_reason, exp_bonus = self.evaluate_experience(job)
        if not is_exp_ok:
            logger.info(f"Rejected [{job.company}] {job.title}: {exp_reason}")
            job.match_score = 0.0
            return 0.0

        # 3. AWS MANDATORY CHECK:
        # Paavansai's core competency is AWS. If AWS is not mentioned in title or description, reject!
        has_aws = bool(re.search(r'\baws\b', full_text) or "amazon web services" in full_text)
        if not has_aws:
            job.match_score = 0.0
            return 0.0

        total_score = 0.0

        # 4. Core Role Relevance (Max 40 points)
        if any(role in title_lower for role in ["aws devops", "aws engineer", "aws cloud"]):
            total_score += 40.0
        elif "devops" in title_lower and has_aws:
            total_score += 35.0
        elif any(role in title_lower for role in ["cloud engineer", "cloud support", "infrastructure", "sre"]):
            total_score += 30.0
        elif any(tool in title_lower for tool in ["docker", "jenkins", "terraform", "linux"]):
            total_score += 26.0
        else:
            total_score += 15.0

        # 5. Tech Stack & Skills Alignment (Max 35 points)
        core_skills = [
            "aws", "ec2", "s3", "iam", "vpc", "docker", "jenkins", "terraform",
            "kubernetes", "linux", "ci/cd", "cloudwatch", "lambda", "python", "git"
        ]
        matched_skills = [s for s in core_skills if re.search(r'\b' + re.escape(s) + r'\b', full_text)]
        skill_ratio = min(1.0, len(matched_skills) / 4.0)  # 4 matching skills = 100%
        total_score += (skill_ratio * 35.0)

        # 6. Experience Alignment Score (Max 15 points)
        total_score += exp_bonus

        # 7. Target Location Alignment (Max 10 points)
        preferred_cities = ["hyderabad", "bengaluru", "bangalore", "remote", "pune", "chennai", "india"]
        if any(city in loc_lower for city in preferred_cities):
            total_score += 10.0
        else:
            total_score += 5.0

        final_score = round(min(100.0, max(0.0, total_score)), 1)
        job.match_score = final_score
        return final_score
