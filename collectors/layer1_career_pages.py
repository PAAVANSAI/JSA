import httpx
import logging
from datetime import datetime
from typing import List, Dict, Any
from collectors.base import BaseCollector
from models.job import JobPost

logger = logging.getLogger("JSA.Layer1")

class CareerPagesCollector(BaseCollector):
    """
    Layer 1: Direct Career Page ATS APIs (Greenhouse, Lever, Ashby, etc.)
    Speed: Fastest (~10 mins check interval)
    Cost: ₹0
    Authority: Highest quality direct company links.
    """
    def __init__(self, target_companies: List[Dict[str, str]] = None):
        super().__init__(name="Career Page ATS APIs", layer=1)
        self.target_companies = target_companies or [
            {"name": "Razorpay", "ats": "greenhouse", "slug": "razorpaysoftwareprivatelimited"},
            {"name": "Postman", "ats": "greenhouse", "slug": "postman"},
            {"name": "Groww", "ats": "lever", "slug": "groww"},
            {"name": "Cred", "ats": "lever", "slug": "cred"},
            {"name": "BrowserStack", "ats": "greenhouse", "slug": "browserstack"},
            {"name": "InMobi", "ats": "greenhouse", "slug": "inmobi"},
        ]

    def _fetch_greenhouse(self, company_name: str, slug: str) -> List[JobPost]:
        url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
        posts = []
        try:
            with httpx.Client(timeout=12.0) as client:
                res = client.get(url)
                if res.status_code != 200:
                    return []
                data = res.json()
                for item in data.get("jobs", []):
                    title = item.get("title", "")
                    job_id = item.get("id", "")
                    raw_apply_url = item.get("absolute_url", "")
                    content_html = item.get("content", "")
                    
                    # Convert to modern human-friendly Greenhouse application URL
                    if "boards-api.greenhouse.io" in raw_apply_url or not raw_apply_url:
                        apply_url = f"https://job-boards.greenhouse.io/{slug}/jobs/{job_id}"
                    elif "boards.greenhouse.io" in raw_apply_url:
                        apply_url = raw_apply_url.replace("boards.greenhouse.io", "job-boards.greenhouse.io")
                    else:
                        apply_url = raw_apply_url

                    location = item.get("location", {}).get("name", "India")
                    posts.append(JobPost(
                        title=title,
                        company=company_name,
                        location=location,
                        apply_url=apply_url,
                        source_layer=1,
                        source_name=f"Career Page: Greenhouse ({company_name})",
                        description=content_html,
                        raw_data=item
                    ))
        except Exception as e:
            logger.warning(f"Error fetching Greenhouse for {company_name}: {e}")
        return posts

    def _fetch_lever(self, company_name: str, slug: str) -> List[JobPost]:
        url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
        posts = []
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.get(url)
                if res.status_code != 200:
                    return []
                data = res.json()
                for item in data:
                    title = item.get("text", "")
                    apply_url = item.get("hostedUrl", "")
                    categories = item.get("categories", {})
                    location = categories.get("location", "India")
                    desc = item.get("descriptionPlain", "")
                    posts.append(JobPost(
                        title=title,
                        company=company_name,
                        location=location,
                        apply_url=apply_url,
                        source_layer=1,
                        source_name=f"Career Page: Lever ({company_name})",
                        description=desc,
                        raw_data=item
                    ))
        except Exception as e:
            logger.warning(f"Error fetching Lever for {company_name}: {e}")
        return posts

    def _fetch_smartrecruiters(self, company_name: str, slug: str) -> List[JobPost]:
        url = f"https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=50"
        posts = []
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.get(url)
                if res.status_code != 200:
                    return []
                data = res.json()
                for item in data.get("content", []):
                    title = item.get("name", "")
                    job_id = item.get("id", "")
                    apply_url = f"https://jobs.smartrecruiters.com/{slug}/{job_id}"
                    loc_data = item.get("location", {})
                    city = loc_data.get("city", "Hyderabad")
                    country = loc_data.get("country", "India")
                    posts.append(JobPost(
                        title=title,
                        company=company_name,
                        location=f"{city}, {country}",
                        apply_url=apply_url,
                        source_layer=1,
                        source_name=f"Career Page: SmartRecruiters ({company_name})",
                        raw_data=item
                    ))
        except Exception as e:
            logger.warning(f"Error fetching SmartRecruiters for {company_name}: {e}")
        return posts

    def collect(self, keywords: List[str], locations: List[str], limit: int = 50) -> List[JobPost]:
        results: List[JobPost] = []
        err_count = 0
        
        # Tokenize search keywords for filtering
        kw_set = [k.lower().strip() for k in keywords]
        loc_set = [loc.lower().strip() for loc in locations]

        for comp in self.target_companies:
            c_name = comp["name"]
            ats = comp.get("ats", "").lower()
            slug = comp.get("slug", "")

            try:
                fetched: List[JobPost] = []
                if ats == "greenhouse":
                    fetched = self._fetch_greenhouse(c_name, slug)
                elif ats == "lever":
                    fetched = self._fetch_lever(c_name, slug)
                elif ats == "smartrecruiters":
                    fetched = self._fetch_smartrecruiters(c_name, slug)
                
                # Filter by keywords and locations
                for job in fetched:
                    title_lower = job.title.lower()
                    loc_lower = job.location.lower()
                    
                    # Match any keyword in title or description
                    kw_match = any(kw in title_lower for kw in kw_set) if kw_set else True
                    # Match location
                    loc_match = any(l in loc_lower for l in loc_set) or "india" in loc_lower or "remote" in loc_lower if loc_set else True

                    if kw_match and loc_match:
                        results.append(job)
            except Exception as e:
                err_count += 1
                logger.error(f"Failed to collect from {c_name}: {e}")

        self.record_run(found=len(results), new=len(results), error="Errors encountered" if err_count > 0 else None)
        return results
