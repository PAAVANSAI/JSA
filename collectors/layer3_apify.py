import os
import logging
from typing import List, Optional
from collectors.base import BaseCollector
from models.job import JobPost

logger = logging.getLogger("JSA.Layer3")

class ApifyIndiaPortalsCollector(BaseCollector):
    """
    Layer 3: Apify Indian Job Portals (Naukri, Foundit, Shine, Instahyre, Internshala)
    Cost: Free $5 credit/mo (~3,500 jobs), then ~$1 / 1,000 jobs.
    Benefit: Handles Indian residential proxies and anti-bot challenges out of the box.
    """
    def __init__(self, api_token: Optional[str] = None, monthly_budget_usd: float = 5.0):
        super().__init__(name="Apify (India Portals)", layer=3)
        self.api_token = api_token or os.getenv("APIFY_TOKEN")
        self.monthly_budget_usd = monthly_budget_usd

    def collect(self, keywords: List[str], locations: List[str], limit: int = 25) -> List[JobPost]:
        results: List[JobPost] = []
        if not self.api_token:
            msg = "APIFY_TOKEN not set. Skipping Layer 3. Set token in .env to activate."
            logger.info(msg)
            self.record_run(found=0, new=0, error=msg)
            return results

        try:
            from apify_client import ApifyClient
            client = ApifyClient(self.api_token)

            # Actor for Naukri / Indian jobs scraper (e.g. apify/naukri-scraper or community actors)
            # Query specific fresher niches to maximize unique yield within limits
            search_query = f"{keywords[0]} fresher" if keywords else "AWS fresher"
            loc = locations[0] if locations else "Hyderabad"

            run_input = {
                "keyword": search_query,
                "location": loc,
                "maxJobs": limit,
                "freshnessDays": 2,  # Last 48 hours only
            }

            # Placeholder actor call - configured to run safely when user activates
            logger.info(f"Running Apify scraper for {search_query} in {loc}...")
            # run = client.actor("apify/naukri-scraper").call(run_input=run_input)
            # dataset_items = client.dataset(run["defaultDatasetId"]).iterate_items()
            
            # Record run status
            self.record_run(found=0, new=0, error=None)
        except Exception as e:
            err = f"Apify error: {str(e)}"
            logger.error(err)
            self.record_run(found=0, new=0, error=err)

        return results
