from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ListingRecord:
    apn: str
    situs_address: str
    minimum_bid: Optional[float]
    source_artifact_url: str


@dataclass(frozen=True)
class DiscoveredArtifact:
    url: str
    link_text: str
    file_type: str
