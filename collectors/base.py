import abc
from datetime import datetime
from typing import List, Optional
from models.job import JobPost, CollectorHealth

class BaseCollector(abc.ABC):
    """
    Abstract interface for every job source collector plugin across Layers 1 to 6.
    Ensures modularity: add or disable any collector without altering the pipeline.
    """
    def __init__(self, name: str, layer: int):
        self.name = name
        self.layer = layer
        self.health = CollectorHealth(source_name=name, layer=layer)

    @abc.abstractmethod
    def collect(self, keywords: List[str], locations: List[str], limit: int = 25) -> List[JobPost]:
        """
        Synchronously or asynchronously fetches job listings from this source.
        Returns normalized List[JobPost].
        """
        pass

    def check_health(self) -> CollectorHealth:
        """
        Returns the current operational status and metrics for the daily heartbeat.
        """
        return self.health

    def record_run(self, found: int, new: int, error: Optional[str] = None):
        self.health.last_run_timestamp = datetime.now()
        self.health.jobs_found = found
        self.health.jobs_new = new
        if error:
            self.health.errors += 1
            self.health.status = "FAILING" if self.health.errors >= 3 else "DEGRADED"
            self.health.notes = error
        else:
            self.health.status = "HEALTHY"
            self.health.notes = "Last run succeeded."
