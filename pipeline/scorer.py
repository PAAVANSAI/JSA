import json
import os
import re
from typing import Dict, Any, List
from models.job import JobPost

class MatchScorer:
    """
    Precision Match Scorer tailored for Charugundla Paavansai.
    Filters strictly for:
    1. AWS MANDATORY: Rejects any role that does not focus on Amazon Web Services (AWS).
       Strictly blocks Azure-only or GCP-only DevOps postings.
    2. Experience Gate: Fresher to 1-3 years experience (Strong penalty for 4+ years / Senior / Lead).
    3. Minimum Score Gate: 60%+ required for notification.
    """
    UNRELATED_TITLES = [
        "frontend", "react", "angular", "vue", "flutter", "ios", "android",
        "qa manual", "sales", "marketing", "accountant", "hr", "recruiter",
        "graphic designer", "ui/ux", "product manager", "scrum master"
    ]

    NON_AWS_CLOUD_TITLES = [
        "azure devops", "azure cloud", "azure engineer", "azure administrator",
        "azure infra", "gcp devops", "gcp engineer", "google cloud engineer",
        "azure platform", "azure architect"
    ]

    SENIOR_INDICATORS = [
        "lead", "principal", "architect", "staff", "manager", "director", "vp",
        "head of", "senior manager", "tech lead", "sr. devops", "sr devops", "sr. aws"
    ]

    HIGH_EXP_PATTERNS = [
        r"\b(4\+|5\+|6\+|7\+|8\+|9\+|10\+|12\+|15\+)\s*(years|yrs|year|yr)\b",
        r"\b(4|5|6|7|8|9|10)\s*-\s*\d+\s*(years|yrs)\b",
        r"\b(4|5|6|7|8|9|10)\s*to\s*\d+\s*(years|yrs)\b",
        r"\bminimum\s*(4|5|6|7|8|9|10)\s*(years|yrs)\b"
    ]

    FRESHER_EXP_PATTERNS = [
        r"\b(0-1|0-2|0-3|1-2|1-3)\s*(years|yrs|year|yr)\b",
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

        # 1. Negative Filter: Reject completely unrelated professions
        for bad in self.UNRELATED_TITLES:
            if re.search(r'\b' + re.escape(bad) + r'\b', title_lower):
                job.match_score = 0.0
                return 0.0

        # 2. Strict Azure/GCP Negative Filter:
        # If the job explicitly specifies Azure or GCP DevOps and does NOT mention AWS, reject!
        for non_aws in self.NON_AWS_CLOUD_TITLES:
            if non_aws in title_lower and "aws" not in title_lower:
                job.match_score = 0.0
                return 0.0

        # 3. AWS Core Requirement:
        # Paavansai's core competency is AWS.
        # If "aws" and "amazon web services" are completely absent, drop immediately!
        has_aws = bool(re.search(r'\baws\b', full_text) or "amazon web services" in full_text)
        if not has_aws:
            job.match_score = 15.0
            return 15.0

        # 4. Negative Filter: Senior/Lead roles penalty
        is_senior = any(re.search(r'\b' + re.escape(s) + r'\b', title_lower) for s in self.SENIOR_INDICATORS)
        has_high_exp = any(re.search(pat, full_text) for pat in self.HIGH_EXP_PATTERNS)

        if is_senior or has_high_exp:
            job.match_score = 25.0
            return 25.0

        total_score = 0.0

        # 5. Core Role Relevance (Max 40 points)
        if any(role in title_lower for role in ["aws devops", "aws engineer", "aws cloud"]):
            total_score += 40.0
        elif "devops" in title_lower and has_aws:
            total_score += 35.0
        elif any(role in title_lower for role in ["cloud engineer", "cloud support", "infrastructure", "sre"]):
            total_score += 30.0
        elif any(tool in title_lower for tool in ["docker", "jenkins", "terraform", "linux"]):
            total_score += 26.0
        else:
            total_score += 10.0

        # 6. Tech Stack & Skills Alignment (Max 35 points)
        core_skills = [
            "aws", "ec2", "s3", "iam", "vpc", "docker", "jenkins", "terraform",
            "kubernetes", "linux", "ci/cd", "cloudwatch", "lambda", "python", "git"
        ]
        matched_skills = [s for s in core_skills if re.search(r'\b' + re.escape(s) + r'\b', full_text)]
        skill_ratio = min(1.0, len(matched_skills) / 5.0)
        total_score += (skill_ratio * 35.0)

        # 7. Experience Alignment (Max 15 points)
        has_fresher_indicator = any(re.search(pat, full_text) for pat in self.FRESHER_EXP_PATTERNS)
        if has_fresher_indicator:
            total_score += 15.0
        else:
            total_score += 8.0

        # 8. Target Location Alignment (Max 10 points)
        preferred_cities = ["hyderabad", "bengaluru", "bangalore", "remote", "pune", "chennai", "india"]
        if any(city in loc_lower for city in preferred_cities):
            total_score += 10.0
        else:
            total_score += 5.0

        final_score = round(min(100.0, max(0.0, total_score)), 1)
        job.match_score = final_score
        return final_score
