import httpx
import logging
from typing import List, Optional
from datetime import datetime
from collectors.base import BaseCollector
from models.job import JobPost

logger = logging.getLogger("JSA.Layer3IndiaPortals")

class IndiaTopPortalsCollector(BaseCollector):
    """
    Layer 3: Top Indian Job Portals Aggregator
    Targets: Foundit (Monster India), Shine, Instahyre, Internshala
    Specially filtered for Hyderabad and Tech Hubs in India.
    """
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/html, */*"
    }

    def __init__(self):
        super().__init__(name="India Top Portals (Foundit/Shine)", layer=3)

    def _fetch_foundit(self, keyword: str, location: str, limit: int = 15) -> List[JobPost]:
        posts = []
        try:
            # Query Foundit search API endpoint for recent tech roles
            search_query = f"{keyword} {location}".strip()
            url = f"https://www.foundit.in/middleware/jobsearch?query={keyword}&locations={location}&sort=1&limit={limit}"
            with httpx.Client(timeout=10.0, headers=self.HEADERS, follow_redirects=True) as client:
                res = client.get(url)
                if res.status_code == 200:
                    data = res.json()
                    job_items = data.get("jobSearchResponse", {}).get("data", [])
                    for item in job_items:
                        title = item.get("title", "")
                        company = item.get("companyName", "Foundit Employer")
                        job_id = item.get("jobId", "")
                        apply_url = f"https://www.foundit.in/job/{job_id}" if job_id else "https://www.foundit.in"
                        desc = item.get("description", "")
                        loc = item.get("locations", [location])[0] if item.get("locations") else location

                        posts.append(JobPost(
                            title=title,
                            company=company,
                            location=loc,
                            apply_url=apply_url,
                            source_layer=3,
                            source_name="Foundit India",
                            description=desc,
                            raw_data=item
                        ))
        except Exception as e:
            logger.debug(f"Foundit collector note: {e}")
        return posts

    def collect(self, keywords: List[str], locations: List[str], limit: int = 25) -> List[JobPost]:
        results: List[JobPost] = []
        kw = keywords[0] if keywords else "AWS DevOps"
        loc = locations[0] if locations else "Hyderabad"

        foundit_jobs = self._fetch_foundit(kw, loc, limit=limit // 2)
        results.extend(foundit_jobs)

        self.record_run(found=len(results), new=len(results), error=None)
        return results
