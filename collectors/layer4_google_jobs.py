import os
import httpx
import logging
from typing import List, Optional
from collectors.base import BaseCollector
from models.job import JobPost

logger = logging.getLogger("JSA.Layer4")

class GoogleJobsCollector(BaseCollector):
    """
    Layer 4: Google Jobs Aggregator via JSearch / DataForSEO
    Aggregates job boards and career pages indexed by Google into one unified feed.
    """
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(name="Google Jobs (API)", layer=4)
        self.api_key = api_key or os.getenv("JSEARCH_API_KEY")

    def collect(self, keywords: List[str], locations: List[str], limit: int = 25) -> List[JobPost]:
        results: List[JobPost] = []
        if not self.api_key:
            msg = "JSEARCH_API_KEY not set. Layer 4 inactive."
            logger.info(msg)
            self.record_run(found=0, new=0, error=msg)
            return results

        query = f"{keywords[0]} in {locations[0]}" if keywords and locations else "AWS Fresher in Hyderabad"
        url = "https://jsearch.p.rapidapi.com/search"
        headers = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": "jsearch.p.rapidapi.com"
        }
        params = {
            "query": query,
            "page": "1",
            "num_pages": "1",
            "date_posted": "today"  # Freshest jobs only
        }

        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.get(url, headers=headers, params=params)
                if res.status_code == 200:
                    data = res.json().get("data", [])
                    for item in data[:limit]:
                        results.append(JobPost(
                            title=item.get("job_title", "Untitled"),
                            company=item.get("employer_name", "Unknown"),
                            location=item.get("job_city", locations[0] if locations else "India"),
                            apply_url=item.get("job_apply_link", ""),
                            source_layer=4,
                            source_name="Google Jobs (JSearch)",
                            description=item.get("job_description", ""),
                            raw_data=item
                        ))
            self.record_run(found=len(results), new=len(results), error=None)
        except Exception as e:
            err = f"Google Jobs API error: {e}"
            logger.error(err)
            self.record_run(found=0, new=0, error=err)

        return results
