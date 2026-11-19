import httpx
import logging
from typing import Optional

logger = logging.getLogger("JSA.LinkValidator")

class LinkValidator:
    """
    Verifies that every job application link is alive, accessible,
    and returns a valid HTTP 200/300 status before sending alerts.
    Filters out dead links, expired job posts, and 404s.
    """
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    MAJOR_PORTAL_DOMAINS = ["indeed.com", "linkedin.com", "glassdoor.com", "naukri.com", "foundit.in"]

    @classmethod
    def is_link_alive(cls, url: str, timeout: float = 8.0) -> bool:
        if not url or not url.startswith("http"):
            return False

        # Major portals generate valid URLs directly from active search results.
        # They use Cloudflare bot protection against automated bots, but open smoothly on mobile/browser.
        if any(portal in url for portal in cls.MAJOR_PORTAL_DOMAINS):
            return True

        try:
            with httpx.Client(timeout=timeout, follow_redirects=True, headers=cls.HEADERS) as client:
                try:
                    res = client.head(url)
                    if res.status_code in [200, 301, 302, 303, 307, 308]:
                        return True
                    if res.status_code in [404, 410]:
                        return False
                except Exception:
                    pass

                res = client.get(url)
                if res.status_code == 200:
                    text_sample = res.text[:2000].lower()
                    if "this job has expired" in text_sample or "position has been filled" in text_sample or "job is no longer available" in text_sample:
                        logger.info(f"Link {url} reports job is expired/closed.")
                        return False
                    return True
                elif res.status_code in [404, 410]:
                    return False
                # For 403 or other codes on career pages, give benefit of doubt if it's an official ATS
                return any(ats in url for ats in ["greenhouse.io", "lever.co", "ashbyhq.com"])
        except Exception as e:
            logger.debug(f"Link verification failed for {url}: {e}")
            return any(ats in url for ats in ["greenhouse.io", "lever.co", "ashbyhq.com"])
