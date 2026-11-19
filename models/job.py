import hashlib
import re
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class JobPost(BaseModel):
    title: str
    company: str
    location: str = "India"
    apply_url: str
    source_layer: int  # 1 to 6
    source_name: str   # e.g., "Career Page: Greenhouse", "JobSpy: LinkedIn", "Apify: Naukri"
    description: str = ""
    posted_date: Optional[datetime] = None
    salary: Optional[str] = None
    experience_level: Optional[str] = None
    raw_data: Dict[str, Any] = Field(default_factory=dict)
    
    # Processed fields
    fingerprint: Optional[str] = None
    scam_score: float = 0.0          # 0.0 = safe, 1.0 = definite scam
    scam_reasons: List[str] = Field(default_factory=list)
    match_score: float = 0.0         # 0.0 to 100.0 against master_profile
    is_fresh: bool = True            # within 48h limit
    alternate_links: List[str] = Field(default_factory=list)

    def generate_fingerprint(self) -> str:
        """
        Generates a canonical hash based on normalized company, title, and city.
        Removes noisy terms like 'fresher', 'urgent', 'hiring', special characters.
        """
        def normalize(text: str) -> str:
            text = text.lower()
            text = re.sub(r'[\(\)\[\]\-_,./\\]', ' ', text)
            # Remove common filler buzzwords in job titles
            noise_words = ['fresher', 'freshers', 'urgent', 'urgently', 'hiring', 'immediate', 'opening', 'openings']
            tokens = [t for t in text.split() if t not in noise_words]
            return " ".join(tokens)

        norm_company = normalize(self.company)
        norm_title = normalize(self.title)
        
        # Normalize location: extract primary city if in India
        cities = ['hyderabad', 'bengaluru', 'bangalore', 'pune', 'mumbai', 'delhi', 'noida', 'gurugram', 'gurgaon', 'chennai', 'remote']
        matched_city = "india"
        loc_lower = self.location.lower()
        for c in cities:
            if c in loc_lower:
                matched_city = 'bengaluru' if c == 'bangalore' else ('gurugram' if c == 'gurgaon' else c)
                break

        key = f"{norm_company}::{norm_title}::{matched_city}"
        hash_digest = hashlib.sha256(key.encode('utf-8')).hexdigest()[:16]
        self.fingerprint = hash_digest
        return hash_digest

class CollectorHealth(BaseModel):
    source_name: str
    layer: int
    jobs_found: int = 0
    jobs_new: int = 0
    errors: int = 0
    status: str = "HEALTHY" # HEALTHY, DEGRADED, FAILING
    last_run_timestamp: Optional[datetime] = None
    notes: Optional[str] = None
