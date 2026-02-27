#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from tax_auction.config import BASE_URL, DEFAULT_ARTIFACT_ROOT, DEFAULT_DB_PATH
from tax_auction.pipeline import run_snapshot


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Sacramento tax sale snapshot ingestion")
    parser.add_argument("--base-url", default=BASE_URL)
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--artifact-root", type=Path, default=DEFAULT_ARTIFACT_ROOT)
    args = parser.parse_args()

    result = run_snapshot(db_path=args.db_path, artifact_root=args.artifact_root, base_url=args.base_url)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
