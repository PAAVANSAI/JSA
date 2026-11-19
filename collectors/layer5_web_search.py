import os
import logging
from typing import List, Optional
from collectors.base import BaseCollector
from models.job import JobPost

logger = logging.getLogger("JSA.Layer5")

class WebSearchAICollector(BaseCollector):
    """
    Layer 5: Open-web search (Tavily/Serper) + AI extraction
    Uncovers unlisted startup openings and career pages directly from recent web crawls.
    """
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(name="Web Search + AI", layer=5)
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")

    def collect(self, keywords: List[str], locations: List[str], limit: int = 15) -> List[JobPost]:
        results: List[JobPost] = []
        if not self.api_key:
            msg = "TAVILY_API_KEY not configured. Layer 5 inactive."
            logger.info(msg)
            self.record_run(found=0, new=0, error=msg)
            return results

        # In production: Tavily query with time_range='day', followed by extraction
        self.record_run(found=0, new=0, error=None)
        return results
