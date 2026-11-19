import json
import os
import re
from typing import Dict, Any, List
from models.job import JobPost

class MatchScorer:
    """
    Precision Match Scorer tailored strictly for Charugundla Paavansai:
    - Experience: 1 Year (Fresher, Trainee, Junior, Associate, 0-2 years ONLY).
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
        
        # Non-AWS Clouds
        r"\bazure\b", r"\bgcp\b", r"\bgoogle cloud\b",
        
        # Unrelated domains
        r"\bfrontend\b", r"\breact\b", r"\bangular\b", r"\bvue\b", r"\bflutter\b",
        r"\bios\b", r"\bandroid\b", r"\bqa manual\b", r"\bsales\b", r"\bmarketing\b",
        r"\baccountant\b", r"\bhr\b", r"\brecruiter\b", r"\bgraphic\b", r"\bui/ux\b",
        r"\bproduct manager\b", r"\bscrum master\b"
    ]

    # Reject if JD requires 3 or more years of experience
    HIGH_EXP_PATTERNS = [
        r"\b(3\+|4\+|5\+|6\+|7\+|8\+|9\+|10\+|12\+|15\+)\s*(years|yrs|year|yr)\b",
        r"\b(3|4|5|6|7|8|9|10)\s*-\s*\d+\s*(years|yrs)\b",
        r"\b(3|4|5|6|7|8|9|10)\s*to\s*\d+\s*(years|yrs)\b",
        r"\bminimum\s*(3|4|5|6|7|8|9|10)\s*(years|yrs)\b",
        r"\bat\s*least\s*(3|4|5|6|7|8|9|10)\s*(years|yrs)\b"
    ]

    # Positive fresher / junior keywords
    FRESHER_EXP_PATTERNS = [
        r"\b(0-1|0-2|1-2|0\s*to\s*1|0\s*to\s*2|1\s*to\s*2)\s*(years|yrs|year|yr)\b",
        r"\b(fresher|freshers|entry level|entry-level|trainee|intern|internship|graduate|junior|jr\.|associate)\b"
    ]

    def __init__(self, profile_path: str = "config/master_profile.json"):
        self.profile = self._load_profile(profile_path)

    def _load_profile(self, path: str) -> Dict[str, Any]:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def score_job(self, job: JobPost) -> float:
        title_lower = job.title.lower()
        desc_lower = job.description.lower()
        loc_lower = job.location.lower()
        full_text = f"{title_lower} {desc_lower}"

        # 1. HARD REJECTION: Check title against senior, non-AWS, and unrelated blacklists
        for pattern in self.HARD_REJECT_TITLES:
            if re.search(pattern, title_lower):
                job.match_score = 0.0
                return 0.0

        # 2. HARD REJECTION: Experience requirement > 2 years
        for exp_pat in self.HIGH_EXP_PATTERNS:
            if re.search(exp_pat, full_text):
                job.match_score = 0.0
                return 0.0

        # 3. AWS MANDATORY CHECK:
        # Paavansai's core competency is AWS. If AWS is not mentioned, reject!
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

        # 6. Experience Alignment (Max 15 points)
        # Rewards explicitly stated fresher/junior/trainee roles
        has_fresher_indicator = any(re.search(pat, full_text) for pat in self.FRESHER_EXP_PATTERNS)
        if has_fresher_indicator:
            total_score += 15.0
        else:
            total_score += 8.0  # Neutral / unstated experience

        # 7. Target Location Alignment (Max 10 points)
        preferred_cities = ["hyderabad", "bengaluru", "bangalore", "remote", "pune", "chennai", "india"]
        if any(city in loc_lower for city in preferred_cities):
            total_score += 10.0
        else:
            total_score += 5.0

        final_score = round(min(100.0, max(0.0, total_score)), 1)
        job.match_score = final_score
        return final_score
