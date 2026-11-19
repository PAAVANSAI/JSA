import logging
from datetime import datetime
from typing import List, Optional
from collectors.base import BaseCollector
from models.job import JobPost

logger = logging.getLogger("JSA.Layer2")

class JobSpyCollector(BaseCollector):
    """
    Layer 2: Multi-portal scraping via JobSpy
    Covers: Indeed, LinkedIn, Glassdoor, Google Jobs, Naukri
    Cost: ₹0
    Note: Naukri often requires an Indian residential IP. If blocked, fallback to Layer 3.
    """
    def __init__(self, sites: Optional[List[str]] = None, enable_naukri: bool = False):
        super().__init__(name="JobSpy (Portals)", layer=2)
        default_sites = ["indeed", "linkedin", "glassdoor", "google"]
        if enable_naukri:
            default_sites.append("naukri")
        self.sites = sites or default_sites

    def collect(self, keywords: List[str], locations: List[str], limit: int = 25) -> List[JobPost]:
        results: List[JobPost] = []
        try:
            from jobspy import scrape_jobs
        except ImportError:
            msg = "python-jobspy library is not installed. Run: pip install python-jobspy"
            logger.warning(msg)
            self.record_run(found=0, new=0, error=msg)
            return results

        # Construct realistic search phrases for job board search engines
        queries = []
        if len(keywords) >= 2:
            queries.append(f"{keywords[0]} {keywords[1]}")
            if "fresher" in [k.lower() for k in keywords]:
                queries.append(f"{keywords[0]} fresher")
            else:
                queries.append(f"{keywords[0]} entry level")
        else:
            queries.append(keywords[0] if keywords else "AWS Fresher")

        primary_query = queries[0]
        location_term = locations[0] if locations else "India"

        total_found = 0
        portal_errors = []

        # Iterate over portals individually to isolate failures (e.g. if LinkedIn limits, Indeed still works)
        for site in self.sites:
            try:
                logger.info(f"Scraping {site} for '{primary_query}' in '{location_term}'...")
                df = scrape_jobs(
                    site_name=[site],
                    search_term=primary_query,
                    location=location_term,
                    results_wanted=limit // len(self.sites) + 5,
                    hours_old=24,  # Strictly last 24 hours (Today or 1 day ago only)
                    country_indeed='India'
                )

                if df is not None and not df.empty:
                    for _, row in df.iterrows():
                        site_name = str(row.get("site", site)).capitalize()
                        title = str(row.get("title", "Untitled"))
                        company = str(row.get("company", "Unknown"))
                        loc = str(row.get("location", location_term))
                        apply_url = str(row.get("job_url", "")) or str(row.get("job_url_direct", ""))
                        desc = str(row.get("description", ""))

                        if apply_url and apply_url.startswith("http"):
                            post = JobPost(
                                title=title,
                                company=company,
                                location=loc,
                                apply_url=apply_url,
                                source_layer=2,
                                source_name=f"JobSpy: {site_name}",
                                description=desc,
                                raw_data=row.to_dict() if hasattr(row, 'to_dict') else {}
                            )
                            results.append(post)
            except Exception as e:
                err_msg = f"{site} scrape notice: {str(e)}"
                logger.warning(err_msg)
                portal_errors.append(err_msg)

        total_found = len(results)
        self.record_run(
            found=total_found,
            new=total_found,
            error="; ".join(portal_errors) if portal_errors else None
        )
        return results
