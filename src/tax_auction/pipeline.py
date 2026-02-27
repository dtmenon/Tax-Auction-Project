from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from .config import BASE_URL
from .parser import extract_listings_from_html
from .scraper import discover_artifacts, download_artifact, fetch_html
from .storage import (
    connect,
    get_previous_snapshot_id,
    get_snapshot_apns,
    init_db,
    insert_artifacts,
    insert_change_events,
    insert_listings,
    insert_snapshot,
)


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _sanitize_filename(url: str) -> str:
    keep = [c if c.isalnum() else "_" for c in url]
    return "".join(keep)[:180]


def _build_change_events(current_apns: set[str], previous_apns: set[str]) -> list[tuple[str, str]]:
    new = sorted(current_apns - previous_apns)
    removed = sorted(previous_apns - current_apns)
    still = sorted(current_apns & previous_apns)
    return [(apn, "newly_listed") for apn in new] + [
        (apn, "removed_since_last_snapshot") for apn in removed
    ] + [(apn, "still_listed") for apn in still]


def run_snapshot(db_path: Path, artifact_root: Path, base_url: str = BASE_URL) -> dict[str, int]:
    html = fetch_html(base_url)
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    snapshot_dir = artifact_root / now
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    html_path = snapshot_dir / "source.html"
    html_bytes = html.encode("utf-8")
    html_path.write_bytes(html_bytes)

    artifacts = discover_artifacts(base_url, html)
    local_path_by_url: dict[str, str] = {}
    for artifact in artifacts:
        if artifact.file_type == "html":
            continue
        destination = snapshot_dir / f"{_sanitize_filename(artifact.url)}"
        try:
            download_artifact(artifact.url, destination)
            local_path_by_url[artifact.url] = str(destination)
        except Exception:
            local_path_by_url[artifact.url] = ""

    listings = extract_listings_from_html(html, source_artifact_url=base_url)

    conn = connect(db_path)
    init_db(conn)
    snapshot_id = insert_snapshot(
        conn=conn,
        captured_at=now,
        source_url=base_url,
        html_path=str(html_path),
        html_sha256=_sha256_bytes(html_bytes),
    )
    insert_artifacts(conn, snapshot_id=snapshot_id, artifacts=artifacts, local_path_by_url=local_path_by_url)
    insert_listings(conn, snapshot_id=snapshot_id, listings=listings)

    previous_snapshot_id = get_previous_snapshot_id(conn, snapshot_id)
    current_apns = get_snapshot_apns(conn, snapshot_id)
    previous_apns = get_snapshot_apns(conn, previous_snapshot_id) if previous_snapshot_id else set()
    change_events = _build_change_events(current_apns=current_apns, previous_apns=previous_apns)
    if change_events:
        insert_change_events(conn, snapshot_id=snapshot_id, change_events=change_events)

    return {
        "snapshot_id": snapshot_id,
        "artifacts_discovered": len(artifacts),
        "listings_extracted": len(listings),
        "change_events_emitted": len(change_events),
    }
