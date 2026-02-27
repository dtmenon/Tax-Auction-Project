from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from .config import REQUEST_TIMEOUT_SECONDS, USER_AGENT
from .models import DiscoveredArtifact


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._in_anchor = False
        self._current_href = ""
        self._current_text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        attr_map = {k.lower(): (v or "") for k, v in attrs}
        href = attr_map.get("href", "").strip()
        if href:
            self._in_anchor = True
            self._current_href = href
            self._current_text_parts = []

    def handle_data(self, data: str) -> None:
        if self._in_anchor:
            self._current_text_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._in_anchor:
            text = " ".join("".join(self._current_text_parts).split())
            self.links.append((self._current_href, text))
            self._in_anchor = False
            self._current_href = ""
            self._current_text_parts = []


def _fetch_bytes(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        return response.read()


def fetch_html(url: str) -> str:
    return _fetch_bytes(url).decode("utf-8", errors="replace")


def discover_artifacts(base_url: str, html: str) -> list[DiscoveredArtifact]:
    parser = _LinkParser()
    parser.feed(html)
    artifacts: list[DiscoveredArtifact] = []
    for href, text in parser.links:
        full_url = urljoin(base_url, href)
        path = urlparse(full_url).path.lower()
        file_type = "html"
        if path.endswith(".pdf"):
            file_type = "pdf"
        elif path.endswith(".csv"):
            file_type = "csv"
        elif path.endswith(".xlsx") or path.endswith(".xls"):
            file_type = "xlsx"
        artifacts.append(DiscoveredArtifact(url=full_url, link_text=text, file_type=file_type))

    dedup: dict[str, DiscoveredArtifact] = {}
    for artifact in artifacts:
        dedup[artifact.url] = artifact
    return list(dedup.values())


def download_artifact(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(_fetch_bytes(url))
