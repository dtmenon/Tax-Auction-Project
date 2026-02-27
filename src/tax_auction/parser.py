from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Optional

from .models import ListingRecord

_APN_PATTERN = re.compile(r"\b\d{3}-\d{3,4}-\d{3,4}\b")
_MONEY_PATTERN = re.compile(r"\$?\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)")


class _TableRowParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self._in_tr = False
        self._in_cell = False
        self._current_row: list[str] = []
        self._current_cell_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "tr":
            self._in_tr = True
            self._current_row = []
        elif tag in {"td", "th"} and self._in_tr:
            self._in_cell = True
            self._current_cell_parts = []

    def handle_data(self, data: str) -> None:
        if self._in_cell:
            self._current_cell_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"td", "th"} and self._in_cell:
            cell = " ".join("".join(self._current_cell_parts).split())
            self._current_row.append(cell)
            self._in_cell = False
            self._current_cell_parts = []
        elif tag == "tr" and self._in_tr:
            if self._current_row:
                self.rows.append(self._current_row)
            self._in_tr = False
            self._current_row = []


def _parse_money(value: str) -> Optional[float]:
    match = _MONEY_PATTERN.search(value.replace(" ", ""))
    if not match:
        return None
    return float(match.group(1).replace(",", ""))


def extract_listings_from_html(html: str, source_artifact_url: str) -> list[ListingRecord]:
    parser = _TableRowParser()
    parser.feed(html)
    listings: list[ListingRecord] = []

    for cells in parser.rows:
        if len(cells) < 2:
            continue
        apn = ""
        bid: Optional[float] = None
        address = ""

        for cell in cells:
            apn_match = _APN_PATTERN.search(cell)
            if apn_match and not apn:
                apn = apn_match.group(0)
                continue
            if bid is None and not any(ch.isalpha() for ch in cell):
                parsed_bid = _parse_money(cell)
                if parsed_bid is not None:
                    bid = parsed_bid
                    continue
            if not address and len(cell) > 6:
                address = cell

        if apn:
            listings.append(
                ListingRecord(
                    apn=apn,
                    situs_address=address,
                    minimum_bid=bid,
                    source_artifact_url=source_artifact_url,
                )
            )

    dedup: dict[str, ListingRecord] = {}
    for listing in listings:
        dedup.setdefault(listing.apn, listing)
    return list(dedup.values())
